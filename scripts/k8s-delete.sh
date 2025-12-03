#!/bin/bash

# Delete Kubernetes deployment for Restaurant Management System

set -e

echo "🗑️  Deleting Restaurant Management System from Kubernetes..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Ask for confirmation
read -p "Are you sure you want to delete the entire deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Deletion cancelled."
    exit 0
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed.${NC}"
    exit 1
fi

# Delete namespace (this will delete all resources in the namespace)
echo "🗑️  Deleting namespace and all resources..."
kubectl delete namespace restaurant-system --ignore-not-found=true

echo ""
echo -e "${GREEN}✅ Deployment deleted successfully!${NC}"
echo ""
echo "📝 Note: This does not delete:"
echo "  - Docker images (use 'docker image rm' to delete)"
echo "  - KIND cluster (use 'kind delete cluster --name restaurant-cluster' to delete)"
echo ""
