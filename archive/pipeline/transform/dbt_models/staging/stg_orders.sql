{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('brazilian_sales', 'public-orders') }}
),

cleaned AS (
    SELECT
        order_id,
        customer_id,
        TRIM(order_status) AS order_status,
        SAFE_CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        SAFE_CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        SAFE_CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        SAFE_CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        SAFE_CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,
        CURRENT_TIMESTAMP() AS dbt_loaded_at
    FROM source
)

SELECT * FROM cleaned
