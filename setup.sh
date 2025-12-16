#!/bin/bash
# ============================================================================
# Brazilian E-Commerce Analytics Platform - Project Setup Script
# ============================================================================
# This script completes the project setup after the conda environment
# has been created and activated.
#
# Pre-requisites:
#   1. Create conda env: conda env create -f environment.yml
#   2. Activate conda env: conda activate ds3
#
# Usage:
#   ./setup.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print error and exit
error_exit() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
    exit 1
}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Brazilian E-Commerce Analytics Platform - Project Setup${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Check if inside the correct conda environment
if [[ "$CONDA_DEFAULT_ENV" != "ds3" ]]; then
    echo -e "${RED}✗ This script must be run inside the 'ds3' conda environment.${NC}"
    echo -e "${YELLOW}Please create and activate the environment first:${NC}"
    echo -e "  1. conda env create -f environment.yml${NC}"
    echo -e "  2. conda activate ds3${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Running in conda environment: $CONDA_DEFAULT_ENV${NC}\n"
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    error_exit "uv package manager not found. Please install it in the conda environment."
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    error_exit "requirements.txt not found in current directory."
fi

# Install Python dependencies using uv
echo -e "${YELLOW}[1/3] Installing Python dependencies with uv...${NC}"
if uv pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Python dependencies installed.${NC}\n"
else
    error_exit "Failed to install Python dependencies."
fi

# Verify critical packages are installed
echo -e "${YELLOW}Verifying installation...${NC}"

# Test dbt command
if ! command -v dbt &> /dev/null; then
    error_exit "dbt command not found. dbt-core may not be installed correctly."
fi

# Test dbt version to ensure it's working
DBT_VERSION=$(dbt --version 2>&1 | head -1)
if [[ $? -ne 0 ]]; then
    error_exit "dbt command failed. Please check the installation."
fi
echo -e "  ${GREEN}✓${NC} dbt: ${DBT_VERSION}"

# Verify Python packages
MISSING_PACKAGES=()

if ! python -c "import kaggle" 2>/dev/null; then
    MISSING_PACKAGES+=("kaggle")
fi

if ! python -c "import dotenv" 2>/dev/null; then
    MISSING_PACKAGES+=("python-dotenv")
fi

if ! python -c "import google.cloud.bigquery" 2>/dev/null; then
    MISSING_PACKAGES+=("google-cloud-bigquery")
fi

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${RED}✗ Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    error_exit "Some critical packages are not installed. Please check the output above."
fi

echo -e "  ${GREEN}✓${NC} Python packages: kaggle, dotenv, google-cloud-bigquery"
echo -e "${GREEN}✓ All critical packages verified.${NC}\n"

# Install dbt dependencies
echo -e "${YELLOW}[2/3] Installing dbt packages...${NC}"
if [ ! -d "transform" ]; then
    error_exit "transform/ directory not found."
fi

cd transform/ || error_exit "Failed to change to transform/ directory."

if [ ! -f "packages.yml" ]; then
    echo -e "${YELLOW}⚠ No packages.yml found, skipping dbt deps...${NC}\n"
    cd ..
else
    # Fix permissions on dbt_packages if it exists
    if [ -d "dbt_packages" ]; then
        echo -e "${YELLOW}  Cleaning existing dbt_packages directory...${NC}"
        chmod -R u+w dbt_packages 2>/dev/null || true
        rm -rf dbt_packages 2>/dev/null || {
            echo -e "${YELLOW}  ⚠ Could not remove dbt_packages, trying with sudo...${NC}"
            sudo rm -rf dbt_packages || {
                cd ..
                error_exit "Failed to remove dbt_packages directory. Please run: sudo rm -rf transform/dbt_packages"
            }
        }
    fi

    if dbt deps; then
        echo -e "${GREEN}✓ dbt packages installed.${NC}\n"
    else
        cd ..
        error_exit "Failed to install dbt packages."
    fi
    cd ..
fi

# Check for .env file
echo -e "${YELLOW}[3/3] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ ! -f ".env.example" ]; then
        error_exit ".env.example template file not found."
    fi
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    cp .env.example .env || error_exit "Failed to create .env file."
    echo -e "${GREEN}✓ .env file created from template.${NC}\n"
else
    echo -e "${GREEN}✓ .env file exists.${NC}\n"
fi

echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✓ Project setup complete!${NC}\n"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Edit .env with your credentials (GCP project, service account, etc.)"
echo -e "  2. Run the pipeline: ${GREEN}./run_pipeline.sh --full${NC}\n"
echo -e "${BLUE}============================================================================${NC}"
