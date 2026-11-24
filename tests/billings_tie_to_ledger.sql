-- monthly billings must add back to the de-duplicated invoice ledger
select 1 from (
    select (select sum(net_billings) from {{ ref('fct_billings_monthly') }}) as mart,
           (select sum(amount) from {{ ref('stg_invoices') }})               as ledger
) where abs(mart - ledger) > 0.01
