# Brazilian E-Commerce Data Pipeline

## NTU DS3 Project

A complete modern data engineering solution using the Olist Brazilian E-Commerce dataset, demonstrating end-to-end ELT pipeline implementation with cloud-native technologies.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [dbt Models](#dbt-models)
- [Data Quality](#data-quality)
- [Analytics](#analytics)
- [Orchestration](#orchestration)
- [Future Enhancements](#future-enhancements)

---

## Overview

This project implements a production-ready ELT (Extract, Load, Transform) data pipeline that:

✅ **Extracts** Brazilian e-commerce data from Kaggle
✅ **Loads** raw CSV files into Google BigQuery with idempotent deduplication
✅ **Transforms** raw data into a star schema using dbt (staging → warehouse layers)
✅ **Validates** data quality through automated dbt tests
✅ **Orchestrates** the entire pipeline using Dagster
✅ **Analyzes** data using Jupyter notebooks

**Business Goal:** Transform raw e-commerce transactions into a clean, queryable data warehouse to enable insights about customer behavior, sales performance, and logistics efficiency.

**Dataset:** [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle (~100k orders from 2016-2018)

---

## Architecture

### High-Level Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Kaggle    │────▶│   Python     │────▶│  BigQuery   │────▶│     dbt      │
│  (Source)   │     │  Ingestion   │     │ (Raw Data)  │     │(Transforms)  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                    ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
                    │   Jupyter    │◀────│  BigQuery   │◀────│  dbt Tests   │
                    │  Notebooks   │     │ (Warehouse) │     │  (Quality)   │
                    └──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Dagster    │ (Orchestrates entire pipeline)
                    └──────────────┘
```

### Data Flow Layers

1. **Ingestion Layer** (Python)

   - Downloads dataset from Kaggle API
   - Uploads raw CSVs to Google Cloud Storage (optional archiving)
   - Loads data into BigQuery raw tables with MD5-based deduplication

2. **Staging Layer** (dbt views)

   - Cleans and standardizes raw data
   - Type casting and basic transformations
   - 7 staging models

3. **Warehouse Layer** (dbt tables)

   - Star schema: 4 dimensions + 2 facts
   - Business logic and metrics
   - Partitioning & clustering for performance

4. **Quality Layer** (dbt tests)

   - Uniqueness, referential integrity, null checks
   - Business rule validations

5. **Analytics Layer** (Jupyter)
   - Exploratory data analysis
   - Business insights and visualizations

---

## Technology Stack

| Component           | Technology                  | Purpose                              |
| ------------------- | --------------------------- | ------------------------------------ |
| **Language**        | Python 3.9+                 | Pipeline orchestration and ingestion |
| **Data Warehouse**  | Google BigQuery             | Serverless, scalable data warehouse  |
| **Storage**         | Google Cloud Storage        | Raw data staging and archiving       |
| **Transformation**  | dbt-bigquery                | SQL-based data transformations       |
| **Orchestration**   | Dagster                     | Pipeline scheduling and monitoring   |
| **Data Source**     | Kaggle API                  | Brazilian E-Commerce dataset         |
| **Analytics**       | Jupyter, Pandas, Matplotlib | Data analysis and visualization      |
| **Version Control** | Git/GitHub                  | Source code management               |

---

## Project Structure

```
DS3-Project-Team/
├── .env.example                 # Environment configuration template
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── data/                        # Local data directory (gitignored)
│   └── raw/                     # Downloaded CSV files
│
├── dbt/                         # dbt project
│   ├── dbt_project.yml          # dbt configuration
│   ├── profiles.yml             # BigQuery connection config
│   ├── packages.yml             # dbt_utils dependency
│   │
│   └── models/
│       ├── staging/             # 7 staging models (views)
│       │   ├── stg_orders.sql
│       │   ├── stg_customers.sql
│       │   ├── stg_products.sql
│       │   ├── stg_order_items.sql
│       │   ├── stg_payments.sql
│       │   ├── stg_sellers.sql
│       │   ├── stg_reviews.sql
│       │   ├── sources.yml      # Source table definitions
│       │   └── schema.yml       # Tests
│       │
│       └── warehouse/           # Star schema models
│           ├── dimensions/      # 4 dimension tables
│           │   ├── dim_customer.sql
│           │   ├── dim_product.sql
│           │   ├── dim_seller.sql
│           │   └── dim_date.sql
│           │
│           ├── facts/           # 2 fact tables (incremental)
│           │   ├── fact_orders.sql
│           │   └── fact_order_items.sql
│           │
│           └── schema.yml       # Tests
│
├── docs/                        # Project documentation
│   ├── architecture.md          # Architecture diagram
│   └── project_report.md        # Project report
│
├── notebooks/                   # Jupyter notebooks
│   └── analysis.ipynb           # Exploratory data analysis
│
├── orchestration/               # Dagster orchestration
│   ├── __init__.py
│   ├── definitions.py           # Main Dagster definitions
│   └── assets/
│       ├── __init__.py
│       ├── ingestion.py         # Ingestion assets
│       └── dbt.py               # dbt assets
│
└── src/                         # Python source code
    ├── __init__.py
    ├── ingestion/               # Data ingestion modules
    │   ├── __init__.py
    │   ├── kaggle_downloader.py # Download from Kaggle
    │   ├── gcs_uploader.py      # Upload to GCS
    │   └── bigquery_loader.py   # Load to BigQuery
    │
    └── utils/                   # Utility modules
        ├── __init__.py
        └── config.py            # Configuration management
```

---

## Setup Instructions

### Prerequisites

1. **Google Cloud Platform Account**

   - Create a GCP project
   - Enable BigQuery API
   - Enable Cloud Storage API (optional)
   - Create a service account with BigQuery Admin role
   - Download service account JSON key

2. **Kaggle Account**

   - Create account at [kaggle.com](https://www.kaggle.com)
   - Go to Account settings → API → "Create New API Token"
   - This downloads `kaggle.json` with your credentials

3. **Python 3.9+**
   - Install Python from [python.org](https://www.python.org)

### Installation Steps

#### 1. Clone Repository

```bash
git clone https://github.com/azniosman/DS3-Project-Team.git
cd DS3-Project-Team
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**.env file:**

```bash
# Environment
ENVIRONMENT=dev

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Kaggle Credentials
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-api-key

# BigQuery Datasets
BQ_DATASET_RAW=staging
BQ_DATASET_STAGING=dev_warehouse_staging
BQ_DATASET_WAREHOUSE=dev_warehouse_warehouse

# GCS Bucket (optional)
GCS_BUCKET_NAME=your-project-raw-data
```

#### 4. Configure dbt Profile

The `dbt/profiles.yml` is already configured to read from environment variables. Verify it points to your GCP project:

```yaml
brazilian_ecommerce:
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: "{{ env_var('GCP_PROJECT_ID') }}"
      dataset: "{{ env_var('BQ_DATASET_STAGING') }}"
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"
      threads: 4
      timeout_seconds: 300
      location: US
```

#### 5. Install dbt Dependencies

```bash
cd dbt
dbt deps
cd ..
```

---

## Pipeline Walkthrough

### Option 1: Run Complete Pipeline with Dagster (Recommended)

Dagster orchestrates the entire pipeline automatically:

```bash
# Start Dagster web UI
dagster dev -f orchestration/definitions.py

# Open browser to http://localhost:3000
# Navigate to "Assets" → Select all → "Materialize"
```

The pipeline will execute in order:

1. Download dataset from Kaggle
2. Upload to GCS (optional)
3. Load to BigQuery raw tables
4. Run dbt transformations (staging → warehouse)

### Option 2: Run Steps Manually

#### Step 1: Data Ingestion

```bash
# Download dataset from Kaggle
python src/ingestion/kaggle_downloader.py --dataset olistbr/brazilian-ecommerce

# (Optional) Upload to GCS for archiving
python src/ingestion/gcs_uploader.py

# Load to BigQuery (idempotent - safe to run multiple times)
python src/ingestion/bigquery_loader.py --directory data/raw/brazilian-ecommerce
```

**What this creates:**

- 9 raw tables in BigQuery `staging` dataset:
  - `orders_raw`
  - `customers_raw`
  - `products_raw`
  - `order_items_raw`
  - `payments_raw`
  - `sellers_raw`
  - `reviews_raw`
  - `geolocation_raw`
  - `product_category_name_translation_raw`
- `_load_metadata` table tracking all loads with MD5 hashes

#### Step 2: dbt Transformations

```bash
cd dbt

# Run all models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve  # Opens browser to http://localhost:8080
```

**What this creates:**

**Staging Layer** (views in `dev_warehouse_staging`):

- `stg_orders` - Cleaned orders with type casting
- `stg_customers` - Customer data with location
- `stg_products` - Product catalog
- `stg_order_items` - Order line items
- `stg_payments` - Payment details
- `stg_sellers` - Seller information
- `stg_reviews` - Customer reviews

**Warehouse Layer** (tables in `dev_warehouse_warehouse`):

_Dimensions:_

- `dim_customer` - Customer demographics with segmentation (Loyal/Repeat/One-time)
- `dim_product` - Products with categories and sales tiers
- `dim_seller` - Sellers with location and volume tiers
- `dim_date` - Date dimension (2016-2020)

_Facts:_

- `fact_orders` - Order-level metrics (incremental, partitioned by date)
- `fact_order_items` - Item-level details (incremental, partitioned)

#### Step 3: Analytics

```bash
jupyter notebook notebooks/analysis.ipynb
```

The notebook contains:

1. Monthly sales trends
2. Top selling product categories
3. Customer segmentation (RFM analysis)
4. Delivery performance by state

---

## dbt Models

### Staging Models (7 models - Views)

Located in `dbt/models/staging/`

**Purpose:** Clean and standardize raw data

| Model             | Description       | Key Transformations                     |
| ----------------- | ----------------- | --------------------------------------- |
| `stg_orders`      | Order header data | Timestamp parsing, status normalization |
| `stg_customers`   | Customer info     | Location standardization                |
| `stg_products`    | Product catalog   | Category translations                   |
| `stg_order_items` | Order line items  | Price/freight calculations              |
| `stg_payments`    | Payment details   | Type and value normalization            |
| `stg_sellers`     | Seller profiles   | Location standardization                |
| `stg_reviews`     | Customer reviews  | Score normalization                     |

### Warehouse Models (6 models - Tables)

Located in `dbt/models/warehouse/`

#### Dimension Tables

**`dim_customer`** - SCD Type 1

```sql
-- Columns:
- customer_key (surrogate key)
- customer_id
- customer_city, customer_state
- total_orders, total_spent
- customer_segment (Loyal/Repeat/One-time)
- first_order_date, last_order_date
```

**`dim_product`** - SCD Type 1

```sql
-- Columns:
- product_key (surrogate key)
- product_id
- product_category_english
- total_quantity_sold, total_revenue
- product_sales_tier (High/Medium/Low)
```

**`dim_seller`** - SCD Type 1

```sql
-- Columns:
- seller_key (surrogate key)
- seller_id
- seller_city, seller_state
- total_items_sold, total_revenue
- seller_volume_tier (High/Medium/Low)
```

**`dim_date`** - Date Dimension (2016-2020)

```sql
-- Columns:
- date_key
- date_day, date_month, date_year
- day_of_week, month_name
- quarter, is_weekend
```

#### Fact Tables (Incremental)

**`fact_orders`** - Order-level aggregates

```sql
-- Partitioned by: order_purchase_date (daily)
-- Clustered by: customer_key, order_status
-- Incremental strategy: merge on order_id

-- Columns:
- order_key (surrogate)
- customer_key, date_key
- order_id, order_status
- order_purchase_date, delivery_date
- total_order_value, freight_value
- payment_count, item_count
- delivery_time_days, estimated_delivery_days
- is_late_delivery
```

**`fact_order_items`** - Item-level detail

```sql
-- Partitioned by: shipping_limit_date (daily)
-- Incremental strategy: merge on order_id + order_item_id

-- Columns:
- order_item_key (surrogate)
- order_key, product_key, seller_key
- order_id, order_item_id
- price, freight_value
- shipping_limit_date
```

---

## Data Quality

### dbt Tests (30+ tests)

**Staging Layer Tests** (`staging/schema.yml`):

- Primary key uniqueness (all staging models)
- NOT NULL constraints on critical fields
- Referential integrity between tables
- Accepted values for order_status, payment_type

**Warehouse Layer Tests** (`warehouse/schema.yml`):

- Surrogate key uniqueness (all dimensions & facts)
- Foreign key relationships (facts → dimensions)
- Business logic validations:
  - `total_order_value >= 0`
  - `delivery_time_days >= 0`
  - Valid customer segments
  - Valid sales tiers

**Run Tests:**

```bash
cd dbt
dbt test  # Run all tests
dbt test --select staging  # Test staging only
dbt test --select warehouse  # Test warehouse only
```

### Idempotent Loading

The BigQuery loader uses MD5 hashing to prevent duplicate loads:

```python
# Tracks all loads in _load_metadata table
# Checks file hash before loading
# Skips if already loaded
```

**Benefits:**

- Safe to re-run ingestion
- Audit trail of all loads
- Prevents data duplication

---

## Analytics

### Jupyter Notebook (`notebooks/analysis.ipynb`)

**Analysis 1: Monthly Sales Trends**

- Time series of order volume and revenue
- Identifies seasonal patterns

**Analysis 2: Top Product Categories**

- Best-selling categories by revenue
- Category distribution

**Analysis 3: Customer Segmentation**

- RFM (Recency, Frequency, Monetary) analysis
- Identifies Loyal, Repeat, and One-time customers

**Analysis 4: Delivery Performance**

- On-time delivery rate by state
- Average delivery time analysis

**Run Notebook:**

```bash
jupyter notebook notebooks/analysis.ipynb
```

---

## Orchestration

### Dagster

The pipeline is orchestrated using Dagster with daily scheduling.

**Assets:**

1. `kaggle_dataset` - Downloads data
2. `gcs_raw_data` - Uploads to GCS
3. `bigquery_raw_tables` - Loads to BigQuery
4. `dbt_project` - Runs dbt transformations

**Start Dagster:**

```bash
dagster dev -f orchestration/definitions.py
```

**Web UI:** http://localhost:3000

**Features:**

- Dependency management (DAG)
- Asset materialization tracking
- Logging and monitoring
- Daily schedule (00:00)

**Configuration:**

```python
# orchestration/definitions.py
ScheduleDefinition(
    name="daily_pipeline",
    job=daily_job,
    cron_schedule="0 0 * * *",  # Every day at midnight
)
```

---

## Future Enhancements

### Planned Features

1. **Data Marts Layer**

   - `mart_sales_daily` - Daily aggregated sales
   - `mart_sales_monthly` - Monthly KPIs
   - `mart_customer_cohorts` - Cohort analysis

2. **Advanced Analytics**

   - Customer churn prediction (ML)
   - Product recommendation engine
   - Demand forecasting

3. **Dashboards**

   - Looker Studio for business metrics
   - Real-time KPI monitoring

4. **Data Quality**

   - Great Expectations integration
   - Data profiling and anomaly detection

5. **CI/CD**

   - Automated testing on PR
   - dbt Slim CI for changed models only

6. **Incremental Ingestion**
   - Change data capture (CDC)
   - Append-only loading strategy

---

## Key Metrics

**Data Volume:**

- ~100,000 orders
- ~112,000 order items
- ~100,000 customers
- ~3,000 sellers
- ~32,000 products

**Performance:**

- Ingestion: ~2-3 minutes
- dbt Run: ~30 seconds
- End-to-end: ~5 minutes

**Data Quality:**

- 30+ automated tests
- 100% test coverage on primary keys
- Referential integrity validated

---

## Troubleshooting

### Common Issues

**1. dbt connection error:**

```bash
# Verify environment variables are set
echo $GCP_PROJECT_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test BigQuery connection
bq ls
```

**2. Kaggle authentication failed:**

```bash
# Ensure KAGGLE_USERNAME and KAGGLE_KEY are set
# Or place kaggle.json in ~/.kaggle/
```

**3. BigQuery permission denied:**

```bash
# Service account needs BigQuery Admin role
# Or at minimum: BigQuery Data Editor + BigQuery Job User
```

**4. dbt deps fails:**

```bash
cd dbt
dbt clean
dbt deps
```

---

## Contributors

Group 3 Project Team

---

## License

This project is for educational purposes as part of NTU DS3 coursework.

**Dataset License:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) (Olist Brazilian E-Commerce)

---

## References

- [Olist Dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [dbt Documentation](https://docs.getdbt.com/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Dagster Documentation](https://docs.dagster.io/)
