#!/bin/bash

# Initialize Restaurant Service Database

echo "🗄️  Initializing Restaurant Service Database..."

# Kill any existing restaurant service
echo "Stopping existing restaurant service..."
sudo pkill -f "uvicorn.*8003" 2>/dev/null || true
sleep 2

# Activate virtual environment
source venv/bin/activate

# Start restaurant service with reload
echo "Starting Restaurant Service on port 8003..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload --app-dir services/restaurant-service > /tmp/restaurant.log 2>&1 &

# Wait for service to initialize
echo "Waiting for service to initialize..."
sleep 5

# Check if service is running
if curl -s http://localhost:8003/health | grep -q "healthy"; then
    echo "✅ Restaurant Service started successfully!"
    echo "📋 Check logs: tail -f /tmp/restaurant.log"
else
    echo "❌ Failed to start Restaurant Service"
    echo "Check logs: tail -100 /tmp/restaurant.log"
    exit 1
fi
