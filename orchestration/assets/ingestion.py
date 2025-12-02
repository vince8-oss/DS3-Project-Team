from dagster import asset, Output, AssetExecutionContext
import sys
import os

# Add project root to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.ingestion.kaggle_downloader import download_dataset
from src.ingestion.gcs_uploader import upload_to_gcs
from src.ingestion.bigquery_loader import load_to_bigquery

@asset(group_name="ingestion")
def kaggle_dataset(context: AssetExecutionContext):
    """Downloads the dataset from Kaggle."""
    context.log.info("Downloading dataset from Kaggle...")
    output_path = "data/raw/brazilian-ecommerce"
    download_dataset(dataset_name="olistbr/brazilian-ecommerce", output_path=output_path)
    return Output(value=output_path, metadata={"path": output_path})

@asset(group_name="ingestion", deps=[kaggle_dataset])
def gcs_raw_data(context: AssetExecutionContext, kaggle_dataset: str):
    """Uploads raw data to GCS."""
    from src.utils.config import Config
    context.log.info("Uploading raw data to GCS...")
    upload_to_gcs(source_dir=kaggle_dataset, bucket_name=Config.GCS_BUCKET_NAME)
    return Output(value="Uploaded to GCS", metadata={"status": "success", "bucket": Config.GCS_BUCKET_NAME})

@asset(group_name="ingestion", deps=[gcs_raw_data])
def bigquery_raw_tables(context: AssetExecutionContext, kaggle_dataset: str):
    """Loads data from local files to BigQuery raw tables."""
    context.log.info("Loading data to BigQuery...")
    load_to_bigquery(source_dir=kaggle_dataset)
    return Output(value="Loaded to BigQuery", metadata={"status": "success"})
