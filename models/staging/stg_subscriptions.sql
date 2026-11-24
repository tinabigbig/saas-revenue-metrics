-- one row per subscription line from the core billing system
select
    subscription_id,
    account_id,
    product_code,
    cast(start_date as date)                         as start_date,
    cast(end_date as date)                           as end_date,
    term_months,
    billing_frequency,
    quantity,
    list_price_annual,
    discount_pct,
    nullif(cast(parent_subscription_id as varchar), '') as parent_subscription_id,
    change_type,
    quantity * list_price_annual * (1 - discount_pct) as net_annual_value,
    'core'                                           as book,
    currency
from read_csv_auto('{{ var("raw_path") }}/subscriptions.csv', all_varchar = false)
