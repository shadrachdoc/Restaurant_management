# Restaurant Menu & Order Management System

A fully responsive, microservices-based restaurant management platform with QR code ordering, real-time updates, and multi-tenant support.

## Architecture

### Microservices
- **Auth Service** (Port 8001) - Authentication & authorization with JWT
- **Master Admin Service** (Port 8002) - Multi-restaurant management
- **Restaurant Service** (Port 8003) - Menu, tables, branding
- **Order Service** (Port 8004) - Order processing
- **Kitchen Service** (Port 8005) - Chef operations
- **Notification Service** (Port 8006) - WebSocket & real-time events
- **API Gateway** (Port 8000) - Unified API entry point

### Tech Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with Vite
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Message Queue**: RabbitMQ
- **Container Orchestration**: Kubernetes (KIND for local dev)
- **CI/CD**: GitHub Actions
- **Monitoring**: New Relic

## Project Structure
```
├── services/
│   ├── auth-service/
│   ├── master-admin-service/
│   ├── restaurant-service/
│   ├── order-service/
│   ├── kitchen-service/
│   ├── notification-service/
│   └── api-gateway/
├── frontend/
│   └── restaurant-app/
├── infrastructure/
│   ├── kubernetes/
│   ├── docker/
│   └── monitoring/
├── shared/
│   ├── models/
│   ├── utils/
│   └── config/
├── scripts/
└── docs/
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- KIND (Kubernetes in Docker)
- PostgreSQL 15+
- Redis 7+
- RabbitMQ

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
cd frontend/restaurant-app
npm install
```

4. **Start infrastructure services**
```bash
docker-compose up -d postgres redis rabbitmq
```

5. **Run database migrations**
```bash
./scripts/migrate.sh
```

6. **Start all microservices**
```bash
./scripts/start-services.sh
```

7. **Start frontend**
```bash
cd frontend/restaurant-app
npm run dev
```

### Docker Deployment

```bash
docker-compose up --build
```

### Kubernetes Deployment

```bash
# Create KIND cluster
kind create cluster --config infrastructure/kubernetes/kind-config.yaml

# Deploy services
kubectl apply -f infrastructure/kubernetes/
```

## API Documentation

Once services are running, access API documentation at:
- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- Master Admin: http://localhost:8002/docs
- Restaurant Service: http://localhost:8003/docs
- Order Service: http://localhost:8004/docs
- Kitchen Service: http://localhost:8005/docs

## Features

### Customer Features
- QR code table scanning
- Real-time menu browsing
- Collaborative ordering (multiple people per table)
- Order tracking
- Assistance requests
- Feedback submission

### Restaurant Admin Features
- Menu management (CRUD operations)
- Table management with QR generation
- Branding customization
- Order monitoring
- Sales reports
- Customer feedback review
- Table assistance alerts

### Chef Features
- Real-time order queue
- Order status updates (Preparing → Ready → Cancelled)
- Assistance notifications
- Kitchen dashboard

### Master Admin Features
- Multi-restaurant management
- Restaurant account creation
- Pricing plan configuration
- Global analytics
- Revenue tracking
- Subscription management

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
cd frontend/restaurant-app
npm test
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- Database credentials
- Redis connection
- RabbitMQ settings
- JWT secrets
- New Relic keys

## License
MIT

## Contributors
- [Your Name]
