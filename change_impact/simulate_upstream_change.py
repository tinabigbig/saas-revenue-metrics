"""Simulate an upstream release: the billing system adds quarterly billing
and a committed cloud-credit product, starts sending two lines in USD, quietly edits three historical lines,
and the acquired company adds an Enterprise plan with no mapping yet."""
import os, shutil, pandas as pd
src, dst = "data/raw", "data/raw_changed"
shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
s = pd.read_csv(f"{dst}/subscriptions.csv")
s.loc[s.index[-2:], "currency"] = "USD"      # two lines now arrive in USD
new = s[s.product_code == "DS"].tail(5).copy()
new["subscription_id"] = [f"S9{i:03d}" for i in range(5)]
new["product_code"] = "CC_COMMIT"           # committed credits: recurring or usage? a decision is needed
new["billing_frequency"] = "quarterly"
new["list_price_annual"] = 1200.0
new["change_type"] = "add_on"
new["parent_subscription_id"] = s[s.product_code == "DS"].tail(5).subscription_id.values
# the release also quietly re-prices three historical lines
s.loc[s.index[:3], "discount_pct"] = s.loc[s.index[:3], "discount_pct"] + 0.05
pd.concat([s, new]).to_csv(f"{dst}/subscriptions.csv", index=False)
a = pd.read_csv(f"{dst}/acq_contracts.csv")
extra = a.tail(1).copy(); extra["contract_ref"] = "ACQ-099"; extra["plan"] = "Enterprise"   # plan with no mapping yet
pd.concat([a, extra]).to_csv(f"{dst}/acq_contracts.csv", index=False)
print("wrote", dst)
