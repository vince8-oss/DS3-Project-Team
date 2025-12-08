# Olist E-Commerce Data Pipeline

## Overview
This project implements an ELT (Extract, Load, Transform) data pipeline for the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

The pipeline extracts raw data from Kaggle, loads it into Google BigQuery and performs transformations with dbt.

## Architecture
![Architecture Diagram](sources/architectural_diagram.png)

The pipeline consists of the following stages:
1.  **Extract**: Downloads raw CSV files from Kaggle API.
2.  **Load**: Ingests raw CSV files into Google BigQuery staging tables (`olist_raw` dataset).
3.  **Transform**: Uses dbt to model data into Fact and Dimension tables.

## Project Structure
```text
.
├── data/
│   └── raw/                    # Local storage for downloaded CSVs
├── notebook/                   # Exploratory notebooks
├── src/                        # Source code for pipeline steps
│   ├── extract/                # Scripts for extracting data from sources
│   └── load/                   # Scripts for loading data into BigQuery
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Setup & Prerequisites

### 1. Environment Variables
Create a `.env` file in the root directory with the following credentials:
```bash
# Kaggle API Credentials
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key

# Google Cloud Platform
GCP_PROJECT=your_gcp_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
```

### 2. Installation (using uv)
This project uses [uv](https://github.com/astral-sh/uv) for fast package management.

1.  Create a virtual environment:
    ```bash
    uv venv
    source .venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

### Extraction
To download the dataset from Kaggle:
```bash
python -m src.extract.kaggle_extract
```

### Loading (Meltano)
First, install plugins:
```bash
meltano install
```

To load data into BigQuery (run for each entity or use a loop):
```bash
meltano elt tap-csv target-bigquery
```
Or specifically for one table:
```bash
meltano elt tap-csv target-bigquery --select raw_customers
```


## Pending Implementation (TODO)

- **Transformation (dbt)**:
    - Initialize dbt project (`dbt init`).
    - Configure `profiles.yml` for BigQuery.
    - Create staging models for all raw tables.
    - Create dimensional models (customers, products, unknown).
    - Create fact models (orders, order_items).
- **Orchestration**:
    - Create an orchestration script (e.g., Python) to run Extraction -> Loading -> Transformation.
    - (Optional) Integrate with Dagster.
- **Data Quality**:
    - Add dbt tests (unique, not_null, relationship).
    - (Optional) Add Great Expectations for raw data validation.

