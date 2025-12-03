#!/bin/bash

# Setup KIND (Kubernetes in Docker) cluster for Restaurant Management System

set -e

echo "🎯 Setting up KIND cluster for Restaurant Management System..."
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

# Check if KIND is installed
if ! command -v kind &> /dev/null; then
    echo -e "${YELLOW}⚠️  KIND is not installed. Installing KIND...${NC}"

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
        chmod +x ./kind
        sudo mv ./kind /usr/local/bin/kind
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install kind
    else
        echo -e "${RED}❌ Unsupported OS. Please install KIND manually from https://kind.sigs.k8s.io/docs/user/quick-start/#installation${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ KIND installed successfully${NC}"
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}⚠️  kubectl is not installed. Installing kubectl...${NC}"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install kubectl
    fi

    echo -e "${GREEN}✓ kubectl installed successfully${NC}"
fi

echo ""

# Delete existing cluster if it exists
if kind get clusters | grep -q "^restaurant-cluster$"; then
    echo -e "${YELLOW}⚠️  Existing cluster found. Deleting...${NC}"
    kind delete cluster --name restaurant-cluster
fi

# Create KIND cluster
echo "🏗️  Creating KIND cluster..."
kind create cluster --config infrastructure/kubernetes/kind-config.yaml

echo -e "${GREEN}✓ KIND cluster created successfully${NC}"
echo ""

# Wait for cluster to be ready
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo -e "${GREEN}✓ Cluster is ready${NC}"
echo ""

# Install NGINX Ingress Controller
echo "🌐 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "⏳ Waiting for Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

echo -e "${GREEN}✓ Ingress Controller is ready${NC}"
echo ""

# Install Metrics Server (for HPA)
echo "📊 Installing Metrics Server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics server for KIND
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'

echo -e "${GREEN}✓ Metrics Server installed${NC}"
echo ""

# Load Docker images (if they exist locally)
echo "🐳 Loading Docker images into KIND cluster..."

images=(
  "restaurant-auth-service:latest"
  "restaurant-restaurant-service:latest"
  "restaurant-order-service:latest"
  "restaurant-kitchen-service:latest"
  "restaurant-api-gateway:latest"
  "restaurant-frontend:latest"
)

for image in "${images[@]}"; do
    if docker image inspect "$image" > /dev/null 2>&1; then
        echo "  Loading $image..."
        kind load docker-image "$image" --name restaurant-cluster
    else
        echo -e "${YELLOW}  ⚠️  Image $image not found locally. You'll need to build it first.${NC}"
    fi
done

echo ""

# Create necessary directories on nodes for PersistentVolumes
echo "📁 Creating storage directories on cluster nodes..."
docker exec restaurant-cluster-control-plane mkdir -p /mnt/data/postgres
docker exec restaurant-cluster-control-plane mkdir -p /mnt/data/redis
docker exec restaurant-cluster-control-plane mkdir -p /mnt/data/rabbitmq
docker exec restaurant-cluster-worker mkdir -p /mnt/data/postgres 2>/dev/null || true
docker exec restaurant-cluster-worker2 mkdir -p /mnt/data/postgres 2>/dev/null || true

echo -e "${GREEN}✓ Storage directories created${NC}"
echo ""

# Display cluster info
echo "📊 Cluster Information:"
echo "======================"
kubectl cluster-info --context kind-restaurant-cluster
echo ""

echo "🔍 Nodes:"
kubectl get nodes
echo ""

echo -e "${GREEN}✅ KIND cluster setup completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "  1. Build Docker images: docker-compose build"
echo "  2. Deploy to Kubernetes: ./scripts/k8s-deploy.sh"
echo "  3. Check deployment: kubectl get pods -n restaurant-system"
echo ""
echo "💡 Useful commands:"
echo "  - View cluster: kubectl cluster-info"
echo "  - Delete cluster: kind delete cluster --name restaurant-cluster"
echo "  - Load image: kind load docker-image <image-name> --name restaurant-cluster"
echo ""
