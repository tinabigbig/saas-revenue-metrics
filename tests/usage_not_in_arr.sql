-- only products the catalog classifies as recurring may reach ARR
select l.*
from {{ ref('int_line_months') }} l
left join {{ ref('product_catalog') }} p on p.product_code = l.product_code
where p.revenue_class is distinct from 'recurring'
