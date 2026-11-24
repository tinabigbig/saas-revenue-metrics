"""Recompute the headline numbers in pandas, without dbt, and compare to the marts."""
import duckdb, pandas as pd
from datetime import date

raw = "data/raw"
subs = pd.read_csv(f"{raw}/subscriptions.csv", parse_dates=["start_date", "end_date"])
acq = pd.read_csv(f"{raw}/acq_contracts.csv", parse_dates=["start", "end"])
inv = pd.read_csv(f"{raw}/invoices.csv", parse_dates=["invoice_date", "loaded_at"])
con = duckdb.connect("data/saas.duckdb", read_only=True)
CLOSE = pd.Timestamp("2025-04-01")
results = []

def check(name, mine, mart, tol=0.01):
    ok = abs(mine - mart) <= tol
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: pandas={mine:,.2f}  mart={mart:,.2f}")

subs["net"] = subs.quantity * subs.list_price_annual * (1 - subs.discount_pct)
acq["net"] = acq.seats * acq.monthly_fee_per_seat * 12

def arr_at(me):
    me = pd.Timestamp(me)
    core = subs[(subs.start_date <= me) & (subs.end_date >= me)].net.sum()
    a = acq[(acq.start.where(acq.start > CLOSE, CLOSE) <= me) & (acq.end >= me) & (acq.end >= CLOSE)].net.sum()
    return core + a

for me in ["2023-12-31", "2024-12-31", "2025-06-30", "2025-12-31"]:
    mart = con.sql(f"select sum(arr) from fct_arr_monthly where month_end = date '{me}'").fetchall()[0][0]
    check(f"ARR at {me}", arr_at(me), mart)

dedup = inv.sort_values("loaded_at").drop_duplicates("invoice_id", keep="last")
check("Net billings, all months", dedup.amount.sum(), con.sql("select sum(net_billings) from fct_billings_monthly").fetchall()[0][0])
check("Distinct invoices", dedup.invoice_id.nunique(), con.sql("select count(*) from stg_invoices").fetchall()[0][0], 0)

# NRR at Dec 2025: accounts with ARR at Dec 2024, their ARR now over their ARR then
def arr_by_acct(me):
    me = pd.Timestamp(me)
    s = subs[(subs.start_date <= me) & (subs.end_date >= me)].groupby("account_id").net.sum()
    a = acq[(acq.start.where(acq.start > CLOSE, CLOSE) <= me) & (acq.end >= me) & (acq.end >= CLOSE)]
    a = a.assign(account_id="X" + a.contract_ref.str[4:]).groupby("account_id").net.sum()
    return pd.concat([s, a])
then, now = arr_by_acct("2024-12-31"), arr_by_acct("2025-12-31")
nrr = now.reindex(then.index).fillna(0).sum() / then.sum()
check("NRR at 2025-12-31 (x1000)", nrr * 1000, con.sql("select nrr*1000 from fct_nrr where month_end = date '2025-12-31'").fetchall()[0][0])

print(f"\n{sum(results)}/{len(results)} checks pass")
