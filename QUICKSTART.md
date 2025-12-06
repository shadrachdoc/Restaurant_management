# Quick Start Guide

Get the Restaurant Management System up and running in minutes!

## Prerequisites

Ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/)

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Clone the repository
cd Restaurant_management

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Redis using Docker
docker-compose up -d postgres redis
```

### 3. Start Backend Services

**Terminal 1 - Auth Service:**
```bash
source venv/bin/activate
./start-auth-service.sh
```

**Terminal 2 - Restaurant Service:**
```bash
source venv/bin/activate
./start-restaurant-service.sh
```

### 4. Start Frontend

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 5. Access the Application

Once all services are running:

- **Frontend**: http://localhost:3000
- **Auth Service API Docs**: http://localhost:8001/docs
- **Restaurant Service API Docs**: http://localhost:8003/docs

## 🐳 Docker Deployment (Alternative)

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ☸️ Kubernetes Deployment

For production deployment using Kubernetes, see [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md).

### Quick K8s Deployment

```bash
# 1. Login to DockerHub
docker login

# 2. Set your DockerHub username
export DOCKERHUB_USERNAME=your_dockerhub_username

# 3. Clean up old services (if any)
./cleanup-old-services.sh

# 4. Deploy to Kubernetes
./deploy-to-dockerhub.sh

# 5. Access the application
kubectl port-forward -n restaurant-system service/frontend 3000:3000
```

Then visit http://localhost:3000

## 📝 Creating Your First Restaurant

### Option 1: Using the Frontend

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Create a MASTER_ADMIN account
4. Login and create your restaurant
5. Add menu items, tables, and staff

### Option 2: Using API Documentation

1. Go to http://localhost:8001/docs
2. Create a Master Admin user via `/api/v1/auth/signup`:
```json
{
  "username": "admin",
  "email": "admin@restaurant.com",
  "password": "Admin@123456",
  "role": "MASTER_ADMIN",
  "full_name": "System Administrator"
}
```
3. Login to get JWT token via `/api/v1/auth/login`
4. Use token to create restaurants and manage system

### Option 3: Using cURL

```bash
# 1. Create Master Admin
curl -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@restaurant.com",
    "password": "Admin@123456",
    "role": "MASTER_ADMIN",
    "full_name": "System Administrator"
  }'

# 2. Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456"
  }'

# Save the access_token from response

# 3. Create Restaurant
curl -X POST http://localhost:8003/api/v1/restaurants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "My Restaurant",
    "address": "123 Main St",
    "phone": "+1234567890",
    "email": "info@myrestaurant.com"
  }'
```

## 🔍 Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# View service logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart specific service
docker-compose restart postgres
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
# Find process using port (e.g., 8001)
lsof -i :8001

# Kill the process
kill -9 [PID]
```

### Frontend not loading

```bash
# Check if backend services are running
curl http://localhost:8001/health
curl http://localhost:8003/health

# Check frontend build
cd frontend
npm run build
```

## 🧪 Testing the API

### Health Check

```bash
# Auth Service
curl http://localhost:8001/health

# Restaurant Service
curl http://localhost:8003/health
```

### Create Restaurant Admin

```bash
curl -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "restaurant_admin_1",
    "email": "admin@myrestaurant.com",
    "password": "SecurePass123!",
    "role": "RESTAURANT_ADMIN",
    "full_name": "John Doe"
  }'
```

## 📚 Next Steps

1. **Explore API Documentation**:
   - Auth Service: http://localhost:8001/docs
   - Restaurant Service: http://localhost:8003/docs

2. **Read the Full README**: [README.md](README.md)

3. **Kubernetes Deployment**: [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)

4. **Frontend Guide**: [FRONTEND_SETUP.md](FRONTEND_SETUP.md)

## 🛑 Stopping Services

### Stop all Docker services

```bash
docker-compose down
```

### Stop and remove volumes (careful - deletes data!)

```bash
docker-compose down -v
```

### Stop individual Python services

Press `Ctrl+C` in each terminal running a service.

## 💡 Useful Commands

```bash
# View all running Docker containers
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

## 📂 Project Structure

```
Restaurant_management/
├── services/
│   ├── auth-service/          # Authentication & user management (Port 8001)
│   └── restaurant-service/    # Restaurant operations (Port 8003)
├── frontend/                  # React application (Port 3000)
├── infrastructure/
│   └── kubernetes/           # Kubernetes manifests
├── shared/                   # Shared models & utilities
├── scripts/                  # Deployment scripts
├── deploy-to-dockerhub.sh   # K8s deployment script
├── cleanup-old-services.sh  # Cleanup script
└── K8S_DEPLOYMENT.md        # K8s deployment guide
```

## 🎯 Available Services

### Backend Services
- **Auth Service** (Port 8001): User authentication, JWT tokens, user management
- **Restaurant Service** (Port 8003): Restaurants, menus, tables, orders, feedback

### Frontend
- **React App** (Port 3000): Complete admin dashboard and customer interface

### Infrastructure
- **PostgreSQL** (Port 5432): Database
- **Redis** (Port 6379): Cache

## 👥 User Roles

- **MASTER_ADMIN**: Full system access, manage all restaurants
- **RESTAURANT_ADMIN**: Manage own restaurant, menu, tables, staff, orders
- **CHEF**: View and update orders for their restaurant
- **CUSTOMER**: Place orders, provide feedback

## 🆘 Getting Help

- **Documentation**: Check the `docs/` folder
- **API Issues**: Review API docs at http://localhost:8001/docs or http://localhost:8003/docs
- **K8s Deployment**: See [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)
- **GitHub Issues**: Report bugs or request features

---

Happy coding! 🎉
