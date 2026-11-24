-- one row per account per usage month
select account_id, cast(usage_month as date) as usage_month, credits
from read_csv_auto('{{ var("raw_path") }}/usage.csv')
