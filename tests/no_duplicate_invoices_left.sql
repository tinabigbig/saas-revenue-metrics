-- the raw feed re-posts rows; after staging, the ledger total must match distinct invoices only
select 1 from (
    select count(*) as n, count(distinct invoice_id) as d from {{ ref('stg_invoices') }}
) where n <> d
