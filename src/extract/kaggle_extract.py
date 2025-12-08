import os
import shutil
import glob
from dotenv import load_dotenv

# Fix for Kaggle SDK 1.7.x User-Agent header issue
# Must be done before importing KaggleApi
try:
    import kagglesdk

    # Patch __init__ to ensure _user_agent is never None
    original_init = kagglesdk.KaggleHttpClient.__init__
    def patched_init(self, *args, **kwargs):
        # If user_agent is passed as None, replace it with a default
        if 'user_agent' in kwargs and kwargs['user_agent'] is None:
            kwargs['user_agent'] = 'kaggle-python-client/1.7.4'
        original_init(self, *args, **kwargs)
        # Double-check _user_agent is set
        if not hasattr(self, '_user_agent') or self._user_agent is None:
            self._user_agent = 'kaggle-python-client/1.7.4'

    kagglesdk.KaggleHttpClient.__init__ = patched_init
except (ImportError, AttributeError):
    pass

from kaggle.api.kaggle_api_extended import KaggleApi

load_dotenv()

# Configuration
DATASET = 'olistbr/brazilian-ecommerce'
BASE_DIR = os.path.abspath('.')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DOWNLOAD_PATH = '/tmp/olist_kaggle_download'

def _ensure_user_agent(api: KaggleApi) -> None:
    """Force a non-null User-Agent on the Kaggle client."""
    if not getattr(api, "config", None):
        raise RuntimeError("Kaggle API configuration is missing.")
    api.config.user_agent = api.config.user_agent or 'kaggle-python-client/1.7.4'
    # Align the underlying HTTP client if present
    if hasattr(api, "api_client") and hasattr(api.api_client, "user_agent"):
        api.api_client.user_agent = api.config.user_agent


def extract_data():
    """Authenticates with Kaggle, downloads the dataset, and moves it to data/raw."""
    # Ensure raw directory exists
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    print("Authenticating with Kaggle...")
    api = KaggleApi()
    _ensure_user_agent(api)
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
