#!/bin/bash
set -e

echo "🧪 Activity Heatmap Mobile App Tests"
echo "============================================"

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source test_venv/bin/activate

# Run the enhanced test suite
echo "🚀 Running core tests with enhanced runner..."
python run_tests.py

echo "🎉 Testing complete!"