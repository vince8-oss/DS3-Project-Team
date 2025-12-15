#!/bin/bash
# ============================================================================
# Brazilian E-Commerce Analytics Platform - Setup Script
# ============================================================================
# This script sets up the development environment and installs dependencies
# Run this once after cloning the repository
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Brazilian E-Commerce Analytics Platform - Setup${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}\n"
else
    echo -e "${RED}✗ Python $REQUIRED_VERSION or higher required. Found $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}[2/7] Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}\n"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}\n"
fi

# Activate virtual environment
echo -e "${YELLOW}[3/7] Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Upgrade pip
echo -e "${YELLOW}[4/7] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}\n"

# Install Python dependencies
echo -e "${YELLOW}[5/7] Installing Python dependencies...${NC}"
echo -e "   ${BLUE}This may take a few minutes...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Install dbt dependencies
echo -e "${YELLOW}[6/7] Installing dbt packages...${NC}"
cd transform
dbt deps > /dev/null 2>&1
cd ..
echo -e "${GREEN}✓ dbt packages installed${NC}\n"

# Check for .env file
echo -e "${YELLOW}[7/7] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}→ Please edit .env with your credentials:${NC}"
    echo -e "   ${BLUE}- GCP_PROJECT_ID${NC}"
    echo -e "   ${BLUE}- GOOGLE_APPLICATION_CREDENTIALS${NC}"
    echo -e "   ${BLUE}- KAGGLE_USERNAME${NC}"
    echo -e "   ${BLUE}- KAGGLE_KEY${NC}\n"
else
    echo -e "${GREEN}✓ .env file exists${NC}\n"
fi

# Final instructions
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}\n"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. ${BLUE}Edit .env file with your credentials${NC}"
echo -e "  2. ${BLUE}Run the pipeline: ./run_pipeline.sh${NC}"
echo -e "  3. ${BLUE}Or run components individually (see README.md)${NC}\n"
echo -e "${YELLOW}To activate the virtual environment later:${NC}"
echo -e "  ${BLUE}source .venv/bin/activate${NC}\n"
echo -e "${BLUE}============================================================================${NC}"
