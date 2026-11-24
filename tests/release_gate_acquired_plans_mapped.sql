-- release gate: every acquired contract must map to one of our products
select subscription_id from {{ ref('stg_acq_contracts') }} where product_code is null
