with source as (
    select * from {{ source('olist_raw', 'raw_order_reviews') }}
)
select
    json_value(data, '$.review_id') as review_id,
    json_value(data, '$.order_id') as order_id,
    cast(json_value(data, '$.review_score') as int64) as review_score,
    json_value(data, '$.review_comment_message') as review_comment_message,
    timestamp(json_value(data, '$.review_creation_date')) as review_created_at
from source