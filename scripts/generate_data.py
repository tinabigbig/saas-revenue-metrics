"""Generate a synthetic subscription book for the case study.

Everything here is simulated. The point is to have realistic edge cases
(multi-year deals, co-termed add-ons, usage billing, credit memos, re-posted
invoice rows and an acquired company with its own schema), not realistic totals.
"""
import numpy as np, pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date

rng = np.random.default_rng(42)
OUT = "data/raw"
LIST = {"DS": 2400.0, "AO": 600.0}          # list price per seat per year
CREDIT_PRICE = 0.50                          # per cloud credit, billed monthly in arrears
WINDOW_END = date(2025, 12, 31)
ACQ_CLOSE = date(2025, 4, 1)

subs, invoices, usage = [], [], []
sid, inv = [1000], [50000]

def next_sid():
    sid[0] += 1; return f"S{sid[0]}"

def add_invoice(sub_id, acct, d, amount, kind="recurring"):
    if d > WINDOW_END: return
    inv[0] += 1
    invoices.append(dict(invoice_id=f"I{inv[0]}", subscription_id=sub_id, account_id=acct,
                         invoice_date=d, amount=round(amount, 2), invoice_type=kind))

def bill_line(s):
    """Write the invoices a line produces under its billing frequency."""
    net = s["quantity"] * s["list_price_annual"] * (1 - s["discount_pct"])
    start, end, freq = s["start_date"], s["end_date"], s["billing_frequency"]
    months = s["term_months"]
    if s["change_type"] == "add_on":                      # co-termed: one prorated invoice up front
        add_invoice(s["subscription_id"], s["account_id"], start, net * months / 12); return
    if freq == "upfront_multi_year":
        add_invoice(s["subscription_id"], s["account_id"], start, net * months / 12)
    elif freq == "annual":
        for k in range(0, months, 12):
            add_invoice(s["subscription_id"], s["account_id"], start + relativedelta(months=k), net)
    else:                                                 # monthly
        for k in range(months):
            add_invoice(s["subscription_id"], s["account_id"], start + relativedelta(months=k), net / 12)

for a in range(1, 301):
    acct = f"A{a:04d}"
    start = date(2023, 1, 1) + relativedelta(months=int(rng.integers(0, 36)))
    seats = int(rng.integers(2, 40))
    term = 36 if rng.random() < 0.2 else 12
    freq = "upfront_multi_year" if (term == 36 and rng.random() < 0.5) else ("annual" if rng.random() < 0.7 else "monthly")
    disc = float(rng.choice([0, 0.05, 0.10, 0.15]))
    while start <= WINDOW_END:
        end = start + relativedelta(months=term) - relativedelta(days=1)
        s = dict(subscription_id=next_sid(), account_id=acct, product_code="DS", start_date=start, end_date=end,
                 term_months=term, billing_frequency=freq, quantity=seats, list_price_annual=LIST["DS"],
                 discount_pct=disc, parent_subscription_id="", change_type="new" if not any(x["account_id"] == acct for x in subs) else "renewal")
        subs.append(s); bill_line(s)
        # mid-term add-on, co-termed to the parent end date
        if rng.random() < 0.25 and term >= 12:
            ao_start = start + relativedelta(months=int(rng.integers(2, term - 1)))
            months_left = (end.year - ao_start.year) * 12 + end.month - ao_start.month + 1
            ao = dict(subscription_id=next_sid(), account_id=acct, product_code="AO", start_date=ao_start, end_date=end,
                      term_months=months_left, billing_frequency=freq, quantity=max(1, seats // 2),
                      list_price_annual=LIST["AO"], discount_pct=disc, parent_subscription_id=s["subscription_id"], change_type="add_on")
            subs.append(ao); bill_line(ao)
        if rng.random() > 0.85: break                     # churn at end of term
        start = end + relativedelta(days=1)
        seats = max(1, seats + int(rng.integers(-5, 8)))  # renewal can expand or contract
        term = 12

    if rng.random() < 0.4:                                # usage-based cloud credits
        m = date(2024, 1, 1)
        while m <= date(2025, 11, 1):
            credits = int(rng.gamma(2.0, 400))
            usage.append(dict(account_id=acct, usage_month=m, credits=credits))
            add_invoice("", acct, m + relativedelta(months=1), credits * CREDIT_PRICE, "usage")
            m += relativedelta(months=1)

inv_df = pd.DataFrame(invoices)
# about 3% of invoices get a credit memo for a pricing error
cm = inv_df.sample(frac=0.03, random_state=1)
memos = cm.assign(invoice_id=lambda d: "CM" + d.invoice_id.str[1:],
                  invoice_date=cm.invoice_date.apply(lambda d: d + relativedelta(days=20)),
                  amount=lambda d: (-d.amount * 0.1).round(2), invoice_type="credit_memo")
inv_df = pd.concat([inv_df, memos], ignore_index=True)
inv_df = inv_df[inv_df.invoice_date <= WINDOW_END]
inv_df["loaded_at"] = pd.to_datetime(inv_df.invoice_date) + pd.Timedelta(hours=2)
# about 1% of rows are re-posted by the upstream feed; the later load wins
dup = inv_df.sample(frac=0.01, random_state=2).assign(loaded_at=lambda d: d.loaded_at + pd.Timedelta(days=1))
inv_df = pd.concat([inv_df, dup], ignore_index=True)

# acquired company: its own schema and plan names, monthly fees
acq = []
for c in range(1, 31):
    st = date(2024, 1, 1) + relativedelta(months=int(rng.integers(0, 18)))
    plan = str(rng.choice(["Pro", "Team"]))
    acq.append(dict(contract_ref=f"ACQ-{c:03d}", customer_name=f"AcqCo Customer {c}",
                    plan=plan, seats=int(rng.integers(1, 15)),
                    monthly_fee_per_seat={"Pro": 180.0, "Team": 45.0}[plan], start=st,
                    end=st + relativedelta(months=24) - relativedelta(days=1),
                    billing=str(rng.choice(["MONTHLY", "ANNUAL"]))))

pd.DataFrame(subs).assign(currency="CAD").to_csv(f"{OUT}/subscriptions.csv", index=False)
inv_df.sort_values(["invoice_date", "invoice_id"]).to_csv(f"{OUT}/invoices.csv", index=False)
pd.DataFrame(usage).to_csv(f"{OUT}/usage.csv", index=False)
pd.DataFrame(acq).to_csv(f"{OUT}/acq_contracts.csv", index=False)
print(len(subs), "subscription lines |", len(inv_df), "invoice rows |", len(usage), "usage rows |", len(acq), "acquired contracts")
