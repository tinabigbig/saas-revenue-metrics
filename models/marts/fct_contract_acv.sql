-- one row per core contract line: total contract value and ACV.
-- ACV = TCV divided by contract years. A co-termed add-on keeps its annual rate as ACV.
select
    s.subscription_id,
    s.account_id,
    s.product_code,
    change_type,
    billing_frequency,
    term_months,
    net_annual_value * term_months / 12.0                         as tcv,
    case when change_type = 'add_on' then net_annual_value
         else (net_annual_value * term_months / 12.0) / (term_months / 12.0) end as acv,
    start_date
from {{ ref('stg_subscriptions') }} s
join {{ ref('product_catalog') }} p on p.product_code = s.product_code and p.revenue_class = 'recurring'
