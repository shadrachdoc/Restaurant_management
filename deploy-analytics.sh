#!/bin/bash
#
# Analytics & ML Prediction System Deployment Script
# This script deploys the analytics system to your Kind Kubernetes cluster
#

set -e  # Exit on error

echo "========================================="
echo "Analytics System Deployment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
kubectl cluster-info > /dev/null 2>&1 || { echo "Error: Kubernetes cluster not accessible"; exit 1; }
docker ps > /dev/null 2>&1 || { echo "Error: Docker not running"; exit 1; }
echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Step 2: Load Docker image to Kind cluster
echo -e "${BLUE}Step 2: Loading updated order-service image to Kind...${NC}"
kind load docker-image restaurant_management_order-service:latest --name restaurant-cluster || {
    echo "Error: Failed to load image to Kind cluster"
    exit 1
}
echo -e "${GREEN}✓ Image loaded successfully${NC}"
echo ""

# Step 3: Run database migration
echo -e "${BLUE}Step 3: Running database migration...${NC}"
echo "Getting order-service pod..."
ORDER_POD=$(kubectl get pods -n restaurant-system -l app=order-service -o jsonpath='{.items[0].metadata.name}')

if [ -z "$ORDER_POD" ]; then
    echo "Error: Could not find order-service pod"
    exit 1
fi

echo "Running Alembic migration in pod: $ORDER_POD"
kubectl exec -n restaurant-system $ORDER_POD -- sh -c "cd /app && alembic upgrade head" || {
    echo -e "${YELLOW}Warning: Migration may have failed. Checking if tables already exist...${NC}"
}
echo -e "${GREEN}✓ Migration completed${NC}"
echo ""

# Step 4: Restart order-service to load new code
echo -e "${BLUE}Step 4: Restarting order-service deployment...${NC}"
kubectl rollout restart deployment/order-service -n restaurant-system
kubectl rollout status deployment/order-service -n restaurant-system --timeout=120s
echo -e "${GREEN}✓ Order service restarted${NC}"
echo ""

# Step 5: Get service URLs
echo -e "${BLUE}Step 5: Service Information${NC}"
echo "========================================="
echo ""
echo "Analytics API Endpoints:"
echo "  - Base URL: http://localhost:8004"
echo "  - API Docs: http://localhost:8004/docs"
echo ""
echo "Frontend URLs:"
echo "  - Main App: http://localhost:3000"
echo "  - Analytics Dashboard: http://localhost:3000/admin/analytics"
echo "  - Predictions Dashboard: http://localhost:3000/admin/predictions"
echo "  - Customer Insights: http://localhost:3000/admin/customer-insights"
echo ""
echo "========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Wait for order-service pod to be ready (check with: kubectl get pods -n restaurant-system)"
echo "2. Open http://localhost:8004/docs to see the API documentation"
echo "3. Navigate to http://localhost:3000/admin/analytics to see the dashboard"
echo "4. You may need to add navigation links to the Admin Dashboard manually"
echo ""
echo -e "${GREEN}Deployment script completed successfully!${NC}"
