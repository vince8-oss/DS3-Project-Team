with source as (
    select * from {{ source('olist_raw', 'raw_orders') }}
)
select
    json_value(data, '$.order_id') as order_id,
    json_value(data, '$.customer_id') as customer_id,
    json_value(data, '$.order_status') as order_status,
    timestamp(json_value(data, '$.order_purchase_timestamp')) as order_purchased_at,
    case
        when json_value(data, '$.order_delivered_customer_date') = '' then null
        else timestamp(json_value(data, '$.order_delivered_customer_date'))
    end as order_delivered_at
from source