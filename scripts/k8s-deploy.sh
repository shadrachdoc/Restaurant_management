#!/bin/bash

# Kubernetes Deployment Script for Restaurant Management System

set -e

echo "🚀 Deploying Restaurant Management System to Kubernetes..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot access Kubernetes cluster. Please ensure cluster is running.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes cluster is accessible${NC}"
echo ""

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f infrastructure/kubernetes/namespace.yaml
echo ""

# Create ConfigMaps and Secrets
echo "🔐 Creating ConfigMaps and Secrets..."
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml
echo ""

# Create Persistent Volumes
echo "💾 Creating Persistent Volumes..."
kubectl apply -f infrastructure/kubernetes/persistent-volumes.yaml
echo ""

# Deploy databases (StatefulSets)
echo "🗄️  Deploying databases..."
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/rabbitmq-statefulset.yaml
echo ""

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n restaurant-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n restaurant-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n restaurant-system --timeout=300s
echo -e "${GREEN}✓ Databases are ready${NC}"
echo ""

# Deploy microservices
echo "🔧 Deploying microservices..."
kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/order-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/kitchen-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/api-gateway-deployment.yaml
echo ""

# Deploy frontend
echo "🎨 Deploying frontend..."
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10
echo ""

# Apply HPA
echo "📊 Configuring Horizontal Pod Autoscaling..."
kubectl apply -f infrastructure/kubernetes/hpa.yaml
echo ""

# Apply Ingress (optional)
if [ -f infrastructure/kubernetes/ingress.yaml ]; then
    echo "🌐 Configuring Ingress..."
    kubectl apply -f infrastructure/kubernetes/ingress.yaml
    echo ""
fi

# Display deployment status
echo "📊 Deployment Status:"
echo "===================="
kubectl get pods -n restaurant-system
echo ""

echo "🔍 Services:"
echo "==========="
kubectl get svc -n restaurant-system
echo ""

echo "📈 Horizontal Pod Autoscalers:"
echo "=============================="
kubectl get hpa -n restaurant-system
echo ""

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "  1. Check pod status: kubectl get pods -n restaurant-system"
echo "  2. View logs: kubectl logs -f <pod-name> -n restaurant-system"
echo "  3. Access services:"
echo "     - API Gateway: kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system"
echo "     - Frontend: kubectl port-forward svc/frontend 3000:3000 -n restaurant-system"
echo ""
echo "  4. Access via Ingress (if configured):"
echo "     - Frontend: http://restaurant.local"
echo "     - API: http://api.restaurant.local"
echo ""
echo "  5. To delete deployment: kubectl delete namespace restaurant-system"
echo ""
