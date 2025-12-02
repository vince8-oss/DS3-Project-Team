with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

customer_orders as (
    select
        customer_id,
        count(order_id) as total_orders,
        min(order_purchase_timestamp) as first_order_date,
        max(order_purchase_timestamp) as last_order_date
    from orders
    group by 1
),

final as (
    select
        c.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        coalesce(co.total_orders, 0) as total_orders,
        co.first_order_date,
        co.last_order_date,
        case
            when coalesce(co.total_orders, 0) >= 5 then 'Loyal'
            when coalesce(co.total_orders, 0) >= 2 then 'Repeat'
            else 'One-time'
        end as customer_segment
    from customers c
    left join customer_orders co on c.customer_id = co.customer_id
)

select * from final
