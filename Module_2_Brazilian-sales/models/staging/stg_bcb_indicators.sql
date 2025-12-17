{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('brazilian_sales', 'bcb_economic_indicators') }}
),

cleaned AS (
    SELECT
        data AS indicator_date,
        valor AS indicator_value,
        series_name,
        series_id,
        extracted_at,
        CURRENT_TIMESTAMP() AS dbt_loaded_at
    FROM source
    WHERE 
        valor IS NOT NULL
        AND data IS NOT NULL
)

SELECT * FROM cleaned