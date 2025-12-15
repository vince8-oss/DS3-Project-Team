{% test expect_valid_numeric_type(model, column_name) %}

WITH source_data AS (
    SELECT 
        {{ column_name }}
    FROM {{ model }}
),

validation AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT({{ column_name }}) AS valid_numeric_rows,
        COUNT(*) - COUNT({{ column_name }}) AS invalid_rows
    FROM source_data
)

SELECT 
    'Data type violation detected' AS error_message,
    invalid_rows,
    total_rows
FROM validation
WHERE invalid_rows > 0

{% endtest %}