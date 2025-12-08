select
    o.order_id,
    o.customer_id,
    o.order_purchased_at,
    o.order_status,
    count(i.order_item_id) as total_items,
    sum(i.price) as total_order_value,
    sum(i.freight_value) as total_freight
from {{ ref('stg_orders') }} o
left join {{ ref('stg_items') }} i using (order_id)
group by 1, 2, 3, 4