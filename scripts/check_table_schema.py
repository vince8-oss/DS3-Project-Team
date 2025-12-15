#!/usr/bin/env python3
"""Check BigQuery table schema"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv('GCP_PROJECT_ID')
DATASET_ID = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)

table_id = f"{PROJECT_ID}.{DATASET_ID}.public-product_category"
table = client.get_table(table_id)

print(f"Schema for {table_id}:")
print("-" * 60)
for field in table.schema:
    print(f"  {field.name}: {field.field_type}")

print(f"\nTotal rows: {table.num_rows:,}")
