#!/bin/bash

# Build Docker images for all microservices and load them into KIND cluster

set -e

echo "🏗️  Building Docker images for Restaurant Management System..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Build all images using docker-compose
echo "📦 Building all services..."
docker-compose build

echo -e "${GREEN}✓ All images built successfully${NC}"
echo ""

# Check if KIND cluster exists
if command -v kind &> /dev/null && kind get clusters | grep -q "^restaurant-cluster$"; then
    echo "🚀 Loading images into KIND cluster..."

    images=(
        "restaurant-auth-service"
        "restaurant-restaurant-service"
        "restaurant-order-service"
        "restaurant-kitchen-service"
        "restaurant-api-gateway"
        "restaurant-frontend"
    )

    for image in "${images[@]}"; do
        echo "  Loading ${image}:latest..."
        kind load docker-image "${image}:latest" --name restaurant-cluster
    done

    echo -e "${GREEN}✓ All images loaded into KIND cluster${NC}"
else
    echo -e "${YELLOW}⚠️  KIND cluster not found. Images built but not loaded.${NC}"
    echo "  To load images later, run: kind load docker-image <image-name> --name restaurant-cluster"
fi

echo ""
echo "📊 Built images:"
docker images | grep "restaurant-"

echo ""
echo -e "${GREEN}✅ Image building completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "  1. Deploy to Kubernetes: ./scripts/k8s-deploy.sh"
echo "  2. Or run with Docker Compose: ./scripts/start-all-services.sh"
echo ""
