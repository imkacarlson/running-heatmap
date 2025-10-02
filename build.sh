#!/bin/bash

set -e  # Exit on error

echo "=== Processing data and building mobile app ==="
echo ""

# Navigate to server directory
cd server

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Process data
echo ""
echo "=== Processing data ==="
python process_data.py

# Build mobile app
echo ""
echo "=== Building mobile app ==="
python build_mobile.py

echo ""
echo "=== Build complete! ==="
