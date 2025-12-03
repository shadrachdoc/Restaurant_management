#!/bin/bash

cd /home/shadrach/Restaurant_management
source venv/bin/activate

export DATABASE_URL="postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production-min-32-characters-long"
export SESSION_SECRET="your-super-secret-session-key-min-32-characters-long"
export APP_AUTH_SERVICE_PORT=8001

cd services/auth-service

echo "🔐 Starting Auth Service on port 8001..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
