"""
Dagster Assets for Brazilian Sales Analytics Pipeline

This module defines all data assets for the Brazilian e-commerce sales analysis,
including extraction from BCB API, dbt transformations, and data quality checks.
"""

import os
import sys
from dagster import asset, AssetExecutionContext, Output, MetadataValue
import subprocess
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from google.cloud import bigquery


# Configuration from environment variables
PROJECT_ROOT = Path(__file__).parent.parent  # Root of unified project
EXTRACT_DIR = PROJECT_ROOT / "extract"
DBT_PROJECT_DIR = PROJECT_ROOT / "transform"
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
BQ_PROJECT = os.getenv('GCP_PROJECT_ID')
BQ_DATASET = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')

# Add extract directory to path for imports
sys.path.insert(0, str(EXTRACT_DIR))


# ============================================================================
# EXTRACTION ASSETS
# ============================================================================

@asset(
    group_name="extraction",
    description="Extract Brazilian Central Bank economic indicators (USD/BRL, IPCA, SELIC)",
    compute_kind="python"
)
def bcb_economic_indicators(context: AssetExecutionContext) -> Output[dict]:
    """
    Extract economic data from Brazilian Central Bank API.
    
    This runs the bcb_data_extractor.py script which fetches:
    - Exchange rates (USD/BRL)
    - Inflation (IPCA)
    - Interest rates (SELIC)
    - Other economic indicators
    """
    context.log.info("Starting BCB economic data extraction...")

    # Run the BCB extractor script
    script_path = EXTRACT_DIR / "bcb_extractor.py"

    result = subprocess.run(
        ["python", str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=os.environ.copy()  # Pass environment variables
    )
    
    context.log.info(f"BCB extraction output:\n{result.stdout}")
    
    # Query BigQuery to get extraction stats
    client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)
    
    query = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT series_name) as series_count,
        MIN(data) as earliest_date,
        MAX(data) as latest_date,
        MAX(extracted_at) as extraction_time
    FROM `{BQ_PROJECT}.{BQ_DATASET}.bcb_economic_indicators`
    """
    
    stats = client.query(query).to_dataframe().iloc[0].to_dict()
    
    context.log.info(f"BCB data stats: {stats}")
    
    return Output(
        value={
            "status": "success",
            "records": int(stats["total_records"]),
            "series_count": int(stats["series_count"]),
            "latest_date": str(stats["latest_date"]),
        },
        metadata={
            "total_records": MetadataValue.int(int(stats["total_records"])),
            "series_count": MetadataValue.int(int(stats["series_count"])),
            "date_range": MetadataValue.text(
                f"{stats['earliest_date']} to {stats['latest_date']}"
            ),
            "extraction_time": MetadataValue.text(str(stats["extraction_time"])),
        }
    )


@asset(
    group_name="extraction",
    description="Extract sales data from PostgreSQL to BigQuery using Meltano",
    compute_kind="meltano"
)
def postgres_sales_data(context: AssetExecutionContext) -> Output[dict]:
    """
    Run Meltano pipeline to extract sales data from PostgreSQL to BigQuery.
    
    This extracts all sales tables:
    - orders, customers, products
    - order_items, payments
    - sellers, reviews, geolocation
    """
    context.log.info("Starting Meltano extraction: PostgreSQL → BigQuery...")
    
    result = subprocess.run(
        ["meltano", "run", "tap-postgres", "target-bigquery"],
        cwd=PROJECT_ROOT.parent,  # Run from meltano project root
        capture_output=True,
        text=True,
        check=True
    )
    
    context.log.info(f"Meltano output:\n{result.stdout}")
    
    # Get row counts from BigQuery
    client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)
    
    tables = [
        "public-orders",
        "public-Order_Items",
        "public-order_payments",
        "public-Customers",
        "public-products"
    ]
    
    total_rows = 0
    for table in tables:
        query = f"SELECT COUNT(*) as cnt FROM `{BQ_PROJECT}.{BQ_DATASET}.{table}`"
        count = client.query(query).to_dataframe().iloc[0]["cnt"]
        total_rows += count
        context.log.info(f"Table {table}: {count:,} rows")
    
    return Output(
        value={"status": "success", "total_rows": total_rows},
        metadata={
            "total_rows": MetadataValue.int(total_rows),
            "tables_extracted": MetadataValue.int(len(tables)),
            "extraction_time": MetadataValue.text(datetime.now().isoformat()),
        }
    )


# ============================================================================
# TRANSFORMATION ASSETS - STAGING
# ============================================================================

@asset(
    group_name="transformation",
    description="Build dbt staging models (cleaned views of raw data)",
    deps=[bcb_economic_indicators, postgres_sales_data],
    compute_kind="dbt"
)
def dbt_staging_models(context: AssetExecutionContext) -> Output[dict]:
    """
    Build all dbt staging models.
    
    Creates cleaned views:
    - stg_orders, stg_customers, stg_products
    - stg_order_items, stg_bcb_indicators
    """
    context.log.info("Building dbt staging models...")

    result = subprocess.run(
        ["dbt", "run", "--select", "stg_*"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True
    )
    
    context.log.info(f"dbt staging output:\n{result.stdout}")
    
    # Parse dbt output for stats
    models_built = result.stdout.count("OK created")
    
    return Output(
        value={"status": "success", "models_built": models_built},
        metadata={
            "models_built": MetadataValue.int(models_built),
            "dbt_output": MetadataValue.text(result.stdout[-500:]),  # Last 500 chars
        }
    )


# ============================================================================
# TRANSFORMATION ASSETS - MARTS
# ============================================================================

@asset(
    group_name="transformation",
    description="Build dbt mart models (analytics tables with economic context)",
    deps=[dbt_staging_models],
    compute_kind="dbt"
)
def dbt_mart_models(context: AssetExecutionContext) -> Output[dict]:
    """
    Build all dbt mart models.
    
    Creates analytics tables:
    - fct_customer_purchases_economics
    - fct_category_performance_economics
    - fct_geographic_sales_economics
    - fct_orders_with_economics
    """
    context.log.info("Building dbt mart models...")

    result = subprocess.run(
        ["dbt", "run", "--select", "fct_*"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True
    )
    
    context.log.info(f"dbt marts output:\n{result.stdout}")
    
    # Get row counts from BigQuery
    client = bigquery.Client.from_service_account_json(CREDENTIALS_PATH)
    
    marts = {
        "fct_customer_purchases_economics": 0,
        "fct_category_performance_economics": 0,
        "fct_geographic_sales_economics": 0,
        "fct_orders_with_economics": 0,
    }
    
    for table_name in marts.keys():
        query = f"""
        SELECT COUNT(*) as cnt 
        FROM `{BQ_PROJECT}.brazilian_sales_marts.{table_name}`
        """
        marts[table_name] = int(client.query(query).to_dataframe().iloc[0]["cnt"])
        context.log.info(f"{table_name}: {marts[table_name]:,} rows")
    
    total_rows = sum(marts.values())
    
    return Output(
        value={"status": "success", "tables": marts, "total_rows": total_rows},
        metadata={
            "total_rows": MetadataValue.int(total_rows),
            "tables_created": MetadataValue.int(len(marts)),
            "row_counts": MetadataValue.md(
                "\n".join([f"- **{k}**: {v:,} rows" for k, v in marts.items()])
            ),
        }
    )


# ============================================================================
# DATA QUALITY ASSETS
# ============================================================================

@asset(
    group_name="quality",
    description="Run dbt data quality tests",
    deps=[dbt_mart_models],
    compute_kind="dbt"
)
def dbt_data_quality_tests(context: AssetExecutionContext) -> Output[dict]:
    """
    Run all dbt data quality tests.
    
    Tests include:
    - Primary key uniqueness
    - Not null constraints
    - Referential integrity
    - Business logic validations
    """
    context.log.info("Running dbt tests...")

    result = subprocess.run(
        ["dbt", "test"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    # Parse test results
    output = result.stdout
    context.log.info(f"dbt test output:\n{output}")
    
    # Extract test counts
    passed = output.count("PASS=")
    warned = output.count("WARN=")
    errors = output.count("ERROR=")
    
    # Parse the summary line
    summary_line = [line for line in output.split("\n") if "Done. PASS=" in line]
    test_stats = {
        "passed": 0,
        "warned": 0,
        "errors": 0,
        "total": 0
    }
    
    if summary_line:
        # Extract numbers from "Done. PASS=X WARN=Y ERROR=Z"
        parts = summary_line[0].split()
        for part in parts:
            if "PASS=" in part:
                test_stats["passed"] = int(part.split("=")[1])
            elif "WARN=" in part:
                test_stats["warned"] = int(part.split("=")[1])
            elif "ERROR=" in part:
                test_stats["errors"] = int(part.split("=")[1])
            elif "TOTAL=" in part:
                test_stats["total"] = int(part.split("=")[1])
    
    # Determine status
    if test_stats["errors"] > 0:
        status = "FAILED"
        context.log.error(f"Data quality tests FAILED: {test_stats['errors']} errors")
    elif test_stats["warned"] > 0:
        status = "WARNING"
        context.log.warning(f"Data quality tests completed with {test_stats['warned']} warnings")
    else:
        status = "SUCCESS"
        context.log.info("All data quality tests passed!")
    
    return Output(
        value={"status": status, "stats": test_stats},
        metadata={
            "test_status": MetadataValue.text(status),
            "tests_passed": MetadataValue.int(test_stats["passed"]),
            "tests_warned": MetadataValue.int(test_stats["warned"]),
            "tests_failed": MetadataValue.int(test_stats["errors"]),
            "total_tests": MetadataValue.int(test_stats["total"]),
            "test_results": MetadataValue.md(
                f"""
                ## Test Results
                - ✅ **Passed**: {test_stats['passed']}
                - ⚠️ **Warnings**: {test_stats['warned']}
                - ❌ **Errors**: {test_stats['errors']}
                - 📊 **Total**: {test_stats['total']}
                """
            ),
        }
    )


# ============================================================================
# CONSUMPTION ASSETS
# ============================================================================

@asset(
    group_name="consumption",
    description="Trigger Streamlit dashboard cache refresh",
    deps=[dbt_data_quality_tests],
    compute_kind="python"
)
def streamlit_cache_refresh(context: AssetExecutionContext) -> Output[dict]:
    """
    Clear Streamlit cache to show fresh data.
    
    This creates a trigger file that Streamlit can watch to know
    when to reload data from BigQuery.
    """
    context.log.info("Triggering Streamlit cache refresh...")
    
    # Create a timestamp file that Streamlit can check
    refresh_file = Path("/tmp/streamlit_refresh.txt")
    refresh_file.write_text(datetime.now().isoformat())
    
    context.log.info(f"Created refresh trigger: {refresh_file}")
    
    return Output(
        value={"status": "success", "timestamp": datetime.now().isoformat()},
        metadata={
            "refresh_time": MetadataValue.text(datetime.now().isoformat()),
            "trigger_file": MetadataValue.text(str(refresh_file)),
        }
    )


# ============================================================================
# MONITORING ASSETS
# ============================================================================

@asset(
    group_name="monitoring",
    description="Generate pipeline execution report",
    deps=[streamlit_cache_refresh],
    compute_kind="python"
)
def pipeline_execution_report(context: AssetExecutionContext) -> Output[dict]:
    """
    Generate a summary report of the pipeline execution.
    
    This can be extended to send emails, Slack messages, or
    save reports to cloud storage.
    """
    context.log.info("Generating pipeline execution report...")
    
    report = {
        "pipeline_name": "Brazilian Sales Analytics",
        "execution_time": datetime.now().isoformat(),
        "status": "SUCCESS",
        "assets_materialized": 8,
        "next_steps": [
            "Open Streamlit dashboard: http://localhost:8501",
            "Check BigQuery for updated tables",
            "Review data quality test results"
        ]
    }
    
    context.log.info(f"Pipeline report: {json.dumps(report, indent=2)}")
    
    return Output(
        value=report,
        metadata={
            "execution_summary": MetadataValue.md(
                f"""
                # Pipeline Execution Report
                
                **Pipeline**: {report['pipeline_name']}  
                **Time**: {report['execution_time']}  
                **Status**: ✅ {report['status']}  
                **Assets Materialized**: {report['assets_materialized']}
                
                ## Next Steps
                """ + "\n".join([f"- {step}" for step in report['next_steps']])
            ),
        }
    )
