"""Publish the marts only if the full build and every test pass.

A failed test stops here: nothing is exported, and the last published files stay as they were.
"""
import subprocess, sys, os, datetime, duckdb

target = sys.argv[1] if len(sys.argv) > 1 else "dev"
extra = sys.argv[2:]
run = subprocess.run(["dbt", "build", "--profiles-dir", ".", "--target", target, *extra])
if run.returncode != 0:
    print("BUILD OR TESTS FAILED: nothing published. Resolve the failures above first.")
    sys.exit(1)

db = {"dev": "data/saas.duckdb", "changed": "data/saas_changed.duckdb"}[target]
os.makedirs("published", exist_ok=True)
con = duckdb.connect(db, read_only=True)
for m in ["fct_arr_monthly", "fct_arr_bridge", "fct_contract_acv", "fct_billings_monthly",
          "rpt_billings_vs_arr", "fct_renewals", "fct_nrr", "fct_usage_monthly"]:
    con.sql(f"select * from {m}").write_csv(f"published/{m}.csv")
open("published/PUBLISHED_AT.txt", "w").write(datetime.datetime.now().isoformat(timespec="seconds") + "\n")
print("All tests passed: marts published to published/")
