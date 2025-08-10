#!/bin/bash
# Wrapper script for manual testing
# Usage: ./manual_test.sh [options]

cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d "test_venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source test_venv/bin/activate
else
    echo "⚠️  Warning: test_venv not found, using system Python"
fi

python3 manual_test.py "$@"