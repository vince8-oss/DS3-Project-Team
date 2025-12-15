#!/usr/bin/env python3
"""Quick script to load reviews table"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DATASET_ID = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)

csv_path = 'data/raw/olist_order_reviews_dataset.csv'
table_id = f"{PROJECT_ID}.{DATASET_ID}.public-reviews"

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    write_disposition='WRITE_TRUNCATE',
)

print(f"Loading reviews to {table_id}...")
with open(csv_path, 'rb') as f:
    job = client.load_table_from_file(f, table_id, job_config=job_config)

job.result()
table = client.get_table(table_id)
print(f"✓ Loaded {table.num_rows:,} rows")
