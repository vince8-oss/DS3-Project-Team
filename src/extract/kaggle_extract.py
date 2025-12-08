import os
import shutil
import glob
from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATASET = 'olistbr/brazilian-ecommerce'
BASE_DIR = os.path.abspath('.')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DOWNLOAD_PATH = '/tmp/olist_kaggle_download'

def extract_data():
    """Authenticates with Kaggle, downloads the dataset, and moves it to data/raw."""
    # Ensure raw directory exists
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    print("Authenticating with Kaggle...")
    api = KaggleApi()
    api.authenticate()

    print(f"Downloading dataset {DATASET}...")
    api.dataset_download_files(DATASET, path=DOWNLOAD_PATH, unzip=True)
    
    print("Download complete. Moving files...")
    csvs = glob.glob(os.path.join(DOWNLOAD_PATH, '*.csv'))
    
    if not csvs:
        print("No CSV files found in download.")
        return

    for f in csvs:
        filename = os.path.basename(f)
        dest = os.path.join(RAW_DIR, filename)
        shutil.copyfile(f, dest)
        print(f"- Copied {filename} to {RAW_DIR}")
        
    print(f"\nSuccessfully extracted {len(csvs)} files to {RAW_DIR}")

if __name__ == "__main__":
    extract_data()
