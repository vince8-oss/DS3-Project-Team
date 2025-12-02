-- FactOrders
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.fact_orders` (
    order_key STRING NOT NULL,
    customer_key STRING NOT NULL,
    order_id STRING NOT NULL,
    customer_id STRING,
    order_status STRING,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    total_order_value FLOAT64,
    total_freight_value FLOAT64,
    total_items INT64,
    delivery_days FLOAT64,
    delivery_delay_days FLOAT64,
    is_on_time BOOLEAN
)
PARTITION BY DATE(order_purchase_timestamp)
CLUSTER BY customer_key, order_status;

-- FactOrderItems
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.fact_order_items` (
    order_item_key STRING NOT NULL,
    order_key STRING NOT NULL,
    product_key STRING NOT NULL,
    seller_key STRING NOT NULL,
    order_id STRING NOT NULL,
    order_item_id INT64,
    product_id STRING,
    seller_id STRING,
    shipping_limit_date TIMESTAMP,
    price FLOAT64,
    freight_value FLOAT64,
    total_item_value FLOAT64
)
PARTITION BY DATE(shipping_limit_date)
CLUSTER BY product_key, seller_key;
