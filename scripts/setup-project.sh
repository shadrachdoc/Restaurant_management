#!/bin/bash

# Initial project setup script

set -e

echo "🎉 Restaurant Management System - Initial Setup"
echo "=============================================="
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }

echo "✅ All prerequisites found"
echo ""

# Create .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please review .env and update sensitive values (JWT_SECRET_KEY, passwords, etc.)"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Create upload directory
echo "📁 Creating upload directory..."
mkdir -p uploads
chmod 755 uploads
echo "✅ Upload directory created"
echo ""

# Initialize database directory
echo "🗄️  Creating database init script directory..."
mkdir -p infrastructure/docker/postgres
echo "✅ Directory created"
echo ""

echo "✅ Setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Review and update the .env file with your configurations"
echo "2. Start infrastructure: ./scripts/start-infrastructure.sh"
echo "3. Run database migrations (once implemented)"
echo "4. Start all services: ./scripts/start-all-services.sh"
echo ""
echo "For development:"
echo "- Activate venv: source venv/bin/activate"
echo "- Run individual service: cd services/[service-name] && uvicorn app.main:app --reload"
echo ""
