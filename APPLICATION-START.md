# Restaurant Management System - Application Startup Guide

**Last Updated**: January 6, 2026
**Version**: 1.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (TL;DR)](#quick-start-tldr)
3. [Detailed Step-by-Step Setup](#detailed-step-by-step-setup)
4. [Port Forwarding](#port-forwarding)
5. [Test Credentials](#test-credentials)
6. [Verification Steps](#verification-steps)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Stopping the Environment](#stopping-the-environment)

---

## 1. Prerequisites

### Required Software

Ensure you have the following installed:

```bash
# Check Docker
docker --version
# Expected: Docker version 20.x or higher

# Check Kind
kind --version
# Expected: kind v0.20.0 or higher

# Check kubectl
kubectl version --client
# Expected: v1.28.x or higher

# Check Helm
helm version
# Expected: v3.13.x or higher

# Check Git
git --version
# Expected: git version 2.x or higher
```

### System Requirements

- **OS**: Linux (Ubuntu 22.04+ recommended)
- **RAM**: Minimum 8GB, Recommended 16GB
- **CPU**: Minimum 4 cores, Recommended 8 cores
- **Disk**: Minimum 20GB free space
- **Network**: Internet connection for pulling images

---

## 2. Quick Start (TL;DR)

**For experienced users who just need the commands:**

```bash
# 1. Navigate to project directory
cd /home/shadrach/Restaurant_management

# 2. Create Kind cluster (if not exists)
kind create cluster --name restaurant-cluster --config infrastructure/kind-config.yaml

# 3. Install Istio
istioctl install --set profile=demo -y

# 4. Label namespace for Istio injection
kubectl label namespace restaurant-system istio-injection=enabled --overwrite

# 5. Deploy all services
kubectl apply -f infrastructure/kubernetes/

# 6. Wait for pods to be ready (2-3 minutes)
kubectl wait --for=condition=ready pod --all -n restaurant-system --timeout=300s

# 7. Start port forwarding
./scripts/start-restaurant-portforward.sh

# 8. Access the application
# Frontend: http://localhost:3000
# Login: admin / admin123
```

---

## 3. Detailed Step-by-Step Setup

### Step 1: Clone Repository (If Not Already)

```bash
# Clone the repository
git clone https://github.com/your-org/Restaurant_management.git

# Navigate to project directory
cd Restaurant_management

# Verify you're in the right directory
ls -la
# You should see: services/, infrastructure/, frontend/, etc.
```

---

### Step 2: Create Kind Cluster

**What is Kind?**
Kind (Kubernetes in Docker) runs a Kubernetes cluster inside Docker containers. Perfect for local development.

**Create the cluster:**

```bash
# Check if cluster already exists
kind get clusters

# If restaurant-cluster exists, delete it to start fresh
kind delete cluster --name restaurant-cluster

# Create new cluster with custom configuration
kind create cluster --name restaurant-cluster --config infrastructure/kind-config.yaml

# Expected output:
# Creating cluster "restaurant-cluster" ...
# ✓ Ensuring node image (kindest/node:v1.28.0) 🖼
# ✓ Preparing nodes 📦 📦 📦
# ✓ Writing configuration 📜
# ✓ Starting control-plane 🕹️
# ✓ Installing CNI 🔌
# ✓ Installing StorageClass 💾
# ✓ Joining worker nodes 🚜
# Set kubectl context to "kind-restaurant-cluster"
```

**Verify cluster is running:**

```bash
# Check cluster info
kubectl cluster-info --context kind-restaurant-cluster

# Expected output:
# Kubernetes control plane is running at https://127.0.0.1:xxxxx
# CoreDNS is running at https://127.0.0.1:xxxxx/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

# Check nodes (should show 3 nodes)
kubectl get nodes

# Expected output:
# NAME                              STATUS   ROLES           AGE   VERSION
# restaurant-cluster-control-plane   Ready    control-plane   1m    v1.28.0
# restaurant-cluster-worker          Ready    <none>          1m    v1.28.0
# restaurant-cluster-worker2         Ready    <none>          1m    v1.28.0
```

---

### Step 3: Install Istio Service Mesh

**What is Istio?**
Istio provides service-to-service security (mTLS), traffic management, and observability.

**Install Istio:**

```bash
# Download and install Istio (if not already installed)
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH
cd ..

# Verify istioctl is available
istioctl version

# Install Istio with demo profile
istioctl install --set profile=demo -y

# Expected output:
# ✔ Istio core installed
# ✔ Istiod installed
# ✔ Ingress gateways installed
# ✔ Egress gateways installed
# ✔ Installation complete
```

**Verify Istio installation:**

```bash
# Check Istio pods in istio-system namespace
kubectl get pods -n istio-system

# Expected output (all Running):
# NAME                                    READY   STATUS    RESTARTS   AGE
# istio-ingressgateway-xxxxxxxxx-xxxxx    1/1     Running   0          1m
# istiod-xxxxxxxxx-xxxxx                  1/1     Running   0          1m
```

---

### Step 4: Create Namespaces

```bash
# Create restaurant-system namespace
kubectl create namespace restaurant-system

# Enable Istio sidecar injection
kubectl label namespace restaurant-system istio-injection=enabled

# Verify label
kubectl get namespace restaurant-system --show-labels

# Expected output should include: istio-injection=enabled
```

---

### Step 5: Deploy Database and Supporting Services

**Deploy PostgreSQL:**

```bash
# Apply PostgreSQL StatefulSet and Service
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n restaurant-system --timeout=120s

# Verify PostgreSQL is running
kubectl get pods -n restaurant-system -l app=postgres

# Expected output:
# NAME         READY   STATUS    RESTARTS   AGE
# postgres-0   1/1     Running   0          2m
```

**Deploy Redis:**

```bash
# Apply Redis deployment
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml

# Verify Redis is running
kubectl get pods -n restaurant-system -l app=redis

# Expected output:
# NAME                     READY   STATUS    RESTARTS   AGE
# redis-xxxxxxxxx-xxxxx    1/1     Running   0          1m
```

**Deploy RabbitMQ:**

```bash
# Apply RabbitMQ deployment
kubectl apply -f infrastructure/kubernetes/rabbitmq-deployment.yaml

# Verify RabbitMQ is running
kubectl get pods -n restaurant-system -l app=rabbitmq

# Expected output:
# NAME                        READY   STATUS    RESTARTS   AGE
# rabbitmq-xxxxxxxxx-xxxxx    1/1     Running   0          1m
```

---

### Step 6: Load Docker Images into Kind

**Why?**
Kind cluster runs in Docker and can't access DockerHub directly in some cases. We load images locally.

```bash
# Load all service images
kind load docker-image shadrach85/api-gateway:debug-auth --name restaurant-cluster
kind load docker-image shadrach85/auth-service:users-path-fix --name restaurant-cluster
kind load docker-image shadrach85/restaurant-service:latest --name restaurant-cluster
kind load docker-image shadrach85/order-service:latest --name restaurant-cluster
kind load docker-image shadrach85/customer-service:latest --name restaurant-cluster
kind load docker-image shadrach85/frontend:latest --name restaurant-cluster

# Each command should output:
# Image: "shadrach85/xxx:xxx" with ID "sha256:..." not yet present on node "...", loading...
```

**Alternative - Pull images first:**

```bash
# If images are on DockerHub, pull them first
docker pull shadrach85/api-gateway:debug-auth
docker pull shadrach85/auth-service:users-path-fix
docker pull shadrach85/restaurant-service:latest
docker pull shadrach85/order-service:latest
docker pull shadrach85/customer-service:latest
docker pull shadrach85/frontend:latest

# Then load into Kind (commands above)
```

---

### Step 7: Deploy Microservices

**Deploy all services at once:**

```bash
# Apply all service deployments
kubectl apply -f infrastructure/kubernetes/api-gateway-deployment.yaml
kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/order-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/customer-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml

# Wait for all pods to be ready (may take 2-3 minutes)
kubectl wait --for=condition=ready pod --all -n restaurant-system --timeout=300s
```

**Verify all services are running:**

```bash
# Check all pods
kubectl get pods -n restaurant-system

# Expected output (all should be 2/2 Running - app + Istio sidecar):
# NAME                                  READY   STATUS    RESTARTS   AGE
# api-gateway-xxxxxxxxx-xxxxx           2/2     Running   0          2m
# auth-service-xxxxxxxxx-xxxxx          2/2     Running   0          2m
# customer-service-xxxxxxxxx-xxxxx      2/2     Running   0          2m
# frontend-xxxxxxxxx-xxxxx              2/2     Running   0          2m
# order-service-xxxxxxxxx-xxxxx         2/2     Running   0          2m
# postgres-0                            1/1     Running   0          5m
# rabbitmq-xxxxxxxxx-xxxxx              2/2     Running   0          4m
# redis-xxxxxxxxx-xxxxx                 2/2     Running   0          4m
# restaurant-service-xxxxxxxxx-xxxxx    2/2     Running   0          2m
```

**Check services:**

```bash
# List all services
kubectl get svc -n restaurant-system

# Expected output:
# NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
# api-gateway          ClusterIP   10.96.x.x       <none>        8000/TCP   2m
# auth-service         ClusterIP   10.96.x.x       <none>        8001/TCP   2m
# customer-service     ClusterIP   10.96.x.x       <none>        8002/TCP   2m
# frontend             ClusterIP   10.96.x.x       <none>        80/TCP     2m
# order-service        ClusterIP   10.96.x.x       <none>        8004/TCP   2m
# postgres             ClusterIP   10.96.x.x       <none>        5432/TCP   5m
# rabbitmq             ClusterIP   10.96.x.x       <none>        5672/TCP   4m
# redis                ClusterIP   10.96.x.x       <none>        6379/TCP   4m
# restaurant-service   ClusterIP   10.96.x.x       <none>        8003/TCP   2m
```

---

### Step 8: Initialize Database

**Run database migrations:**

```bash
# Get auth-service pod name
AUTH_POD=$(kubectl get pods -n restaurant-system -l app=auth-service -o jsonpath='{.items[0].metadata.name}')

# Execute migrations (if using Alembic)
kubectl exec -it $AUTH_POD -n restaurant-system -c auth-service -- alembic upgrade head

# Create initial master admin user (if not exists)
kubectl exec -it $AUTH_POD -n restaurant-system -c auth-service -- python -c "
from app.database import SessionLocal
from app.models import User
from app.security import hash_password
from shared.models.enums import UserRole
import asyncio

async def create_admin():
    async with SessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            print('Admin user already exists')
            return

        # Create admin user
        admin = User(
            username='admin',
            email='admin@restaurant.com',
            hashed_password=hash_password('admin123'),
            role=UserRole.MASTER_ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        await db.commit()
        print('Master admin created successfully')

asyncio.run(create_admin())
"
```

---

### Step 9: Deploy Monitoring Stack (Optional but Recommended)

**Deploy Prometheus:**

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace istio-system \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Verify Prometheus is running
kubectl get pods -n istio-system -l app.kubernetes.io/name=prometheus
```

**Deploy Grafana:**

```bash
# Grafana is included in kube-prometheus-stack
# Get Grafana admin password
kubectl get secret -n istio-system prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# Default username: admin
# Password: (output from above command)
```

---

## 4. Port Forwarding

### Using the Automated Script

**Start all port forwards:**

```bash
# Make script executable (if not already)
chmod +x scripts/start-restaurant-portforward.sh

# Run the script
./scripts/start-restaurant-portforward.sh

# Expected output:
# =============================================================
# Starting Restaurant Management System Port Forwards
# =============================================================
#
# 1. Starting Frontend...
#    ✅ Frontend on http://localhost:3000
#
# 2. Starting API Gateway...
#    ✅ API Gateway on http://localhost:8000
#
# 3. Starting Auth Service...
#    ✅ Auth Service on http://localhost:8001
#
# ... (more services)
#
# =============================================================
# All services started successfully!
# =============================================================
```

**The script forwards these ports:**

| Service | Local Port | Container Port | URL |
|---------|-----------|----------------|-----|
| Frontend | 3000 | 80 | http://localhost:3000 |
| API Gateway | 8000 | 8000 | http://localhost:8000 |
| Auth Service | 8001 | 8001 | http://localhost:8001 |
| Customer Service | 8002 | 8002 | http://localhost:8002 |
| Restaurant Service | 8003 | 8003 | http://localhost:8003 |
| Order Service | 8004 | 8004 | http://localhost:8004 |
| PostgreSQL | 5432 | 5432 | localhost:5432 |
| Redis | 6379 | 6379 | localhost:6379 |
| RabbitMQ | 5672 | 5672 | localhost:5672 |
| RabbitMQ Management | 15672 | 15672 | http://localhost:15672 |
| ArgoCD | 8080 | 80 | http://localhost:8080 |
| Grafana | 3001 | 3000 | http://localhost:3001 |

### Manual Port Forwarding (Alternative)

If you prefer to forward specific services manually:

```bash
# Frontend
kubectl port-forward -n restaurant-system svc/frontend 3000:80 &

# API Gateway
kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000 &

# Auth Service
kubectl port-forward -n restaurant-system svc/auth-service 8001:8001 &

# Restaurant Service
kubectl port-forward -n restaurant-system svc/restaurant-service 8003:8003 &

# Order Service
kubectl port-forward -n restaurant-system svc/order-service 8004:8004 &

# PostgreSQL (for database access)
kubectl port-forward -n restaurant-system svc/postgres 5432:5432 &

# RabbitMQ Management UI
kubectl port-forward -n restaurant-system svc/rabbitmq 15672:15672 &

# Grafana
kubectl port-forward -n istio-system svc/prometheus-grafana 3001:3000 &
```

### Check Port Forward Status

```bash
# List all kubectl port-forward processes
ps aux | grep "kubectl port-forward"

# Check if ports are listening
netstat -tuln | grep -E "3000|8000|8001|8002|8003|8004|5432|6379|15672"
```

---

## 5. Test Credentials

### Application Users

#### Master Admin (Full System Access)

```
Username: admin
Password: admin123
Role: MASTER_ADMIN

Access:
- Create/manage all restaurants
- Create/manage all users
- View all orders
- System configuration
```

#### Restaurant Admin (Sample Restaurant)

```
Username: restaurant_admin
Password: admin123
Role: RESTAURANT_ADMIN
Restaurant: Sample Restaurant

Access:
- Manage own restaurant details
- Manage menu items
- Create chefs/staff for own restaurant
- View own restaurant orders
```

#### Chef (Sample Restaurant)

```
Username: chef1
Password: chef123
Role: CHEF
Restaurant: Sample Restaurant

Access:
- View orders for own restaurant
- Update order status
- View menu items
```

#### Customer

```
Username: customer1
Password: customer123
Role: CUSTOMER

Access:
- Browse menus
- Place orders
- View order history
- Provide feedback
```

### Infrastructure Services

#### PostgreSQL Database

```
Host: localhost (when port-forwarded)
Port: 5432
Database: restaurant_db
Username: restaurant_user
Password: restaurant_pass

Connection String:
postgresql://restaurant_user:restaurant_pass@localhost:5432/restaurant_db
```

#### RabbitMQ Management

```
URL: http://localhost:15672
Username: guest
Password: guest

Queues to monitor:
- orders_queue
- kitchen_notifications
- order_status_updates
```

#### Redis

```
Host: localhost
Port: 6379
Password: (none - no auth by default)

Connect via CLI:
redis-cli -h localhost -p 6379
```

#### Grafana

```
URL: http://localhost:3001
Username: admin
Password: (get from command below)

# Get password:
kubectl get secret -n istio-system prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

#### ArgoCD

```
URL: http://localhost:8080
Username: admin
Password: (get from command below)

# Get initial password:
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

---

## 6. Verification Steps

### Step 1: Check All Pods are Running

```bash
kubectl get pods -n restaurant-system

# All pods should show:
# - READY: 2/2 (or 1/1 for databases)
# - STATUS: Running
# - RESTARTS: 0 (or low number)
```

### Step 2: Test Frontend Access

```bash
# Open browser or use curl
curl -I http://localhost:3000

# Expected: HTTP/1.1 200 OK

# Or open in browser:
xdg-open http://localhost:3000
```

### Step 3: Test API Gateway Health

```bash
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","service":"api-gateway"}
```

### Step 4: Test Authentication

```bash
# Login request
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Expected output:
# {
#   "access_token": "eyJhbGci...",
#   "refresh_token": "...",
#   "token_type": "bearer",
#   "expires_in": 1800,
#   "user": {
#     "id": "...",
#     "username": "admin",
#     "email": "admin@restaurant.com",
#     "role": "master_admin",
#     ...
#   }
# }
```

### Step 5: Test User Management (Master Admin Only)

```bash
# Save access token from login
TOKEN="your_access_token_here"

# Get all users
curl http://localhost:8000/api/v1/auth/users \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array of user objects
```

### Step 6: Check Database Connectivity

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n restaurant-system -- \
  psql -U restaurant_user -d restaurant_db -c "\dt"

# Expected: List of database tables
# - users
# - refresh_tokens
# - restaurants
# - menu_items
# - tables
# - orders
# - order_sessions
# etc.
```

### Step 7: Check Service Logs

```bash
# Check auth service logs
kubectl logs -n restaurant-system -l app=auth-service --tail=50

# Should see:
# - "Starting Auth Service..."
# - "Database initialized"
# - "Uvicorn running on http://0.0.0.0:8001"

# Check for errors (should return nothing)
kubectl logs -n restaurant-system -l app=auth-service --tail=100 | grep ERROR
```

### Step 8: Verify Istio Sidecar Injection

```bash
# Check that services have 2 containers (app + Envoy sidecar)
kubectl get pods -n restaurant-system -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Expected output for each service:
# auth-service-xxx    auth-service    istio-proxy
# api-gateway-xxx     api-gateway     istio-proxy
```

---

## 7. Common Issues & Solutions

### Issue 1: Pods Stuck in Pending State

**Symptom:**
```bash
kubectl get pods -n restaurant-system
# NAME                     READY   STATUS    RESTARTS   AGE
# auth-service-xxx         0/2     Pending   0          5m
```

**Cause:** Not enough resources on Kind nodes

**Solution:**
```bash
# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# If nodes are full, recreate cluster with more resources
kind delete cluster --name restaurant-cluster

# Edit infrastructure/kind-config.yaml to increase resources
# Then recreate cluster
kind create cluster --name restaurant-cluster --config infrastructure/kind-config.yaml
```

---

### Issue 2: ImagePullBackOff Error

**Symptom:**
```bash
kubectl get pods -n restaurant-system
# NAME                     READY   STATUS             RESTARTS   AGE
# auth-service-xxx         0/2     ImagePullBackOff   0          2m
```

**Cause:** Image not loaded into Kind cluster or wrong image tag

**Solution:**
```bash
# Check the exact image name in deployment
kubectl get deployment auth-service -n restaurant-system -o jsonpath='{.spec.template.spec.containers[0].image}'

# Load the correct image
kind load docker-image shadrach85/auth-service:users-path-fix --name restaurant-cluster

# If image doesn't exist locally, pull it first
docker pull shadrach85/auth-service:users-path-fix
kind load docker-image shadrach85/auth-service:users-path-fix --name restaurant-cluster

# Set imagePullPolicy to Never for local images
kubectl patch deployment auth-service -n restaurant-system -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"auth-service","imagePullPolicy":"Never"}]}}}}'
```

---

### Issue 3: Database Connection Failed

**Symptom:**
```bash
# Service logs show:
kubectl logs -n restaurant-system -l app=auth-service --tail=20
# Error: could not connect to server: Connection refused
```

**Cause:** PostgreSQL not ready or wrong connection string

**Solution:**
```bash
# 1. Check PostgreSQL is running
kubectl get pods -n restaurant-system -l app=postgres

# 2. If not running, check logs
kubectl logs -n restaurant-system postgres-0

# 3. Verify service exists
kubectl get svc postgres -n restaurant-system

# 4. Test connection from another pod
kubectl run test-db --rm -it --image=postgres:15 -- \
  psql postgresql://restaurant_user:restaurant_pass@postgres:5432/restaurant_db

# 5. Check secret has correct credentials
kubectl get secret db-credentials -n restaurant-system -o yaml

# 6. Restart auth service after postgres is ready
kubectl rollout restart deployment/auth-service -n restaurant-system
```

---

### Issue 4: Port Forward Dies/Disconnects

**Symptom:**
```bash
curl http://localhost:3000
# curl: (7) Failed to connect to localhost port 3000: Connection refused
```

**Cause:** kubectl port-forward process died

**Solution:**
```bash
# 1. Check if port-forward is running
ps aux | grep "kubectl port-forward"

# 2. Kill any existing port-forwards
pkill -f "kubectl port-forward"

# 3. Restart port forwarding
./scripts/start-restaurant-portforward.sh

# Or start specific service manually
kubectl port-forward -n restaurant-system svc/frontend 3000:80
```

---

### Issue 5: 401 Unauthorized on API Requests

**Symptom:**
```bash
# Browser console shows:
# GET /api/v1/auth/users 401 (Unauthorized)
```

**Cause:** Token expired or not being sent correctly

**Solution:**
```bash
# 1. Login again to get fresh token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Check token expiry (decode at jwt.io)
# Access tokens expire after 30 minutes

# 3. Check Authorization header in API Gateway logs
kubectl logs -n restaurant-system -l app=api-gateway --tail=50 | grep -i authorization

# 4. Verify JWT secrets match
kubectl get deployment api-gateway -n restaurant-system -o yaml | grep JWT_SECRET
kubectl get deployment auth-service -n restaurant-system -o yaml | grep JWT_SECRET

# 5. Clear browser localStorage and login again
# In browser console: localStorage.clear()
```

---

### Issue 6: Istio Sidecar Not Injected

**Symptom:**
```bash
kubectl get pods -n restaurant-system
# NAME                     READY   STATUS    RESTARTS   AGE
# auth-service-xxx         1/1     Running   0          2m
# Should be 2/2 (app + sidecar)
```

**Cause:** Namespace not labeled for Istio injection

**Solution:**
```bash
# 1. Label namespace
kubectl label namespace restaurant-system istio-injection=enabled --overwrite

# 2. Restart deployments to get sidecar
kubectl rollout restart deployment -n restaurant-system

# 3. Verify label
kubectl get namespace restaurant-system --show-labels

# 4. Check pod has both containers
kubectl get pod <pod-name> -n restaurant-system -o jsonpath='{.spec.containers[*].name}'
# Expected: auth-service istio-proxy
```

---

### Issue 7: Services Can't Communicate (503 errors)

**Symptom:**
```bash
# API Gateway logs show:
# Error forwarding request: Service Unavailable
```

**Cause:** Service discovery issue or Istio mTLS mismatch

**Solution:**
```bash
# 1. Check all services have Istio sidecars (2/2 containers)
kubectl get pods -n restaurant-system

# 2. Verify service endpoints exist
kubectl get endpoints -n restaurant-system

# 3. Test connectivity from one pod to another
kubectl exec -it <api-gateway-pod> -n restaurant-system -c api-gateway -- \
  curl http://auth-service:8001/health

# 4. Check Istio configuration
istioctl analyze -n restaurant-system

# 5. Restart all deployments to sync Istio config
kubectl rollout restart deployment -n restaurant-system
```

---

## 8. Stopping the Environment

### Stop Port Forwards Only

```bash
# Kill all kubectl port-forward processes
pkill -f "kubectl port-forward"

# Verify they're stopped
ps aux | grep "kubectl port-forward"
```

### Stop Services (Keep Cluster Running)

```bash
# Scale all deployments to 0
kubectl scale deployment --all --replicas=0 -n restaurant-system

# Or delete all resources
kubectl delete -f infrastructure/kubernetes/ -n restaurant-system
```

### Completely Stop and Delete Cluster

```bash
# Delete the entire Kind cluster
kind delete cluster --name restaurant-cluster

# This removes:
# - All pods and services
# - All data (including PostgreSQL data)
# - All configurations

# Verify cluster is deleted
kind get clusters
# Should not show restaurant-cluster
```

### Cleanup Docker Images (Optional)

```bash
# Remove unused images
docker image prune -a

# Remove specific images
docker rmi shadrach85/auth-service:users-path-fix
docker rmi shadrach85/api-gateway:debug-auth
# etc.
```

---

## Quick Reference Card

### Start Everything

```bash
cd /home/shadrach/Restaurant_management
kind create cluster --name restaurant-cluster --config infrastructure/kind-config.yaml
istioctl install --set profile=demo -y
kubectl label namespace restaurant-system istio-injection=enabled
kubectl apply -f infrastructure/kubernetes/
kubectl wait --for=condition=ready pod --all -n restaurant-system --timeout=300s
./scripts/start-restaurant-portforward.sh
```

### Access Points

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Grafana**: http://localhost:3001
- **RabbitMQ UI**: http://localhost:15672

### Default Login

- **Username**: admin
- **Password**: admin123

### Essential Commands

```bash
# Check all pods
kubectl get pods -n restaurant-system

# Check logs
kubectl logs -n restaurant-system -l app=auth-service --tail=50

# Restart service
kubectl rollout restart deployment/auth-service -n restaurant-system

# Execute into pod
kubectl exec -it <pod-name> -n restaurant-system -- /bin/bash

# Port forward single service
kubectl port-forward -n restaurant-system svc/frontend 3000:80
```

---

## Support & Troubleshooting

If you encounter issues not covered in this guide:

1. **Check pod logs**: `kubectl logs -n restaurant-system <pod-name>`
2. **Check pod events**: `kubectl describe pod -n restaurant-system <pod-name>`
3. **Check service endpoints**: `kubectl get endpoints -n restaurant-system`
4. **Verify Istio**: `istioctl analyze -n restaurant-system`
5. **Review ISSUES.md**: Contains solutions to recently encountered problems

---

**Document Version**: 1.0
**Last Updated**: January 6, 2026
**Maintained By**: DevOps Team
