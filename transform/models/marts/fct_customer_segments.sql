{{ config(materialized='table') }}

WITH customer_metrics AS (
    SELECT
        customer_unique_id,
        customer_state,
        customer_city,

        -- Date metrics
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date,
        DATE_DIFF(CURRENT_DATE(), MAX(order_date), DAY) AS days_since_last_order,
        DATE_DIFF(MAX(order_date), MIN(order_date), DAY) AS customer_lifespan_days,

        -- Order metrics
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT product_id) AS unique_products_purchased,
        COUNT(DISTINCT product_category_name) AS unique_categories_purchased,

        -- Revenue metrics
        ROUND(SUM(total_item_value), 2) AS total_spent_brl,
        ROUND(SUM(total_item_value_usd), 2) AS total_spent_usd,
        ROUND(AVG(total_item_value_usd), 2) AS avg_order_value_usd,

        -- Calculate average days between orders
        CASE
            WHEN COUNT(DISTINCT order_id) > 1
            THEN DATE_DIFF(MAX(order_date), MIN(order_date), DAY) / NULLIF(COUNT(DISTINCT order_id) - 1, 0)
            ELSE NULL
        END AS avg_days_between_orders,

        -- Economic context of customer
        AVG(usd_brl_rate) AS avg_exchange_rate_experienced,
        AVG(inflation_rate) AS avg_inflation_experienced,
        AVG(interest_rate) AS avg_interest_rate_experienced,

        CURRENT_TIMESTAMP() AS dbt_updated_at

    FROM {{ ref('fct_customer_purchases_economics') }}
    WHERE order_status IN ('delivered', 'shipped', 'approved')
    GROUP BY
        customer_unique_id,
        customer_state,
        customer_city
),

rfm_scores AS (
    SELECT
        *,

        -- RFM Scores (1-5, where 5 is best)
        NTILE(5) OVER (ORDER BY days_since_last_order DESC) AS recency_score,  -- Lower days = better, so DESC
        NTILE(5) OVER (ORDER BY total_orders ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY total_spent_usd ASC) AS monetary_score,

        -- Combined RFM score
        CAST(
            NTILE(5) OVER (ORDER BY days_since_last_order DESC) AS STRING
        ) || CAST(
            NTILE(5) OVER (ORDER BY total_orders ASC) AS STRING
        ) || CAST(
            NTILE(5) OVER (ORDER BY total_spent_usd ASC) AS STRING
        ) AS rfm_score

    FROM customer_metrics
),

customer_segments AS (
    SELECT
        *,

        -- Customer Lifetime Value (simple calculation)
        ROUND(
            (total_spent_usd / NULLIF(customer_lifespan_days, 0)) * 365,
            2
        ) AS annualized_clv_usd,

        -- Predicted next purchase (based on average frequency)
        CASE
            WHEN avg_days_between_orders IS NOT NULL
            THEN DATE_ADD(last_order_date, INTERVAL CAST(avg_days_between_orders AS INT64) DAY)
            ELSE NULL
        END AS predicted_next_purchase_date,

        -- Customer type
        CASE
            WHEN total_orders = 1 THEN 'One-time Buyer'
            WHEN total_orders BETWEEN 2 AND 3 THEN 'Occasional Buyer'
            WHEN total_orders BETWEEN 4 AND 10 THEN 'Regular Customer'
            ELSE 'VIP Customer'
        END AS customer_type,

        -- Customer status
        CASE
            WHEN days_since_last_order <= 90 THEN 'Active'
            WHEN days_since_last_order BETWEEN 91 AND 180 THEN 'At Risk'
            WHEN days_since_last_order BETWEEN 181 AND 365 THEN 'Dormant'
            ELSE 'Churned'
        END AS customer_status,

        -- RFM Segment labels
        CASE
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'Loyal Customers'
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
            WHEN recency_score <= 2 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'At Risk'
            WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost'
            WHEN monetary_score >= 4 THEN 'Big Spenders'
            WHEN recency_score >= 3 AND monetary_score <= 2 THEN 'Promising'
            ELSE 'Need Attention'
        END AS rfm_segment,

        -- Value tier
        CASE
            WHEN total_spent_usd >= PERCENTILE_CONT(total_spent_usd, 0.9) OVER () THEN 'High Value'
            WHEN total_spent_usd >= PERCENTILE_CONT(total_spent_usd, 0.5) OVER () THEN 'Medium Value'
            ELSE 'Low Value'
        END AS value_tier

    FROM rfm_scores
)

SELECT * FROM customer_segments
ORDER BY total_spent_usd DESC
