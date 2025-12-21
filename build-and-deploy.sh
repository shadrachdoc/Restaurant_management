#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

KIND_CLUSTER_NAME="restaurant-cluster"
NAMESPACE="restaurant-system"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restaurant Management System - Build & Deploy${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Build all Docker images
echo -e "${YELLOW}[1/5] Building Docker Images...${NC}"

echo -e "${GREEN}Building Frontend...${NC}"
docker build -f frontend/Dockerfile -t restaurant-frontend:latest .
docker tag restaurant-frontend:latest frontend:latest

echo -e "${GREEN}Building API Gateway...${NC}"
docker build -f services/api-gateway/Dockerfile -t api-gateway:latest .

echo -e "${GREEN}Building Auth Service...${NC}"
docker build -f services/auth-service/Dockerfile -t auth-service:latest .

echo -e "${GREEN}Building Restaurant Service...${NC}"
docker build -f services/restaurant-service/Dockerfile -t restaurant-service:latest .

echo -e "${GREEN}Building Order Service...${NC}"
docker build -f services/order-service/Dockerfile -t order-service:latest .

echo -e "${GREEN}✓ All images built successfully!${NC}"
echo ""

# Step 2: Load images into KIND
echo -e "${YELLOW}[2/5] Loading Images into KIND Cluster...${NC}"

kind load docker-image restaurant-frontend:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image frontend:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image api-gateway:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image auth-service:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image restaurant-service:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image order-service:latest --name ${KIND_CLUSTER_NAME}

echo -e "${GREEN}✓ All images loaded into KIND!${NC}"
echo ""

# Step 3: Restart deployments to use new images
echo -e "${YELLOW}[3/5] Restarting Deployments...${NC}"

kubectl rollout restart deployment/frontend -n ${NAMESPACE}
kubectl rollout restart deployment/api-gateway -n ${NAMESPACE}
kubectl rollout restart deployment/auth-service -n ${NAMESPACE}
kubectl rollout restart deployment/restaurant-service -n ${NAMESPACE}
kubectl rollout restart deployment/order-service -n ${NAMESPACE}

echo -e "${GREEN}✓ Deployments restarted!${NC}"
echo ""

# Step 4: Wait for rollouts to complete
echo -e "${YELLOW}[4/5] Waiting for Rollouts to Complete...${NC}"

kubectl rollout status deployment/frontend -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/api-gateway -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/auth-service -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/restaurant-service -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/order-service -n ${NAMESPACE} --timeout=300s

echo -e "${GREEN}✓ All deployments rolled out successfully!${NC}"
echo ""

# Step 5: Verify deployments
echo -e "${YELLOW}[5/5] Verifying Deployments...${NC}"
echo ""

echo -e "${BLUE}Pod Status:${NC}"
kubectl get pods -n ${NAMESPACE}
echo ""

echo -e "${BLUE}Service Status:${NC}"
kubectl get svc -n ${NAMESPACE}
echo ""

echo -e "${BLUE}Ingress Status:${NC}"
kubectl get ingress -n ${NAMESPACE}
echo ""

# Health checks
echo -e "${YELLOW}Running Health Checks...${NC}"
sleep 5

# Port forward temporarily for health checks
kubectl port-forward svc/auth-service -n ${NAMESPACE} 8002:8001 &
PF_AUTH=$!
kubectl port-forward svc/restaurant-service -n ${NAMESPACE} 8003:8003 &
PF_REST=$!
kubectl port-forward svc/order-service -n ${NAMESPACE} 8004:8004 &
PF_ORDER=$!

sleep 5

# Health check auth service
if curl -s -f http://localhost:8002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Auth Service: Healthy${NC}"
else
    echo -e "${RED}✗ Auth Service: Unhealthy${NC}"
fi

# Health check restaurant service
if curl -s -f http://localhost:8003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Restaurant Service: Healthy${NC}"
else
    echo -e "${RED}✗ Restaurant Service: Unhealthy${NC}"
fi

# Health check order service
if curl -s -f http://localhost:8004/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Order Service: Healthy${NC}"
else
    echo -e "${RED}✗ Order Service: Unhealthy${NC}"
fi

# Cleanup port-forwards
kill $PF_AUTH $PF_REST $PF_ORDER 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Via Ingress: http://restaurant.local:8080"
echo "  (Requires port-forward: kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80)"
echo ""
echo -e "${BLUE}Or via individual port-forwards:${NC}"
echo "  Frontend:            http://localhost:3000"
echo "  API Gateway:         http://localhost:8001"
echo "  Auth Service:        http://localhost:8002"
echo "  Restaurant Service:  http://localhost:8003"
echo "  Order Service:       http://localhost:8004"
echo ""
echo -e "${YELLOW}Run 'kubectl logs -f deployment/<service-name> -n ${NAMESPACE}' to view logs${NC}"
