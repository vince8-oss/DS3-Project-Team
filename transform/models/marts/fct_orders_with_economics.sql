{{ config(materialized='table') }}

WITH orders AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        CAST(order_purchase_timestamp AS DATE) AS order_date,
        order_purchase_timestamp
    FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT
        order_id,
        SUM(price) AS total_price,
        SUM(freight_value) AS total_freight
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

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

orders_with_economics AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_date,
        o.order_purchase_timestamp,
        
        oi.total_price AS order_value_brl,
        oi.total_freight AS freight_value_brl,
        (oi.total_price + oi.total_freight) AS total_order_value_brl,
        
        ex.usd_brl_rate,
        ROUND((oi.total_price + oi.total_freight) / NULLIF(ex.usd_brl_rate, 0), 2) AS total_order_value_usd,
        
        ipca.ipca_value AS ipca_month,
        selic.selic_rate AS selic_month,
        
        CURRENT_TIMESTAMP() AS dbt_updated_at
        
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN exchange_rate ex ON o.order_date = ex.indicator_date
    LEFT JOIN ipca ON DATE_TRUNC(o.order_date, MONTH) = DATE_TRUNC(ipca.indicator_date, MONTH)
    LEFT JOIN selic ON DATE_TRUNC(o.order_date, MONTH) = DATE_TRUNC(selic.indicator_date, MONTH)
)

SELECT * FROM orders_with_economics