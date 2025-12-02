import os
import argparse
import logging
from typing import Optional
from google.cloud import storage
from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_to_gcs(source_dir: str, bucket_name: str) -> None:
    """
    Upload CSV files from source directory to Google Cloud Storage bucket.

    Args:
        source_dir: Local directory path containing CSV files to upload
        bucket_name: Name of the GCS bucket (will be created if doesn't exist)

    Raises:
        Exception: If GCS upload or bucket creation fails

    Notes:
        - Only uploads files with .csv extension
        - Creates bucket in US region if it doesn't exist
        - Preserves directory structure in GCS

    Example:
        >>> upload_to_gcs('data/raw', 'my-project-raw-data')
    """
    try:
        storage_client = storage.Client(project=Config.GCP_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)

        if not bucket.exists():
            logger.info(f"Bucket {bucket_name} does not exist. Creating it...")
            bucket.create(location="US")  # Default to US, can be parameterized

        uploaded_count = 0
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.csv'):
                    local_path = os.path.join(root, file)
                    blob_name = os.path.relpath(local_path, source_dir)
                    blob = bucket.blob(blob_name)

                    logger.info(f"Uploading {local_path} to gs://{bucket_name}/{blob_name}...")
                    blob.upload_from_filename(local_path)
                    uploaded_count += 1

        logger.info(f"Upload complete. {uploaded_count} files uploaded.")

    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload raw data to GCS")
    parser.add_argument("--kaggle", action="store_true", help="Upload Kaggle dataset")
    args = parser.parse_args()
    
    try:
        Config.validate()
        source_dir = str(Config.RAW_DATA_DIR / 'brazilian-ecommerce')
        upload_to_gcs(source_dir, Config.GCS_BUCKET_NAME)
    except Exception as e:
        logger.error(str(e))
        exit(1)
