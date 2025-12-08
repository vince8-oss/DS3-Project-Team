# Olist E-Commerce Data Pipeline

## Overview

This project implements an ELT (Extract, Load, Transform) data pipeline for the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) using modern data engineering tools.

The pipeline extracts 9 CSV files from Kaggle, loads them into Google BigQuery using Meltano, and is designed for future transformation with dbt.

**Current Status**:

- ✅ Extract (Kaggle API)
- ✅ Load (Meltano → BigQuery)
- 🔄 Transform (dbt - Pending Implementation)

## Architecture

![Architecture Diagram](sources/architectural_diagram.png)

The pipeline consists of the following stages:

1.  **Extract**: Downloads raw CSV files from Kaggle API using Python SDK.
2.  **Load**: Ingests raw CSV files into Google BigQuery raw tables (`olist_raw` dataset) using Meltano.
3.  **Transform**: (Planned) Uses dbt to model data into staging, fact, and dimension tables.

## Project Structure

```text
.
├── .meltano/                   # Meltano runtime and plugin installations
├── data/
│   └── raw/                    # Local storage for downloaded CSVs
├── notebook/                   # Jupyter notebooks for exploration
│   └── olist_pipeline_nodbt.ipynb
├── plugins/                    # Meltano plugin lock files
│   ├── extractors/
│   │   └── tap-csv--meltanolabs.lock
│   └── loaders/
│       └── target-bigquery--z3z1ma.lock
├── sources/                    # Documentation assets
│   └── architectural_diagram.png
├── src/                        # Source code for pipeline steps
│   ├── extract/                # Data extraction scripts
│   │   ├── __init__.py
│   │   └── kaggle_extract.py   # Kaggle API extraction with SDK fix
│   └── load/                   # Load scripts (placeholder)
│       └── __init__.py
├── .env.example                # Environment variable template
├── meltano.yml                 # Meltano configuration (ELT orchestration)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup & Prerequisites

### 1. Prerequisites

- Python 3.11+
- Google Cloud Platform account with BigQuery enabled
- Kaggle account
- `meltano` CLI installed

### 2. Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Environment
ENVIRONMENT=dev

# Google Cloud Platform (Required)
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# BigQuery Datasets
BQ_DATASET_RAW=olist_raw

# Kaggle API Credentials (Required)
# Get these from https://www.kaggle.com/settings/account
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-api-key
```

**Note**: The Kaggle credentials can also be placed in `~/.kaggle/kaggle.json`:

```json
{
  "username": "your-kaggle-username",
  "key": "your-kaggle-api-key"
}
```

### 3. Installation

1.  Create and activate a virtual environment:

    ```bash
      conda create -n ds3 python=3.11.14 -y
      conda activate ds3
    ```

2.  Install Python dependencies:

    ```bash
    uv pip install -r requirements.txt
    ```

3.  Install Meltano plugins:

    ```bash
    meltano install
    ```

    This will install:

    - `tap-csv` (MeltanoLabs variant) - CSV file extractor
    - `target-bigquery` (z3z1ma variant) - BigQuery loader

## Usage

### Step 1: Extract Data from Kaggle

Download the Olist dataset from Kaggle and save it to `data/raw/`:

```bash
python -m src.extract.kaggle_extract
```

This will:

1. Authenticate with Kaggle API
2. Download the `olistbr/brazilian-ecommerce` dataset
3. Extract 9 CSV files to `data/raw/` directory

**Output**:

```
Authenticating with Kaggle...
Downloading dataset olistbr/brazilian-ecommerce...
Download complete. Moving files...
- Copied olist_sellers_dataset.csv to /path/to/data/raw
- Copied product_category_name_translation.csv to /path/to/data/raw
...
Successfully extracted 9 files to /path/to/data/raw
```

### Step 2: Load Data to BigQuery

Load all CSV files into BigQuery using Meltano:

```bash
meltano run tap-csv target-bigquery
```

**Alternative**: Load a specific table only:

```bash
meltano run tap-csv target-bigquery --select raw_customers
```

**Meltano Configuration** (from `meltano.yml`):

- **Extractor**: `tap-csv` (MeltanoLabs) - reads CSV files from `data/raw/`
- **Loader**: `target-bigquery` (z3z1ma) - loads into BigQuery `olist_raw` dataset
- **Batch Size**: 500 rows per batch
- **Max Workers**: 4 concurrent workers
- **Timeout**: 600 seconds

### Step 3: Transform Data (Pending)

dbt transformation is planned but not yet implemented:

- Staging models
- Fact and dimension tables
- Data quality tests

## Verification

### Verify Data Load

Check table row counts in BigQuery:

```bash
# List all tables in the dataset
bq ls --project_id=YOUR_PROJECT_ID olist_raw

# Count rows in a specific table
bq query --project_id=YOUR_PROJECT_ID --use_legacy_sql=false \
  'SELECT
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_customers`) as customers,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_geolocation`) as geolocation,   
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_orders`) as orders,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_order_items`) as order_items,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_payments`) as payments,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_products`) as products,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID_raw.raw_sellers`) as sellers'
```

Expected row counts:

- `raw_customers`: 99,441
- `raw_geolocation`: 1,000,163
- `raw_order_items`: 112,650
- `raw_orders`: 99,441
- `raw_payments`: 103,886
- `raw_products`: 32,951
- `raw_sellers`: 3,095

## Technology Stack

- **Language**: Python 3.11+
- **Data Extraction**: Kaggle API, Python SDK
- **Data Loading**: Meltano, Singer Protocol (tap-csv, target-bigquery)
- **Data Warehouse**: Google BigQuery
- **Data Transformation**: dbt (planned)
- **Orchestration**: Meltano (current), Dagster (optional future)
- **Environment Management**: python-dotenv

## Pending Implementation (TODO)

### High Priority

- [ ] **dbt Initialization**:

  - Initialize dbt project (`dbt init`)
  - Configure `profiles.yml` for BigQuery
  - Set up project structure (staging, warehouse layers)

- [ ] **dbt Staging Models**:

  - Create staging models for all 9 raw tables
  - Add basic transformations (column renaming, type casting)
  - Document models with descriptions

- [ ] **dbt Warehouse Models**:
  - Design star schema (facts and dimensions)
  - Create dimension tables: `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`
  - Create fact tables: `fct_orders`, `fct_order_items`, `fct_payments`, `fct_reviews`

### Medium Priority

- [ ] **Data Quality Tests**:

  - Add dbt tests (unique, not_null, relationships, accepted_values)
  - Add custom data quality checks
  - Set up test coverage reporting

- [ ] **Orchestration Enhancement**:
  - Create end-to-end orchestration script (Extract → Load → Transform)
  - Add error handling and retry logic
  - Consider Dagster integration for scheduling

### Low Priority

- [ ] **Advanced Features**:
  - Incremental loading strategy
  - Data lineage tracking
  - Great Expectations for raw data validation
  - CI/CD pipeline with GitHub Actions
  - Cost monitoring and optimization

## License

This project uses the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) which is available under the CC BY-NC-SA 4.0 license.
