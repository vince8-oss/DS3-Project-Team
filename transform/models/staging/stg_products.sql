{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('brazilian_sales', 'public-products') }}
),

cleaned AS (
    SELECT
        -- Primary key
        product_id,
        
        -- Category
        TRIM(product_category_name) AS product_category_name,
        
        -- Product attributes - use SAFE_CAST for numeric fields
        SAFE_CAST(product_name_lenght AS INT64) AS product_name_length,
        SAFE_CAST(product_description_lenght AS INT64) AS product_description_length,
        SAFE_CAST(product_photos_qty AS INT64) AS product_photos_qty,
        
        -- Physical dimensions - critical for data integrity
        SAFE_CAST(product_weight_g AS FLOAT64) AS product_weight_g,
        SAFE_CAST(product_length_cm AS FLOAT64) AS product_length_cm,
        SAFE_CAST(product_height_cm AS FLOAT64) AS product_height_cm,
        SAFE_CAST(product_width_cm AS FLOAT64) AS product_width_cm,
        
        -- Metadata
        CURRENT_TIMESTAMP() AS dbt_loaded_at
        
    FROM source
)

SELECT * FROM cleaned