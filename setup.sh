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

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Track if there were any errors
SETUP_FAILED=0

# Function to print error
print_error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
    SETUP_FAILED=1
}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Brazilian E-Commerce Analytics Platform - Project Setup${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Check if inside the correct conda environment
if [[ "$CONDA_DEFAULT_ENV" != "ds3" ]]; then
    echo -e "${RED}✗ This script must be run inside the 'ds3' conda environment.${NC}"
    echo -e "${YELLOW}Please create and activate the environment first:${NC}"
    echo -e "  1. conda env create -f environment.yml"
    echo -e "  2. conda activate ds3${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Running in conda environment: $CONDA_DEFAULT_ENV${NC}\n"
fi

# Check if uv is available
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠ uv package manager not found. Installing...${NC}"
    conda install -c conda-forge uv -y
    if ! command -v uv &> /dev/null; then
        print_error "Failed to install uv package manager."
        exit 1
    fi
    echo -e "${GREEN}✓ uv installed successfully.${NC}"
else
    echo -e "${GREEN}✓ uv package manager found.${NC}"
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in current directory."
    exit 1
fi
echo ""

# ============================================================================
# STEP 1: Install Python dependencies
# ============================================================================
echo -e "${YELLOW}[1/4] Installing Python dependencies...${NC}"
if uv pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Python dependencies installed.${NC}\n"
else
    print_error "Failed to install Python dependencies."
    exit 1
fi

# ============================================================================
# STEP 2: Verify and fix missing packages
# ============================================================================
echo -e "${YELLOW}[2/4] Verifying critical packages...${NC}"

# Check dbt
if ! command -v dbt &> /dev/null; then
    echo -e "${YELLOW}⚠ dbt command not found. Installing dbt packages...${NC}"
    uv pip install dbt-core==1.7.16 dbt-bigquery==1.7.9
fi

if command -v dbt &> /dev/null; then
    DBT_VERSION=$(dbt --version 2>&1 | head -1)
    echo -e "  ${GREEN}✓${NC} dbt: ${DBT_VERSION}"
else
    print_error "dbt installation failed."
fi

# Check Python packages and install if missing
PACKAGES_TO_CHECK=(
    "kaggle:kaggle==1.6.17"
    "dotenv:python-dotenv"
    "google.cloud.bigquery:google-cloud-bigquery"
    "dagster:dagster==1.6.6"
    "dagster_webserver:dagster-webserver==1.6.6"
    "dagster_dbt:dagster-dbt==0.22.6"
)

MISSING_PACKAGES=()
PACKAGES_TO_INSTALL=()

for package in "${PACKAGES_TO_CHECK[@]}"; do
    IFS=':' read -r import_name pip_name <<< "$package"

    if ! python -c "import ${import_name}" 2>/dev/null; then
        MISSING_PACKAGES+=("$import_name")
        PACKAGES_TO_INSTALL+=("$pip_name")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠ Missing packages detected: ${MISSING_PACKAGES[*]}${NC}"
    echo -e "${YELLOW}  Installing missing packages...${NC}"

    for pkg in "${PACKAGES_TO_INSTALL[@]}"; do
        echo -e "  Installing ${pkg}..."
        if uv pip install "$pkg"; then
            echo -e "  ${GREEN}✓${NC} ${pkg} installed"
        else
            print_error "Failed to install ${pkg}"
        fi
    done
    echo ""
fi

# Verify all packages again
echo -e "${YELLOW}  Verifying all packages...${NC}"
ALL_INSTALLED=1

for package in "${PACKAGES_TO_CHECK[@]}"; do
    IFS=':' read -r import_name pip_name <<< "$package"

    if python -c "import ${import_name}" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} ${import_name}"
    else
        echo -e "  ${RED}✗${NC} ${import_name} - NOT INSTALLED"
        ALL_INSTALLED=0
    fi
done

if [ $ALL_INSTALLED -eq 1 ]; then
    echo -e "${GREEN}✓ All critical packages verified.${NC}\n"
else
    echo -e "${RED}✗ Some packages failed to install. Please check the output above.${NC}\n"
    SETUP_FAILED=1
fi

# ============================================================================
# STEP 3: Install dbt packages
# ============================================================================
echo -e "${YELLOW}[3/4] Installing dbt packages...${NC}"

if [ ! -d "transform" ]; then
    print_error "transform/ directory not found."
    exit 1
fi

cd transform/ || exit 1

if [ ! -f "packages.yml" ]; then
    echo -e "${YELLOW}⚠ No packages.yml found, skipping dbt deps...${NC}\n"
    cd ..
else
    # Fix permissions on dbt_packages if it exists
    if [ -d "dbt_packages" ]; then
        echo -e "${YELLOW}  Cleaning existing dbt_packages directory...${NC}"

        # Try multiple methods to remove the directory
        chmod -R u+w dbt_packages 2>/dev/null || true

        if rm -rf dbt_packages 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Removed dbt_packages"
        else
            echo -e "${YELLOW}  ⚠ Could not remove dbt_packages with regular permissions.${NC}"
            echo -e "${YELLOW}  Trying with sudo (you may be prompted for password)...${NC}"

            if sudo rm -rf dbt_packages 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} Removed dbt_packages with sudo"
            else
                cd ..
                print_error "Failed to remove dbt_packages. Please manually run: sudo rm -rf transform/dbt_packages"
                exit 1
            fi
        fi
    fi

    # Install dbt packages
    echo -e "${YELLOW}  Running dbt deps...${NC}"
    if dbt deps; then
        echo -e "${GREEN}✓ dbt packages installed.${NC}\n"
    else
        cd ..
        print_error "Failed to install dbt packages."
        exit 1
    fi
    cd ..
fi

# ============================================================================
# STEP 4: Environment configuration
# ============================================================================
echo -e "${YELLOW}[4/4] Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    if [ ! -f ".env.example" ]; then
        print_error ".env.example template file not found."
        exit 1
    fi
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    if cp .env.example .env; then
        echo -e "${GREEN}✓ .env file created from template.${NC}"
        echo -e "${YELLOW}⚠ IMPORTANT: Edit .env with your credentials before running the pipeline.${NC}\n"
    else
        print_error "Failed to create .env file."
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists.${NC}\n"
fi

# ============================================================================
# Final Summary
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"

if [ $SETUP_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ Project setup complete! ✓✓✓${NC}\n"

    echo -e "${YELLOW}Installed components:${NC}"
    echo -e "  ✓ Python dependencies (150+ packages)"
    echo -e "  ✓ dbt-core $(dbt --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
    echo -e "  ✓ Dagster $(dagster --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
    echo -e "  ✓ dbt packages (dbt_utils, dbt_expectations)"
    echo -e "  ✓ Environment configuration (.env)"
    echo ""

    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Edit .env with your credentials:"
    echo -e "     ${BLUE}nano .env${NC}  or  ${BLUE}vim .env${NC}"
    echo -e ""
    echo -e "  2. Required credentials:"
    echo -e "     - GCP_PROJECT_ID"
    echo -e "     - GOOGLE_APPLICATION_CREDENTIALS"
    echo -e "     - KAGGLE_USERNAME"
    echo -e "     - KAGGLE_KEY"
    echo -e ""
    echo -e "  3. Run the pipeline:"
    echo -e "     ${GREEN}./run_pipeline.sh --full${NC}"
    echo -e ""
    echo -e "  4. Or launch Dagster orchestration:"
    echo -e "     ${GREEN}cd orchestration/dagster && dagster dev${NC}"
    echo -e ""
else
    echo -e "${RED}✗✗✗ Setup completed with errors ✗✗✗${NC}\n"
    echo -e "${YELLOW}Please review the errors above and try again.${NC}"
    echo -e "${YELLOW}You can also check SETUP_TROUBLESHOOTING.md for solutions.${NC}\n"
    exit 1
fi

echo -e "${BLUE}============================================================================${NC}"
