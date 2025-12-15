{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('brazilian_sales', 'public-Order_Items') }}
),

cleaned AS (
    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        SAFE_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
        SAFE_CAST(price AS FLOAT64) AS price,
        SAFE_CAST(freight_value AS FLOAT64) AS freight_value,
        CURRENT_TIMESTAMP() AS dbt_loaded_at
    FROM source
)

SELECT * FROM cleaned
