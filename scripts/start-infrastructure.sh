#!/bin/bash

# Start infrastructure services only (PostgreSQL, Redis, RabbitMQ)
# Useful for local development when you want to run services manually

set -e

echo "🚀 Starting Restaurant Management Infrastructure..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "📦 Starting PostgreSQL..."
docker-compose up -d postgres

echo "🔴 Starting Redis..."
docker-compose up -d redis

echo "🐰 Starting RabbitMQ..."
docker-compose up -d rabbitmq

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U restaurant_admin > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet, you may need to wait a bit longer"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is not ready yet"
fi

echo ""
echo "✅ Infrastructure started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - RabbitMQ: localhost:5672"
echo "  - RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo ""
echo "To stop infrastructure: docker-compose down"
echo "To view logs: docker-compose logs -f postgres redis rabbitmq"
