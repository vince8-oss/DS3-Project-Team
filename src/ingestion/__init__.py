"""
Data ingestion module for Brazilian E-Commerce pipeline.
Handles downloading from Kaggle, uploading to GCS, and loading to BigQuery.
"""

from .kaggle_downloader import download_dataset
from .gcs_uploader import upload_to_gcs
from .bigquery_loader import load_to_bigquery

__all__ = ['download_dataset', 'upload_to_gcs', 'load_to_bigquery']
