import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
    
    # GCP
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # BigQuery Datasets
    BQ_DATASET_RAW = os.getenv('BQ_DATASET_RAW', 'staging')
    BQ_DATASET_STAGING = os.getenv('BQ_DATASET_STAGING', 'dev_warehouse_staging')
    BQ_DATASET_WAREHOUSE = os.getenv('BQ_DATASET_WAREHOUSE', 'dev_warehouse_warehouse')
    
    # GCS
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', f"{GCP_PROJECT_ID}-raw-data")
    
    # Kaggle
    KAGGLE_USERNAME = os.getenv('KAGGLE_USERNAME')
    KAGGLE_KEY = os.getenv('KAGGLE_KEY')
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    RAW_DATA_DIR = DATA_DIR / 'raw'

    @classmethod
    def validate(cls):
        required_vars = ['GCP_PROJECT_ID', 'KAGGLE_USERNAME', 'KAGGLE_KEY']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
