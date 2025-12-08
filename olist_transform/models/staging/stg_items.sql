with source as (
    select * from {{ source('olist_raw', 'raw_order_items') }}
)
select
    json_value(data, '$.order_id') as order_id,
    cast(json_value(data, '$.order_item_id') as int64) as order_item_id,
    json_value(data, '$.product_id') as product_id,
    json_value(data, '$.seller_id') as seller_id,
    cast(json_value(data, '$.price') as float64) as price,
    cast(json_value(data, '$.freight_value') as float64) as freight_value
from source