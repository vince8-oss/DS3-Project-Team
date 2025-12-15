#!/usr/bin/env python3
"""
CSV to BigQuery Loader
Loads Kaggle CSV files from data/raw/ into BigQuery
"""

import os
import glob
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


class CSVLoader:
    """Load CSV files to BigQuery"""

    # Mapping of CSV filenames to BigQuery table names
    TABLE_MAPPING = {
        'olist_customers_dataset.csv': 'public-Customers',
        'olist_geolocation_dataset.csv': 'public-Geolocation',
        'olist_order_items_dataset.csv': 'public-Order_Items',
        'olist_order_payments_dataset.csv': 'public-order_payments',
        'olist_order_reviews_dataset.csv': 'public-reviews',
        'olist_orders_dataset.csv': 'public-orders',
        'olist_products_dataset.csv': 'public-products',
        'olist_sellers_dataset.csv': 'public-sellers',
        'product_category_name_translation.csv': 'public-product_category',
    }

    def __init__(self, project_id, dataset_id, credentials_path):
        """Initialize with BigQuery credentials"""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.credentials_path = credentials_path
        self.client = bigquery.Client.from_service_account_json(credentials_path)
        self._ensure_dataset_exists()

    def _ensure_dataset_exists(self):
        """Create dataset if it doesn't exist"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"

        try:
            self.client.get_dataset(dataset_ref)
            print(f"✓ Dataset {dataset_ref} exists")
        except Exception:
            print(f"Creating dataset {dataset_ref}...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset.description = "Brazilian E-Commerce raw data"
            self.client.create_dataset(dataset, exists_ok=True)
            print(f"✓ Created dataset {dataset_ref}")

    def _get_schema_for_table(self, table_name):
        """Get explicit schema for specific tables"""
        schemas = {
            'public-product_category': [
                bigquery.SchemaField("product_category_name", "STRING"),
                bigquery.SchemaField("product_category_name_english", "STRING"),
            ]
        }
        return schemas.get(table_name)

    def load_csv_to_bigquery(self, csv_path, table_name):
        """
        Load a CSV file to BigQuery

        Args:
            csv_path: Path to the CSV file
            table_name: Target table name in BigQuery
        """
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"

        # Get explicit schema if available, otherwise use autodetect
        explicit_schema = self._get_schema_for_table(table_name)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,  # Skip header row
            write_disposition='WRITE_TRUNCATE',  # Replace existing data
            allow_quoted_newlines=True,  # Allow newlines in quoted fields
            allow_jagged_rows=True,  # Allow missing trailing columns
            max_bad_records=1000,  # Allow up to 1000 bad records
        )

        if explicit_schema:
            job_config.schema = explicit_schema
        else:
            job_config.autodetect = True  # Auto-detect schema

        print(f"Loading {os.path.basename(csv_path)} to {table_id}...")

        with open(csv_path, 'rb') as source_file:
            job = self.client.load_table_from_file(
                source_file, table_id, job_config=job_config
            )

        job.result()  # Wait for completion

        # Get row count
        table = self.client.get_table(table_id)
        print(f"✓ Loaded {table.num_rows:,} rows to {table_name}")

        return table.num_rows

    def load_all_csvs(self, csv_dir='data/raw'):
        """Load all CSV files from the directory to BigQuery"""
        csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))

        if not csv_files:
            print(f"No CSV files found in {csv_dir}")
            return

        print(f"\nFound {len(csv_files)} CSV files to load\n")

        total_rows = 0
        loaded_tables = []

        for csv_path in sorted(csv_files):
            filename = os.path.basename(csv_path)

            if filename not in self.TABLE_MAPPING:
                print(f"⚠️  Skipping {filename} (not in table mapping)")
                continue

            table_name = self.TABLE_MAPPING[filename]

            try:
                rows = self.load_csv_to_bigquery(csv_path, table_name)
                total_rows += rows
                loaded_tables.append(table_name)
            except Exception as e:
                print(f"✗ Error loading {filename}: {e}")
                continue

        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"Tables loaded: {len(loaded_tables)}")
        print(f"Total rows: {total_rows:,}")
        print(f"\nLoaded tables:")
        for table in loaded_tables:
            print(f"  - {table}")
        print(f"\n✓ All CSV files loaded to BigQuery!")
        print(f"Dataset: {self.project_id}.{self.dataset_id}")


def main():
    """Main execution"""
    # Configuration from environment variables
    PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    DATASET_RAW = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')
    DATASET_PROD = os.getenv('BQ_DATASET_PROD', 'brazilian_sales_prod')
    CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID environment variable not set")
    if not CREDENTIALS_PATH:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

    print("=" * 60)
    print("CSV to BigQuery Loader")
    print("=" * 60)

    # Create and load to raw dataset
    loader = CSVLoader(PROJECT_ID, DATASET_RAW, CREDENTIALS_PATH)
    loader.load_all_csvs()

    # Also ensure prod dataset exists (for dbt transformations)
    print(f"\nEnsuring prod dataset exists...")
    prod_loader = CSVLoader(PROJECT_ID, DATASET_PROD, CREDENTIALS_PATH)
    print(f"✓ Prod dataset {DATASET_PROD} ready for dbt transformations")


if __name__ == "__main__":
    main()
