-- fct_arr_monthly must have one row per account per month end
select account_id, month_end, count(*) from {{ ref('fct_arr_monthly') }}
group by 1, 2 having count(*) > 1
