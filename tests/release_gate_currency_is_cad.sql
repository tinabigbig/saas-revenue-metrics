-- release gate: every line must be in CAD until an FX rule is approved (see METRIC_DEFINITIONS.md)
select subscription_id, currency
from {{ ref('stg_subscriptions') }}
where currency is distinct from 'CAD'
