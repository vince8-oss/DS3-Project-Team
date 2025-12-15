#!/usr/bin/env python3
"""
BCB (Brazilian Central Bank) Economic Data Extractor
Extracts exchange rate, inflation, and interest rate data and loads into BigQuery
"""

import os
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BCBExtractor:
    """Extract economic data from Brazilian Central Bank API"""

    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"

    # Available economic indicator series
    SERIES = {
        'exchange_rate_usd': 1,      # Daily USD/BRL exchange rate
        'ipca': 433,                  # IPCA inflation index
        'selic': 4189,                # SELIC interest rate (Brazil's base rate)
        'igpm': 189,                  # IGP-M inflation
        'exchange_commercial': 12,    # Commercial USD/BRL
    }

    def __init__(self, project_id=None, dataset_id=None, credentials_path=None):
        """
        Initialize with BigQuery credentials

        Args:
            project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)
            dataset_id: BigQuery dataset (defaults to BQ_DATASET_RAW env var)
            credentials_path: Path to service account JSON (defaults to GOOGLE_APPLICATION_CREDENTIALS)
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.dataset_id = dataset_id or os.getenv('BQ_DATASET_RAW')
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        if not all([self.project_id, self.dataset_id, self.credentials_path]):
            raise ValueError(
                "Missing required configuration. Set GCP_PROJECT_ID, BQ_DATASET_RAW, "
                "and GOOGLE_APPLICATION_CREDENTIALS environment variables"
            )

        self.client = bigquery.Client.from_service_account_json(self.credentials_path)

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
            raise ValueError(
                f"Unknown series: {series_name}. "
                f"Available: {list(self.SERIES.keys())}"
            )

        series_id = self.SERIES[series_name]
        url = self.BASE_URL.format(series_id=series_id)

        params = {'formato': 'json'}
        if start_date:
            params['dataInicial'] = start_date
        if end_date:
            params['dataFinal'] = end_date

        print(f"📊 Fetching {series_name} (series {series_id})...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(data)

        if df.empty:
            print(f"⚠️  No data returned for {series_name}")
            return df

        # Convert date format from DD/MM/YYYY to YYYY-MM-DD
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

        # Add metadata
        df['series_name'] = series_name
        df['series_id'] = series_id
        df['extracted_at'] = datetime.now()

        print(f"✅ Extracted {len(df):,} records for {series_name}")
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

        print(f"📤 Loading {len(df):,} records to {table_id}...")
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"✅ Loaded {len(df):,} rows to {table_id}")

    def extract_and_load_all(self, start_date='01/01/2016', end_date=None):
        """
        Extract all economic indicator series and load into BigQuery

        Args:
            start_date: Start date in DD/MM/YYYY format
            end_date: End date in DD/MM/YYYY format (defaults to today)

        Returns:
            Combined DataFrame of all series
        """
        all_data = []

        print("\n" + "=" * 70)
        print("🇧🇷 BCB Economic Indicators Extraction")
        print("=" * 70)

        for series_name in self.SERIES.keys():
            try:
                df = self.extract_series(series_name, start_date, end_date)
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                print(f"❌ Error extracting {series_name}: {e}")
                continue

        if not all_data:
            print("❌ No data extracted!")
            return None

        # Combine all series
        combined_df = pd.concat(all_data, ignore_index=True)

        # Load to BigQuery
        self.load_to_bigquery(combined_df, 'bcb_economic_indicators')

        # Print summary
        print("\n" + "=" * 70)
        print("📈 Summary")
        print("=" * 70)
        print(f"Total records: {len(combined_df):,}")
        print(f"\nRecords per series:")
        print(combined_df.groupby('series_name').size())
        print(f"\nDate range: {combined_df['data'].min()} to {combined_df['data'].max()}")
        print(f"\n✅ Data successfully loaded to BigQuery!")
        print(f"📊 Table: {self.project_id}.{self.dataset_id}.bcb_economic_indicators")
        print("=" * 70)

        return combined_df


def main():
    """Main execution"""
    try:
        # Initialize extractor (reads from environment variables)
        extractor = BCBExtractor()

        # Extract data from 2016 onwards (to match sales data timeframe)
        df = extractor.extract_and_load_all(start_date='01/01/2016')

        if df is not None:
            print("\n✅ BCB economic data extraction completed successfully!")
        else:
            print("\n❌ BCB economic data extraction failed!")
            return 1

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
