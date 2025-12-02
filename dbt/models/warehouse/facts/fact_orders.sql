{{ config(
    materialized='incremental',
    unique_key='order_id',
    partition_by={
        "field": "order_purchase_date",
        "data_type": "date",
        "granularity": "day"
    },
    cluster_by=['customer_id', 'order_status']
) }}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
        where order_purchase_timestamp > (select max(order_purchase_timestamp) from {{ this }})
    {% endif %}
),

order_items as (
    select
        order_id,
        count(distinct product_id) as total_products,
        sum(price) as total_price,
        sum(freight_value) as total_freight
    from {{ ref('stg_order_items') }}
    group by 1
),

payments as (
    select
        order_id,
        sum(payment_value) as total_payment_value
    from {{ ref('stg_payments') }}
    group by 1
),

final as (
    select
        o.order_id,
        o.customer_id,
        o.order_status,
        date(o.order_purchase_timestamp) as order_purchase_date,
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        
        coalesce(oi.total_products, 0) as total_products,
        coalesce(oi.total_price, 0) as total_order_value,
        coalesce(oi.total_freight, 0) as total_freight_value,
        coalesce(p.total_payment_value, 0) as total_payment_value,
        
        timestamp_diff(o.order_delivered_customer_date, o.order_purchase_timestamp, day) as delivery_days,
        timestamp_diff(o.order_delivered_customer_date, o.order_estimated_delivery_date, day) as delivery_delay_days,
        
        case 
            when o.order_delivered_customer_date <= o.order_estimated_delivery_date then true 
            else false 
        end as is_on_time_delivery

    from orders o
    left join order_items oi on o.order_id = oi.order_id
    left join payments p on o.order_id = p.order_id
)

select * from final
