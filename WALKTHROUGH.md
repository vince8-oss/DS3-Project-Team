# Brazilian E-Commerce Data Pipeline - Complete Implementation Walkthrough

## Table of Contents
1. [Prerequisites Setup](#prerequisites-setup)
2. [Google Cloud Platform Setup](#google-cloud-platform-setup)
3. [Kaggle API Setup](#kaggle-api-setup)
4. [Project Installation](#project-installation)
5. [Environment Configuration](#environment-configuration)
6. [Running the Pipeline](#running-the-pipeline)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Common Commands Reference](#common-commands-reference)

---

## Prerequisites Setup

### 1. Install Python 3.9+

**macOS:**
```bash
# Using Homebrew
brew install python@3.9

# Verify installation
python3 --version
```

**Windows:**
```bash
# Download from https://www.python.org/downloads/
# During installation, check "Add Python to PATH"

# Verify installation
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.9 python3-pip python3-venv

# Verify installation
python3 --version
```

### 2. Install Git

**macOS:**
```bash
brew install git
```

**Windows:**
```bash
# Download from https://git-scm.com/download/win
# Follow installer instructions
```

**Linux:**
```bash
sudo apt install git
```

### 3. Create Required Accounts

**Google Cloud Platform:**
- Go to https://console.cloud.google.com
- Sign in with Google account
- Accept terms of service
- Enable billing (free tier available with $300 credit)

**Kaggle:**
- Go to https://www.kaggle.com
- Click "Register" and create account
- Verify your email address

---

## Google Cloud Platform Setup

### Step 1: Create GCP Project

```bash
# Option A: Using Web Console
# 1. Go to https://console.cloud.google.com
# 2. Click "Select a project" → "New Project"
# 3. Project name: "ds3-ecommerce-pipeline" (or your choice)
# 4. Click "Create"
# 5. Wait 30-60 seconds for project creation
# 6. Note your PROJECT_ID (shown in dashboard)

# Option B: Using gcloud CLI (if installed)
gcloud projects create ds3-ecommerce-pipeline
gcloud config set project ds3-ecommerce-pipeline
```

### Step 2: Enable Required APIs

```bash
# Option A: Using Web Console
# 1. Go to "APIs & Services" → "Enable APIs and Services"
# 2. Search and enable:
#    - BigQuery API
#    - Cloud Storage API
#    - BigQuery Storage API

# Option B: Using gcloud CLI
gcloud services enable bigquery.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
```

### Step 3: Create Service Account

**Using Web Console:**

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Service account details:
   - Name: `ds3-pipeline-sa`
   - Description: `Service account for DS3 data pipeline`
   - Click **Create and Continue**
4. Grant roles:
   - Add role: **BigQuery Admin**
   - Add role: **Storage Admin** (optional, for GCS)
   - Click **Continue**
5. Click **Done**

### Step 4: Generate Service Account Key

1. In Service Accounts list, click on `ds3-pipeline-sa@...`
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**
6. File downloads automatically (e.g., `ds3-ecommerce-pipeline-xxxxx.json`)
7. **IMPORTANT:** Move this file to a secure location:
   ```bash
   # Create credentials directory
   mkdir -p ~/.gcp

   # Move the downloaded key (replace with your actual filename)
   mv ~/Downloads/ds3-ecommerce-pipeline-xxxxx.json ~/.gcp/service-account-key.json

   # Secure the file (macOS/Linux)
   chmod 600 ~/.gcp/service-account-key.json
   ```

### Step 5: Create BigQuery Datasets

**Option A: Using Web Console**

1. Go to **BigQuery** → **SQL workspace**
2. Click on your project name
3. Click three dots → **Create dataset**

Create three datasets:

**Dataset 1: staging (raw data)**
- Dataset ID: `staging`
- Location: `US (multiple regions in United States)`
- Click **Create dataset**

**Dataset 2: dev_warehouse_staging**
- Dataset ID: `dev_warehouse_staging`
- Location: `US`
- Click **Create dataset**

**Dataset 3: dev_warehouse_warehouse**
- Dataset ID: `dev_warehouse_warehouse`
- Location: `US`
- Click **Create dataset**

**Option B: Using bq CLI**

```bash
# Install Google Cloud SDK first: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project ds3-ecommerce-pipeline

# Create datasets
bq mk --location=US --dataset staging
bq mk --location=US --dataset dev_warehouse_staging
bq mk --location=US --dataset dev_warehouse_warehouse

# Verify datasets created
bq ls
```

### Step 6: Create GCS Bucket (Optional)

This is for archiving raw CSV files.

```bash
# Using Web Console:
# 1. Go to Cloud Storage → Buckets
# 2. Click "Create"
# 3. Name: ds3-ecommerce-raw-data (must be globally unique)
# 4. Location: US (region)
# 5. Storage class: Standard
# 6. Click "Create"

# Using gsutil CLI:
gsutil mb -l US gs://ds3-ecommerce-raw-data-YOUR-UNIQUE-SUFFIX/
```

---

## Kaggle API Setup

### Step 1: Generate API Token

1. Log in to https://www.kaggle.com
2. Click on your profile picture (top right) → **Settings**
3. Scroll to **API** section
4. Click **Create New API Token**
5. File `kaggle.json` downloads automatically

### Step 2: Configure Kaggle Credentials

**Option A: Place kaggle.json in default location (recommended)**

```bash
# macOS/Linux
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
mkdir %USERPROFILE%\.kaggle
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\
```

**Option B: Use environment variables (alternative)**

Open `kaggle.json` and note the username and key:
```json
{"username":"your_username","key":"your_api_key"}
```

You'll add these to `.env` file later.

---

## Project Installation

### Step 1: Clone Repository

```bash
# Navigate to your projects directory
cd ~/Projects  # or your preferred location

# Clone the repository
git clone <repository-url>
cd DS3-Project-Team

# Verify you're in the correct directory
ls -la
# You should see: README.md, requirements.txt, dbt/, src/, etc.
```

### Step 2: Create Python Virtual Environment

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 3: Install Python Dependencies

```bash
# Ensure virtual environment is activated (you should see (venv) in prompt)

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install:
# - pandas, sqlalchemy (data processing)
# - google-cloud-bigquery, google-cloud-storage (GCP)
# - kaggle (dataset download)
# - dbt-bigquery (transformations)
# - dagster, dagster-webserver (orchestration)
# - jupyter, matplotlib, seaborn (analytics)

# Verify installations
pip list
```

### Step 4: Install dbt Packages

```bash
# Navigate to dbt directory
cd dbt

# Install dbt dependencies (dbt_utils)
dbt deps

# You should see: "Installing dbt_utils"
# This creates dbt_packages/ directory

cd ..
```

---

## Environment Configuration

### Step 1: Create Environment File

```bash
# Copy the example file
cp .env.example .env

# Open .env in your editor
nano .env  # or use: vim, code, or your preferred editor
```

### Step 2: Configure .env File

Edit `.env` with your actual values:

```bash
# =============================================================================
# Environment
# =============================================================================
ENVIRONMENT=dev

# =============================================================================
# Google Cloud Platform
# =============================================================================
# Replace with YOUR project ID from GCP Console
GCP_PROJECT_ID=ds3-ecommerce-pipeline

# Replace with YOUR service account key path
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourusername/.gcp/service-account-key.json
# Windows example: C:/Users/yourusername/.gcp/service-account-key.json

# =============================================================================
# BigQuery Datasets
# =============================================================================
BQ_DATASET_RAW=staging
BQ_DATASET_STAGING=dev_warehouse_staging
BQ_DATASET_WAREHOUSE=dev_warehouse_warehouse

# =============================================================================
# Google Cloud Storage (Optional)
# =============================================================================
# Replace with your bucket name (or leave as is if you skipped GCS)
GCS_BUCKET_NAME=ds3-ecommerce-raw-data-YOUR-UNIQUE-SUFFIX

# =============================================================================
# Kaggle API Credentials
# =============================================================================
# If you placed kaggle.json in ~/.kaggle/, you can leave these blank
# Otherwise, copy from your kaggle.json file:
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-api-key
```

**Save and close the file.**

### Step 3: Verify Environment Variables

```bash
# Source the environment file (macOS/Linux)
export $(cat .env | grep -v '^#' | xargs)

# Windows (PowerShell)
Get-Content .env | ForEach-Object {
    if ($_ -notmatch '^#' -and $_ -match '=') {
        $var = $_.Split('=')
        [Environment]::SetEnvironmentVariable($var[0], $var[1], 'Process')
    }
}

# Test environment variables are set
echo $GCP_PROJECT_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# Verify GCP authentication
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('BigQuery connection successful!')"
```

### Step 4: Test Kaggle Connection

```bash
# Test Kaggle API
kaggle datasets list --page 1

# You should see a list of datasets
# If you get authentication error, check your kaggle.json setup
```

---

## Running the Pipeline

### Option 1: Orchestrated Pipeline with Dagster (Recommended)

This runs the complete end-to-end pipeline automatically.

#### Step 1: Start Dagster Web Server

```bash
# Ensure you're in project root directory
cd /path/to/DS3-Project-Team

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Start Dagster
dagster dev -f orchestration/definitions.py

# You should see:
# Serving dagster-webserver on http://127.0.0.1:3000
```

#### Step 2: Materialize Assets via Web UI

1. Open browser to http://localhost:3000
2. Click **Assets** in left sidebar
3. You'll see the asset graph:
   - `kaggle_dataset` → `gcs_raw_data` → `bigquery_raw_tables` → `dbt_project`
4. Click **Materialize all** button (top right)
5. Confirm materialization
6. Watch real-time progress in the UI

**Expected Timeline:**
- Kaggle download: 1-2 minutes
- GCS upload: 30 seconds (optional)
- BigQuery load: 1-2 minutes
- dbt transformations: 30 seconds
- **Total: ~5 minutes**

#### Step 3: Monitor Progress

- Click on each asset to see logs
- Green checkmark = success
- Red X = failure (check logs)

#### Step 4: Schedule for Daily Runs (Optional)

```python
# Already configured in orchestration/definitions.py
# Schedule runs daily at midnight (00:00)
# To activate:
# 1. In Dagster UI, click "Overview" → "Schedules"
# 2. Find "daily_pipeline"
# 3. Toggle to "ON"
```

---

### Option 2: Manual Pipeline Execution (Step-by-Step)

Run each component individually for more control.

#### Step 1: Download Data from Kaggle

```bash
# Navigate to project root
cd /path/to/DS3-Project-Team

# Activate virtual environment
source venv/bin/activate

# Run Kaggle downloader
python -m src.ingestion.kaggle_downloader

# Expected output:
# "Downloading olistbr/brazilian-ecommerce..."
# "Dataset downloaded to: data/raw/brazilian-ecommerce/"
# Files: olist_customers_dataset.csv, olist_orders_dataset.csv, etc.

# Verify files downloaded
ls -lh data/raw/brazilian-ecommerce/
# You should see 9 CSV files
```

#### Step 2: Upload to GCS (Optional)

```bash
# Upload raw data to Google Cloud Storage for archiving
python -m src.ingestion.gcs_uploader

# Expected output:
# "Uploading to gs://your-bucket/raw/..."
# "Upload complete"

# Verify upload (if you have gsutil installed)
gsutil ls gs://ds3-ecommerce-raw-data-YOUR-UNIQUE-SUFFIX/raw/
```

#### Step 3: Load to BigQuery

```bash
# Load CSV files to BigQuery raw tables
python -m src.ingestion.bigquery_loader

# Expected output:
# "Loading olist_customers_dataset.csv..."
# "Table customers_raw created/updated"
# "Loading olist_orders_dataset.csv..."
# "Table orders_raw created/updated"
# ... (repeats for all 9 tables)
# "_load_metadata table updated"

# This script is IDEMPOTENT (safe to run multiple times)
# It uses MD5 hashing to prevent duplicate loads

# Verify tables created in BigQuery
bq ls staging

# You should see:
# - customers_raw
# - orders_raw
# - products_raw
# - order_items_raw
# - payments_raw
# - sellers_raw
# - reviews_raw
# - geolocation_raw
# - product_category_name_translation_raw
# - _load_metadata
```

#### Step 4: Run dbt Transformations

```bash
# Navigate to dbt directory
cd dbt

# Run all dbt models
dbt run

# Expected output:
# "Running with dbt=1.x.x"
# "Found 13 models, 30+ tests, 0 snapshots..."
# "Completed successfully"
#
# Model results:
# - 7 staging models (views) in dev_warehouse_staging
# - 4 dimension tables in dev_warehouse_warehouse
# - 2 fact tables in dev_warehouse_warehouse

# Verify models created
bq ls dev_warehouse_staging  # Should show 7 views
bq ls dev_warehouse_warehouse  # Should show 6 tables

# Run specific model layers (optional)
dbt run --select staging  # Only staging models
dbt run --select warehouse  # Only warehouse models
```

#### Step 5: Run Data Quality Tests

```bash
# Still in dbt directory
dbt test

# Expected output:
# "Running tests..."
# "PASS: unique_stg_orders_order_id"
# "PASS: not_null_stg_orders_order_id"
# ... (repeats for 30+ tests)
# "Completed with 0 failures"

# Run tests for specific models (optional)
dbt test --select stg_orders
dbt test --select warehouse
```

#### Step 6: Generate dbt Documentation

```bash
# Generate documentation
dbt docs generate

# Serve documentation site
dbt docs serve

# Opens browser to http://localhost:8080
# Explore:
# - Lineage graphs
# - Model descriptions
# - Column details
# - Test results
```

---

## Verification & Testing

### 1. Verify BigQuery Tables

```bash
# Check row counts in raw tables
bq query --use_legacy_sql=false '
SELECT
  (SELECT COUNT(*) FROM staging.orders_raw) as orders,
  (SELECT COUNT(*) FROM staging.customers_raw) as customers,
  (SELECT COUNT(*) FROM staging.products_raw) as products
'

# Expected:
# orders: ~100,000
# customers: ~100,000
# products: ~32,000
```

### 2. Verify dbt Models

```bash
# Check staging models
bq query --use_legacy_sql=false '
SELECT COUNT(*) as order_count
FROM dev_warehouse_staging.stg_orders
'

# Check warehouse fact table
bq query --use_legacy_sql=false '
SELECT
  COUNT(*) as total_orders,
  SUM(total_order_value) as total_revenue
FROM dev_warehouse_warehouse.fact_orders
'
```

### 3. Test Sample Queries

```bash
# Top 5 customers by total spend
bq query --use_legacy_sql=false '
SELECT
  customer_id,
  customer_segment,
  total_orders,
  total_spent
FROM dev_warehouse_warehouse.dim_customer
ORDER BY total_spent DESC
LIMIT 5
'

# Monthly sales trend
bq query --use_legacy_sql=false '
SELECT
  FORMAT_DATE("%Y-%m", order_purchase_date) as month,
  COUNT(*) as order_count,
  SUM(total_order_value) as revenue
FROM dev_warehouse_warehouse.fact_orders
GROUP BY month
ORDER BY month
'
```

### 4. Run Analytics Notebook

```bash
# Navigate back to project root
cd ..

# Start Jupyter
jupyter notebook notebooks/analysis.ipynb

# In Jupyter:
# 1. Click "Cell" → "Run All"
# 2. Verify all cells execute successfully
# 3. View generated charts:
#    - Monthly sales trends
#    - Top product categories
#    - Customer segmentation
#    - Delivery performance
```

---

## Troubleshooting

### Issue 1: BigQuery Authentication Failed

**Error:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
```bash
# Verify GOOGLE_APPLICATION_CREDENTIALS is set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Check file exists
ls -l $GOOGLE_APPLICATION_CREDENTIALS

# Re-export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Test authentication
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
```

### Issue 2: Kaggle Authentication Failed

**Error:**
```
OSError: Could not find kaggle.json
```

**Solution:**
```bash
# Option A: Place kaggle.json in default location
mkdir -p ~/.kaggle
cp /path/to/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Option B: Export environment variables
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_api_key
```

### Issue 3: dbt Connection Error

**Error:**
```
Runtime Error: Could not find profile named 'brazilian_ecommerce'
```

**Solution:**
```bash
# Verify profiles.yml exists
cat dbt/profiles.yml

# Ensure environment variables are set
echo $GCP_PROJECT_ID
echo $BQ_DATASET_STAGING

# Try running with explicit profile
dbt run --profiles-dir dbt
```

### Issue 4: dbt deps Fails

**Error:**
```
Error downloading dbt_utils
```

**Solution:**
```bash
cd dbt

# Clean dbt artifacts
dbt clean

# Reinstall packages
dbt deps

# If still fails, check internet connection and try again
```

### Issue 5: BigQuery Permission Denied

**Error:**
```
403 Access Denied: BigQuery BigQuery: Permission denied
```

**Solution:**
1. Go to GCP Console → IAM & Admin → IAM
2. Find your service account (ds3-pipeline-sa@...)
3. Edit permissions
4. Ensure these roles are assigned:
   - BigQuery Admin (or at minimum: BigQuery Data Editor + BigQuery Job User)
   - Storage Admin (if using GCS)
5. Save changes
6. Wait 1-2 minutes for propagation
7. Retry your command

### Issue 6: Dagster Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 3000
lsof -ti:3000

# Kill the process
kill -9 $(lsof -ti:3000)

# Or use different port
dagster dev -f orchestration/definitions.py -p 3001
```

### Issue 7: Module Not Found Error

**Error:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
pip list | grep pandas
```

---

## Common Commands Reference

### Environment Management

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Deactivate virtual environment
deactivate

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)  # macOS/Linux
```

### Dagster Commands

```bash
# Start Dagster web server
dagster dev -f orchestration/definitions.py

# Start on different port
dagster dev -f orchestration/definitions.py -p 3001

# Run specific asset
dagster asset materialize -f orchestration/definitions.py --select kaggle_dataset
```

### dbt Commands

```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_orders
dbt run --select fact_orders

# Run models and downstream dependencies
dbt run --select stg_orders+

# Run tests
dbt test
dbt test --select stg_orders

# Generate and serve docs
dbt docs generate
dbt docs serve

# Clean artifacts
dbt clean

# Install packages
dbt deps

# Compile SQL without running
dbt compile

# Debug connection
dbt debug
```

### BigQuery Commands

```bash
# List datasets
bq ls

# List tables in dataset
bq ls staging
bq ls dev_warehouse_staging

# Show table schema
bq show staging.orders_raw

# Run query
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM staging.orders_raw'

# Export table to CSV
bq extract --destination_format=CSV staging.orders_raw gs://bucket/export.csv
```

### GCS Commands

```bash
# List buckets
gsutil ls

# List files in bucket
gsutil ls gs://bucket-name/

# Upload file
gsutil cp local-file.csv gs://bucket-name/

# Download file
gsutil cp gs://bucket-name/file.csv ./
```

### Python Commands

```bash
# Run ingestion scripts
python -m src.ingestion.kaggle_downloader
python -m src.ingestion.gcs_uploader
python -m src.ingestion.bigquery_loader

# Run Python script
python script.py

# Interactive Python shell
python
>>> from google.cloud import bigquery
>>> client = bigquery.Client()
>>> print(client.project)
```

### Jupyter Commands

```bash
# Start Jupyter server
jupyter notebook

# Start specific notebook
jupyter notebook notebooks/analysis.ipynb

# Convert notebook to HTML
jupyter nbconvert --to html notebooks/analysis.ipynb

# List running servers
jupyter notebook list
```

---

## Pipeline Execution Checklist

Use this checklist to verify successful pipeline execution:

- [ ] **Prerequisites**
  - [ ] Python 3.9+ installed
  - [ ] GCP project created
  - [ ] BigQuery API enabled
  - [ ] Service account created with JSON key
  - [ ] Kaggle account and API token obtained

- [ ] **Installation**
  - [ ] Repository cloned
  - [ ] Virtual environment created and activated
  - [ ] Python dependencies installed (`pip install -r requirements.txt`)
  - [ ] dbt packages installed (`dbt deps`)

- [ ] **Configuration**
  - [ ] `.env` file created and populated
  - [ ] GCP credentials file path correct
  - [ ] BigQuery datasets created (staging, dev_warehouse_staging, dev_warehouse_warehouse)
  - [ ] Environment variables exported

- [ ] **Data Ingestion**
  - [ ] Kaggle dataset downloaded (9 CSV files)
  - [ ] Data loaded to BigQuery (10 tables in staging dataset)
  - [ ] `_load_metadata` table shows successful loads

- [ ] **Data Transformation**
  - [ ] dbt staging models created (7 views)
  - [ ] dbt warehouse models created (6 tables)
  - [ ] All dbt tests passed (30+ tests)

- [ ] **Verification**
  - [ ] Row counts match expected values
  - [ ] Sample queries return valid data
  - [ ] dbt documentation generated successfully

- [ ] **Orchestration (Optional)**
  - [ ] Dagster web UI accessible
  - [ ] All assets materialized successfully
  - [ ] Schedule configured (if using scheduling)

---

## Next Steps

After successfully running the pipeline:

1. **Explore the Data**
   - Run queries in BigQuery console
   - Explore dbt documentation
   - Analyze business metrics

2. **Customize the Pipeline**
   - Add new dbt models
   - Modify staging logic
   - Create data marts

3. **Set Up Monitoring**
   - Configure Dagster schedules
   - Set up email notifications
   - Monitor pipeline health

4. **Build Dashboards**
   - Connect Looker Studio to BigQuery
   - Create business dashboards
   - Share insights with stakeholders

5. **Implement CI/CD**
   - Set up GitHub Actions
   - Automate dbt tests on PRs
   - Deploy to production

---

## Support & Resources

**Documentation:**
- dbt: https://docs.getdbt.com/
- BigQuery: https://cloud.google.com/bigquery/docs
- Dagster: https://docs.dagster.io/
- Kaggle API: https://github.com/Kaggle/kaggle-api

**Troubleshooting:**
- Check project README.md for architecture details
- Review error logs in Dagster UI
- Check GCP Console for BigQuery job history
- Verify service account permissions

**Getting Help:**
- Open issue in project repository
- Check dbt community Slack
- Review BigQuery Stack Overflow

---

## Estimated Costs

**Google Cloud Platform:**
- BigQuery storage: ~$0.02/GB/month (< $0.10 for this dataset)
- BigQuery queries: First 1 TB free per month
- Cloud Storage: ~$0.02/GB/month (if used)
- **Total monthly cost: < $1 (within free tier)**

**Kaggle:**
- Free API access

**Development Tools:**
- All open-source (free)

---

## Project Completion Criteria

Your pipeline is successfully implemented when:

1. All 9 CSV files are loaded into BigQuery `staging` dataset
2. 7 staging views are created in `dev_warehouse_staging`
3. 6 warehouse tables are created in `dev_warehouse_warehouse`
4. All 30+ dbt tests pass successfully
5. Dagster can materialize all assets without errors
6. Sample queries return expected results
7. Jupyter notebook runs end-to-end

Congratulations! You've built a production-ready ELT data pipeline!
