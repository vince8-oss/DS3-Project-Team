import os
import argparse
import logging
import hashlib
from datetime import datetime
from google.cloud import bigquery
from src.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def create_metadata_table_if_not_exists(client: bigquery.Client, dataset_id: str):
    """Create _load_metadata table if it doesn't exist."""
    table_id = f"{Config.GCP_PROJECT_ID}.{dataset_id}._load_metadata"
    schema = [
        bigquery.SchemaField("table_name", "STRING"),
        bigquery.SchemaField("file_name", "STRING"),
        bigquery.SchemaField("file_hash", "STRING"),
        bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("load_status", "STRING"),
        bigquery.SchemaField("row_count", "INTEGER"),
    ]
    
    try:
        client.get_table(table_id)
    except Exception:
        logger.info(f"Creating metadata table {table_id}...")
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)

def is_file_already_loaded(client: bigquery.Client, dataset_id: str, table_name: str, file_hash: str) -> bool:
    """Check if file was already loaded using MD5 hash."""
    query = f"""
    SELECT COUNT(*) as count
    FROM `{Config.GCP_PROJECT_ID}.{dataset_id}._load_metadata`
    WHERE table_name = '{table_name}'
    AND file_hash = '{file_hash}'
    AND load_status = 'success'
    """
    try:
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            return row.count > 0
    except Exception as e:
        logger.warning(f"Could not check metadata: {e}")
        return False
    return False

def log_load_status(client: bigquery.Client, dataset_id: str, table_name: str, file_name: str, file_hash: str, status: str, row_count: int = 0):
    """Log load status to metadata table."""
    table_id = f"{Config.GCP_PROJECT_ID}.{dataset_id}._load_metadata"
    rows_to_insert = [{
        "table_name": table_name,
        "file_name": file_name,
        "file_hash": file_hash,
        "load_timestamp": datetime.utcnow().isoformat(),
        "load_status": status,
        "row_count": row_count
    }]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        logger.error(f"Failed to insert metadata: {errors}")

def load_to_bigquery(source_dir: str):
    """
    Load CSV files from source directory to BigQuery.
    """
    try:
        client = bigquery.Client(project=Config.GCP_PROJECT_ID)
        dataset_id = Config.BQ_DATASET_RAW
        
        # Ensure dataset exists
        dataset_ref = bigquery.DatasetReference(Config.GCP_PROJECT_ID, dataset_id)
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            logger.info(f"Dataset {dataset_id} does not exist. Creating it...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset)
            
        create_metadata_table_if_not_exists(client, dataset_id)
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    table_name = os.path.splitext(file)[0].replace('olist_', '').replace('_dataset', '') + '_raw'
                    
                    # Calculate hash
                    file_hash = calculate_md5(file_path)
                    
                    if is_file_already_loaded(client, dataset_id, table_name, file_hash):
                        logger.info(f"Skipping {file} (already loaded).")
                        continue
                        
                    logger.info(f"Loading {file} to {dataset_id}.{table_name}...")
                    
                    # Load job config
                    job_config = bigquery.LoadJobConfig(
                        source_format=bigquery.SourceFormat.CSV,
                        skip_leading_rows=1,
                        autodetect=True,
                        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                    )
                    
                    with open(file_path, "rb") as source_file:
                        job = client.load_table_from_file(
                            source_file,
                            dataset_ref.table(table_name),
                            job_config=job_config
                        )
                        
                    job.result()  # Wait for job to complete
                    
                    table = client.get_table(dataset_ref.table(table_name))
                    logger.info(f"Loaded {table.num_rows} rows into {table_name}.")
                    
                    log_load_status(client, dataset_id, table_name, file, file_hash, 'success', table.num_rows)
                    
    except Exception as e:
        logger.error(f"Failed to load to BigQuery: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load raw data to BigQuery")
    parser.add_argument("--directory", type=str, help="Directory containing raw CSVs")
    args = parser.parse_args()
    
    try:
        Config.validate()
        source_dir = args.directory if args.directory else str(Config.RAW_DATA_DIR / 'brazilian-ecommerce')
        load_to_bigquery(source_dir)
    except Exception as e:
        logger.error(str(e))
        exit(1)
