{{ config(
    materialized='incremental',
    unique_key='order_item_key',
    partition_by={
        "field": "shipping_limit_date",
        "data_type": "timestamp",
        "granularity": "day"
    },
    cluster_by=['product_id', 'seller_id']
) }}

with order_items as (
    select * from {{ ref('stg_order_items') }}
    {% if is_incremental() %}
        where shipping_limit_date > (select max(shipping_limit_date) from {{ this }})
    {% endif %}
),

orders as (
    select order_id, customer_id, order_status from {{ ref('stg_orders') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['oi.order_id', 'oi.order_item_id']) }} as order_item_key,
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,
        o.customer_id,
        o.order_status,
        oi.shipping_limit_date,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) as total_item_value
    from order_items oi
    left join orders o on oi.order_id = o.order_id
)

select * from final
