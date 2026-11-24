-- one row per invoice. The feed re-posts some rows; the latest load wins.
with ranked as (
    select *,
           row_number() over (partition by invoice_id order by loaded_at desc) as rn
    from read_csv_auto('{{ var("raw_path") }}/invoices.csv')
)
select
    invoice_id,
    nullif(cast(subscription_id as varchar), '') as subscription_id,
    account_id,
    cast(invoice_date as date) as invoice_date,
    amount,
    invoice_type
from ranked
where rn = 1
