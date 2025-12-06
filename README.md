# Restaurant Menu & Order Management System

A fully responsive restaurant management platform with QR code ordering, real-time updates, and comprehensive admin controls.

## Architecture

### Services
- **Auth Service** (Port 8001) - Authentication, authorization, and user management with JWT
- **Restaurant Service** (Port 8003) - Restaurant, menu, table, order, and feedback management
- **Frontend** (Port 3000) - React SPA with Vite

### Tech Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with Vite, TailwindCSS
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Container Orchestration**: Kubernetes / Docker Compose
- **Image Registry**: DockerHub

## Project Structure
```
├── services/
│   ├── auth-service/          # Authentication & user management
│   └── restaurant-service/    # Restaurant operations
├── frontend/                  # React application
├── infrastructure/
│   └── kubernetes/           # K8s manifests
├── shared/                   # Shared models & utilities
│   ├── models/
│   ├── utils/
│   └── config/
├── scripts/                  # Deployment scripts
└── docs/                     # Documentation
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Restaurant_management
```

2. **Set up Python virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
```

4. **Start infrastructure services**
```bash
docker-compose up -d postgres redis
```

5. **Start backend services**

Terminal 1 - Auth Service:
```bash
source venv/bin/activate
cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

Terminal 2 - Restaurant Service:
```bash
source venv/bin/activate
cd services/restaurant-service
uvicorn app.main:app --reload --port 8003
```

6. **Start frontend**
```bash
cd frontend
npm run dev
```

### Quick Start with Scripts

```bash
# Start auth service
./start-auth-service.sh

# Start restaurant service
./start-restaurant-service.sh

# Start frontend
cd frontend && npm run dev
```

## Kubernetes Deployment

See [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md) for comprehensive Kubernetes deployment guide using DockerHub.

### Quick K8s Deployment

```bash
# 1. Login to DockerHub
docker login

# 2. Set your DockerHub username
export DOCKERHUB_USERNAME=your_dockerhub_username

# 3. Clean up old services (optional)
./cleanup-old-services.sh

# 4. Deploy to Kubernetes
./deploy-to-dockerhub.sh
```

## API Documentation

Once services are running, access API documentation at:
- Auth Service: http://localhost:8001/docs
- Restaurant Service: http://localhost:8003/docs

## Features

### Customer Features
- QR code table scanning
- Real-time menu browsing with categories
- Order placement and tracking
- Feedback submission
- Dietary information display

### Restaurant Admin Features
- **Restaurant Management**: Profile, branding, business hours
- **Menu Management**: CRUD operations, categories, pricing, availability
- **Table Management**: QR code generation, table status tracking
- **Order Management**: Real-time order monitoring, status updates
- **Staff Management**: Create and manage chef and customer accounts
- **Feedback Review**: Customer feedback and ratings
- **Analytics**: Sales reports and performance metrics

### Chef Features
- Real-time order queue
- Order status updates (Pending → Preparing → Ready → Delivered)
- Kitchen dashboard with active orders

### Master Admin Features
- Multi-restaurant management
- System-wide user management
- Global analytics

## Current Implementation Status

### ✅ Fully Implemented
- **Auth Service**: Complete with JWT authentication, role-based access control, user management
- **Restaurant Service**: Restaurant CRUD, menu management, table management with QR codes, order processing, feedback system
- **Frontend**: Complete React application with admin dashboard, menu management, table management, staff management, order tracking
- **Database Models**: All models implemented with proper relationships
- **API Endpoints**: RESTful APIs for all operations
- **Docker Support**: Dockerfiles for all services
- **Kubernetes**: Complete K8s manifests and deployment scripts

### 🎯 Key Features
- JWT-based authentication with refresh tokens
- Role-based access control (MASTER_ADMIN, RESTAURANT_ADMIN, CHEF, CUSTOMER)
- QR code generation for tables
- Real-time order status tracking
- Staff account management (chef and customer creation)
- Comprehensive menu management with categories and dietary info
- Table management with status tracking
- Feedback and ratings system
- Multi-tenant restaurant support

## Development Guidelines

### Code Style
- Python: Follow PEP 8, use Black formatter
- JavaScript/React: ESLint + Prettier
- Git commits: Conventional Commits format

### Testing
```bash
# Backend tests
pytest services/*/tests/

# Frontend tests
cd frontend
npm test
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- Database credentials
- Redis connection
- JWT secrets
- Service ports

## API Endpoints

### Auth Service (Port 8001)

**Authentication:**
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/change-password` - Password change

**User Management:**
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update current user
- `PATCH /api/v1/users/me/restaurant` - Update restaurant association
- `GET /api/v1/users/staff/{restaurant_id}` - List staff members
- `POST /api/v1/users/chef` - Create chef account
- `POST /api/v1/users/customer` - Create customer account
- `PATCH /api/v1/users/{user_id}` - Update staff member
- `PATCH /api/v1/users/{user_id}/toggle-status` - Toggle user status
- `DELETE /api/v1/users/chef/{chef_id}` - Delete chef
- `DELETE /api/v1/users/customer/{customer_id}` - Delete customer

### Restaurant Service (Port 8003)

**Restaurants:**
- `GET /api/v1/restaurants` - List restaurants
- `POST /api/v1/restaurants` - Create restaurant
- `GET /api/v1/restaurants/{id}` - Get restaurant details
- `PUT /api/v1/restaurants/{id}` - Update restaurant
- `DELETE /api/v1/restaurants/{id}` - Delete restaurant
- `PATCH /api/v1/restaurants/{id}/branding` - Update branding
- `PATCH /api/v1/restaurants/{id}/toggle-status` - Toggle status

**Menu Items:**
- `GET /api/v1/restaurants/{id}/menu-items` - List menu items
- `POST /api/v1/restaurants/{id}/menu-items` - Create menu item
- `GET /api/v1/restaurants/{id}/menu-items/{item_id}` - Get menu item
- `PUT /api/v1/restaurants/{id}/menu-items/{item_id}` - Update menu item
- `DELETE /api/v1/restaurants/{id}/menu-items/{item_id}` - Delete menu item
- `PATCH /api/v1/restaurants/{id}/menu-items/{item_id}/toggle-availability` - Toggle availability

**Tables:**
- `GET /api/v1/restaurants/{id}/tables` - List tables
- `POST /api/v1/restaurants/{id}/tables` - Create table with QR code
- `GET /api/v1/restaurants/{id}/tables/{table_id}` - Get table details
- `PUT /api/v1/restaurants/{id}/tables/{table_id}` - Update table
- `DELETE /api/v1/restaurants/{id}/tables/{table_id}` - Delete table
- `PATCH /api/v1/restaurants/{id}/tables/{table_id}/status` - Update table status
- `GET /api/v1/restaurants/{id}/tables/{table_id}/qr-code` - Get QR code
- `POST /api/v1/restaurants/{id}/tables/{table_id}/regenerate-qr` - Regenerate QR code

**Orders:**
- `GET /api/v1/restaurants/{id}/orders` - List orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{order_id}` - Get order details
- `PATCH /api/v1/orders/{order_id}/status` - Update order status
- `DELETE /api/v1/orders/{order_id}` - Cancel order

**Feedback:**
- `GET /api/v1/restaurants/{id}/feedback` - List feedback
- `POST /api/v1/restaurants/{id}/feedback` - Submit feedback
- `GET /api/v1/restaurants/{id}/feedback/{feedback_id}` - Get feedback
- `DELETE /api/v1/restaurants/{id}/feedback/{feedback_id}` - Delete feedback
- `GET /api/v1/restaurants/{id}/feedback/stats/summary` - Feedback summary

## Access Levels

- **MASTER_ADMIN**: Full system access, manage all restaurants
- **RESTAURANT_ADMIN**: Manage own restaurant, menu, tables, staff, orders
- **CHEF**: View and update orders for their restaurant
- **CUSTOMER**: Place orders, provide feedback

## Deployment

### Docker Compose
```bash
docker-compose up -d
```

### Kubernetes
See detailed guide: [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)

```bash
# Quick deployment
export DOCKERHUB_USERNAME=your_username
./deploy-to-dockerhub.sh
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                │
│                       Port: 3000                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTP/REST
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│ Auth Service │              │  Restaurant  │
│   Port 8001  │              │   Service    │
│              │              │   Port 8003  │
│ - Auth       │              │ - Restaurants│
│ - Users      │              │ - Menus      │
│ - JWT        │              │ - Tables     │
│ - RBAC       │              │ - Orders     │
└──────┬───────┘              │ - Feedback   │
       │                      └──────┬───────┘
       │                             │
       └──────────────┬──────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
    ┌──────────┐            ┌─────────┐
    │PostgreSQL│            │  Redis  │
    │  :5432   │            │  :6379  │
    └──────────┘            └─────────┘
```

## License
MIT

## Contributors
- Restaurant Management Team

---

**Last Updated**: 2025-12-06
**Status**: Production Ready
