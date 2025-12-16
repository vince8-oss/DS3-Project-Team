{{ config(materialized='table') }}

WITH daily_aggregates AS (
    SELECT
        order_date,

        -- Order metrics
        COUNT(DISTINCT order_id) AS daily_orders,
        COUNT(DISTINCT customer_id) AS daily_customers,

        -- Revenue metrics (BRL)
        SUM(order_value_brl) AS daily_revenue_brl,
        SUM(freight_value_brl) AS daily_freight_brl,
        SUM(total_order_value_brl) AS daily_total_brl,

        -- Revenue metrics (USD)
        SUM(total_order_value_usd) AS daily_revenue_usd,

        -- Average metrics
        AVG(total_order_value_brl) AS avg_order_value_brl,
        AVG(total_order_value_usd) AS avg_order_value_usd,

        -- Economic indicators
        AVG(usd_brl_rate) AS avg_exchange_rate,
        AVG(ipca_month) AS inflation_rate,
        AVG(selic_month) AS interest_rate,

        -- Date parts for analysis
        EXTRACT(YEAR FROM order_date) AS order_year,
        EXTRACT(MONTH FROM order_date) AS order_month,
        EXTRACT(QUARTER FROM order_date) AS order_quarter,
        EXTRACT(DAYOFWEEK FROM order_date) AS day_of_week,
        EXTRACT(WEEK FROM order_date) AS week_of_year,
        FORMAT_DATE('%A', order_date) AS day_name,
        FORMAT_DATE('%B', order_date) AS month_name,

        CURRENT_TIMESTAMP() AS dbt_updated_at

    FROM {{ ref('fct_orders_with_economics') }}
    WHERE order_status IN ('delivered', 'shipped', 'approved')
    GROUP BY order_date
)

SELECT * FROM daily_aggregates
ORDER BY order_date
