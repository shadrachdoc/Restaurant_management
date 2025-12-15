#!/bin/bash

echo "🚀 Starting Customer Service..."
echo "================================"
echo ""
echo "Customer Service will run on: http://localhost:8007"
echo "API Documentation: http://localhost:8007/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Add project root to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

cd "$PROJECT_ROOT/services/customer-service"

# Activate virtual environment and run
source venv/bin/activate
python run.py
