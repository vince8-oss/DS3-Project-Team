import os
import argparse
import logging
from typing import Optional
from kaggle.api.kaggle_api_extended import KaggleApi
from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_dataset(dataset_name: str, output_path: str) -> None:
    """
    Download dataset from Kaggle to the specified output path.

    Args:
        dataset_name: The Kaggle dataset identifier (e.g., 'olistbr/brazilian-ecommerce')
        output_path: Local directory path where dataset will be downloaded and extracted

    Raises:
        Exception: If dataset download or authentication fails

    Example:
        >>> download_dataset('olistbr/brazilian-ecommerce', 'data/raw')
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Authenticate with Kaggle
        api = KaggleApi()
        api.authenticate()

        logger.info(f"Downloading dataset '{dataset_name}' to '{output_path}'...")
        api.dataset_download_files(dataset_name, path=output_path, unzip=True)

        logger.info("Download complete.")

    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download dataset from Kaggle")
    parser.add_argument("--dataset", type=str, default="olistbr/brazilian-ecommerce", help="Kaggle dataset name")
    args = parser.parse_args()
    
    try:
        Config.validate()
        download_dataset(args.dataset, str(Config.RAW_DATA_DIR / 'brazilian-ecommerce'))
    except Exception as e:
        logger.error(str(e))
        exit(1)
