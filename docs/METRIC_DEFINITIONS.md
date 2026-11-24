# Metric definitions and treatment decisions

Every metric below says what one row is, what is in scope, and how the hard cases are treated.
When an upstream change creates a case this page does not cover, the decision is made, written here, and only then built.

## ARR (Annual Recurring Revenue)
- **One row:** one account at one month end (`fct_arr_monthly`).
- **Rule:** the annual net value (quantity x list price x (1 - discount)) of every recurring seat line active on the month end.
- **In scope:** seat products DS and AO, core and acquired books.
- **Out of scope:** usage (cloud credits). Usage is reported separately as a run rate (`fct_usage_monthly`), because it is not contracted and moves month to month.
- **Active on the month end:** a line counts if it started on or before the month end and ends on or after it. A line starting mid-month counts from that month's end.

## ARR movements (`fct_arr_bridge`)
Each account's ARR is compared with the prior month end:
| Movement | Rule |
|---|---|
| New | Had no ARR last month, has ARR now (includes win-backs) |
| Acquired | Account from the acquired book appearing in the close month |
| Expansion / contraction | ARR went up / down |
| Churn | Had ARR last month, has none now |

Tests prove opening + movements = closing every month, and each opening equals the prior closing.

## ACV (Annual Contract Value)
- **One row:** one contract line (`fct_contract_acv`).
- **Rule:** total contract value (TCV) divided by contract years. A 36-month deal at $30,000 a year has TCV $90,000 and ACV $30,000.
- **Scope:** core book only. Acquired contracts are not in `fct_contract_acv` yet, because their contract terms (term, discount, signing date) are not in the acquired feed. Acquired ARR is in `fct_arr_monthly`.
- **Co-termed add-ons:** an add-on bought mid-term ends on the parent's end date. Its ACV is its full annual rate, not the prorated amount billed, so ACV stays comparable across add-ons bought at different points in the term. Its TCV is the prorated value.

## Billings
- **Approved billing frequencies:** `seeds/approved_billing_frequencies.csv` (annual, monthly, upfront multi-year). A new frequency, such as quarterly, fails `release_gate_billing_frequency_approved` until its billing schedule and treatment are decided and added.
- **One row:** one month (`fct_billings_monthly`).
- **Rule:** invoiced amounts by invoice date, net of credit memos, from the de-duplicated invoice ledger (the feed re-posts some rows; the latest load wins).
- **Billing schedules:** annual lines bill each year up front, monthly lines bill monthly, multi-year upfront lines bill the full TCV at signing, co-termed add-ons bill once, prorated to the parent end date, usage bills monthly in arrears.
- **Why billings and ARR differ:** upfront and annual billing on a growing book pull billings ahead of ARR (`rpt_billings_vs_arr`).

## Renewals and NRR
- **Renewal (`fct_renewals`):** one row per expiring seat line (new or renewal) ending in the window. Renewed if a renewal line for the same account and product starts the next day. Reported as a **contract-line** renewal rate and an ARR renewal rate (renewed ARR / expiring ARR, so expansions and contractions at renewal are included). This is not a logo rate: an account with two expiries in the window counts twice.
- **NRR (`fct_nrr`):** accounts with ARR 12 months earlier; their ARR now divided by their ARR then. New accounts are excluded; churned accounts count as zero.

## Acquisitions
- The acquired company's contracts are mapped onto our product codes through `seeds/plan_map.csv` (Pro and Team both map to DS).
- **Decision:** acquired ARR counts from the close date (2025-04-01) and shows as its own movement. History is not restated, so pre-close growth is not mixed with organic growth.
- **Known issue:** the acquired book still bills from its own system, so its invoices are not in billings yet. Billings figures are core book only until the billing migration.

## Product approval (release gate)
- `seeds/product_catalog.csv` lists every approved product, its revenue class (recurring or usage), who approved it and when.
- Only `recurring` products reach ARR and ACV. A product missing from the catalog, or an acquired plan missing from `seeds/plan_map.csv`, is held in `int_unclassified_lines` and fails a release test until it is classified. Adding a row to the catalog or plan map is the sign-off.
- Publishing (`scripts/publish.py`) only happens when every test passes.

## Currency
- All metrics are reported in CAD. The subscription feed carries a `currency` column, and `release_gate_currency_is_cad` fails on any other value.
- **Assumption:** the acquired feed has no currency column, so its lines are set to CAD in staging. If the acquired company starts sending a currency column, the change detector flags it as a new column on that feed, and the assumption must be reviewed before the next release.
- **Decision:** if a feed starts carrying another currency, those lines are not converted on the fly. A month-end FX rule (source, rate date, which metrics use which rate) must be approved and written here first. Until then the release gate blocks publishing, and the change detector names the new currency in its report.
