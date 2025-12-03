#!/bin/bash

# Start all services using Docker Compose

set -e

echo "🚀 Starting Restaurant Management System (All Services)..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update values if needed."
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "🏗️  Building and starting all services..."
docker-compose up --build -d

echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check service health
echo ""
echo "🔍 Checking service health..."

services=("postgres" "redis" "rabbitmq")
for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
    fi
done

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Gateway: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Auth Service: http://localhost:8001"
echo "  - Restaurant Service: http://localhost:8003"
echo "  - Order Service: http://localhost:8004"
echo "  - Kitchen Service: http://localhost:8005"
echo "  - RabbitMQ Management: http://localhost:15672"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose logs -f [service-name]"
echo "  - Stop all: docker-compose down"
echo "  - Restart service: docker-compose restart [service-name]"
echo ""
