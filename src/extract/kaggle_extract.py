import os
import shutil
import glob
from dotenv import load_dotenv

# Fix for Kaggle SDK 1.7.x User-Agent header issue
# Must be done before importing KaggleApi
try:
    from kagglesdk.kaggle_http_client import KaggleHttpClient

    # Patch __init__ to ensure _user_agent is never None
    original_init = KaggleHttpClient.__init__
    def patched_init(self, env=None, verbose=False, username=None, password=None, api_token=None, user_agent="kaggle-python-client/1.7.4"):
        # If user_agent is passed as None, replace it with a default
        if user_agent is None:
            user_agent = 'kaggle-python-client/1.7.4'
        original_init(self, env=env, verbose=verbose, username=username, password=password, api_token=api_token, user_agent=user_agent)

    KaggleHttpClient.__init__ = patched_init
except (ImportError, AttributeError):
    pass

from kaggle.api.kaggle_api_extended import KaggleApi

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
