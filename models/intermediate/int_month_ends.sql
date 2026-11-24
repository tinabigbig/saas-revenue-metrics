-- one row per month end, from the opening month (Dec 2023) to the end of the window
select last_day(cast(d as date)) as month_end
from range(date '2023-12-01', date '2026-01-01', interval 1 month) t(d)
