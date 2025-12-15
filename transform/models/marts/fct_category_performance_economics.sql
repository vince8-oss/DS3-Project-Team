{{ config(materialized='table') }}

WITH product_categories AS (
    SELECT
        product_category_name AS category_pt,
        product_category_name_english AS category_en
    FROM {{ source('brazilian_sales', 'public-product_category') }}
),

product_sales AS (
    SELECT
        p.product_category_name AS product_category_name,
        COALESCE(pc.category_en, p.product_category_name) AS category_name_english,
        DATE_TRUNC(CAST(o.order_purchase_timestamp AS DATE), MONTH) AS order_month,
        c.customer_state,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) AS total_value,
        ex.indicator_value AS usd_brl_rate
    FROM {{ ref('stg_order_items') }} oi
    INNER JOIN {{ ref('stg_orders') }} o ON oi.order_id = o.order_id
    INNER JOIN {{ ref('stg_products') }} p ON oi.product_id = p.product_id
    INNER JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
    -- Join product category translation table
    LEFT JOIN product_categories pc ON p.product_category_name = pc.category_pt
    LEFT JOIN (
        SELECT indicator_date, indicator_value
        FROM {{ ref('stg_bcb_indicators') }}
        WHERE series_name = 'exchange_rate_usd'
    ) ex ON CAST(o.order_purchase_timestamp AS DATE) = ex.indicator_date
    WHERE o.order_status IN ('delivered', 'shipped', 'approved')
),

category_aggregates AS (
    SELECT
        -- Use English category name, fallback to Portuguese if missing
        category_name_english AS category_name,
        product_category_name AS category_name_pt,
        order_month,
        customer_state,
        COUNT(*) AS order_count,
        ROUND(AVG(total_value), 2) AS avg_order_value_brl,
        ROUND(SUM(total_value), 2) AS total_revenue_brl,
        ROUND(AVG(usd_brl_rate), 4) AS avg_exchange_rate,
        ROUND(SUM(total_value / NULLIF(usd_brl_rate, 0)), 2) AS total_revenue_usd,
        CASE
            WHEN AVG(usd_brl_rate) < 3.5 THEN 'Strong BRL'
            WHEN AVG(usd_brl_rate) BETWEEN 3.5 AND 4.5 THEN 'Moderate BRL'
            ELSE 'Weak BRL'
        END AS exchange_rate_period,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM product_sales
    WHERE product_category_name IS NOT NULL
    GROUP BY
        category_name_english,
        product_category_name,
        order_month,
        customer_state
)

SELECT * FROM category_aggregates
