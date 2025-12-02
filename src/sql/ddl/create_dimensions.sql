-- DimCustomer
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.dim_customer` (
    customer_key STRING NOT NULL, -- Surrogate Key
    customer_id STRING NOT NULL, -- Natural Key
    customer_unique_id STRING,
    customer_city STRING,
    customer_state STRING,
    customer_zip_code_prefix STRING,
    total_orders INT64,
    total_lifetime_value FLOAT64,
    first_order_date TIMESTAMP,
    last_order_date TIMESTAMP,
    avg_delivery_days FLOAT64,
    customer_segment STRING
);

-- DimProduct
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.dim_product` (
    product_key STRING NOT NULL, -- Surrogate Key
    product_id STRING NOT NULL, -- Natural Key
    product_category_name STRING,
    product_category_name_en STRING,
    product_name_length INT64,
    product_description_length INT64,
    product_photos_qty INT64,
    product_weight_g FLOAT64,
    product_length_cm FLOAT64,
    product_height_cm FLOAT64,
    product_width_cm FLOAT64,
    sales_tier STRING
);

-- DimSeller
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.dim_seller` (
    seller_key STRING NOT NULL, -- Surrogate Key
    seller_id STRING NOT NULL, -- Natural Key
    seller_city STRING,
    seller_state STRING,
    seller_zip_code_prefix STRING,
    total_items_sold INT64,
    total_revenue FLOAT64,
    seller_tier STRING
);

-- DimDate (Pre-populated or generated via dbt)
CREATE TABLE IF NOT EXISTS `{{ project_id }}.{{ dataset_id }}.dim_date` (
    date_key STRING NOT NULL,
    date_day DATE NOT NULL,
    year INT64,
    quarter INT64,
    month INT64,
    week_of_year INT64,
    day_of_week INT64,
    month_name STRING,
    day_name STRING,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);
