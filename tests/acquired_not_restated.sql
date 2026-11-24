-- no acquired ARR may appear before the close date
select * from {{ ref('fct_arr_monthly') }}
where book = 'acquired' and month_end < date '{{ var("acq_close_date") }}'
