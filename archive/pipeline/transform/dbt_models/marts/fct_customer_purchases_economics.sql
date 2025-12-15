{{ config(materialized='table') }}

WITH customers AS (
    SELECT
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state,
        customer_zip_code_prefix
    FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        CAST(order_purchase_timestamp AS DATE) AS order_date,
        order_purchase_timestamp
    FROM {{ ref('stg_orders') }}
    WHERE order_status IN ('delivered', 'shipped', 'approved')
),

order_items AS (
    SELECT
        order_id,
        product_id,
        seller_id,
        price,
        freight_value,
        (price + freight_value) AS total_item_value
    FROM {{ ref('stg_order_items') }}
),

products AS (
    SELECT
        product_id,
        product_category_name,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm
    FROM {{ ref('stg_products') }}
),

-- Economic indicators
exchange_rate AS (
    SELECT
        indicator_date,
        indicator_value AS usd_brl_rate
    FROM {{ ref('stg_bcb_indicators') }}
    WHERE series_name = 'exchange_rate_usd'
),

ipca AS (
    SELECT
        indicator_date,
        indicator_value AS ipca_value
    FROM {{ ref('stg_bcb_indicators') }}
    WHERE series_name = 'ipca'
),

selic AS (
    SELECT
        indicator_date,
        indicator_value AS selic_rate
    FROM {{ ref('stg_bcb_indicators') }}
    WHERE series_name = 'selic'
),

-- Aggregate customer orders
customer_orders AS (
    SELECT
        c.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        c.customer_zip_code_prefix,
        
        o.order_id,
        o.order_date,
        o.order_status,
        
        oi.product_id,
        p.product_category_name,
        oi.price,
        oi.freight_value,
        oi.total_item_value,
        
        -- Economic indicators
        ex.usd_brl_rate,
        ipca.ipca_value AS inflation_rate,
        selic.selic_rate AS interest_rate,
        
        -- Calculate USD values
        ROUND(oi.total_item_value / NULLIF(ex.usd_brl_rate, 0), 2) AS total_item_value_usd,
        
        -- Economic context categories
        CASE
            WHEN ex.usd_brl_rate < 3.5 THEN 'Strong BRL (< 3.5)'
            WHEN ex.usd_brl_rate BETWEEN 3.5 AND 4.5 THEN 'Moderate BRL (3.5-4.5)'
            ELSE 'Weak BRL (> 4.5)'
        END AS exchange_rate_category,
        
        CASE
            WHEN selic.selic_rate < 7 THEN 'Low Interest (< 7%)'
            WHEN selic.selic_rate BETWEEN 7 AND 12 THEN 'Moderate Interest (7-12%)'
            ELSE 'High Interest (> 12%)'
        END AS interest_rate_category,
        
        CURRENT_TIMESTAMP() AS dbt_updated_at
        
    FROM customers c
    INNER JOIN orders o ON c.customer_id = o.customer_id
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN exchange_rate ex ON o.order_date = ex.indicator_date
    LEFT JOIN ipca ON DATE_TRUNC(o.order_date, MONTH) = DATE_TRUNC(ipca.indicator_date, MONTH)
    LEFT JOIN selic ON DATE_TRUNC(o.order_date, MONTH) = DATE_TRUNC(selic.indicator_date, MONTH)
)

SELECT * FROM customer_orders
