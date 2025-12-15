#!/usr/bin/env python3
"""
Brazilian Sales Analytics - Master Pipeline Orchestrator
Runs the complete ELT pipeline: Extract → Load → Transform → Validate

Usage:
    python scripts/run_pipeline.py --full              # Run complete pipeline
    python scripts/run_pipeline.py --extract           # Extract only
    python scripts/run_pipeline.py --load              # Load only
    python scripts/run_pipeline.py --transform         # Transform only
    python scripts/run_pipeline.py --no-bcb            # Skip BCB economic data
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv()


class PipelineOrchestrator:
    """Orchestrates the complete data pipeline"""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.start_time = datetime.now()
        self.project_root = PROJECT_ROOT

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "STEP": "🔄"
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")

    def run_command(self, command, cwd=None, description=None):
        """Run shell command and handle errors"""
        if description:
            self.log(description, "STEP")

        if self.verbose:
            self.log(f"Running: {command}", "INFO")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=not self.verbose,
                text=True
            )
            if result.stdout and not self.verbose:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", "ERROR")
            if e.stderr:
                print(e.stderr)
            return False

    def extract_kaggle(self):
        """Extract data from Kaggle"""
        self.log("=" * 70, "INFO")
        self.log("STEP 1: Extract Kaggle Data", "STEP")
        self.log("=" * 70, "INFO")

        success = self.run_command(
            "python -m pipeline.extract.kaggle_extract",
            description="Downloading Brazilian e-commerce dataset from Kaggle..."
        )

        if success:
            self.log("Kaggle data extraction completed", "SUCCESS")
        else:
            self.log("Kaggle data extraction failed", "ERROR")
            raise Exception("Failed to extract Kaggle data")

        return success

    def extract_bcb(self):
        """Extract Brazilian Central Bank economic data"""
        self.log("=" * 70, "INFO")
        self.log("STEP 2: Extract BCB Economic Data", "STEP")
        self.log("=" * 70, "INFO")

        success = self.run_command(
            "python -m pipeline.extract.bcb_extract",
            description="Fetching economic indicators from BCB API..."
        )

        if success:
            self.log("BCB economic data extraction completed", "SUCCESS")
        else:
            self.log("BCB economic data extraction failed (continuing...)", "WARNING")

        return success

    def load_to_bigquery(self):
        """Load data to BigQuery using Meltano"""
        self.log("=" * 70, "INFO")
        self.log("STEP 3: Load Data to BigQuery", "STEP")
        self.log("=" * 70, "INFO")

        # Change to pipeline/load directory where meltano.yml is located
        meltano_dir = self.project_root / "pipeline" / "load"

        success = self.run_command(
            "meltano run tap-csv target-bigquery",
            cwd=meltano_dir,
            description="Loading CSV files to BigQuery using Meltano..."
        )

        if success:
            self.log("Data load to BigQuery completed", "SUCCESS")
        else:
            self.log("Data load to BigQuery failed", "ERROR")
            raise Exception("Failed to load data to BigQuery")

        return success

    def transform_with_dbt(self):
        """Transform data using dbt"""
        self.log("=" * 70, "INFO")
        self.log("STEP 4: Transform Data with dbt", "STEP")
        self.log("=" * 70, "INFO")

        dbt_dir = self.project_root / "pipeline" / "transform"

        # Install dbt dependencies
        self.run_command(
            "dbt deps",
            cwd=dbt_dir,
            description="Installing dbt dependencies..."
        )

        # Run dbt models
        success = self.run_command(
            "dbt run --profiles-dir .",
            cwd=dbt_dir,
            description="Running dbt transformations..."
        )

        if not success:
            self.log("dbt transformations failed", "ERROR")
            raise Exception("Failed to run dbt transformations")

        # Run dbt tests
        test_success = self.run_command(
            "dbt test --profiles-dir .",
            cwd=dbt_dir,
            description="Running dbt tests..."
        )

        if test_success:
            self.log("dbt transformations and tests completed", "SUCCESS")
        else:
            self.log("dbt tests had failures (check output above)", "WARNING")

        return success

    def validate_pipeline(self):
        """Validate pipeline results"""
        self.log("=" * 70, "INFO")
        self.log("STEP 5: Validate Pipeline Results", "STEP")
        self.log("=" * 70, "INFO")

        # Run validation script if it exists
        validation_script = self.project_root / "scripts" / "validate_data.py"
        if validation_script.exists():
            success = self.run_command(
                f"python {validation_script}",
                description="Running data validation checks..."
            )
            if success:
                self.log("Data validation passed", "SUCCESS")
            else:
                self.log("Data validation had warnings", "WARNING")
        else:
            self.log("No validation script found, skipping...", "INFO")

    def print_summary(self):
        """Print pipeline execution summary"""
        duration = datetime.now() - self.start_time
        self.log("=" * 70, "INFO")
        self.log("PIPELINE EXECUTION SUMMARY", "SUCCESS")
        self.log("=" * 70, "INFO")
        self.log(f"Total execution time: {duration}", "INFO")
        self.log("=" * 70, "INFO")

    def run_full_pipeline(self, skip_bcb=False):
        """Run the complete pipeline"""
        try:
            self.log("=" * 70, "INFO")
            self.log("🚀 BRAZILIAN SALES ANALYTICS PIPELINE", "INFO")
            self.log("=" * 70, "INFO")

            # Extract
            self.extract_kaggle()
            if not skip_bcb:
                self.extract_bcb()

            # Load
            self.load_to_bigquery()

            # Transform
            self.transform_with_dbt()

            # Validate
            self.validate_pipeline()

            # Summary
            self.print_summary()

            self.log("Pipeline completed successfully! 🎉", "SUCCESS")
            return 0

        except Exception as e:
            self.log(f"Pipeline failed: {e}", "ERROR")
            self.print_summary()
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Brazilian Sales Analytics Pipeline Orchestrator"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run complete pipeline (Extract → Load → Transform)"
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Run extraction only (Kaggle + BCB)"
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Run load to BigQuery only"
    )
    parser.add_argument(
        "--transform",
        action="store_true",
        help="Run dbt transformations only"
    )
    parser.add_argument(
        "--no-bcb",
        action="store_true",
        help="Skip BCB economic data extraction"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = PipelineOrchestrator(verbose=not args.quiet)

    # Determine what to run
    if args.extract:
        orchestrator.extract_kaggle()
        if not args.no_bcb:
            orchestrator.extract_bcb()
        return 0
    elif args.load:
        return 0 if orchestrator.load_to_bigquery() else 1
    elif args.transform:
        return 0 if orchestrator.transform_with_dbt() else 1
    elif args.full or len(sys.argv) == 1:
        # Default to full pipeline if no arguments
        return orchestrator.run_full_pipeline(skip_bcb=args.no_bcb)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
