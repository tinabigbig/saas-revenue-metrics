-- one row per approved recurring subscription line, core and acquired together.
-- Gate: a line only reaches ARR if its product is in seeds/product_catalog.csv as 'recurring'.
-- Unknown products are held in int_unclassified_lines until a business owner classifies them.
-- Acquired lines only count from the close date (history is not restated).
with unioned as (
    select * from {{ ref('stg_subscriptions') }}
    union all
    select * from {{ ref('stg_acq_contracts') }}
)
select
    u.*,
    case when u.book = 'acquired'
         then greatest(u.start_date, date '{{ var("acq_close_date") }}')
         else u.start_date end as effective_start
from unioned u
join {{ ref('product_catalog') }} p
  on p.product_code = u.product_code and p.revenue_class = 'recurring'
where not (u.book = 'acquired' and u.end_date < date '{{ var("acq_close_date") }}')
