#!/bin/bash

# Simple Backend Startup Script (Without Kubernetes)
# This runs the backend services directly for testing

echo "🚀 Starting Restaurant Management System Backend..."
echo ""

# Check if databases are running
echo "📊 Checking databases..."
if ! docker ps | grep -q restaurant-postgres; then
    echo "❌ PostgreSQL not running. Starting..."
    docker run -d --name restaurant-postgres \
        -e POSTGRES_USER=restaurant_admin \
        -e POSTGRES_PASSWORD=restaurant_pass_2024 \
        -e POSTGRES_DB=restaurant_db \
        -p 5432:5432 \
        postgres:15-alpine
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
fi

if ! docker ps | grep -q restaurant-redis; then
    echo "❌ Redis not running. Starting..."
    docker run -d --name restaurant-redis \
        -p 6379:6379 \
        redis:7-alpine
fi

echo "✅ Databases are running!"
echo ""

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production-min-32-characters-long"
export SESSION_SECRET="your-super-secret-session-key-min-32-characters-long"
export APP_AUTH_SERVICE_PORT=8001
export APP_RESTAURANT_SERVICE_PORT=8003

# Install Python dependencies if needed
echo "📦 Installing Python dependencies..."
cd /home/shadrach/Restaurant_management
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "🗄️  Running database migrations..."
cd services/auth-service
alembic upgrade head 2>/dev/null || echo "⚠️  Auth migrations skipped (tables may already exist)"

cd ../restaurant-service
alembic upgrade head 2>/dev/null || echo "⚠️  Restaurant migrations skipped (tables may already exist)"

cd ../..

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To start services manually, open 2 terminals and run:"
echo ""
echo "Terminal 1 - Auth Service:"
echo "  cd /home/shadrach/Restaurant_management"
echo "  source venv/bin/activate"
echo "  export DATABASE_URL=\"postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db\""
echo "  export JWT_SECRET_KEY=\"your-super-secret-jwt-key-change-in-production-min-32-characters-long\""
echo "  export APP_AUTH_SERVICE_PORT=8001"
echo "  cd services/auth-service"
echo "  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "Terminal 2 - Restaurant Service:"
echo "  cd /home/shadrach/Restaurant_management"
echo "  source venv/bin/activate"
echo "  export DATABASE_URL=\"postgresql+asyncpg://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db\""
echo "  export JWT_SECRET_KEY=\"your-super-secret-jwt-key-change-in-production-min-32-characters-long\""
echo "  export SESSION_SECRET=\"your-super-secret-session-key-min-32-characters-long\""
echo "  export APP_RESTAURANT_SERVICE_PORT=8003"
echo "  cd services/restaurant-service"
echo "  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"
echo ""
echo "Or use the screen sessions (run them in background):"
echo "  ./start-auth-service.sh"
echo "  ./start-restaurant-service.sh"
echo ""
