# Upstream change impact report

Compared `data/raw_changed` with the saved snapshot.

## subscriptions.csv (read by `stg_subscriptions`)

- New values in `product_code`: CC_COMMIT. Rule affected: ARR scope: only seat products (DS, AO) are recurring; usage must stay out of ARR
- New values in `billing_frequency`: quarterly. Rule affected: billing schedule; unapproved frequencies fail the release gate (seeds/approved_billing_frequencies.csv)
- New values in `currency`: USD. Rule affected: all metrics are reported in CAD; any other currency needs an approved FX rule first
- 3 existing records were edited (history revised), e.g. S1001, S1002, S1003

Downstream models (9): `fct_arr_bridge`, `fct_arr_monthly`, `fct_contract_acv`, `fct_nrr`, `fct_renewals`, `int_line_months`, `int_subscription_lines`, `int_unclassified_lines`, `rpt_billings_vs_arr`

Tests to rerun (18): `acquired_not_restated`, `arr_bridge_chains`, `arr_bridge_reconciles`, `arr_month_one_row_per_account`, `coterm_end_matches_parent`, `not_null_fct_arr_bridge_month_end`, `not_null_fct_contract_acv_subscription_id`, `not_null_fct_renewals_subscription_id`, `not_null_int_subscription_lines_net_annual_value`, `not_null_int_subscription_lines_subscription_id`, `release_gate_billing_frequency_approved`, `release_gate_currency_is_cad`, `release_gate_no_unclassified_products`, `unique_fct_arr_bridge_month_end`, `unique_fct_contract_acv_subscription_id`, `unique_fct_renewals_subscription_id`, `unique_int_subscription_lines_subscription_id`, `usage_not_in_arr`

## acq_contracts.csv (read by `stg_acq_contracts`)

- New values in `plan`: Enterprise. Rule affected: mapping of acquired plans onto our products (seeds/plan_map.csv); unmapped plans fail the release gate
- Total of `seats` moved more than 2%: 269.00 to 277.00

Downstream models (7): `fct_arr_bridge`, `fct_arr_monthly`, `fct_nrr`, `int_line_months`, `int_subscription_lines`, `int_unclassified_lines`, `rpt_billings_vs_arr`

Tests to rerun (13): `acquired_not_restated`, `arr_bridge_chains`, `arr_bridge_reconciles`, `arr_month_one_row_per_account`, `not_null_fct_arr_bridge_month_end`, `not_null_int_subscription_lines_net_annual_value`, `not_null_int_subscription_lines_subscription_id`, `release_gate_acquired_plans_mapped`, `release_gate_billing_frequency_approved`, `release_gate_no_unclassified_products`, `unique_fct_arr_bridge_month_end`, `unique_int_subscription_lines_subscription_id`, `usage_not_in_arr`

## Decisions needed before release
- For each new value: is it recurring (ARR), usage, or one-time? Who signs off?
- Fix upstream, or handle in our staging layer? Record the decision in docs/METRIC_DEFINITIONS.md.
- Rerun `dbt build` on the changed feed and confirm every test passes before publishing.
