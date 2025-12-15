#!/usr/bin/env python3
"""
BCB (Brazilian Central Bank) Data Extractor
Extracts exchange rate and economic data and loads into BigQuery
"""

import os
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BCBExtractor:
    """Extract data from Brazilian Central Bank API"""
    
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
    
    # Available series
    SERIES = {
        'exchange_rate_usd': 1,      # Daily USD/BRL exchange rate
        'ipca': 433,                  # IPCA inflation index
        'selic': 4189,                # SELIC interest rate
        'igpm': 189,                  # IGP-M inflation
        'exchange_commercial': 12,    # Commercial USD/BRL
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
            dataset.location = "US"  # Set location
            dataset.description = "Brazilian E-Commerce raw data"
            self.client.create_dataset(dataset, exists_ok=True)
            print(f"✓ Created dataset {dataset_ref}")

    def extract_series(self, series_name, start_date=None, end_date=None):
        """
        Extract data from BCB API
        
        Args:
            series_name: Name from SERIES dict
            start_date: Start date in format 'DD/MM/YYYY'
            end_date: End date in format 'DD/MM/YYYY'
        
        Returns:
            pandas DataFrame
        """
        if series_name not in self.SERIES:
            raise ValueError(f"Unknown series: {series_name}. Available: {list(self.SERIES.keys())}")
        
        series_id = self.SERIES[series_name]
        url = self.BASE_URL.format(series_id=series_id)
        
        params = {'formato': 'json'}
        if start_date:
            params['dataInicial'] = start_date
        if end_date:
            params['dataFinal'] = end_date
        
        print(f"Fetching {series_name} (series {series_id})...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            print(f"No data returned for {series_name}")
            return df
        
        # Convert date format from DD/MM/YYYY to YYYY-MM-DD
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Add metadata
        df['series_name'] = series_name
        df['series_id'] = series_id
        df['extracted_at'] = datetime.now()
        
        print(f"Extracted {len(df)} records for {series_name}")
        return df
    
    def load_to_bigquery(self, df, table_name, write_disposition='WRITE_TRUNCATE'):
        """
        Load DataFrame to BigQuery
        
        Args:
            df: pandas DataFrame
            table_name: Target table name
            write_disposition: 'WRITE_TRUNCATE' or 'WRITE_APPEND'
        """
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            schema=[
                bigquery.SchemaField("data", "DATE"),
                bigquery.SchemaField("valor", "FLOAT64"),
                bigquery.SchemaField("series_name", "STRING"),
                bigquery.SchemaField("series_id", "INTEGER"),
                bigquery.SchemaField("extracted_at", "TIMESTAMP"),
            ]
        )
        
        print(f"Loading {len(df)} records to {table_id}...")
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        print(f"✅ Loaded {len(df)} rows to {table_id}")
    
    def extract_and_load_all(self, start_date='01/01/2016', end_date=None):
        """Extract all series and combine into one table"""
        all_data = []
        
        for series_name in self.SERIES.keys():
            try:
                df = self.extract_series(series_name, start_date, end_date)
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                print(f"⚠️  Error extracting {series_name}: {e}")
                continue
        
        if not all_data:
            print("No data extracted!")
            return
        
        # Combine all series
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Load to BigQuery
        self.load_to_bigquery(combined_df, 'bcb_economic_indicators')
        
        return combined_df


def main():
    """Main execution"""
    # Configuration from environment variables
    PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    DATASET_ID = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')
    CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID environment variable not set")
    if not CREDENTIALS_PATH:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

    # Initialize extractor
    extractor = BCBExtractor(PROJECT_ID, DATASET_ID, CREDENTIALS_PATH)
    
    # Extract data from 2016 onwards (to match your sales data timeframe)
    print("=" * 60)
    print("BCB Economic Indicators Extractor")
    print("=" * 60)
    
    df = extractor.extract_and_load_all(start_date='01/01/2016')
    
    if df is not None:
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"Total records: {len(df)}")
        print(f"\nRecords per series:")
        print(df.groupby('series_name').size())
        print(f"\nDate range: {df['data'].min()} to {df['data'].max()}")
        print("\n✅ Data successfully loaded to BigQuery!")
        print(f"Table: {PROJECT_ID}.{DATASET_ID}.bcb_economic_indicators")


if __name__ == "__main__":
    main()
