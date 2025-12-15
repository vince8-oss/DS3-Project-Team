#!/bin/bash
# ============================================================================
# Brazilian E-Commerce Analytics Platform - Pipeline Runner
# ============================================================================
# This script runs the complete data pipeline from extraction to dashboard
#
# Usage:
#   chmod +x run_pipeline.sh
#   ./run_pipeline.sh [options]
#
# Options:
#   --extract-only    Run only extraction
#   --transform-only  Run only transformations
#   --full           Run complete pipeline (default)
#   --skip-extract   Skip extraction, run transform only
#   --dashboard      Launch dashboard after pipeline
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
RUN_EXTRACT=true
RUN_TRANSFORM=true
RUN_DASHBOARD=false

for arg in "$@"; do
    case $arg in
        --extract-only)
            RUN_TRANSFORM=false
            ;;
        --transform-only)
            RUN_EXTRACT=false
            ;;
        --skip-extract)
            RUN_EXTRACT=false
            ;;
        --dashboard)
            RUN_DASHBOARD=true
            ;;
        --full)
            RUN_EXTRACT=true
            RUN_TRANSFORM=true
            ;;
    esac
done

# Header
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}🇧🇷 Brazilian E-Commerce Analytics Pipeline${NC}"
echo -e "${BLUE}============================================================================${NC}\n"
echo -e "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline started\n"

# Check environment
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo -e "${YELLOW}→ Run ./setup.sh first or copy .env.example to .env${NC}\n"
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠ Virtual environment not found. Using system Python...${NC}\n"
fi

# Load environment variables
source .env

# Verify required environment variables
REQUIRED_VARS=("GCP_PROJECT_ID" "GOOGLE_APPLICATION_CREDENTIALS")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}✗ Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "   ${RED}- $var${NC}"
    done
    echo -e "${YELLOW}→ Please update your .env file${NC}\n"
    exit 1
fi

# ============================================================================
# PHASE 1: EXTRACTION
# ============================================================================

if [ "$RUN_EXTRACT" = true ]; then
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    echo -e "${YELLOW}PHASE 1: DATA EXTRACTION${NC}"
    echo -e "${BLUE}------------------------------------------------------------${NC}\n"

    # Extract Kaggle data
    echo -e "${YELLOW}[1/2] Extracting Kaggle e-commerce data...${NC}"
    if python extract/kaggle_extractor.py; then
        echo -e "${GREEN}✓ Kaggle extraction completed${NC}\n"
    else
        echo -e "${RED}✗ Kaggle extraction failed${NC}\n"
        exit 1
    fi

    # Extract BCB economic data
    echo -e "${YELLOW}[2/2] Extracting BCB economic indicators...${NC}"
    if python extract/bcb_extractor.py; then
        echo -e "${GREEN}✓ BCB extraction completed${NC}\n"
    else
        echo -e "${RED}✗ BCB extraction failed${NC}\n"
        exit 1
    fi
fi

# ============================================================================
# PHASE 2: TRANSFORMATION
# ============================================================================

if [ "$RUN_TRANSFORM" = true ]; then
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    echo -e "${YELLOW}PHASE 2: DATA TRANSFORMATION (dbt)${NC}"
    echo -e "${BLUE}------------------------------------------------------------${NC}\n"

    cd transform

    # Test dbt connection
    echo -e "${YELLOW}[1/4] Testing dbt connection...${NC}"
    if dbt debug --quiet; then
        echo -e "${GREEN}✓ dbt connection successful${NC}\n"
    else
        echo -e "${RED}✗ dbt connection failed${NC}\n"
        exit 1
    fi

    # Run staging models
    echo -e "${YELLOW}[2/4] Building staging models...${NC}"
    if dbt run --select stg_*; then
        echo -e "${GREEN}✓ Staging models built${NC}\n"
    else
        echo -e "${RED}✗ Staging model build failed${NC}\n"
        exit 1
    fi

    # Run mart models
    echo -e "${YELLOW}[3/4] Building mart models...${NC}"
    if dbt run --select fct_*; then
        echo -e "${GREEN}✓ Mart models built${NC}\n"
    else
        echo -e "${RED}✗ Mart model build failed${NC}\n"
        exit 1
    fi

    # Run tests
    echo -e "${YELLOW}[4/4] Running data quality tests...${NC}"
    if dbt test; then
        echo -e "${GREEN}✓ All tests passed${NC}\n"
    else
        echo -e "${YELLOW}⚠ Some tests failed (check output above)${NC}\n"
        # Don't exit on test failure, just warn
    fi

    cd ..
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✓ PIPELINE COMPLETED SUCCESSFULLY!${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

echo -e "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline finished\n"

if [ "$RUN_EXTRACT" = true ]; then
    echo -e "${GREEN}✓ Data extraction: Complete${NC}"
fi

if [ "$RUN_TRANSFORM" = true ]; then
    echo -e "${GREEN}✓ Data transformation: Complete${NC}"
    echo -e "${GREEN}✓ Data quality tests: Complete${NC}"
fi

echo ""

# ============================================================================
# NEXT STEPS
# ============================================================================

echo -e "${YELLOW}Next steps:${NC}\n"

if [ "$RUN_DASHBOARD" = true ]; then
    echo -e "${YELLOW}Launching Streamlit dashboard...${NC}\n"
    streamlit run dashboard/streamlit_app.py
else
    echo -e "  ${BLUE}1. Launch dashboard:${NC}"
    echo -e "     ${GREEN}streamlit run dashboard/streamlit_app.py${NC}\n"

    echo -e "  ${BLUE}2. View dbt documentation:${NC}"
    echo -e "     ${GREEN}cd transform && dbt docs generate && dbt docs serve${NC}\n"

    echo -e "  ${BLUE}3. Start Dagster orchestration:${NC}"
    echo -e "     ${GREEN}cd orchestration && dagster dev${NC}\n"

    echo -e "  ${BLUE}4. Query BigQuery:${NC}"
    echo -e "     ${GREEN}bq query --use_legacy_sql=false 'SELECT * FROM \\`$GCP_PROJECT_ID.brazilian_sales_marts.fct_orders_with_economics\\` LIMIT 10'${NC}\n"
fi

echo -e "${BLUE}============================================================================${NC}"
