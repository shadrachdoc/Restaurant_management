#!/bin/bash

cd /home/shadrach/Restaurant_management
source venv/bin/activate

# Database configuration
export DATABASE_URL="postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"
export POSTGRES_USER="restaurant_admin"
export POSTGRES_PASSWORD="restaurant_pass_2024"
export POSTGRES_DB="restaurant_db"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"

# Redis
export REDIS_URL="redis://localhost:6379"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Security
export JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production-min-32-characters-long"
export SESSION_SECRET="your-super-secret-session-key-min-32-characters-long"

# Service configuration
export APP_RESTAURANT_SERVICE_PORT=8003
export QR_CODE_BASE_URL="http://192.168.86.142:5173/menu"
export ENVIRONMENT="development"

export PYTHONPATH="/home/shadrach/Restaurant_management:${PYTHONPATH}"
cd services/restaurant-service

echo "🍽️  Starting Restaurant Service on port 8003..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
