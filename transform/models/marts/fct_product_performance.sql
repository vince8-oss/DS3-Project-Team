{{ config(materialized='table') }}

WITH product_categories AS (
    SELECT
        product_category_name AS category_pt,
        product_category_name_english AS category_en
    FROM {{ source('brazilian_sales', 'public-product_category') }}
),

product_sales AS (
    SELECT
        cp.product_id,
        p.product_category_name AS category_name_pt,
        COALESCE(pc.category_en, p.product_category_name) AS category_name_en,
        DATE_TRUNC(CAST(cp.order_date AS DATE), MONTH) AS order_month,
        cp.order_date,
        cp.price,
        cp.freight_value,
        cp.total_item_value,
        cp.total_item_value_usd,

        -- Product attributes
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,

        -- Calculate volumetric weight (length * height * width / 6000)
        CASE
            WHEN p.product_length_cm IS NOT NULL
                AND p.product_height_cm IS NOT NULL
                AND p.product_width_cm IS NOT NULL
            THEN (p.product_length_cm * p.product_height_cm * p.product_width_cm) / 6000
            ELSE NULL
        END AS volumetric_weight_kg,

        -- Customer info
        cp.customer_state

    FROM {{ ref('fct_customer_purchases_economics') }} cp
    LEFT JOIN {{ ref('stg_products') }} p ON cp.product_id = p.product_id
    LEFT JOIN product_categories pc ON p.product_category_name = pc.category_pt
    WHERE cp.order_status IN ('delivered', 'shipped', 'approved')
),

product_aggregates AS (
    SELECT
        product_id,
        category_name_en AS category_name,
        category_name_pt,

        -- Time aggregations
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date,
        DATE_DIFF(MAX(order_date), MIN(order_date), DAY) AS days_on_platform,

        -- Sales metrics
        COUNT(*) AS total_orders,
        COUNT(DISTINCT order_month) AS months_active,
        COUNT(DISTINCT customer_state) AS states_sold_to,

        -- Revenue metrics
        ROUND(SUM(total_item_value), 2) AS total_revenue_brl,
        ROUND(SUM(total_item_value_usd), 2) AS total_revenue_usd,
        ROUND(AVG(price), 2) AS avg_price_brl,
        ROUND(AVG(total_item_value_usd), 2) AS avg_price_usd,

        -- Freight metrics
        ROUND(SUM(freight_value), 2) AS total_freight_brl,
        ROUND(AVG(freight_value), 2) AS avg_freight_brl,
        ROUND(AVG(freight_value / NULLIF(price, 0)) * 100, 2) AS avg_freight_percentage,

        -- Product attributes (should be same for all orders)
        MAX(product_weight_g) AS product_weight_g,
        MAX(product_length_cm) AS product_length_cm,
        MAX(product_height_cm) AS product_height_cm,
        MAX(product_width_cm) AS product_width_cm,
        MAX(volumetric_weight_kg) AS volumetric_weight_kg,

        -- Performance metrics
        ROUND(SUM(total_item_value_usd) / NULLIF(COUNT(*), 0), 2) AS revenue_per_order,
        ROUND(
            COUNT(*) / NULLIF(
                DATE_DIFF(MAX(order_date), MIN(order_date), DAY),
                0
            ),
            2
        ) AS avg_orders_per_day,

        CURRENT_TIMESTAMP() AS dbt_updated_at

    FROM product_sales
    WHERE product_id IS NOT NULL
    GROUP BY
        product_id,
        category_name_en,
        category_name_pt
),

-- Add ranking within category
ranked_products AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY category_name ORDER BY total_revenue_usd DESC) AS rank_in_category,
        ROW_NUMBER() OVER (ORDER BY total_revenue_usd DESC) AS overall_rank,

        -- Calculate percentile
        PERCENT_RANK() OVER (ORDER BY total_revenue_usd) AS revenue_percentile

    FROM product_aggregates
)

SELECT * FROM ranked_products
ORDER BY total_revenue_usd DESC
