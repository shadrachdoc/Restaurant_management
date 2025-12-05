#!/bin/bash

# Kubernetes Deployment Script for Restaurant Management System
# This script builds Docker images, pushes them to DockerHub, and deploys to K8s

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-yourusername}"  # Change this or set environment variable
VERSION="${VERSION:-latest}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restaurant Management K8s Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if logged into DockerHub
echo -e "\n${YELLOW}Step 1: Checking DockerHub login...${NC}"
if ! docker info | grep -q "Username:"; then
    echo -e "${RED}Please login to DockerHub first:${NC}"
    echo "docker login"
    exit 1
fi
echo -e "${GREEN}✓ Logged into DockerHub${NC}"

# Build and push images
echo -e "\n${YELLOW}Step 2: Building and pushing Docker images...${NC}"

# Auth Service
echo -e "\n${YELLOW}Building auth-service...${NC}"
cd services/auth-service
docker build -t ${DOCKERHUB_USERNAME}/restaurant-auth-service:${VERSION} .
docker push ${DOCKERHUB_USERNAME}/restaurant-auth-service:${VERSION}
echo -e "${GREEN}✓ auth-service pushed${NC}"
cd ../..

# Restaurant Service
echo -e "\n${YELLOW}Building restaurant-service...${NC}"
cd services/restaurant-service
docker build -t ${DOCKERHUB_USERNAME}/restaurant-restaurant-service:${VERSION} .
docker push ${DOCKERHUB_USERNAME}/restaurant-restaurant-service:${VERSION}
echo -e "${GREEN}✓ restaurant-service pushed${NC}"
cd ../..

# Frontend
echo -e "\n${YELLOW}Building frontend...${NC}"
cd frontend
docker build -t ${DOCKERHUB_USERNAME}/restaurant-frontend:${VERSION} .
docker push ${DOCKERHUB_USERNAME}/restaurant-frontend:${VERSION}
echo -e "${GREEN}✓ frontend pushed${NC}"
cd ..

echo -e "\n${GREEN}✓ All images built and pushed successfully!${NC}"

# Update Kubernetes manifests
echo -e "\n${YELLOW}Step 3: Updating Kubernetes manifests with DockerHub images...${NC}"

# Update auth-service deployment
sed -i "s|image: restaurant_management_auth-service:latest|image: ${DOCKERHUB_USERNAME}/restaurant-auth-service:${VERSION}|g" infrastructure/kubernetes/auth-service-deployment.yaml
sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" infrastructure/kubernetes/auth-service-deployment.yaml

# Update restaurant-service deployment
sed -i "s|image: restaurant_management_restaurant-service:latest|image: ${DOCKERHUB_USERNAME}/restaurant-restaurant-service:${VERSION}|g" infrastructure/kubernetes/restaurant-service-deployment.yaml
sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" infrastructure/kubernetes/restaurant-service-deployment.yaml

# Update frontend deployment
sed -i "s|image: restaurant-frontend:latest|image: ${DOCKERHUB_USERNAME}/restaurant-frontend:${VERSION}|g" infrastructure/kubernetes/frontend-deployment.yaml
sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" infrastructure/kubernetes/frontend-deployment.yaml

echo -e "${GREEN}✓ Kubernetes manifests updated${NC}"

# Deploy to Kubernetes
echo -e "\n${YELLOW}Step 4: Deploying to Kubernetes...${NC}"

# Create namespace if not exists
kubectl create namespace restaurant-system --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
echo -e "\n${YELLOW}Applying namespace and configs...${NC}"
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml
kubectl apply -f infrastructure/kubernetes/configmap.yaml

# Deploy infrastructure
echo -e "\n${YELLOW}Deploying infrastructure (postgres, redis)...${NC}"
kubectl apply -f infrastructure/kubernetes/persistent-volumes.yaml
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-statefulset.yaml

# Wait for infrastructure to be ready
echo -e "\n${YELLOW}Waiting for infrastructure to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n restaurant-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=redis -n restaurant-system --timeout=120s || true

# Deploy services
echo -e "\n${YELLOW}Deploying backend services...${NC}"
kubectl apply -f infrastructure/kubernetes/auth-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/restaurant-service-deployment.yaml

# Wait for backend services
echo -e "\n${YELLOW}Waiting for backend services to be ready...${NC}"
sleep 10
kubectl wait --for=condition=ready pod -l app=auth-service -n restaurant-system --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=restaurant-service -n restaurant-system --timeout=120s || true

# Deploy frontend
echo -e "\n${YELLOW}Deploying frontend...${NC}"
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml

# Deploy ingress (optional)
if [ -f infrastructure/kubernetes/ingress.yaml ]; then
    echo -e "\n${YELLOW}Deploying ingress...${NC}"
    kubectl apply -f infrastructure/kubernetes/ingress.yaml
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show deployment status
echo -e "\n${YELLOW}Current Pod Status:${NC}"
kubectl get pods -n restaurant-system

echo -e "\n${YELLOW}Current Service Status:${NC}"
kubectl get services -n restaurant-system

echo -e "\n${YELLOW}To view logs:${NC}"
echo "kubectl logs -f deployment/auth-service -n restaurant-system"
echo "kubectl logs -f deployment/restaurant-service -n restaurant-system"
echo "kubectl logs -f deployment/frontend -n restaurant-system"

echo -e "\n${YELLOW}To access the application:${NC}"
echo "kubectl port-forward -n restaurant-system service/frontend 3000:3000"
echo "Then visit: http://localhost:3000"
