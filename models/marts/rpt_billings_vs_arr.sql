-- one row per month: why billings and ARR move differently (core book only)
with arr as (
    select month_end, sum(arr) as core_arr
    from {{ ref('fct_arr_monthly') }} where book = 'core' group by 1
),
b as (select * from {{ ref('fct_billings_monthly') }})
select
    a.month_end,
    a.core_arr,
    a.core_arr / 12.0                                              as arr_monthly_run_rate,
    coalesce(b.recurring_billings, 0)                              as recurring_billings,
    sum(coalesce(b.recurring_billings, 0)) over w12                as recurring_billings_ttm,
    avg(a.core_arr) over w12                                       as avg_core_arr_ttm
from arr a
left join b on b.month_end = a.month_end
where a.month_end between date '{{ var("window_start") }}' and date '{{ var("window_end") }}'
window w12 as (order by a.month_end rows between 11 preceding and current row)
