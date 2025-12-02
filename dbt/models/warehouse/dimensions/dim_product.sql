with products as (
    select * from {{ ref('stg_products') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

product_sales as (
    select
        product_id,
        count(order_id) as total_orders,
        sum(price) as total_revenue
    from order_items
    group by 1
),

final as (
    select
        p.product_id,
        p.product_category_name,
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,
        coalesce(ps.total_orders, 0) as total_orders,
        coalesce(ps.total_revenue, 0) as total_revenue,
        case
            when coalesce(ps.total_orders, 0) >= 100 then 'Best Seller'
            when coalesce(ps.total_orders, 0) >= 50 then 'Popular'
            else 'Standard'
        end as sales_tier
    from products p
    left join product_sales ps on p.product_id = ps.product_id
)

select * from final
