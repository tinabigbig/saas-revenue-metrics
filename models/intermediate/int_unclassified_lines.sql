-- one row per subscription line, core or acquired, whose product is unmapped or not in the approved catalog.
-- These are held out of every metric; the release gate test fails while any exist.
with unioned as (
    select * from {{ ref('stg_subscriptions') }}
    union all
    select * from {{ ref('stg_acq_contracts') }}
)
select u.*
from unioned u
left join {{ ref('product_catalog') }} p on p.product_code = u.product_code
where p.product_code is null
