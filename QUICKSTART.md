# Quick Start Guide

Get the Restaurant Management System up and running in minutes!

## 🌐 Production Access

**Live URL**: https://restaurant.corpv3.com

**Test Credentials**: See [TEST_CREDENTIALS.md](TEST_CREDENTIALS.md)
- Master Admin: `admin` / `password`
- Chef: `adminchef1` / `password`
- Restaurant Admin: `adminres` / `password`

---

## Prerequisites

For local development, ensure you have:

- **Kubernetes (Kind)** - [Install](https://kind.sigs.k8s.io/)
- **kubectl** - [Install](https://kubernetes.io/docs/tasks/tools/)
- **Docker** - [Download](https://www.docker.com/products/docker-desktop/)
- **Helm 3+** - [Install](https://helm.sh/docs/intro/install/)
- **Git** - [Download](https://git-scm.com/)

## 🚀 Quick Start (Kubernetes Deployment)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Restaurant_management
```

### 2. Create Kind Cluster

```bash
# Create cluster
kind create cluster --name restaurant-cluster --config infrastructure/kind/kind-config.yaml

# Verify cluster
kubectl cluster-info --context kind-restaurant-cluster
```

### 3. Deploy with Helm

```bash
# Create namespace
kubectl create namespace restaurant-system

# Install Helm chart
helm install restaurant-system ./helm/restaurant-system -n restaurant-system

# Watch pods start
kubectl get pods -n restaurant-system -w
```

### 4. Access the Application

```bash
# Port-forward frontend
kubectl port-forward -n restaurant-system svc/frontend 80:80
```

Then visit **http://localhost** or setup ingress for https://restaurant.corpv3.com

### 5. Login

Use credentials from [TEST_CREDENTIALS.md](TEST_CREDENTIALS.md):
- **URL**: http://localhost (or https://restaurant.corpv3.com)
- **Master Admin**: `admin` / `password`
- **Chef**: `adminchef1` / `password`
- **Restaurant Admin**: `adminres` / `password`

## 📝 Test Restaurant Already Available

The system comes with a pre-configured test restaurant:

**Restaurant**: phalwan Briyani
- **ID**: `52c0d315-b894-40c6-be52-3416a9d0a1e7`
- **Currency**: INR (₹)
- **Billing**: Enabled (₹10 table / ₹15 online)
- **Menu**: 8 items (Biryani varieties)
- **Tables**: 5 tables (T1-T5)
- **Orders**: 240 test orders (16 days)

### Creating Additional Restaurants

1. Login as Master Admin: https://restaurant.corpv3.com/master-admin
2. Click "Create Restaurant"
3. Fill in details:
   - Name, Description, Address
   - Country & Currency (auto-detected)
   - Billing fees (optional)
4. Restaurant is created with unique slug
5. Assign admins/chefs via User Management

## 🔍 Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n restaurant-system

# Describe pod for errors
kubectl describe pod -n restaurant-system <pod-name>

# Check logs
kubectl logs -n restaurant-system <pod-name> --tail=50

# Restart deployment
kubectl rollout restart deployment/<deployment-name> -n restaurant-system
```

### Database connection issues

```bash
# Check PostgreSQL pod
kubectl get pods -n restaurant-system | grep postgres

# Check PostgreSQL logs
kubectl logs -n restaurant-system -l app=postgres

# Connect to PostgreSQL
kubectl exec -it -n restaurant-system deployment/postgres -- psql -U restaurant_admin -d restaurant_db
```

### Frontend not loading

```bash
# Check frontend pod
kubectl get pods -n restaurant-system -l app=frontend

# Check frontend logs
kubectl logs -n restaurant-system -l app=frontend

# Restart frontend
kubectl delete pod -n restaurant-system -l app=frontend
```

### Image pull errors

```bash
# Check image pull policy
kubectl get deployment -n restaurant-system <deployment-name> -o yaml | grep -i image

# Load local images to kind
kind load docker-image <image-name>:latest --name restaurant-cluster

# Set imagePullPolicy to IfNotPresent
kubectl set image deployment/<name> <container>=<image> -n restaurant-system
kubectl patch deployment/<name> -n restaurant-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","imagePullPolicy":"IfNotPresent"}]}}}}'
```

## 🧪 Testing the API

### Health Check via Port-Forward

```bash
# Port-forward API Gateway
kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/auth/health
curl http://localhost:8000/api/v1/restaurants/health
```

### Access API Docs

```bash
# Port-forward API Gateway
kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000

# Open in browser
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## 📚 Next Steps

1. **Explore the System**:
   - Master Admin Dashboard: https://restaurant.corpv3.com/master-admin
   - User Management: Create new users and assign roles
   - Billing & Invoices: Generate invoices for restaurants

2. **API Documentation**:
   - Port-forward: `kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000`
   - Swagger UI: http://localhost:8000/docs

3. **Read Documentation**:
   - [README.md](README.md) - Full project overview
   - [TEST_CREDENTIALS.md](TEST_CREDENTIALS.md) - Login credentials
   - [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) - Billing system details
   - [BILLING_INVOICE_IMPLEMENTATION_SUMMARY.md](BILLING_INVOICE_IMPLEMENTATION_SUMMARY.md) - Invoice system

## 🛑 Stopping Services

### Uninstall Helm release

```bash
helm uninstall restaurant-system -n restaurant-system
```

### Delete namespace

```bash
kubectl delete namespace restaurant-system
```

### Delete Kind cluster

```bash
kind delete cluster --name restaurant-cluster
```

## 💡 Useful Kubernetes Commands

```bash
# View all pods
kubectl get pods -n restaurant-system

# View services
kubectl get svc -n restaurant-system

# View deployments
kubectl get deployments -n restaurant-system

# Watch pods in real-time
kubectl get pods -n restaurant-system -w

# View logs
kubectl logs -n restaurant-system <pod-name> --tail=100 -f

# Execute command in pod
kubectl exec -it -n restaurant-system <pod-name> -- /bin/sh

# Port-forward service
kubectl port-forward -n restaurant-system svc/<service-name> 8000:8000

# Restart deployment
kubectl rollout restart deployment/<name> -n restaurant-system

# Check Helm releases
helm list -n restaurant-system

# Update Helm release
helm upgrade restaurant-system ./helm/restaurant-system -n restaurant-system
```

## 📂 Project Structure

```
Restaurant_management/
├── services/
│   ├── auth-service/          # Authentication (Port 8001)
│   ├── restaurant-service/    # Restaurant ops (Port 8003)
│   ├── order-service/         # Orders & analytics (Port 8004)
│   ├── customer-service/      # Customer management (Port 8007)
│   └── api-gateway/           # API Gateway (Port 8000)
├── frontend/                  # React application
├── helm/
│   └── restaurant-system/    # Helm chart
├── shared/                   # Shared models & utilities
└── docs/                     # Documentation
```

## 🎯 Available Services

### Backend Microservices (Kubernetes)
- **API Gateway** (Port 8000): Routes requests to services
- **Auth Service** (Port 8001): JWT authentication, user management
- **Restaurant Service** (Port 8003): Restaurants, menus, tables, billing, invoices
- **Order Service** (Port 8004): Orders, analytics, predictions
- **Customer Service** (Port 8007): Customer registration and profiles

### Frontend
- **React App** (Port 80): Complete dashboard (Master Admin, Chef, Restaurant Admin)

### Infrastructure
- **PostgreSQL**: Shared database
- **Redis**: Cache and sessions
- **RabbitMQ**: Message queue

## 👥 User Roles

- **master_admin**: Full system access, manage all restaurants, billing, invoices
- **restaurant_admin**: Manage restaurant, menu, tables, staff, orders
- **chef**: View and update orders, kitchen operations
- **customer**: Place orders, provide feedback

## 🆘 Getting Help

- **Test Credentials**: [TEST_CREDENTIALS.md](TEST_CREDENTIALS.md)
- **Billing System**: [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)
- **Documentation**: `docs/` folder
- **Production**: https://restaurant.corpv3.com

---

**Last Updated**: December 29, 2025
**Environment**: Kubernetes (Kind) + Helm
**Domain**: https://restaurant.corpv3.com
