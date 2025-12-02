import os
import argparse
import logging
from google.cloud import storage
from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_to_gcs(source_dir: str, bucket_name: str):
    """
    Upload files from source directory to GCS bucket.
    """
    try:
        storage_client = storage.Client(project=Config.GCP_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        
        if not bucket.exists():
            logger.info(f"Bucket {bucket_name} does not exist. Creating it...")
            bucket.create(location="US") # Default to US, can be parameterized
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.csv'):
                    local_path = os.path.join(root, file)
                    blob_name = os.path.relpath(local_path, source_dir)
                    blob = bucket.blob(blob_name)
                    
                    logger.info(f"Uploading {local_path} to gs://{bucket_name}/{blob_name}...")
                    blob.upload_from_filename(local_path)
                    
        logger.info("Upload complete.")
        
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
