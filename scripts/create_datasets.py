#!/usr/bin/env python3
"""
Create all required BigQuery datasets
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def create_datasets():
    """Create all required BigQuery datasets"""
    PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    BQ_LOCATION = os.getenv('BQ_LOCATION', 'US')

    if not PROJECT_ID or not CREDENTIALS_PATH:
        raise ValueError("GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS must be set")

    client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)

    # Datasets to create
    datasets = [
        ('brazilian_sales', 'Raw Brazilian e-commerce data'),
        ('brazilian_sales_prod', 'Production transformed data'),
        ('brazilian_sales_staging', 'Staging models'),
        ('brazilian_sales_intermediate', 'Intermediate models'),
        ('brazilian_sales_marts', 'Mart models for analytics'),
    ]

    print("=" * 60)
    print("BigQuery Dataset Creator")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {BQ_LOCATION}\n")

    for dataset_name, description in datasets:
        dataset_ref = f"{PROJECT_ID}.{dataset_name}"

        try:
            client.get_dataset(dataset_ref)
            print(f"✓ Dataset {dataset_name} already exists")
        except Exception:
            print(f"Creating dataset {dataset_name}...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = BQ_LOCATION
            dataset.description = description
            client.create_dataset(dataset, exists_ok=True)
            print(f"✓ Created dataset {dataset_name}")

    print("\n" + "=" * 60)
    print("✓ All datasets ready!")
    print("=" * 60)

if __name__ == "__main__":
    create_datasets()
