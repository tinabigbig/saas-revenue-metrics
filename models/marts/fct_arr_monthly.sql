-- one row per account per month end with recurring ARR. Usage is not ARR.
select
    account_id,
    month_end,
    max(book)                       as book,
    sum(net_annual_value)           as arr
from {{ ref('int_line_months') }}
group by 1, 2
