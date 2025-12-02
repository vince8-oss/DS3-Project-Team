from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets, DbtProject
from pathlib import Path
import os

# Define dbt project path
DBT_PROJECT_DIR = Path(__file__).joinpath("..", "..", "..", "dbt").resolve()

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
)

dbt_project.prepare_if_dev()

@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_warehouse_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
