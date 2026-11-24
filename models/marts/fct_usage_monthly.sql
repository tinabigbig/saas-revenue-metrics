-- one row per month: usage billings and a trailing 3-month run rate, reported apart from ARR
with u as (
    select last_day(invoice_date) as month_end, sum(amount) as usage_billings
    from {{ ref('stg_invoices') }} where invoice_type = 'usage' group by 1
)
select month_end, usage_billings,
       avg(usage_billings) over (order by month_end rows between 2 preceding and current row) * 12 as usage_run_rate_annualized
from u
