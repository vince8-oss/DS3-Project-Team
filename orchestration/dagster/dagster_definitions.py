"""
Dagster Definitions and Schedules for Brazilian Sales Pipeline

This module defines jobs, schedules, and sensors for orchestrating
the Brazilian e-commerce sales analytics pipeline.
"""

from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    AssetSelection,
    RunRequest,
    SkipReason,
    sensor,
    DefaultSensorStatus,
)
from dagster_assets import (
    bcb_economic_indicators,
    postgres_sales_data,
    dbt_staging_models,
    dbt_mart_models,
    dbt_data_quality_tests,
    streamlit_cache_refresh,
    pipeline_execution_report,
)
from datetime import datetime
from pathlib import Path


# ============================================================================
# JOBS
# ============================================================================

# Full daily pipeline - runs everything
daily_full_pipeline = define_asset_job(
    name="daily_full_pipeline",
    description="Complete daily refresh: extract → transform → test → refresh dashboard",
    selection=AssetSelection.all(),
    tags={"pipeline": "full", "frequency": "daily"}
)

# Quick economic update - just BCB data and dependent models
economic_update_pipeline = define_asset_job(
    name="economic_update_pipeline",
    description="Quick update: BCB data → dbt marts → tests",
    selection=AssetSelection.assets(
        bcb_economic_indicators,
        dbt_staging_models,
        dbt_mart_models,
        dbt_data_quality_tests,
        streamlit_cache_refresh,
    ),
    tags={"pipeline": "economic", "frequency": "multiple"}
)

# Data quality check only - run tests without rebuilding
quality_check_pipeline = define_asset_job(
    name="quality_check_pipeline",
    description="Run data quality tests only",
    selection=AssetSelection.assets(dbt_data_quality_tests),
    tags={"pipeline": "quality", "frequency": "hourly"}
)

# Sales data refresh - PostgreSQL extraction and dependent transforms
sales_refresh_pipeline = define_asset_job(
    name="sales_refresh_pipeline",
    description="Refresh sales data: PostgreSQL → staging → marts",
    selection=AssetSelection.assets(
        postgres_sales_data,
        dbt_staging_models,
        dbt_mart_models,
        dbt_data_quality_tests,
    ),
    tags={"pipeline": "sales", "frequency": "weekly"}
)


# ============================================================================
# SCHEDULES
# ============================================================================

# Daily full refresh at 6 AM
daily_morning_refresh = ScheduleDefinition(
    name="daily_morning_refresh",
    job=daily_full_pipeline,
    cron_schedule="0 6 * * *",  # 6 AM every day
    description="Daily full pipeline: extract all data, transform, test, and refresh dashboard",
    tags={"schedule": "production", "priority": "high"}
)

# Afternoon economic update at 2 PM (after BCB typically publishes data)
afternoon_economic_update = ScheduleDefinition(
    name="afternoon_economic_update",
    job=economic_update_pipeline,
    cron_schedule="0 14 * * *",  # 2 PM every day
    description="Afternoon BCB data refresh and dependent models",
    tags={"schedule": "production", "priority": "medium"}
)

# Hourly quality checks (8 AM - 6 PM, weekdays only)
hourly_quality_checks = ScheduleDefinition(
    name="hourly_quality_checks",
    job=quality_check_pipeline,
    cron_schedule="0 8-18 * * 1-5",  # Every hour 8 AM-6 PM, Mon-Fri
    description="Hourly data quality validation during business hours",
    tags={"schedule": "monitoring", "priority": "low"}
)

# Weekly full sales refresh (Sundays at 3 AM)
weekly_sales_refresh = ScheduleDefinition(
    name="weekly_sales_refresh",
    job=sales_refresh_pipeline,
    cron_schedule="0 3 * * 0",  # 3 AM every Sunday
    description="Weekly complete sales data refresh from PostgreSQL",
    tags={"schedule": "maintenance", "priority": "medium"}
)


# ============================================================================
# SENSORS
# ============================================================================

@sensor(
    name="bcb_data_freshness_sensor",
    job=economic_update_pipeline,
    minimum_interval_seconds=3600,  # Check every hour
    default_status=DefaultSensorStatus.STOPPED,  # Start disabled
    description="Trigger economic update when BCB data is stale (>24 hours old)"
)
def bcb_data_freshness_sensor(context):
    """
    Monitor BCB data freshness and trigger update if data is stale.
    
    This sensor checks if the BCB economic indicators table has been
    updated in the last 24 hours. If not, it triggers a refresh.
    """
    from google.cloud import bigquery
    
    credentials_path = "/home/eugen/ProjectM2/meltano-bigquery-py311/apc-data-science-and-ai-1c8f5b9e267b.json"
    client = bigquery.Client.from_service_account_json(credentials_path)
    
    query = """
    SELECT 
        MAX(extracted_at) as last_update,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(extracted_at), HOUR) as hours_since_update
    FROM `apc-data-science-and-ai.brazilian_sales.bcb_economic_indicators`
    """
    
    try:
        result = client.query(query).to_dataframe().iloc[0]
        hours_old = result["hours_since_update"]
        
        context.log.info(f"BCB data is {hours_old} hours old")
        
        if hours_old > 24:
            context.log.warning(f"BCB data is stale ({hours_old} hours old). Triggering refresh...")
            return RunRequest(
                run_key=f"bcb_refresh_{datetime.now().isoformat()}",
                tags={"trigger": "sensor", "reason": "stale_data"}
            )
        else:
            return SkipReason(f"BCB data is fresh ({hours_old} hours old)")
            
    except Exception as e:
        context.log.error(f"Error checking BCB data freshness: {e}")
        return SkipReason(f"Error: {e}")


@sensor(
    name="streamlit_refresh_sensor",
    job=define_asset_job(
        name="streamlit_only_refresh",
        selection=AssetSelection.assets(streamlit_cache_refresh)
    ),
    minimum_interval_seconds=300,  # Check every 5 minutes
    default_status=DefaultSensorStatus.STOPPED,  # Start disabled
    description="Trigger Streamlit refresh when data tables are updated"
)
def streamlit_refresh_sensor(context):
    """
    Monitor BigQuery tables and trigger Streamlit refresh when they're updated.
    
    This checks the modification time of mart tables and triggers a
    Streamlit cache refresh if they've been updated recently.
    """
    from google.cloud import bigquery
    
    credentials_path = "/home/eugen/ProjectM2/meltano-bigquery-py311/apc-data-science-and-ai-1c8f5b9e267b.json"
    client = bigquery.Client.from_service_account_json(credentials_path)
    
    # Check if any mart tables were modified in last 10 minutes
    query = """
    SELECT 
        table_name,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), 
                      TIMESTAMP_MILLIS(last_modified_time), 
                      MINUTE) as minutes_since_update
    FROM `apc-data-science-and-ai.brazilian_sales_marts.__TABLES__`
    WHERE table_name LIKE 'fct_%'
    ORDER BY last_modified_time DESC
    LIMIT 1
    """
    
    try:
        result = client.query(query).to_dataframe()
        
        if result.empty:
            return SkipReason("No mart tables found")
        
        latest_update = result.iloc[0]
        minutes_old = latest_update["minutes_since_update"]
        table_name = latest_update["table_name"]
        
        context.log.info(f"Latest table update: {table_name} ({minutes_old} min ago)")
        
        if minutes_old < 10:
            context.log.info(f"Tables recently updated. Triggering Streamlit refresh...")
            return RunRequest(
                run_key=f"streamlit_refresh_{datetime.now().isoformat()}",
                tags={"trigger": "sensor", "reason": "tables_updated", "table": table_name}
            )
        else:
            return SkipReason(f"No recent table updates ({minutes_old} min since last)")
            
    except Exception as e:
        context.log.error(f"Error checking table freshness: {e}")
        return SkipReason(f"Error: {e}")


# ============================================================================
# RESOURCE DEFINITIONS
# ============================================================================

from dagster import ConfigurableResource

class BigQueryResource(ConfigurableResource):
    """BigQuery client resource"""
    project_id: str
    credentials_path: str
    
    def get_client(self):
        from google.cloud import bigquery
        return bigquery.Client.from_service_account_json(self.credentials_path)


class DBTResource(ConfigurableResource):
    """dbt CLI resource"""
    project_dir: str
    profiles_dir: str = None
    
    def run_command(self, command: str):
        import subprocess
        args = ["dbt"] + command.split()
        return subprocess.run(
            args,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            check=True
        )


# ============================================================================
# DEFINITIONS
# ============================================================================

defs = Definitions(
    assets=[
        bcb_economic_indicators,
        postgres_sales_data,
        dbt_staging_models,
        dbt_mart_models,
        dbt_data_quality_tests,
        streamlit_cache_refresh,
        pipeline_execution_report,
    ],
    jobs=[
        daily_full_pipeline,
        economic_update_pipeline,
        quality_check_pipeline,
        sales_refresh_pipeline,
    ],
    schedules=[
        daily_morning_refresh,
        afternoon_economic_update,
        hourly_quality_checks,
        weekly_sales_refresh,
    ],
    sensors=[
        bcb_data_freshness_sensor,
        streamlit_refresh_sensor,
    ],
    resources={
        "bigquery": BigQueryResource(
            project_id="apc-data-science-and-ai",
            credentials_path="/home/eugen/ProjectM2/meltano-bigquery-py311/apc-data-science-and-ai-1c8f5b9e267b.json"
        ),
        "dbt": DBTResource(
            project_dir="/home/eugen/ProjectM2/meltano-bigquery-py311/Brazilian_Sales"
        ),
    },
)
