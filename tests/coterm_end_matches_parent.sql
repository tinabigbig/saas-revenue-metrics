-- a co-termed add-on must end on the same day as its parent line
select c.subscription_id
from {{ ref('stg_subscriptions') }} c
join {{ ref('stg_subscriptions') }} p on p.subscription_id = c.parent_subscription_id
where c.change_type = 'add_on' and c.end_date <> p.end_date
