#!/bin/bash
# Setup script for SpreadsheetBench without Docker
# Supports Ubuntu environment

set -e

echo "========================================"
echo "SpreadsheetBench Local Setup (No Docker)"
echo "========================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo "Error: Python 3.8+ is required"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Jupyter kernel
echo "Installing Python kernel for Jupyter..."
python -m ipykernel install --user --name python3 --display-name "Python 3"

# Create necessary directories
mkdir -p inference/outputs
mkdir -p inference/log

echo "========================================"
echo "Setup completed successfully!"
echo ""
echo "Usage:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Set local mode: export USE_LOCAL_KERNEL=1"
echo "  3. Run inference: cd inference && python inference_single.py --model your_model --base_url http://localhost:8000/v1 --api_key your_key"
echo "========================================"
