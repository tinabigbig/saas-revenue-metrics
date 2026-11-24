-- one row per month: opening ARR, the movements, closing ARR
with accounts as (select distinct account_id, book from {{ ref('fct_arr_monthly') }}),
grid as (
    select a.account_id, a.book, m.month_end, coalesce(f.arr, 0) as arr
    from accounts a
    cross join {{ ref('int_month_ends') }} m
    left join {{ ref('fct_arr_monthly') }} f
      on f.account_id = a.account_id and f.month_end = m.month_end
),
moves as (
    select *,
           lag(arr) over (partition by account_id order by month_end) as prev_arr
    from grid
),
classified as (
    select month_end, prev_arr, arr,
        case
            when prev_arr = 0 and arr > 0 and book = 'acquired'
                 and month_end = last_day(date '{{ var("acq_close_date") }}') then 'acquired'
            when prev_arr = 0 and arr > 0  then 'new'
            when prev_arr > 0 and arr = 0  then 'churn'
            when arr > prev_arr            then 'expansion'
            when arr < prev_arr            then 'contraction'
            else 'flat'
        end as movement
    from moves
    where prev_arr is not null
)
select
    month_end,
    sum(prev_arr)                                                   as opening_arr,
    sum(case when movement = 'new'         then arr - prev_arr end) as new_arr,
    sum(case when movement = 'acquired'    then arr - prev_arr end) as acquired_arr,
    sum(case when movement = 'expansion'   then arr - prev_arr end) as expansion_arr,
    sum(case when movement = 'contraction' then arr - prev_arr end) as contraction_arr,
    sum(case when movement = 'churn'       then arr - prev_arr end) as churn_arr,
    sum(arr)                                                        as closing_arr
from classified
where month_end between date '{{ var("window_start") }}' and date '{{ var("window_end") }}'
group by 1
