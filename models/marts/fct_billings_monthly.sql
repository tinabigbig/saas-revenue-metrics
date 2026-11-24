-- one row per month: invoiced amounts net of credit memos, core book only
-- (the acquired company still bills from its own system; see known issues)
select
    last_day(invoice_date)                                              as month_end,
    sum(case when invoice_type = 'recurring'   then amount else 0 end)  as recurring_billings,
    sum(case when invoice_type = 'usage'       then amount else 0 end)  as usage_billings,
    sum(case when invoice_type = 'credit_memo' then amount else 0 end)  as credit_memos,
    sum(amount)                                                         as net_billings
from {{ ref('stg_invoices') }}
group by 1
