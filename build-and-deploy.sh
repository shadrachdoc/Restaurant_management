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
echo -e "${BLUE}Restaurant Management System${NC}"
echo -e "${BLUE}Build & Load to KIND${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Build all Docker images
echo -e "${YELLOW}[1/2] Building Docker Images...${NC}"

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
echo -e "${YELLOW}[2/2] Loading Images into KIND Cluster...${NC}"

kind load docker-image restaurant-frontend:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image frontend:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image api-gateway:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image auth-service:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image restaurant-service:latest --name ${KIND_CLUSTER_NAME}
kind load docker-image order-service:latest --name ${KIND_CLUSTER_NAME}

echo -e "${GREEN}✓ All images loaded into KIND!${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build & Load Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Images loaded into cluster: ${KIND_CLUSTER_NAME}${NC}"
echo "  ✓ restaurant-frontend:latest"
echo "  ✓ api-gateway:latest"
echo "  ✓ auth-service:latest"
echo "  ✓ restaurant-service:latest"
echo "  ✓ order-service:latest"
echo ""
echo -e "${YELLOW}ArgoCD will automatically sync and deploy.${NC}"
echo ""
echo -e "${BLUE}Manual Options:${NC}"
echo "  - ArgoCD UI: https://localhost:8081"
echo "  - Or run: kubectl rollout restart deployment/<service> -n ${NAMESPACE}"
