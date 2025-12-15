{{ config(materialized='table') }}

WITH product_categories AS (
    SELECT
        product_category_name AS category_pt,
        product_category_name_english AS category_en
    FROM {{ source('brazilian_sales', 'public-product_category') }}
),

geographic_sales AS (
    SELECT
        c.customer_state,
        c.customer_city,
        DATE_TRUNC(CAST(o.order_purchase_timestamp AS DATE), MONTH) AS order_month,
        p.product_category_name AS product_category_name,
        COALESCE(pc.category_en, p.product_category_name) AS category_name_english,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) AS total_value,
        ex.indicator_value AS usd_brl_rate
    FROM {{ ref('stg_customers') }} c
    INNER JOIN {{ ref('stg_orders') }} o ON c.customer_id = o.customer_id
    INNER JOIN {{ ref('stg_order_items') }} oi ON o.order_id = oi.order_id
    LEFT JOIN {{ ref('stg_products') }} p ON oi.product_id = p.product_id
    -- Join product category translation table
    LEFT JOIN product_categories pc ON p.product_category_name = pc.category_pt
    LEFT JOIN (
        SELECT indicator_date, indicator_value
        FROM {{ ref('stg_bcb_indicators') }}
        WHERE series_name = 'exchange_rate_usd'
    ) ex ON CAST(o.order_purchase_timestamp AS DATE) = ex.indicator_date
    WHERE o.order_status IN ('delivered', 'shipped', 'approved')
),

state_summary AS (
    SELECT
        customer_state,
        customer_city,
        order_month,
        -- Use English category name, fallback to Portuguese if missing
        category_name_english AS category_name,
        product_category_name AS category_name_pt,
        COUNT(*) AS order_count,
        ROUND(SUM(total_value), 2) AS total_revenue_brl,
        ROUND(AVG(usd_brl_rate), 4) AS avg_exchange_rate,
        ROUND(SUM(total_value / NULLIF(usd_brl_rate, 0)), 2) AS total_revenue_usd,
        CASE
            WHEN AVG(usd_brl_rate) < 3.5 THEN 'Strong BRL'
            ELSE 'Weak BRL'
        END AS currency_strength,
        CURRENT_TIMESTAMP() AS dbt_updated_at
    FROM geographic_sales
    GROUP BY
        customer_state,
        customer_city,
        order_month,
        category_name_english,
        product_category_name
)

SELECT * FROM state_summary
