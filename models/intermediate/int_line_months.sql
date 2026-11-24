-- one row per subscription line per month end it is active on
select l.subscription_id, l.account_id, l.product_code, l.book, m.month_end, l.net_annual_value
from {{ ref('int_subscription_lines') }} l
join {{ ref('int_month_ends') }} m
  on l.effective_start <= m.month_end and l.end_date >= m.month_end
