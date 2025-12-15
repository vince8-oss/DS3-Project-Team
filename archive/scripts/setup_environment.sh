#!/bin/bash
# Brazilian Sales Analytics - Environment Setup Script
# This script helps set up the development environment

set -e  # Exit on error

echo "======================================================================"
echo "🚀 Brazilian Sales Analytics - Environment Setup"
echo "======================================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please edit it with your credentials!${NC}"
    echo ""
    echo "Required configuration:"
    echo "  - GCP_PROJECT_ID"
    echo "  - GOOGLE_APPLICATION_CREDENTIALS"
    echo "  - KAGGLE_USERNAME"
    echo "  - KAGGLE_KEY"
    echo ""
    read -p "Press Enter after you've configured .env file..."
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python version: $python_version${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_unified.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Install Meltano plugins
echo ""
echo "Installing Meltano plugins..."
cd pipeline/load
meltano install
cd ../..
echo -e "${GREEN}✅ Meltano plugins installed${NC}"

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p pipeline/transform/target
mkdir -p pipeline/transform/logs
echo -e "${GREEN}✅ Data directories created${NC}"

# Check if dbt packages need to be installed
if [ -f "pipeline/transform/packages.yml" ]; then
    echo ""
    echo "Installing dbt packages..."
    cd pipeline/transform
    dbt deps --profiles-dir .
    cd ../..
    echo -e "${GREEN}✅ dbt packages installed${NC}"
fi

# Summary
echo ""
echo "======================================================================"
echo -e "${GREEN}✅ Environment setup complete!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Verify your .env configuration"
echo "  2. Test extraction: python scripts/run_pipeline.py --extract"
echo "  3. Run full pipeline: python scripts/run_pipeline.py --full"
echo "  4. Launch dashboard: streamlit run visualization/dashboard.py"
echo ""
echo "For detailed instructions, see:"
echo "  - README_UNIFIED.md"
echo "  - docs/PRESENTATION_GUIDE.md"
echo ""
echo "Happy coding! 🎉"
echo ""
