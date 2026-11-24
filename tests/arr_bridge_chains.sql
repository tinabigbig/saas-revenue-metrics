-- each month's opening ARR must equal the prior month's closing ARR
select * from (
    select month_end, opening_arr, lag(closing_arr) over (order by month_end) as prior_close
    from {{ ref('fct_arr_bridge') }}
) where prior_close is not null and abs(opening_arr - prior_close) > 0.01
