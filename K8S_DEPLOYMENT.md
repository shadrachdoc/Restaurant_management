# Kubernetes Deployment Guide for Restaurant Management System

This guide provides step-by-step instructions to deploy the Restaurant Management System to Kubernetes using DockerHub.

## Prerequisites

1. **Docker** - Installed and running
2. **Kubernetes Cluster** - Running cluster (kind, minikube, or cloud provider)
3. **kubectl** - Configured to connect to your cluster
4. **DockerHub Account** - For storing images

## Quick Start (Automated Deployment)

### Step 1: Login to DockerHub

```bash
docker login
```

### Step 2: Set Your DockerHub Username

```bash
export DOCKERHUB_USERNAME=your_dockerhub_username
```

### Step 3: Clean Up Old Services (Optional but Recommended)

The current cluster has some old failing services. Clean them up first:

```bash
./cleanup-old-services.sh
```

### Step 4: Run the Deployment Script

```bash
./deploy-to-dockerhub.sh
```

This script will:
- Build Docker images for all services
- Push images to DockerHub
- Update Kubernetes manifests
- Deploy to your Kubernetes cluster

## Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

### 1. Login to DockerHub

```bash
docker login
```

### 2. Build and Push Images

Replace `yourusername` with your DockerHub username.

#### Auth Service
```bash
cd services/auth-service
docker build -t yourusername/restaurant-auth-service:latest .
docker push yourusername/restaurant-auth-service:latest
cd ../..
```

#### Restaurant Service
```bash
cd services/restaurant-service
docker build -t yourusername/restaurant-restaurant-service:latest .
docker push yourusername/restaurant-restaurant-service:latest
cd ../..
```

#### Frontend
```bash
cd frontend
docker build -t yourusername/restaurant-frontend:latest .
docker push yourusername/restaurant-frontend:latest
cd ..
```

### 3. Update Kubernetes Manifests

Edit the following files and replace the image names:

**infrastructure/kubernetes/auth-service-deployment.yaml**
```yaml
image: yourusername/restaurant-auth-service:latest
imagePullPolicy: Always
```

**infrastructure/kubernetes/restaurant-service-deployment.yaml**
```yaml
image: yourusername/restaurant-restaurant-service:latest
imagePullPolicy: Always
```

**infrastructure/kubernetes/frontend-deployment.yaml**
```yaml
image: yourusername/restaurant-frontend:latest
imagePullPolicy: Always
```

### 4. Deploy to Kubernetes

#### Create Namespace
```bash
kubectl create namespace restaurant-system
```

#### Apply Configurations
```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml
kubectl apply -f infrastructure/kubernetes/configmap.yaml
```

#### Deploy Infrastructure (Postgres, Redis)
```bash
kubectl apply -f infrastructure/kubernetes/persistent-volumes.yaml
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-statefulset.yaml
```

Wait for infrastructure to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=postgres -n restaurant-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n restaurant-system --timeout=120s
```

#### Deploy Backend Services
```bash
kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml
```

Wait for services to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=auth-service -n restaurant-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=restaurant-service -n restaurant-system --timeout=120s
```

#### Deploy Frontend
```bash
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
```

## Verify Deployment

### Check Pod Status
```bash
kubectl get pods -n restaurant-system
```

All pods should show `Running` status.

### Check Services
```bash
kubectl get services -n restaurant-system
```

### View Logs

#### Auth Service
```bash
kubectl logs -f deployment/auth-service -n restaurant-system
```

#### Restaurant Service
```bash
kubectl logs -f deployment/restaurant-service -n restaurant-system
```

#### Frontend
```bash
kubectl logs -f deployment/frontend -n restaurant-system
```

## Access the Application

### Using Port Forward

```bash
# Access frontend
kubectl port-forward -n restaurant-system service/frontend 3000:3000

# Access auth-service
kubectl port-forward -n restaurant-system service/auth-service 8001:8001

# Access restaurant-service
kubectl port-forward -n restaurant-system service/restaurant-service 8003:8003
```

Then visit:
- Frontend: http://localhost:3000
- Auth Service: http://localhost:8001/docs
- Restaurant Service: http://localhost:8003/docs

### Using LoadBalancer (if supported)

If your cluster supports LoadBalancer services:

```bash
kubectl get services -n restaurant-system
```

Look for the EXTERNAL-IP of the frontend service.

## Troubleshooting

### Pods Not Starting

Check pod events:
```bash
kubectl describe pod <pod-name> -n restaurant-system
```

### Image Pull Errors

Ensure:
1. Images are pushed to DockerHub
2. Image names in manifests match your DockerHub username
3. Images are public or you've configured image pull secrets

### Database Connection Issues

Check if Postgres is running:
```bash
kubectl get pods -l app=postgres -n restaurant-system
kubectl logs -l app=postgres -n restaurant-system
```

### Service Connection Issues

Check service endpoints:
```bash
kubectl get endpoints -n restaurant-system
```

## Scaling

### Scale Backend Services

```bash
# Scale auth-service
kubectl scale deployment auth-service --replicas=3 -n restaurant-system

# Scale restaurant-service
kubectl scale deployment restaurant-service --replicas=3 -n restaurant-system
```

### Scale Frontend

```bash
kubectl scale deployment frontend --replicas=3 -n restaurant-system
```

## Update Deployment

To deploy new changes:

1. Build and push new images with a new tag:
   ```bash
   docker build -t yourusername/restaurant-auth-service:v2 .
   docker push yourusername/restaurant-auth-service:v2
   ```

2. Update the deployment:
   ```bash
   kubectl set image deployment/auth-service auth-service=yourusername/restaurant-auth-service:v2 -n restaurant-system
   ```

Or re-run the deployment script after updating code.

## Clean Up

To remove all resources:

```bash
kubectl delete namespace restaurant-system
```

## Architecture

The deployment includes:

- **auth-service** (2 replicas) - Authentication and user management
- **restaurant-service** (2 replicas) - Restaurant, menu, table, order management
- **frontend** (2 replicas) - React SPA served by Nginx
- **postgres** (StatefulSet) - Database
- **redis** (StatefulSet) - Caching and sessions

### Removed Services

The following old services have been removed as they're no longer needed:
- api-gateway (functionality merged into direct service calls)
- kitchen-service (functionality merged into restaurant-service)
- order-service (functionality merged into restaurant-service)
- rabbitmq (not currently used)

## Environment Variables

Important environment variables are configured via:
- **ConfigMap**: infrastructure/kubernetes/configmap.yaml
- **Secrets**: infrastructure/kubernetes/secrets.yaml

Make sure to update these with your actual values before deploying to production.

## Production Considerations

1. **Secrets Management**: Use proper secret management (e.g., Sealed Secrets, External Secrets)
2. **Persistent Volumes**: Configure proper storage classes for StatefulSets
3. **Ingress**: Set up proper ingress with TLS certificates
4. **Monitoring**: Add Prometheus and Grafana for monitoring
5. **Logging**: Configure centralized logging (e.g., ELK stack)
6. **Backup**: Set up automated database backups
7. **Resource Limits**: Adjust resource requests/limits based on load
8. **Health Checks**: Ensure liveness and readiness probes are configured correctly
