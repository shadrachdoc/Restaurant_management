# Quick Start Guide

Get the Restaurant Management System up and running in minutes!

## Prerequisites

Ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/)

## 🚀 Quick Start (Docker - Recommended)

### 1. Clone and Setup

```bash
# Clone the repository
cd Restaurant_management

# Run initial setup
chmod +x scripts/*.sh
./scripts/setup-project.sh
```

### 2. Review Configuration

Open `.env` file and update values if needed (especially for production):

```bash
nano .env  # or use your preferred editor
```

Key values to review:
- `JWT_SECRET_KEY` - Change for production
- `SESSION_SECRET` - Change for production
- `POSTGRES_PASSWORD` - Change for production

### 3. Start All Services

```bash
./scripts/start-all-services.sh
```

This will:
- Start PostgreSQL database
- Start Redis cache
- Start RabbitMQ message broker
- Build and start all microservices
- Start the React frontend

### 4. Access the Application

Once all services are running:

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🛠️ Development Setup

For active development, you may want to run services individually:

### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Infrastructure Only

```bash
./scripts/start-infrastructure.sh
```

This starts only PostgreSQL, Redis, and RabbitMQ.

### 3. Run Individual Services

Open separate terminals for each service:

**Terminal 1 - Auth Service:**
```bash
source venv/bin/activate
cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - Restaurant Service:**
```bash
source venv/bin/activate
cd services/restaurant-service
uvicorn app.main:app --reload --port 8003
```

**Terminal 3 - Order Service:**
```bash
source venv/bin/activate
cd services/order-service
uvicorn app.main:app --reload --port 8004
```

**Terminal 4 - Kitchen Service:**
```bash
source venv/bin/activate
cd services/kitchen-service
uvicorn app.main:app --reload --port 8005
```

**Terminal 5 - API Gateway:**
```bash
source venv/bin/activate
cd services/api-gateway
uvicorn app.main:app --reload --port 8000
```

**Terminal 6 - Frontend:**
```bash
cd frontend/restaurant-app
npm install
npm run dev
```

## 📝 Creating Your First Restaurant

### Option 1: Using API Documentation

1. Go to http://localhost:8000/docs
2. Create a Master Admin user via `/api/v1/auth/signup`
3. Login to get JWT token
4. Use token to create restaurants and manage system

### Option 2: Using cURL

```bash
# 1. Create Master Admin
curl -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@restaurant.com",
    "password": "Admin@123456",
    "role": "master_admin",
    "full_name": "System Administrator"
  }'

# 2. Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456"
  }'

# Save the access_token from response for next requests
```

## 🔍 Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# View service logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Connect to PostgreSQL directly
docker-compose exec postgres psql -U restaurant_admin -d restaurant_db
```

### Port already in use

```bash
# Find process using port (e.g., 8000)
lsof -i :8000

# Kill the process
kill -9 [PID]
```

## 🧪 Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

### Create Restaurant Admin

```bash
curl -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "restaurant_admin_1",
    "email": "admin@myrestaurant.com",
    "password": "SecurePass123!",
    "role": "restaurant_admin",
    "full_name": "John Doe"
  }'
```

## 📚 Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Read the Full README**: [README.md](README.md)
3. **Check the Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
4. **Review Database Schema**: [docs/DATABASE.md](docs/DATABASE.md)

## 🛑 Stopping Services

### Stop all services

```bash
docker-compose down
```

### Stop and remove volumes (careful - deletes data!)

```bash
docker-compose down -v
```

## 💡 Useful Commands

```bash
# View all running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f auth-service

# Rebuild specific service
docker-compose up -d --build auth-service

# Execute command in container
docker-compose exec postgres psql -U restaurant_admin -d restaurant_db

# Check Redis
docker-compose exec redis redis-cli ping
```

## 🆘 Getting Help

- **Documentation**: Check the `docs/` folder
- **API Issues**: Review API docs at http://localhost:8000/docs
- **Database Issues**: Check [docs/DATABASE.md](docs/DATABASE.md)
- **GitHub Issues**: Report bugs or request features

---

Happy coding! 🎉
