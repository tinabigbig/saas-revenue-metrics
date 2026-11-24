-- one row per acquired contract, mapped onto our product codes and column names
select
    'ACQ' || substr(a.contract_ref, 5)              as subscription_id,
    'X' || substr(a.contract_ref, 5)                as account_id,
    m.product_code,
    cast(a."start" as date)                         as start_date,
    cast(a."end" as date)                           as end_date,
    24                                              as term_months,
    lower(a.billing)                                as billing_frequency,
    a.seats                                         as quantity,
    a.monthly_fee_per_seat * 12                     as list_price_annual,
    0.0                                             as discount_pct,
    cast(null as varchar)                           as parent_subscription_id,
    'acquired'                                      as change_type,
    a.seats * a.monthly_fee_per_seat * 12           as net_annual_value,
    'acquired'                                      as book,
    'CAD'                                           as currency   -- assumption: the acquired feed has no currency column; see METRIC_DEFINITIONS.md
from read_csv_auto('{{ var("raw_path") }}/acq_contracts.csv') a
left join {{ ref('plan_map') }} m on m.acq_plan = a.plan   -- left join: an unmapped plan is kept with a null product and caught by the release gate
