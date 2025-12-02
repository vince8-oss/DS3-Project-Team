from dagster import Definitions, load_assets_from_modules, ScheduleDefinition, define_asset_job
from dagster_dbt import DbtCliResource
from .assets import ingestion, dbt
import os

# Load assets
ingestion_assets = load_assets_from_modules([ingestion])
dbt_assets = load_assets_from_modules([dbt])

# Define job
daily_pipeline_job = define_asset_job(
    name="daily_pipeline_job",
    selection=ingestion_assets + dbt_assets
)

# Define schedule
daily_schedule = ScheduleDefinition(
    job=daily_pipeline_job,
    cron_schedule="0 0 * * *",  # Daily at midnight
)

# Resources
resources = {
    "dbt": DbtCliResource(project_dir=os.path.abspath("dbt")),
}

defs = Definitions(
    assets=ingestion_assets + dbt_assets,
    schedules=[daily_schedule],
    jobs=[daily_pipeline_job],
    resources=resources,
)
