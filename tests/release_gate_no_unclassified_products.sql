-- release gate: every product in the feed must be classified and approved before publishing
select * from {{ ref('int_unclassified_lines') }}
