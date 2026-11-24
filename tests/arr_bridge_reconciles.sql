-- opening + every movement must equal closing, every month
select * from {{ ref('fct_arr_bridge') }}
where abs(opening_arr + coalesce(new_arr,0) + coalesce(acquired_arr,0) + coalesce(expansion_arr,0)
          + coalesce(contraction_arr,0) + coalesce(churn_arr,0) - closing_arr) > 0.01
