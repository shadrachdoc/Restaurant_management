# Kubernetes Deployment Guide

Complete guide for deploying Restaurant Management System on Kubernetes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with KIND](#quick-start-with-kind)
3. [Manual Kubernetes Deployment](#manual-kubernetes-deployment)
4. [Architecture](#architecture)
5. [Configuration](#configuration)
6. [Scaling](#scaling)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Docker Desktop** or **Docker Engine** (version 20.10+)
- **kubectl** (version 1.25+)
- **KIND** (Kubernetes in Docker) for local development

### Install KIND

```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS
brew install kind

# Windows
choco install kind
```

### Install kubectl

```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# macOS
brew install kubectl

# Windows
choco install kubernetes-cli
```

## Quick Start with KIND

### 1. Setup KIND Cluster

```bash
# Automated setup
./scripts/k8s-setup-kind.sh
```

This script will:
- ✅ Create a 3-node KIND cluster (1 control-plane, 2 workers)
- ✅ Install NGINX Ingress Controller
- ✅ Install Metrics Server for autoscaling
- ✅ Configure port mappings for services
- ✅ Create storage directories

### 2. Build and Load Docker Images

```bash
# Build all services and load into KIND
./scripts/k8s-build-images.sh
```

### 3. Deploy Application

```bash
# Deploy all resources to Kubernetes
./scripts/k8s-deploy.sh
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n restaurant-system

# Check services
kubectl get svc -n restaurant-system

# Check autoscaling
kubectl get hpa -n restaurant-system
```

### 5. Access Services

**Option 1: Port Forwarding**

```bash
# API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system

# Frontend
kubectl port-forward svc/frontend 3000:3000 -n restaurant-system

# RabbitMQ Management
kubectl port-forward svc/rabbitmq-service 15672:15672 -n restaurant-system
```

**Option 2: Using Ingress**

Add to `/etc/hosts`:
```
127.0.0.1 restaurant.local
127.0.0.1 api.restaurant.local
127.0.0.1 auth.restaurant.local
```

Access:
- Frontend: http://restaurant.local
- API: http://api.restaurant.local
- API Docs: http://api.restaurant.local/docs

## Manual Kubernetes Deployment

### Step-by-Step Deployment

#### 1. Create Namespace

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
```

#### 2. Create ConfigMaps and Secrets

```bash
# ConfigMap
kubectl apply -f infrastructure/kubernetes/configmap.yaml

# Secrets (update values first!)
kubectl apply -f infrastructure/kubernetes/secrets.yaml
```

**⚠️ Important**: Update secrets in production:

```bash
kubectl create secret generic restaurant-secrets \
  --from-literal=POSTGRES_PASSWORD=your_secure_password \
  --from-literal=JWT_SECRET_KEY=your_jwt_secret \
  --from-literal=SESSION_SECRET=your_session_secret \
  --namespace=restaurant-system
```

#### 3. Create Persistent Volumes

```bash
kubectl apply -f infrastructure/kubernetes/persistent-volumes.yaml
```

#### 4. Deploy Databases

```bash
# PostgreSQL
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml

# Redis
kubectl apply -f infrastructure/kubernetes/redis-statefulset.yaml

# RabbitMQ
kubectl apply -f infrastructure/kubernetes/rabbitmq-statefulset.yaml

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n restaurant-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n restaurant-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n restaurant-system --timeout=300s
```

#### 5. Deploy Microservices

```bash
# Auth Service
kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml

# Restaurant Service
kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml

# Order Service
kubectl apply -f infrastructure/kubernetes/order-service-deployment.yaml

# Kitchen Service
kubectl apply -f infrastructure/kubernetes/kitchen-service-deployment.yaml

# API Gateway
kubectl apply -f infrastructure/kubernetes/api-gateway-deployment.yaml

# Frontend
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
```

#### 6. Configure Autoscaling

```bash
kubectl apply -f infrastructure/kubernetes/hpa.yaml
```

#### 7. Setup Ingress (Optional)

```bash
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

## Architecture

### Cluster Layout

```
┌─────────────────────────────────────────────────────────┐
│                   KIND Cluster                          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Control Plane Node                      │  │
│  │  - API Server                                   │  │
│  │  - Scheduler                                    │  │
│  │  - Controller Manager                           │  │
│  │  - NGINX Ingress Controller                     │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │ Worker Node 1│         │ Worker Node 2│            │
│  │              │         │              │            │
│  │ - Pods       │         │ - Pods       │            │
│  │ - Storage    │         │ - Storage    │            │
│  └──────────────┘         └──────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Namespace: restaurant-system

**StatefulSets** (Databases):
- `postgres` - PostgreSQL database (1 replica)
- `redis` - Redis cache (1 replica)
- `rabbitmq` - Message broker (1 replica)

**Deployments** (Microservices):
- `auth-service` - Authentication (2-10 replicas)
- `restaurant-service` - Restaurant management (2-10 replicas)
- `order-service` - Order processing (2-15 replicas)
- `kitchen-service` - Kitchen operations (2-10 replicas)
- `api-gateway` - API Gateway (2-20 replicas)
- `frontend` - React frontend (2-10 replicas)

**Services**:
- ClusterIP services for internal communication
- LoadBalancer services for external access (API Gateway, Frontend)

**HorizontalPodAutoscalers**:
- Auto-scale based on CPU (70%) and Memory (80%) utilization
- Min replicas: 2, Max replicas: 10-20 (varies by service)

## Configuration

### Resource Limits

Each microservice has resource requests and limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Environment Variables

Managed via ConfigMap and Secrets:

**ConfigMap** (`restaurant-config`):
- Database URLs
- Service ports
- Redis/RabbitMQ hosts
- Non-sensitive settings

**Secret** (`restaurant-secrets`):
- Database passwords
- JWT secrets
- API keys

### Persistent Storage

**PostgreSQL**: 10Gi
**Redis**: 5Gi
**RabbitMQ**: 5Gi

Stored in hostPath for KIND (use cloud storage in production).

## Scaling

### Manual Scaling

```bash
# Scale specific deployment
kubectl scale deployment auth-service --replicas=5 -n restaurant-system

# Scale all microservices
kubectl scale deployment --all --replicas=3 -n restaurant-system
```

### Automatic Scaling

HPA automatically scales based on metrics:

```bash
# View current HPA status
kubectl get hpa -n restaurant-system

# Describe HPA
kubectl describe hpa auth-service-hpa -n restaurant-system
```

### Database Scaling

StatefulSets for databases (manual scaling):

```bash
# Scale PostgreSQL (careful with data!)
kubectl scale statefulset postgres --replicas=3 -n restaurant-system
```

**Note**: Database scaling requires proper replication setup.

## Monitoring

### View Logs

```bash
# Single pod
kubectl logs -f <pod-name> -n restaurant-system

# All pods of a deployment
kubectl logs -f deployment/auth-service -n restaurant-system

# Previous container logs
kubectl logs <pod-name> --previous -n restaurant-system
```

### Resource Usage

```bash
# Node metrics
kubectl top nodes

# Pod metrics
kubectl top pods -n restaurant-system

# Container metrics
kubectl top pod <pod-name> --containers -n restaurant-system
```

### Events

```bash
# All events in namespace
kubectl get events -n restaurant-system

# Watch events
kubectl get events -n restaurant-system --watch

# Describe resource for events
kubectl describe pod <pod-name> -n restaurant-system
```

### Dashboard (Optional)

```bash
# Install Kubernetes Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Create admin user
kubectl create serviceaccount dashboard-admin -n kube-system
kubectl create clusterrolebinding dashboard-admin --clusterrole=cluster-admin --serviceaccount=kube-system:dashboard-admin

# Get token
kubectl create token dashboard-admin -n kube-system

# Access dashboard
kubectl proxy
# Visit: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n restaurant-system

# Describe pod for events
kubectl describe pod <pod-name> -n restaurant-system

# Check logs
kubectl logs <pod-name> -n restaurant-system

# Common issues:
# - Image pull errors: Check if images are loaded (kind load docker-image)
# - CrashLoopBackOff: Check logs and environment variables
# - Pending: Check PV/PVC status
```

### Database Connection Issues

```bash
# Check database pods
kubectl get pods -l app=postgres -n restaurant-system

# Test database connection
kubectl exec -it <app-pod> -n restaurant-system -- /bin/sh
# Inside pod: psql -h postgres-service -U restaurant_admin -d restaurant_db

# Check service endpoints
kubectl get endpoints -n restaurant-system
```

### Service Communication Issues

```bash
# Test service connectivity
kubectl run debug --image=busybox -it --rm -n restaurant-system -- sh
# Inside debug pod: wget -O- http://auth-service:8001/health

# Check service
kubectl describe svc auth-service -n restaurant-system

# Check DNS
kubectl exec -it <pod-name> -n restaurant-system -- nslookup postgres-service
```

### Storage Issues

```bash
# Check PV and PVC
kubectl get pv
kubectl get pvc -n restaurant-system

# Describe PVC
kubectl describe pvc postgres-pvc -n restaurant-system

# For KIND, check node storage
docker exec restaurant-cluster-control-plane ls -la /mnt/data/
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress restaurant-ingress -n restaurant-system

# Test ingress
curl -H "Host: api.restaurant.local" http://localhost/health
```

## Cleanup

### Delete Deployment

```bash
# Automated cleanup
./scripts/k8s-delete.sh

# Manual cleanup
kubectl delete namespace restaurant-system
```

### Delete KIND Cluster

```bash
kind delete cluster --name restaurant-cluster
```

### Remove Docker Images

```bash
docker rmi $(docker images | grep "restaurant-" | awk '{print $3}')
```

## Production Deployment

### Differences for Production

1. **Use managed Kubernetes** (GKE, EKS, AKS)
2. **External databases** (Cloud SQL, RDS, etc.)
3. **Proper secrets management** (Vault, Sealed Secrets)
4. **TLS/HTTPS** with cert-manager
5. **Production ingress** with proper domain
6. **Monitoring** (Prometheus, Grafana)
7. **Logging** (ELK, Loki)
8. **Backup** strategies for databases
9. **CI/CD** integration
10. **Network policies** for security

### Example Production Changes

```yaml
# Use LoadBalancer type in cloud
spec:
  type: LoadBalancer

# Use StorageClass for persistent volumes
storageClassName: gp2  # AWS EBS

# Add resource quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: restaurant-quota
  namespace: restaurant-system
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 100Gi
    limits.cpu: "200"
    limits.memory: 200Gi
```

## Useful Commands Cheat Sheet

```bash
# Get all resources
kubectl get all -n restaurant-system

# Delete pod (will be recreated)
kubectl delete pod <pod-name> -n restaurant-system

# Execute command in pod
kubectl exec -it <pod-name> -n restaurant-system -- /bin/sh

# Copy files
kubectl cp <pod-name>:/path/file ./local-file -n restaurant-system

# Port forward
kubectl port-forward svc/<service-name> <local-port>:<remote-port> -n restaurant-system

# Restart deployment
kubectl rollout restart deployment/<deployment-name> -n restaurant-system

# View rollout status
kubectl rollout status deployment/<deployment-name> -n restaurant-system

# View rollout history
kubectl rollout history deployment/<deployment-name> -n restaurant-system
```

---

For more information, see:
- [KIND Documentation](https://kind.sigs.k8s.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
