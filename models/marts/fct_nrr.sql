-- one row per month end in 2025: net revenue retention of accounts that had ARR a year earlier
with base as (select account_id, month_end, arr from {{ ref('fct_arr_monthly') }})
select
    cur.month_end,
    sum(prior.arr)                         as cohort_arr_12m_ago,
    sum(coalesce(now_.arr, 0))             as cohort_arr_now,
    sum(coalesce(now_.arr, 0)) / sum(prior.arr) as nrr
from {{ ref('int_month_ends') }} cur
join base prior on prior.month_end = last_day(cur.month_end - interval 12 month)
left join base now_ on now_.account_id = prior.account_id and now_.month_end = cur.month_end
where cur.month_end >= date '2024-12-31'
group by 1
