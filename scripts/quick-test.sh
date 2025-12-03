#!/bin/bash

# Quick test script - starts infrastructure and runs tests

set -e

echo "🚀 Quick Test - Restaurant Service"
echo "==================================="
echo ""

# Check if infrastructure is running
if ! docker ps | grep -q restaurant-postgres; then
    echo "📦 Starting infrastructure (PostgreSQL, Redis, RabbitMQ)..."
    ./scripts/start-infrastructure.sh
    echo "⏳ Waiting for services to be ready (15 seconds)..."
    sleep 15
else
    echo "✓ Infrastructure is already running"
fi

echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Run ./scripts/setup-project.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start Restaurant Service in background
echo "🔧 Starting Restaurant Service..."
cd services/restaurant-service
uvicorn app.main:app --port 8003 > /tmp/restaurant-service.log 2>&1 &
SERVICE_PID=$!
cd ../..

echo "⏳ Waiting for service to start (5 seconds)..."
sleep 5

# Check if service is running
if ! curl -s http://localhost:8003/health > /dev/null; then
    echo "❌ Service failed to start. Check logs:"
    tail -20 /tmp/restaurant-service.log
    kill $SERVICE_PID 2>/dev/null || true
    exit 1
fi

echo "✓ Service is running"
echo ""

# Run automated tests
echo "🧪 Running automated tests..."
echo ""
./scripts/test-restaurant-service.sh

# Ask if user wants to keep service running
echo ""
read -p "Keep service running for manual testing? (y/n): " keep_running

if [ "$keep_running" != "y" ]; then
    echo "🛑 Stopping Restaurant Service..."
    kill $SERVICE_PID
    echo "✓ Service stopped"
else
    echo ""
    echo "✅ Service is running at: http://localhost:8003"
    echo "📚 API Documentation: http://localhost:8003/docs"
    echo ""
    echo "To stop the service:"
    echo "  kill $SERVICE_PID"
    echo ""
    echo "View logs:"
    echo "  tail -f /tmp/restaurant-service.log"
    echo ""
fi
