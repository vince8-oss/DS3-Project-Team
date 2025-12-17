{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('brazilian_sales', 'public-Customers') }}
),

cleaned AS (
    SELECT
        -- Primary key
        customer_id,
        customer_unique_id,
        
        -- Location info
        customer_zip_code_prefix,
        TRIM(customer_city) AS customer_city,
        TRIM(UPPER(customer_state)) AS customer_state,
        
        -- Metadata
        CURRENT_TIMESTAMP() AS dbt_loaded_at
        
    FROM source
)

SELECT * FROM cleaned