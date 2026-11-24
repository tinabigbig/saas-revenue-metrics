-- release gate: every billing frequency, core or acquired, must be on the approved list
with lines as (
    select subscription_id, billing_frequency from {{ ref('stg_subscriptions') }}
    union all
    select subscription_id, billing_frequency from {{ ref('stg_acq_contracts') }}
)
select l.*
from lines l
left join {{ ref('approved_billing_frequencies') }} a on a.billing_frequency = l.billing_frequency
where a.billing_frequency is null
