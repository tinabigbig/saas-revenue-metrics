-- one row per expiring core seat line (new or renewal) that ends inside the window
with expiring as (
    select * from {{ ref('stg_subscriptions') }}
    where product_code = 'DS' and change_type in ('new', 'renewal')
      and end_date between date '{{ var("window_start") }}' and date '{{ var("window_end") }}'
)
select
    e.subscription_id,
    e.account_id,
    e.end_date,
    e.net_annual_value                 as expiring_arr,
    r.subscription_id                  as renewal_subscription_id,
    coalesce(r.net_annual_value, 0)    as renewed_arr,
    r.subscription_id is not null      as renewed
from expiring e
left join {{ ref('stg_subscriptions') }} r
  on r.account_id = e.account_id and r.product_code = 'DS'
 and r.change_type = 'renewal' and r.start_date = e.end_date + 1
