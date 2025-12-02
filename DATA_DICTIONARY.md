# Brazilian E-Commerce Data Pipeline - Data Dictionary

## Table of Contents

1. [Overview](#overview)
2. [Raw Layer Tables](#raw-layer-tables)
3. [Staging Layer Models](#staging-layer-models)
4. [Warehouse Layer - Dimensions](#warehouse-layer---dimensions)
5. [Warehouse Layer - Facts](#warehouse-layer---facts)
6. [Metadata Tables](#metadata-tables)
7. [Data Types Reference](#data-types-reference)
8. [Business Rules](#business-rules)

---

## Overview

### Dataset Information

- **Source**: Olist Brazilian E-Commerce Public Dataset
- **Dataset URL**: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Time Period**: September 2016 - August 2018
- **Total Records**: ~100,000 orders, ~112,000 order items
- **Geography**: Brazil (all states)

### Layer Structure

```
Raw Layer (staging dataset)
  ↓
Staging Layer (dev_warehouse_staging)
  ↓
Warehouse Layer (dev_warehouse_warehouse)
  ├── Dimensions (4 tables)
  └── Facts (2 tables)
```

---

## Raw Layer Tables

### Dataset: `staging`

Location: BigQuery dataset specified by `BQ_DATASET_RAW` environment variable

---

## 1. orders_raw

**Description**: Raw order header data from e-commerce platform

**Row Count**: ~99,441 orders

**Primary Key**: `order_id`

| Column Name                     | Data Type | Nullable | Description                                  | Example Value                      |
| ------------------------------- | --------- | -------- | -------------------------------------------- | ---------------------------------- |
| `order_id`                      | STRING    | No       | Unique identifier for each order             | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id`                   | STRING    | No       | Foreign key to customer who placed the order | `9ef432eb6251297304e76186b10a928d` |
| `order_status`                  | STRING    | No       | Current status of the order                  | `delivered`, `shipped`, `canceled` |
| `order_purchase_timestamp`      | STRING    | Yes      | Timestamp when order was placed              | `2017-10-02 10:56:33`              |
| `order_approved_at`             | STRING    | Yes      | Timestamp when payment was approved          | `2017-10-02 11:07:15`              |
| `order_delivered_carrier_date`  | STRING    | Yes      | Timestamp when order was handed to logistics | `2017-10-04 19:55:00`              |
| `order_delivered_customer_date` | STRING    | Yes      | Actual delivery timestamp to customer        | `2017-10-10 21:25:13`              |
| `order_estimated_delivery_date` | STRING    | Yes      | Estimated delivery date shown to customer    | `2017-10-18 00:00:00`              |

**Business Rules**:

- One order can have multiple items (1:N with order_items)
- One order can have multiple payments (1:N with payments)
- Order status values: `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`
- Timestamps follow progression: purchase → approved → delivered to carrier → delivered to customer

---

## 2. customers_raw

**Description**: Customer demographic and location information

**Row Count**: ~99,441 customers (unique customers per order)

**Primary Key**: `customer_id`

| Column Name                | Data Type | Nullable | Description                                              | Example Value                      |
| -------------------------- | --------- | -------- | -------------------------------------------------------- | ---------------------------------- |
| `customer_id`              | STRING    | No       | Unique identifier for customer per order                 | `06b8999e2fba1a1fbc88172c00ba8bc7` |
| `customer_unique_id`       | STRING    | No       | True unique customer ID (can have multiple customer_ids) | `861eff4711a542e4b93843c6dd7febb0` |
| `customer_zip_code_prefix` | STRING    | Yes      | First 5 digits of customer postal code                   | `14409`                            |
| `customer_city`            | STRING    | Yes      | Customer city name                                       | `sao paulo`, `rio de janeiro`      |
| `customer_state`           | STRING    | Yes      | Two-letter state code                                    | `SP`, `RJ`, `MG`                   |

**Business Rules**:

- `customer_id` is unique per order but same person can have multiple IDs
- `customer_unique_id` tracks the same person across multiple orders
- Brazilian states use 2-letter codes (e.g., SP=São Paulo, RJ=Rio de Janeiro)
- ZIP codes are truncated to 5 digits for privacy

---

## 3. products_raw

**Description**: Product catalog with physical dimensions

**Row Count**: ~32,951 products

**Primary Key**: `product_id`

| Column Name                  | Data Type | Nullable | Description                             | Example Value                      |
| ---------------------------- | --------- | -------- | --------------------------------------- | ---------------------------------- |
| `product_id`                 | STRING    | No       | Unique product identifier               | `1e9e8ef04dbcff4541ed26657ea517e5` |
| `product_category_name`      | STRING    | Yes      | Category name in Portuguese             | `beleza_saude`, `esporte_lazer`    |
| `product_name_lenght`        | STRING    | Yes      | Character length of product name        | `58`                               |
| `product_description_lenght` | STRING    | Yes      | Character length of product description | `394`                              |
| `product_photos_qty`         | STRING    | Yes      | Number of product photos                | `4`                                |
| `product_weight_g`           | STRING    | Yes      | Product weight in grams                 | `700`                              |
| `product_length_cm`          | STRING    | Yes      | Product package length in cm            | `30`                               |
| `product_height_cm`          | STRING    | Yes      | Product package height in cm            | `10`                               |
| `product_width_cm`           | STRING    | Yes      | Product package width in cm             | `20`                               |

**Business Rules**:

- Dimensions represent package size, not product size
- Weight includes packaging
- Category names are in Portuguese (translated in staging layer)
- Zero values are possible for dimensions (e.g., digital products)

---

## 4. order_items_raw

**Description**: Line items for each order (products purchased)

**Row Count**: ~112,650 order items

**Composite Primary Key**: `order_id` + `order_item_id`

| Column Name           | Data Type | Nullable | Description                                      | Example Value                      |
| --------------------- | --------- | -------- | ------------------------------------------------ | ---------------------------------- |
| `order_id`            | STRING    | No       | Foreign key to orders table                      | `00010242fe8c5a6d1ba2dd792cb16214` |
| `order_item_id`       | STRING    | No       | Sequential item number within order (1, 2, 3...) | `1`                                |
| `product_id`          | STRING    | No       | Foreign key to products table                    | `4244733e06e7ecb4970a6e2683c13e61` |
| `seller_id`           | STRING    | No       | Foreign key to sellers table                     | `48436dade18ac8b2bce089ec2a041202` |
| `shipping_limit_date` | STRING    | Yes      | Seller shipping deadline                         | `2017-09-19 09:45:35`              |
| `price`               | STRING    | Yes      | Item price in Brazilian Reals (BRL)              | `58.90`                            |
| `freight_value`       | STRING    | Yes      | Shipping cost allocated to this item             | `13.29`                            |

**Business Rules**:

- One order can have multiple items (order_item_id starts at 1 for each order)
- Total order value = sum(price + freight_value) for all items
- Freight is allocated per item (not per order)
- Same product can be sold by different sellers at different prices

---

## 5. order_payments_raw

**Description**: Payment transactions for orders

**Row Count**: ~103,886 payment records

**Composite Primary Key**: `order_id` + `payment_sequential`

| Column Name            | Data Type | Nullable | Description                                          | Example Value                         |
| ---------------------- | --------- | -------- | ---------------------------------------------------- | ------------------------------------- |
| `order_id`             | STRING    | No       | Foreign key to orders table                          | `b81ef226f3fe1789b1e8b2acac839d17`    |
| `payment_sequential`   | INTEGER   | No       | Payment sequence number (1, 2, 3 for split payments) | `1`                                   |
| `payment_type`         | STRING    | No       | Payment method used                                  | `credit_card`, `boleto`, `debit_card` |
| `payment_installments` | INTEGER   | Yes      | Number of installments (1 = full payment)            | `10`                                  |
| `payment_value`        | STRING    | Yes      | Payment amount in BRL                                | `141.80`                              |

**Business Rules**:

- One order can have multiple payments (split payment)
- Payment types: `credit_card`, `boleto`, `voucher`, `debit_card`
- Installments common in Brazil (up to 24x for credit cards)
- Total payment value should match total order value

---

## 6. sellers_raw

**Description**: Seller/merchant information and location

**Row Count**: ~3,095 sellers

**Primary Key**: `seller_id`

| Column Name              | Data Type | Nullable | Description                          | Example Value                      |
| ------------------------ | --------- | -------- | ------------------------------------ | ---------------------------------- |
| `seller_id`              | STRING    | No       | Unique seller identifier             | `3442f8959a84dea7ee197c632cb2df15` |
| `seller_zip_code_prefix` | STRING    | Yes      | First 5 digits of seller postal code | `13023`                            |
| `seller_city`            | STRING    | Yes      | Seller city name                     | `campinas`, `sao paulo`            |
| `seller_state`           | STRING    | Yes      | Two-letter state code                | `SP`, `PR`                         |

**Business Rules**:

- Sellers are third-party merchants on Olist marketplace
- One seller can fulfill multiple order items
- Location affects shipping time and cost

---

## 7. order_reviews_raw

**Description**: Customer reviews and ratings for orders

**Row Count**: ~99,224 reviews

**Primary Key**: `review_id`

| Column Name               | Data Type | Nullable | Description                       | Example Value                           |
| ------------------------- | --------- | -------- | --------------------------------- | --------------------------------------- |
| `review_id`               | STRING    | No       | Unique review identifier          | `7bc2406110b926393aa56f80a40eba40`      |
| `order_id`                | STRING    | No       | Foreign key to orders table       | `73fc7af87114b39712e6da79b0a377eb`      |
| `review_score`            | STRING    | Yes      | Rating from 1 (worst) to 5 (best) | `4`                                     |
| `review_comment_title`    | STRING    | Yes      | Review title/summary              | `Satisfeito`                            |
| `review_comment_message`  | STRING    | Yes      | Review text body                  | `Entrega rápida e produto de qualidade` |
| `review_creation_date`    | STRING    | Yes      | When review was written           | `2018-01-18 00:00:00`                   |
| `review_answer_timestamp` | STRING    | Yes      | When seller responded to review   | `2018-01-18 21:46:59`                   |

**Business Rules**:

- One order can have 0 or 1 review (optional)
- Review score: 1 = very dissatisfied, 5 = very satisfied
- Comments are in Portuguese
- Not all reviews have comments (score only)

---

## 8. geolocation_raw

**Description**: Geographic coordinates for Brazilian postal codes

**Row Count**: ~1,000,163 geolocation records

**Composite Key**: `geolocation_zip_code_prefix` + `geolocation_lat` + `geolocation_lng`

| Column Name                   | Data Type | Nullable | Description                   | Example Value |
| ----------------------------- | --------- | -------- | ----------------------------- | ------------- |
| `geolocation_zip_code_prefix` | STRING    | Yes      | First 5 digits of postal code | `01037`       |
| `geolocation_lat`             | STRING    | Yes      | Latitude coordinate           | `-23.545621`  |
| `geolocation_lng`             | STRING    | Yes      | Longitude coordinate          | `-46.639292`  |
| `geolocation_city`            | STRING    | Yes      | City name                     | `sao paulo`   |
| `geolocation_state`           | STRING    | Yes      | Two-letter state code         | `SP`          |

**Business Rules**:

- Multiple lat/lng entries per ZIP code (ZIP code areas, not points)
- Used to calculate delivery distances
- Not currently used in warehouse layer (future enhancement)

---

## 9. product_category_name_translation_raw

**Description**: Translation mapping from Portuguese to English category names

**Row Count**: 71 category translations

**Primary Key**: `product_category_name` (Portuguese)

| Column Name                     | Data Type | Nullable | Description                 | Example Value   |
| ------------------------------- | --------- | -------- | --------------------------- | --------------- |
| `product_category_name`         | STRING    | No       | Category name in Portuguese | `beleza_saude`  |
| `product_category_name_english` | STRING    | No       | Category name in English    | `health_beauty` |

**Business Rules**:

- Used to join with products for English category names
- Some Portuguese categories may not have translations (NULL)
- Categories use snake_case naming

---

## Staging Layer Models

### Dataset: `dev_warehouse_staging`

Location: BigQuery dataset specified by `BQ_DATASET_STAGING` environment variable

**Purpose**: Cleaned and type-cast views on raw data. No business logic or aggregations.

**Materialization**: All staging models are **VIEWS** (virtual tables)

---

## 10. stg_orders

**Description**: Cleaned and type-cast orders data

**Type**: VIEW

**Source**: `orders_raw`

| Column Name                     | Data Type | Nullable | Description               | Transformation          | Example                            |
| ------------------------------- | --------- | -------- | ------------------------- | ----------------------- | ---------------------------------- |
| `order_id`                      | STRING    | No       | Unique order identifier   | Pass-through            | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id`                   | STRING    | No       | Foreign key to customer   | Pass-through            | `9ef432eb6251297304e76186b10a928d` |
| `order_status`                  | STRING    | No       | Order status code         | Pass-through, validated | `delivered`                        |
| `order_purchase_timestamp`      | TIMESTAMP | Yes      | Order placement time      | CAST to TIMESTAMP       | `2017-10-02 10:56:33 UTC`          |
| `order_approved_at`             | TIMESTAMP | Yes      | Payment approval time     | CAST to TIMESTAMP       | `2017-10-02 11:07:15 UTC`          |
| `order_delivered_carrier_date`  | TIMESTAMP | Yes      | Handoff to logistics time | CAST to TIMESTAMP       | `2017-10-04 19:55:00 UTC`          |
| `order_delivered_customer_date` | TIMESTAMP | Yes      | Actual delivery time      | CAST to TIMESTAMP       | `2017-10-10 21:25:13 UTC`          |
| `order_estimated_delivery_date` | TIMESTAMP | Yes      | Estimated delivery        | CAST to TIMESTAMP       | `2017-10-18 00:00:00 UTC`          |

**Tests**:

- ✓ `order_id` is unique and not null
- ✓ `order_status` has accepted values: `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`

---

## 11. stg_customers

**Description**: Cleaned customer data

**Type**: VIEW

**Source**: `customers_raw`

| Column Name                | Data Type | Nullable | Description             | Transformation | Example                            |
| -------------------------- | --------- | -------- | ----------------------- | -------------- | ---------------------------------- |
| `customer_id`              | STRING    | No       | Order-level customer ID | Pass-through   | `06b8999e2fba1a1fbc88172c00ba8bc7` |
| `customer_unique_id`       | STRING    | No       | True customer ID        | Pass-through   | `861eff4711a542e4b93843c6dd7febb0` |
| `customer_zip_code_prefix` | STRING    | Yes      | 5-digit ZIP code        | Pass-through   | `14409`                            |
| `customer_city`            | STRING    | Yes      | City name               | Pass-through   | `sao paulo`                        |
| `customer_state`           | STRING    | Yes      | State code              | Pass-through   | `SP`                               |

**Tests**:

- ✓ `customer_id` is unique and not null

---

## 12. stg_products

**Description**: Cleaned product catalog with type casting and dimension fixes

**Type**: VIEW

**Source**: `products_raw`

| Column Name                  | Data Type | Nullable | Description                 | Transformation          | Example                            |
| ---------------------------- | --------- | -------- | --------------------------- | ----------------------- | ---------------------------------- |
| `product_id`                 | STRING    | No       | Unique product ID           | Pass-through            | `1e9e8ef04dbcff4541ed26657ea517e5` |
| `product_category_name`      | STRING    | Yes      | Category in Portuguese      | Pass-through            | `beleza_saude`                     |
| `product_name_length`        | INT64     | Yes      | Name character count        | CAST to INT64, fix typo | `58`                               |
| `product_description_length` | INT64     | Yes      | Description character count | CAST to INT64, fix typo | `394`                              |
| `product_photos_qty`         | INT64     | Yes      | Number of photos            | CAST to INT64           | `4`                                |
| `product_weight_g`           | FLOAT64   | Yes      | Weight in grams             | CAST to FLOAT64         | `700.0`                            |
| `product_length_cm`          | FLOAT64   | Yes      | Package length              | CAST to FLOAT64         | `30.0`                             |
| `product_height_cm`          | FLOAT64   | Yes      | Package height              | CAST to FLOAT64         | `10.0`                             |
| `product_width_cm`           | FLOAT64   | Yes      | Package width               | CAST to FLOAT64         | `20.0`                             |

**Tests**:

- ✓ `product_id` is unique and not null

**Notes**:

- Fixed typo: `product_name_lenght` → `product_name_length`
- Fixed typo: `product_description_lenght` → `product_description_length`

---

## 13. stg_order_items

**Description**: Cleaned order line items with type casting

**Type**: VIEW

**Source**: `order_items_raw`

| Column Name           | Data Type | Nullable | Description            | Transformation    | Example                            |
| --------------------- | --------- | -------- | ---------------------- | ----------------- | ---------------------------------- |
| `order_id`            | STRING    | No       | Foreign key to order   | Pass-through      | `00010242fe8c5a6d1ba2dd792cb16214` |
| `order_item_id`       | INT64     | No       | Item sequence number   | CAST to INT64     | `1`                                |
| `product_id`          | STRING    | No       | Foreign key to product | Pass-through      | `4244733e06e7ecb4970a6e2683c13e61` |
| `seller_id`           | STRING    | No       | Foreign key to seller  | Pass-through      | `48436dade18ac8b2bce089ec2a041202` |
| `shipping_limit_date` | TIMESTAMP | Yes      | Seller deadline        | CAST to TIMESTAMP | `2017-09-19 09:45:35 UTC`          |
| `price`               | FLOAT64   | Yes      | Item price in BRL      | CAST to FLOAT64   | `58.90`                            |
| `freight_value`       | FLOAT64   | Yes      | Shipping cost          | CAST to FLOAT64   | `13.29`                            |

**Tests**:

- ✓ Composite key (`order_id` + `order_item_id`) is unique
- ✓ Foreign key relationships validated

---

## 14. stg_payments

**Description**: Cleaned payment data

**Type**: VIEW

**Source**: `order_payments_raw`

| Column Name            | Data Type | Nullable | Description          | Transformation  | Example                            |
| ---------------------- | --------- | -------- | -------------------- | --------------- | ---------------------------------- |
| `order_id`             | STRING    | No       | Foreign key to order | Pass-through    | `b81ef226f3fe1789b1e8b2acac839d17` |
| `payment_sequential`   | INTEGER   | No       | Payment sequence     | Pass-through    | `1`                                |
| `payment_type`         | STRING    | No       | Payment method       | Pass-through    | `credit_card`                      |
| `payment_installments` | INTEGER   | Yes      | Installment count    | Pass-through    | `10`                               |
| `payment_value`        | FLOAT64   | Yes      | Payment amount       | CAST to FLOAT64 | `141.80`                           |

**Tests**:

- ✓ Composite key (`order_id` + `payment_sequential`) is unique

---

## 15. stg_sellers

**Description**: Cleaned seller data

**Type**: VIEW

**Source**: `sellers_raw`

| Column Name              | Data Type | Nullable | Description      | Transformation | Example                            |
| ------------------------ | --------- | -------- | ---------------- | -------------- | ---------------------------------- |
| `seller_id`              | STRING    | No       | Unique seller ID | Pass-through   | `3442f8959a84dea7ee197c632cb2df15` |
| `seller_zip_code_prefix` | STRING    | Yes      | 5-digit ZIP      | Pass-through   | `13023`                            |
| `seller_city`            | STRING    | Yes      | City name        | Pass-through   | `campinas`                         |
| `seller_state`           | STRING    | Yes      | State code       | Pass-through   | `SP`                               |

**Tests**:

- ✓ `seller_id` is unique and not null

---

## 16. stg_reviews

**Description**: Cleaned review data with type casting

**Type**: VIEW

**Source**: `order_reviews_raw`

| Column Name               | Data Type | Nullable | Description          | Transformation    | Example                            |
| ------------------------- | --------- | -------- | -------------------- | ----------------- | ---------------------------------- |
| `review_id`               | STRING    | No       | Unique review ID     | Pass-through      | `7bc2406110b926393aa56f80a40eba40` |
| `order_id`                | STRING    | No       | Foreign key to order | Pass-through      | `73fc7af87114b39712e6da79b0a377eb` |
| `review_score`            | INT64     | Yes      | Rating 1-5           | CAST to INT64     | `4`                                |
| `review_comment_title`    | STRING    | Yes      | Comment title        | Pass-through      | `Satisfeito`                       |
| `review_comment_message`  | STRING    | Yes      | Comment text         | Pass-through      | `Entrega rápida...`                |
| `review_creation_date`    | TIMESTAMP | Yes      | Review date          | CAST to TIMESTAMP | `2018-01-18 00:00:00 UTC`          |
| `review_answer_timestamp` | TIMESTAMP | Yes      | Seller response time | CAST to TIMESTAMP | `2018-01-18 21:46:59 UTC`          |

---

## Warehouse Layer - Dimensions

### Dataset: `dev_warehouse_warehouse`

Location: BigQuery dataset specified by `BQ_DATASET_WAREHOUSE` environment variable

**Purpose**: Business-ready dimension tables with derived attributes and aggregations

**Materialization**: All dimensions are **TABLES** (physically stored)

**SCD Type**: Type 1 (overwrite) - full refresh on each run

---

## 17. dim_customer

**Description**: Customer dimension with segmentation and lifetime metrics

**Type**: TABLE (SCD Type 1)

**Grain**: One row per unique customer (customer_id level)

**Source**: `stg_customers` + `stg_orders`

**Row Count**: ~96,096 customers

| Column Name          | Data Type | Nullable | Description                               | Derivation                    | Example                            |
| -------------------- | --------- | -------- | ----------------------------------------- | ----------------------------- | ---------------------------------- |
| `customer_id`        | STRING    | No       | **Primary Key** - Order-level customer ID | From stg_customers            | `06b8999e2fba1a1fbc88172c00ba8bc7` |
| `customer_unique_id` | STRING    | No       | True customer identifier                  | From stg_customers            | `861eff4711a542e4b93843c6dd7febb0` |
| `customer_city`      | STRING    | Yes      | Customer city                             | From stg_customers            | `sao paulo`                        |
| `customer_state`     | STRING    | Yes      | Customer state                            | From stg_customers            | `SP`                               |
| `total_orders`       | INT64     | No       | Lifetime order count                      | COUNT(orders)                 | `3`                                |
| `first_order_date`   | TIMESTAMP | Yes      | Date of first purchase                    | MIN(order_purchase_timestamp) | `2017-01-15 10:23:45 UTC`          |
| `last_order_date`    | TIMESTAMP | Yes      | Date of most recent purchase              | MAX(order_purchase_timestamp) | `2018-03-22 14:56:12 UTC`          |
| `customer_segment`   | STRING    | No       | Loyalty segment                           | Business logic (see below)    | `Loyal`, `Repeat`, `One-time`      |

**Business Logic**:

**Customer Segmentation Rules**:

```sql
CASE
    WHEN total_orders >= 5 THEN 'Loyal'      -- 5+ orders
    WHEN total_orders >= 2 THEN 'Repeat'     -- 2-4 orders
    ELSE 'One-time'                          -- 1 order
END
```

**Tests**:

- ✓ `customer_id` is unique and not null
- ✓ `total_orders` >= 0
- ✓ `customer_segment` has accepted values: `Loyal`, `Repeat`, `One-time`

**Usage**: Join to fact_orders on `customer_id` for customer analysis and segmentation reports

---

## 18. dim_product

**Description**: Product dimension with sales performance metrics

**Type**: TABLE (SCD Type 1)

**Grain**: One row per product

**Source**: `stg_products` + `stg_order_items`

**Row Count**: ~32,951 products

| Column Name                  | Data Type | Nullable | Description                         | Derivation                 | Example                              |
| ---------------------------- | --------- | -------- | ----------------------------------- | -------------------------- | ------------------------------------ |
| `product_id`                 | STRING    | No       | **Primary Key** - Unique product ID | From stg_products          | `1e9e8ef04dbcff4541ed26657ea517e5`   |
| `product_category_name`      | STRING    | Yes      | Category (Portuguese)               | From stg_products          | `beleza_saude`                       |
| `product_name_length`        | INT64     | Yes      | Name character count                | From stg_products          | `58`                                 |
| `product_description_length` | INT64     | Yes      | Description character count         | From stg_products          | `394`                                |
| `product_photos_qty`         | INT64     | Yes      | Photo count                         | From stg_products          | `4`                                  |
| `product_weight_g`           | FLOAT64   | Yes      | Weight in grams                     | From stg_products          | `700.0`                              |
| `product_length_cm`          | FLOAT64   | Yes      | Package length                      | From stg_products          | `30.0`                               |
| `product_height_cm`          | FLOAT64   | Yes      | Package height                      | From stg_products          | `10.0`                               |
| `product_width_cm`           | FLOAT64   | Yes      | Package width                       | From stg_products          | `20.0`                               |
| `total_orders`               | INT64     | No       | Times ordered                       | COUNT(DISTINCT order_id)   | `145`                                |
| `total_revenue`              | FLOAT64   | No       | Lifetime revenue (BRL)              | SUM(price)                 | `8,542.50`                           |
| `sales_tier`                 | STRING    | No       | Performance tier                    | Business logic (see below) | `Best Seller`, `Popular`, `Standard` |

**Business Logic**:

**Sales Tier Rules**:

```sql
CASE
    WHEN total_orders >= 100 THEN 'Best Seller'  -- Top sellers
    WHEN total_orders >= 50  THEN 'Popular'      -- Mid-range
    ELSE 'Standard'                               -- New or low-volume
END
```

**Tests**:

- ✓ `product_id` is unique and not null
- ✓ `total_orders` >= 0
- ✓ `total_revenue` >= 0
- ✓ `sales_tier` has accepted values: `Best Seller`, `Popular`, `Standard`

**Usage**: Join to fact_order_items on `product_id` for product performance analysis

---

## 19. dim_seller

**Description**: Seller dimension with volume metrics

**Type**: TABLE (SCD Type 1)

**Grain**: One row per seller

**Source**: `stg_sellers` + `stg_order_items`

**Row Count**: ~3,095 sellers

| Column Name        | Data Type | Nullable | Description                        | Derivation                 | Example                                      |
| ------------------ | --------- | -------- | ---------------------------------- | -------------------------- | -------------------------------------------- |
| `seller_id`        | STRING    | No       | **Primary Key** - Unique seller ID | From stg_sellers           | `3442f8959a84dea7ee197c632cb2df15`           |
| `seller_city`      | STRING    | Yes      | Seller city                        | From stg_sellers           | `campinas`                                   |
| `seller_state`     | STRING    | Yes      | Seller state                       | From stg_sellers           | `SP`                                         |
| `total_orders`     | INT64     | No       | Orders fulfilled                   | COUNT(DISTINCT order_id)   | `87`                                         |
| `total_items_sold` | INT64     | No       | Items sold count                   | COUNT(\*)                  | `132`                                        |
| `total_revenue`    | FLOAT64   | No       | Lifetime revenue (BRL)             | SUM(price)                 | `12,456.78`                                  |
| `seller_tier`      | STRING    | No       | Volume tier                        | Business logic (see below) | `High Volume`, `Medium Volume`, `Low Volume` |

**Business Logic**:

**Seller Tier Rules**:

```sql
CASE
    WHEN total_items_sold >= 100 THEN 'High Volume'    -- High-volume sellers
    WHEN total_items_sold >= 50  THEN 'Medium Volume'  -- Mid-volume
    ELSE 'Low Volume'                                   -- New or low-volume
END
```

**Tests**:

- ✓ `seller_id` is unique and not null
- ✓ `total_items_sold` >= 0
- ✓ `total_revenue` >= 0
- ✓ `seller_tier` has accepted values: `High Volume`, `Medium Volume`, `Low Volume`

**Usage**: Join to fact_order_items on `seller_id` for seller performance analysis

---

## 20. dim_date

**Description**: Date dimension for time-based analysis

**Type**: TABLE

**Grain**: One row per calendar day

**Source**: Generated using dbt_utils.date_spine

**Row Count**: 1,461 days (2016-01-01 to 2020-01-01)

| Column Name    | Data Type | Nullable | Description                     | Derivation            | Example      |
| -------------- | --------- | -------- | ------------------------------- | --------------------- | ------------ |
| `date_day`     | DATE      | No       | **Primary Key** - Calendar date | Generated date spine  | `2017-10-15` |
| `year`         | INT64     | No       | Year                            | EXTRACT(year)         | `2017`       |
| `quarter`      | INT64     | No       | Quarter (1-4)                   | EXTRACT(quarter)      | `4`          |
| `month`        | INT64     | No       | Month (1-12)                    | EXTRACT(month)        | `10`         |
| `week_of_year` | INT64     | No       | Week number (1-53)              | EXTRACT(week)         | `42`         |
| `day_of_week`  | INT64     | No       | Day of week (1=Sun, 7=Sat)      | EXTRACT(dayofweek)    | `7`          |
| `month_name`   | STRING    | No       | Month name                      | FORMAT_DATE('%B')     | `October`    |
| `day_name`     | STRING    | No       | Day name                        | FORMAT_DATE('%A')     | `Sunday`     |
| `is_weekend`   | BOOLEAN   | No       | Weekend flag                    | day_of_week IN (1, 7) | `true`       |

**Tests**:

- ✓ `date_day` is unique and not null
- ✓ Continuous date range with no gaps

**Usage**: Join to facts on date columns for time-series analysis and reporting

**Future Enhancements**:

- Add fiscal calendar (if different from calendar year)
- Add Brazilian holidays flag
- Add business day calculations

---

## Warehouse Layer - Facts

### Dataset: `dev_warehouse_warehouse`

**Purpose**: Transaction-level fact tables optimized for analytical queries

**Materialization**: **INCREMENTAL TABLES** (append/update new records only)

**Performance**: Partitioned by date, clustered by foreign keys

---

## 21. fact_orders

**Description**: Order-level fact table with aggregated metrics and delivery performance

**Type**: INCREMENTAL TABLE

**Grain**: One row per order

**Source**: `stg_orders` + `stg_order_items` + `stg_payments`

**Row Count**: ~96,478 orders

**Incremental Strategy**: Merge on `order_id`

**Partitioning**: Daily partition on `order_purchase_date`

**Clustering**: `customer_id`, `order_status`

| Column Name                     | Data Type | Nullable | Description                       | Derivation                            | Example                            |
| ------------------------------- | --------- | -------- | --------------------------------- | ------------------------------------- | ---------------------------------- |
| `order_id`                      | STRING    | No       | **Primary Key** - Unique order ID | From stg_orders                       | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id`                   | STRING    | No       | **Foreign Key** to dim_customer   | From stg_orders                       | `9ef432eb6251297304e76186b10a928d` |
| `order_status`                  | STRING    | No       | Order status                      | From stg_orders                       | `delivered`                        |
| `order_purchase_date`           | DATE      | No       | Purchase date (for partitioning)  | DATE(order_purchase_timestamp)        | `2017-10-02`                       |
| `order_purchase_timestamp`      | TIMESTAMP | Yes      | Purchase timestamp                | From stg_orders                       | `2017-10-02 10:56:33 UTC`          |
| `order_approved_at`             | TIMESTAMP | Yes      | Approval timestamp                | From stg_orders                       | `2017-10-02 11:07:15 UTC`          |
| `order_delivered_customer_date` | TIMESTAMP | Yes      | Delivery timestamp                | From stg_orders                       | `2017-10-10 21:25:13 UTC`          |
| `order_estimated_delivery_date` | TIMESTAMP | Yes      | Estimated delivery                | From stg_orders                       | `2017-10-18 00:00:00 UTC`          |
| `total_products`                | INT64     | No       | Distinct product count            | COUNT(DISTINCT product_id)            | `3`                                |
| `total_order_value`             | FLOAT64   | No       | Order subtotal (BRL)              | SUM(price) from order_items           | `189.90`                           |
| `total_freight_value`           | FLOAT64   | No       | Total shipping cost (BRL)         | SUM(freight_value) from order_items   | `23.45`                            |
| `total_payment_value`           | FLOAT64   | No       | Total paid (BRL)                  | SUM(payment_value) from payments      | `213.35`                           |
| `delivery_days`                 | INT64     | Yes      | Actual delivery time              | DAYS(delivered_date - purchase_date)  | `8`                                |
| `delivery_delay_days`           | INT64     | Yes      | Delay vs estimate                 | DAYS(delivered_date - estimated_date) | `-8` (8 days early)                |
| `is_on_time_delivery`           | BOOLEAN   | No       | On-time flag                      | delivered_date <= estimated_date      | `true`                             |

**Business Logic**:

**Metrics Calculation**:

- `total_order_value` = SUM of all item prices (excludes freight)
- `total_freight_value` = SUM of all item freight costs
- `total_payment_value` = Should equal (total_order_value + total_freight_value)
- `delivery_days` = Calendar days from purchase to delivery
- `delivery_delay_days` = Negative means early, positive means late
- `is_on_time_delivery` = TRUE if delivered on or before estimated date

**Incremental Logic**:

```sql
WHERE order_purchase_timestamp > (SELECT MAX(order_purchase_timestamp) FROM {{ this }})
```

**Tests**:

- ✓ `order_id` is unique and not null
- ✓ `customer_id` has valid FK relationship to dim_customer
- ✓ `total_order_value` >= 0
- ✓ `delivery_days` >= 0 (if not null)

**Usage**: Primary fact for order-level analysis, customer behavior, delivery performance

**Query Performance**:

- **Partitioning** on `order_purchase_date` enables fast date range queries
- **Clustering** on `customer_id` optimizes customer analysis queries
- **Clustering** on `order_status` optimizes status filtering

**Example Query**:

```sql
-- Monthly delivered orders
SELECT
    FORMAT_DATE('%Y-%m', order_purchase_date) as month,
    COUNT(*) as orders,
    SUM(total_order_value) as revenue
FROM fact_orders
WHERE order_status = 'delivered'
  AND order_purchase_date BETWEEN '2017-01-01' AND '2017-12-31'
GROUP BY month
ORDER BY month;
```

---

## 22. fact_order_items

**Description**: Order item-level fact table with product and seller details

**Type**: INCREMENTAL TABLE

**Grain**: One row per order item (order_id + order_item_id)

**Source**: `stg_order_items` + `stg_orders`

**Row Count**: ~112,650 order items

**Incremental Strategy**: Merge on `order_item_key` (surrogate key)

**Partitioning**: Daily partition on `shipping_limit_date`

**Clustering**: `product_id`, `seller_id`

| Column Name           | Data Type | Nullable | Description                     | Derivation                     | Example                            |
| --------------------- | --------- | -------- | ------------------------------- | ------------------------------ | ---------------------------------- |
| `order_item_key`      | STRING    | No       | **Primary Key** - Surrogate key | MD5(order_id + order_item_id)  | `a3f4b2c1...`                      |
| `order_id`            | STRING    | No       | **Foreign Key** to fact_orders  | From stg_order_items           | `00010242fe8c5a6d1ba2dd792cb16214` |
| `order_item_id`       | INT64     | No       | Item sequence number            | From stg_order_items           | `1`                                |
| `product_id`          | STRING    | No       | **Foreign Key** to dim_product  | From stg_order_items           | `4244733e06e7ecb4970a6e2683c13e61` |
| `seller_id`           | STRING    | No       | **Foreign Key** to dim_seller   | From stg_order_items           | `48436dade18ac8b2bce089ec2a041202` |
| `customer_id`         | STRING    | No       | **Foreign Key** to dim_customer | From stg_orders (via order_id) | `9ef432eb6251297304e76186b10a928d` |
| `order_status`        | STRING    | No       | Order status                    | From stg_orders (via order_id) | `delivered`                        |
| `shipping_limit_date` | TIMESTAMP | Yes      | Seller deadline                 | From stg_order_items           | `2017-09-19 09:45:35 UTC`          |
| `price`               | FLOAT64   | Yes      | Item price (BRL)                | From stg_order_items           | `58.90`                            |
| `freight_value`       | FLOAT64   | Yes      | Item shipping cost (BRL)        | From stg_order_items           | `13.29`                            |
| `total_item_value`    | FLOAT64   | No       | Item total (BRL)                | price + freight_value          | `72.19`                            |

**Business Logic**:

**Surrogate Key Generation**:

```sql
MD5(CONCAT(order_id, '-', CAST(order_item_id AS STRING)))
```

**Metrics**:

- `total_item_value` = price + freight_value (full cost of item)

**Incremental Logic**:

```sql
WHERE shipping_limit_date > (SELECT MAX(shipping_limit_date) FROM {{ this }})
```

**Tests**:

- ✓ `order_item_key` is unique and not null
- ✓ `order_id` has valid FK relationship to fact_orders
- ✓ `product_id` has valid FK relationship to dim_product
- ✓ `seller_id` has valid FK relationship to dim_seller
- ✓ `price` >= 0, `freight_value` >= 0

**Usage**: Item-level analysis, product performance, seller analysis, basket analysis

**Query Performance**:

- **Partitioning** on `shipping_limit_date` enables fast date range queries
- **Clustering** on `product_id` optimizes product analysis
- **Clustering** on `seller_id` optimizes seller analysis

**Example Query**:

```sql
-- Top 10 products by revenue
SELECT
    p.product_category_name,
    COUNT(*) as items_sold,
    SUM(f.price) as revenue
FROM fact_order_items f
JOIN dim_product p ON f.product_id = p.product_id
WHERE f.order_status = 'delivered'
GROUP BY p.product_category_name
ORDER BY revenue DESC
LIMIT 10;
```

---

## Metadata Tables

### Dataset: `staging`

---

## 23. \_load_metadata

**Description**: Audit trail for all data loads to track idempotency

**Type**: TABLE

**Purpose**: Prevents duplicate loads using MD5 hash tracking

**Created By**: `bigquery_loader.py` ingestion script

| Column Name      | Data Type | Nullable | Description               | Example                                      |
| ---------------- | --------- | -------- | ------------------------- | -------------------------------------------- |
| `file_name`      | STRING    | No       | Name of loaded CSV file   | `olist_orders_dataset.csv`                   |
| `file_path`      | STRING    | No       | Full path to source file  | `/path/to/data/raw/olist_orders_dataset.csv` |
| `file_hash`      | STRING    | No       | MD5 hash of file contents | `a3f4b2c1d5e6f7...`                          |
| `table_name`     | STRING    | No       | Target BigQuery table     | `orders_raw`                                 |
| `row_count`      | INT64     | No       | Number of rows loaded     | `99441`                                      |
| `load_timestamp` | TIMESTAMP | No       | When load completed       | `2024-01-15 10:23:45 UTC`                    |
| `load_status`    | STRING    | No       | Load result status        | `SUCCESS`, `FAILED`                          |
| `error_message`  | STRING    | Yes      | Error details if failed   | `NULL` or error text                         |

**Business Logic**:

**Idempotency Check**:

1. Calculate MD5 hash of CSV file
2. Check if hash exists in `_load_metadata`
3. If exists: Skip load (already processed)
4. If new: Load data and record metadata

**Benefits**:

- Safe to re-run ingestion scripts
- Audit trail of all loads
- Prevents data duplication
- Tracks data lineage

---

## Data Types Reference

### BigQuery Data Types Used

| Data Type   | Description               | Example                   | Storage Size |
| ----------- | ------------------------- | ------------------------- | ------------ |
| `STRING`    | Variable-length text      | `"São Paulo"`             | Variable     |
| `INT64`     | 64-bit integer            | `12345`                   | 8 bytes      |
| `FLOAT64`   | 64-bit floating point     | `123.45`                  | 8 bytes      |
| `BOOLEAN`   | True/false                | `true`, `false`           | 1 byte       |
| `DATE`      | Calendar date             | `2017-10-15`              | 8 bytes      |
| `TIMESTAMP` | Date + time with timezone | `2017-10-15 10:23:45 UTC` | 8 bytes      |

### Type Casting Rules

**Raw → Staging**:

- All timestamp strings → TIMESTAMP
- Numeric strings → INT64 or FLOAT64
- Everything else → STRING (pass-through)

**Staging → Warehouse**:

- Aggregations → INT64 (counts) or FLOAT64 (sums)
- Derived flags → BOOLEAN
- Date extraction → DATE
- Segmentation → STRING (categorical)

---

## Business Rules

### Order Lifecycle

```
created → approved → processing → invoiced → shipped → delivered
                                     ↓
                                 canceled
```

### Brazilian E-Commerce Context

1. **Payment Installments**: Common in Brazil to pay in 2-24 installments
2. **Boleto**: Brazilian payment slip (bank transfer, cash payment)
3. **State Codes**: 27 Brazilian states, each with 2-letter code
4. **ZIP Codes**: 8-digit CEP (Código de Endereçamento Postal), truncated to 5 digits for privacy
5. **Currency**: All amounts in BRL (Brazilian Real, R$)

### Data Quality Rules

**Referential Integrity**:

- Every `order_id` in facts must exist in `stg_orders`
- Every `customer_id` in facts must exist in `dim_customer`
- Every `product_id` in facts must exist in `dim_product`
- Every `seller_id` in facts must exist in `dim_seller`

**Business Logic Validations**:

- Order amounts must be >= 0
- Delivery days must be >= 0 (if not null)
- Review scores must be 1-5
- Customer segments must be: Loyal, Repeat, or One-time
- Sales tiers must be: Best Seller, Popular, or Standard

**Incremental Load Rules**:

- Facts use merge strategy (upsert based on primary key)
- Dimensions use full refresh (SCD Type 1 overwrite)
- Load only records newer than MAX timestamp in target table

---

## Column Naming Conventions

### Prefixes

- `is_` = Boolean flag (e.g., `is_weekend`, `is_on_time_delivery`)
- `total_` = Aggregated sum or count (e.g., `total_orders`, `total_revenue`)
- `customer_` = Customer attribute
- `product_` = Product attribute
- `seller_` = Seller attribute
- `order_` = Order attribute

### Suffixes

- `_id` = Identifier, usually foreign key
- `_key` = Surrogate key (generated)
- `_date` = Date only (no time)
- `_timestamp` = Date + time
- `_value` = Monetary amount
- `_days` = Time duration in days
- `_tier` / `_segment` = Categorical grouping

---

## Query Examples

### 1. Customer Lifetime Value by Segment

```sql
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) as customer_count,
    AVG(c.total_orders) as avg_orders_per_customer,
    SUM(f.total_order_value) as total_revenue,
    AVG(f.total_order_value) as avg_order_value
FROM dim_customer c
JOIN fact_orders f ON c.customer_id = f.customer_id
WHERE f.order_status = 'delivered'
GROUP BY c.customer_segment
ORDER BY total_revenue DESC;
```

### 2. Product Performance by Category

```sql
SELECT
    p.product_category_name,
    p.sales_tier,
    COUNT(DISTINCT p.product_id) as product_count,
    SUM(f.total_item_value) as revenue,
    COUNT(*) as items_sold
FROM dim_product p
JOIN fact_order_items f ON p.product_id = f.product_id
WHERE f.order_status = 'delivered'
GROUP BY p.product_category_name, p.sales_tier
ORDER BY revenue DESC
LIMIT 20;
```

### 3. Delivery Performance by State

```sql
SELECT
    c.customer_state,
    COUNT(*) as total_orders,
    AVG(f.delivery_days) as avg_delivery_days,
    SUM(CASE WHEN f.is_on_time_delivery THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as on_time_pct
FROM fact_orders f
JOIN dim_customer c ON f.customer_id = c.customer_id
WHERE f.order_status = 'delivered'
  AND f.delivery_days IS NOT NULL
GROUP BY c.customer_state
ORDER BY total_orders DESC;
```

### 4. Monthly Sales Trend

```sql
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.order_id) as orders,
    SUM(f.total_order_value) as revenue,
    AVG(f.total_order_value) as avg_order_value
FROM fact_orders f
JOIN dim_date d ON f.order_purchase_date = d.date_day
WHERE f.order_status = 'delivered'
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;
```

### 5. Seller Performance

```sql
SELECT
    s.seller_state,
    s.seller_tier,
    COUNT(DISTINCT s.seller_id) as seller_count,
    SUM(f.total_item_value) as revenue,
    SUM(f.price) as product_revenue,
    SUM(f.freight_value) as freight_revenue
FROM dim_seller s
JOIN fact_order_items f ON s.seller_id = f.seller_id
WHERE f.order_status = 'delivered'
GROUP BY s.seller_state, s.seller_tier
ORDER BY revenue DESC;
```

---

## Appendix: Complete Table List

### By Layer

**Raw Layer (9 tables)**:

1. orders_raw
2. customers_raw
3. products_raw
4. order_items_raw
5. order_payments_raw
6. sellers_raw
7. order_reviews_raw
8. geolocation_raw
9. product_category_name_translation_raw

**Staging Layer (7 views)**: 10. stg_orders 11. stg_customers 12. stg_products 13. stg_order_items 14. stg_payments 15. stg_sellers 16. stg_reviews

**Warehouse Dimensions (4 tables)**: 17. dim_customer 18. dim_product 19. dim_seller 20. dim_date

**Warehouse Facts (2 tables)**: 21. fact_orders 22. fact_order_items

**Metadata (1 table)**: 23. \_load_metadata

**Total**: 23 tables/views

---

## Document Version

- **Version**: 1.0
- **Last Updated**: 2024-01-15
- **Project**: Brazilian E-Commerce Data Pipeline
- **Team**: Group 3 Project Team

---

## Feedback & Updates

This data dictionary should be updated when:

- New columns are added to existing tables
- New tables/views are created
- Business logic changes
- Data types are modified
- New metrics or KPIs are introduced

To update this dictionary, edit this markdown file and commit changes to version control with clear commit messages describing what changed.
