# Getting Started with Restaurant Management System

This guide will help you understand the project structure and start development.

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Setup Instructions](#setup-instructions)
5. [Development Workflow](#development-workflow)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Project Overview

The Restaurant Management System is a microservices-based application that enables:

- **Customers**: Scan QR codes, view menus, place orders collaboratively
- **Restaurant Admins**: Manage menus, tables, view orders and analytics
- **Chefs**: Receive orders, update cooking status, manage kitchen queue
- **Master Admins**: Manage multiple restaurants, pricing plans, and subscriptions

## System Architecture

### Microservices

1. **Auth Service** (Port 8001)
   - User authentication and authorization
   - JWT token management
   - Role-based access control

2. **Restaurant Service** (Port 8003)
   - Restaurant management
   - Menu item CRUD
   - Table management
   - QR code generation

3. **Order Service** (Port 8004)
   - Order processing
   - Collaborative ordering (table sessions)
   - Assistance requests

4. **Kitchen Service** (Port 8005)
   - Kitchen order queue
   - Order status updates
   - Chef notifications

5. **Notification Service** (Port 8006)
   - Real-time WebSocket updates
   - Event-driven notifications via RabbitMQ

6. **API Gateway** (Port 8000)
   - Single entry point for all requests
   - Request routing
   - Authentication middleware

### Infrastructure

- **PostgreSQL** (Port 5432): Primary database
- **Redis** (Port 6379): Caching and session storage
- **RabbitMQ** (Port 5672): Message queue for events

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy with asyncpg
- **Authentication**: JWT with python-jose
- **Validation**: Pydantic v2
- **API Documentation**: OpenAPI/Swagger (auto-generated)

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **State Management**: React Context / Redux (TBD)
- **UI Library**: TailwindCSS / Material-UI (TBD)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (KIND for local)
- **CI/CD**: GitHub Actions
- **Monitoring**: New Relic

### Database
- **Primary DB**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Message Queue**: RabbitMQ 3+

## Setup Instructions

### Prerequisites

Install the following:
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git

### Quick Setup

```bash
# 1. Navigate to project
cd Restaurant_management

# 2. Run setup script
./scripts/setup-project.sh

# 3. Review configuration
nano .env

# 4. Start all services
./scripts/start-all-services.sh

# 5. Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (for Development)

```bash
# 1. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start infrastructure only
./scripts/start-infrastructure.sh

# 4. Run services individually (in separate terminals)
# Terminal 1:
cd services/auth-service
uvicorn app.main:app --reload --port 8001

# Terminal 2:
cd services/restaurant-service
uvicorn app.main:app --reload --port 8003

# ... and so on for each service
```

## Development Workflow

### Creating a New Microservice

1. **Create service directory**:
   ```bash
   mkdir -p services/new-service/app
   ```

2. **Create models** (`app/models.py`):
   ```python
   from sqlalchemy import Column, String
   from .database import Base

   class MyModel(Base):
       __tablename__ = "my_table"
       id = Column(UUID, primary_key=True)
       name = Column(String(255))
   ```

3. **Create schemas** (`app/schemas.py`):
   ```python
   from pydantic import BaseModel

   class MyModelCreate(BaseModel):
       name: str
   ```

4. **Create routes** (`app/routes.py`):
   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/")
   async def list_items():
       return {"items": []}
   ```

5. **Create main app** (`app/main.py`):
   ```python
   from fastapi import FastAPI
   from .routes import router

   app = FastAPI(title="New Service")
   app.include_router(router)
   ```

### Database Migrations (TODO)

```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Running Tests (TODO)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test file
pytest services/auth-service/tests/test_auth.py
```

## API Documentation

### Accessing API Docs

Once services are running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication Flow

1. **Signup**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "SecurePass123!",
       "role": "restaurant_admin"
     }'
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "SecurePass123!"
     }'
   ```

3. **Use Token**:
   ```bash
   curl -X GET http://localhost:8001/api/v1/users/me \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### User Roles

- `master_admin`: Full system access
- `restaurant_admin`: Restaurant management
- `chef`: Kitchen operations
- `customer`: Order placement (optional auth)

## Testing

### Unit Tests

```python
# services/auth-service/tests/test_auth.py
import pytest
from app.security import hash_password, verify_password

def test_password_hashing():
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
```

### Integration Tests

```python
# Test API endpoints
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_signup():
    response = client.post("/api/v1/auth/signup", json={
        "username": "test",
        "email": "test@test.com",
        "password": "Test123!",
        "role": "customer"
    })
    assert response.status_code == 201
```

## Deployment

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes (Production)

```bash
# Create KIND cluster
kind create cluster --config infrastructure/kubernetes/kind-config.yaml

# Deploy services
kubectl apply -f infrastructure/kubernetes/

# Check status
kubectl get pods
```

### Environment-Specific Configs

- **Development**: `.env` with debug settings
- **Staging**: Update `.env` with staging URLs
- **Production**: Use Kubernetes secrets for sensitive data

## Common Issues & Solutions

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. ✅ Complete Restaurant Service implementation
2. ✅ Complete Order Service implementation
3. ✅ Implement Kitchen Service
4. ✅ Build React frontend
5. ✅ Add real-time WebSocket support
6. ✅ Write comprehensive tests
7. ✅ Deploy to Kubernetes

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [React Documentation](https://react.dev/)

## Support

For questions or issues:
- Check [PROJECT_STATUS.md](../PROJECT_STATUS.md)
- Review [QUICKSTART.md](../QUICKSTART.md)
- Check API documentation at http://localhost:8000/docs

---

**Happy Coding!** 🚀
