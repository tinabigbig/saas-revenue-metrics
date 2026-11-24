"""Detect upstream changes in the raw feeds and list what they touch downstream.

Step 1  compare each raw file with the saved snapshot: columns added or removed,
        and new values in the columns our business rules depend on.
Step 2  walk the dbt lineage (target/manifest.json) from the staging model that
        reads the file, to every model and test downstream.
Step 3  write a review report, plus a prompt file an analyst can hand to an LLM
        (Claude, Copilot) to draft the rule change. This step is LLM-ready, not an
        automated agent: no model is called here, and a person reviews and decides.

Usage:
  python change_impact/detect_changes.py --snapshot            # save today's state
  python change_impact/detect_changes.py --raw data/raw_changed  # compare and report
"""
import argparse, json, os
import pandas as pd

SNAPSHOT = "change_impact/schema_snapshot.json"
# which staging model reads which raw file, and which columns carry business rules
FEEDS = {
    "subscriptions.csv": ("stg_subscriptions", ["product_code", "billing_frequency", "change_type", "currency"]),
    "invoices.csv":      ("stg_invoices",      ["invoice_type"]),
    "usage.csv":         ("stg_usage",         []),
    "acq_contracts.csv": ("stg_acq_contracts", ["plan", "billing", "currency"]),
}
# plain-language note on where each rule column is used, for the report
RULE_NOTES = {
    "currency": "all metrics are reported in CAD; any other currency needs an approved FX rule first",
    "product_code": "ARR scope: only seat products (DS, AO) are recurring; usage must stay out of ARR",
    "billing_frequency": "billing schedule; unapproved frequencies fail the release gate (seeds/approved_billing_frequencies.csv)",
    "change_type": "ACV treatment of co-termed add-ons and the renewal match",
    "invoice_type": "billings split into recurring, usage and credit memos",
    "plan": "mapping of acquired plans onto our products (seeds/plan_map.csv); unmapped plans fail the release gate",
    "billing": "acquired billing frequency, lower-cased in staging",
}

KEYS = {"subscriptions.csv": "subscription_id", "invoices.csv": "invoice_id",
        "usage.csv": None, "acq_contracts.csv": "contract_ref"}

def type_family(t):
    """Name a column type the same way on every pandas version (object, str and string are all text)."""
    t = str(t).lower()
    if t.startswith(("int", "uint")): return "integer"
    if t.startswith("float"): return "decimal"
    if t.startswith("bool"): return "boolean"
    if t.startswith("datetime"): return "datetime"
    return "text"

def profile(raw):
    out = {}
    for f, (_, rule_cols) in FEEDS.items():
        df = pd.read_csv(os.path.join(raw, f))
        num = df.select_dtypes("number")
        key = KEYS[f]
        # a fingerprint of each existing record, so silent edits to history show up
        hashes = ({str(k): str(pd.util.hash_pandas_object(r.drop(labels=[c for c in ["currency"] if c in r]), index=False).sum())
                   for k, r in df.set_index(key, drop=False).iterrows()} if key else {})
        out[f] = {"columns": list(df.columns),
                  "dtypes": {c: type_family(t) for c, t in df.dtypes.items()},
                  "rows": len(df),
                  "null_rate": {c: round(float(df[c].isna().mean()), 4) for c in df.columns},
                  "totals": {c: round(float(num[c].sum()), 2) for c in num.columns},
                  "values": {c: sorted(map(str, df[c].dropna().unique())) for c in rule_cols if c in df},
                  "row_hashes": hashes}
    return out

def data_checks(b, n):
    """Checks beyond schema: volume, types, nulls, totals and changed history."""
    out = []
    if b["rows"] and abs(n["rows"] - b["rows"]) / b["rows"] > 0.05:
        out.append(f"Row count moved more than 5%: {b['rows']} to {n['rows']}")
    for c, t in n["dtypes"].items():
        if c in b["dtypes"] and b["dtypes"][c] != t:
            out.append(f"Type of `{c}` changed: {b['dtypes'][c]} to {t}")
    for c, r in n["null_rate"].items():
        if c in b["null_rate"] and r - b["null_rate"][c] > 0.01:
            out.append(f"Null rate of `{c}` rose: {b['null_rate'][c]:.1%} to {r:.1%}")
    for c, v in n["totals"].items():
        old = b["totals"].get(c)
        if old and abs(v - old) / abs(old) > 0.02:
            out.append(f"Total of `{c}` moved more than 2%: {old:,.2f} to {v:,.2f}")
    revised = [k for k, h in n["row_hashes"].items() if k in b["row_hashes"] and b["row_hashes"][k] != h]
    dropped = [k for k in b["row_hashes"] if k not in n["row_hashes"]]
    if revised: out.append(f"{len(revised)} existing records were edited (history revised), e.g. {', '.join(revised[:3])}")
    if dropped: out.append(f"{len(dropped)} existing records disappeared, e.g. {', '.join(dropped[:3])}")
    return out

def downstream(manifest, model):
    nodes = {n.split(".")[-1]: n for n in manifest["nodes"] if n.startswith("model.")}
    seen, todo = set(), [nodes[model]]
    while todo:
        n = todo.pop()
        for child in manifest["child_map"].get(n, []):
            if child not in seen:
                seen.add(child); todo.append(child)
    models = sorted(c.split(".")[-1] for c in seen if c.startswith("model."))
    tests = sorted(c.split(".")[2] for c in seen if c.startswith("test."))
    return models, tests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--out", default="docs/change_impact_example.md")
    a = ap.parse_args()
    if a.snapshot:
        json.dump(profile(a.raw), open(SNAPSHOT, "w"), indent=2); print("snapshot saved"); return

    before, after = json.load(open(SNAPSHOT)), profile(a.raw)
    manifest = json.load(open("target/manifest.json"))
    lines, prompt_ctx = ["# Upstream change impact report", "", f"Compared `{a.raw}` with the saved snapshot.", ""], []
    for f, (model, _) in FEEDS.items():
        b, n = before[f], after[f]
        added = [c for c in n["columns"] if c not in b["columns"]]
        removed = [c for c in b["columns"] if c not in n["columns"]]
        new_vals = {c: [v for v in vals if v not in b["values"].get(c, [])] for c, vals in n["values"].items() if c not in added}
        new_vals = {c: v for c, v in new_vals.items() if v}
        checks = data_checks(b, n)
        if not (added or removed or new_vals or checks):
            continue
        models, tests = downstream(manifest, model)
        lines += [f"## {f} (read by `{model}`)", ""]
        if added:   lines.append(f"- Columns added: {', '.join(added)}")
        if removed: lines.append(f"- Columns removed: {', '.join(removed)}")
        for c, v in new_vals.items():
            lines.append(f"- New values in `{c}`: {', '.join(v)}. Rule affected: {RULE_NOTES.get(c, 'n/a')}")
        for c in added:
            if c in RULE_NOTES: lines.append(f"- New column `{c}`. Rule affected: {RULE_NOTES[c]}")
        for msg in checks:
            lines.append(f"- {msg}")
        lines += ["", f"Downstream models ({len(models)}): " + ", ".join(f"`{m}`" for m in models),
                  "", f"Tests to rerun ({len(tests)}): " + ", ".join(f"`{t}`" for t in tests), ""]
        prompt_ctx.append(dict(file=f, staging_model=model, added=added, removed=removed,
                               new_values=new_vals, data_checks=checks, downstream_models=models))
    if not prompt_ctx:
        lines += ["No changes detected against the snapshot.", ""]
    lines += ["## Decisions needed before release",
              "- For each new value: is it recurring (ARR), usage, or one-time? Who signs off?",
              "- Fix upstream, or handle in our staging layer? Record the decision in docs/METRIC_DEFINITIONS.md.",
              "- Rerun `dbt build` on the changed feed and confirm every test passes before publishing."]
    open(a.out, "w").write("\n".join(lines) + "\n")
    prompt = ("You are helping a finance data team review an upstream change.\n"
              "Using the change summary and our metric rules in docs/METRIC_DEFINITIONS.md, draft:\n"
              "1) the proposed treatment of each new value in ARR, ACV and billings, with reasons,\n"
              "2) the SQL change to the named staging or mart model,\n"
              "3) the dbt test that would prove the change is right.\n"
              "Mark anything you are unsure about as an open question. A person will review before release.\n\n"
              "Change summary:\n" + json.dumps(prompt_ctx, indent=2))
    open("change_impact/llm_review_prompt.txt", "w").write(prompt)
    print(open(a.out).read())

if __name__ == "__main__":
    main()
