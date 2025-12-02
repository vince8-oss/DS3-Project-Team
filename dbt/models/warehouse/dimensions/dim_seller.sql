with sellers as (
    select * from {{ ref('stg_sellers') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

seller_sales as (
    select
        seller_id,
        count(distinct order_id) as total_orders,
        count(product_id) as total_items_sold,
        sum(price) as total_revenue
    from order_items
    group by 1
),

final as (
    select
        s.seller_id,
        s.seller_city,
        s.seller_state,
        coalesce(ss.total_orders, 0) as total_orders,
        coalesce(ss.total_items_sold, 0) as total_items_sold,
        coalesce(ss.total_revenue, 0) as total_revenue,
        case
            when coalesce(ss.total_items_sold, 0) >= 100 then 'High Volume'
            when coalesce(ss.total_items_sold, 0) >= 50 then 'Medium Volume'
            else 'Low Volume'
        end as seller_tier
    from sellers s
    left join seller_sales ss on s.seller_id = ss.seller_id
)

select * from final
