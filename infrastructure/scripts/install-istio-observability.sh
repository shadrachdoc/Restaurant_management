#!/bin/bash

# Installation script for Istio and Observability Stack
# Restaurant Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ISTIO_VERSION="1.20.1"
NAMESPACE_APP="restaurant-management"
NAMESPACE_ISTIO="istio-system"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Restaurant Management - Istio & Observability Setup     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ kubectl found${NC}"

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ helm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ helm found${NC}"

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
echo ""

# Step 1: Install Istio
echo -e "${YELLOW}Step 1: Installing Istio ${ISTIO_VERSION}...${NC}"

if kubectl get namespace $NAMESPACE_ISTIO &> /dev/null; then
    echo -e "${YELLOW}⚠️  Istio namespace already exists. Skipping Istio installation.${NC}"
else
    # Download Istio
    echo "Downloading Istio..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
    cd istio-$ISTIO_VERSION

    # Install Istio
    echo "Installing Istio control plane..."
    ./bin/istioctl install -f ../infrastructure/istio/istio-config.yaml -y

    # Wait for Istio to be ready
    echo "Waiting for Istio to be ready..."
    kubectl wait --for=condition=ready pod -l app=istiod -n $NAMESPACE_ISTIO --timeout=300s

    cd ..
    echo -e "${GREEN}✅ Istio installed successfully${NC}"
fi
echo ""

# Step 2: Add Helm repositories
echo -e "${YELLOW}Step 2: Adding Helm repositories...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo add kiali https://kiali.org/helm-charts
helm repo update
echo -e "${GREEN}✅ Helm repositories added${NC}"
echo ""

# Step 3: Install Prometheus
echo -e "${YELLOW}Step 3: Installing Prometheus...${NC}"
helm upgrade --install prometheus prometheus-community/prometheus \
    -f infrastructure/helm/prometheus-values.yaml \
    -n $NAMESPACE_ISTIO --create-namespace \
    --wait --timeout=10m
echo -e "${GREEN}✅ Prometheus installed${NC}"
echo ""

# Step 4: Install Grafana
echo -e "${YELLOW}Step 4: Installing Grafana...${NC}"
helm upgrade --install grafana grafana/grafana \
    -f infrastructure/helm/grafana-values.yaml \
    -n $NAMESPACE_ISTIO \
    --wait --timeout=10m

# Get Grafana password
GRAFANA_PASSWORD=$(kubectl get secret --namespace $NAMESPACE_ISTIO grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
echo -e "${GREEN}✅ Grafana installed${NC}"
echo -e "${YELLOW}   Grafana admin password: ${GRAFANA_PASSWORD}${NC}"
echo ""

# Step 5: Install Loki
echo -e "${YELLOW}Step 5: Installing Loki + Promtail...${NC}"
helm upgrade --install loki grafana/loki-stack \
    -f infrastructure/helm/loki-values.yaml \
    -n $NAMESPACE_ISTIO \
    --wait --timeout=10m
echo -e "${GREEN}✅ Loki + Promtail installed${NC}"
echo ""

# Step 6: Install Jaeger
echo -e "${YELLOW}Step 6: Installing Jaeger...${NC}"
helm upgrade --install jaeger jaegertracing/jaeger \
    -f infrastructure/helm/jaeger-values.yaml \
    -n $NAMESPACE_ISTIO \
    --wait --timeout=10m
echo -e "${GREEN}✅ Jaeger installed${NC}"
echo ""

# Step 7: Install Kiali
echo -e "${YELLOW}Step 7: Installing Kiali...${NC}"
helm upgrade --install kiali-server kiali/kiali-server \
    -f infrastructure/helm/kiali-values.yaml \
    -n $NAMESPACE_ISTIO \
    --wait --timeout=10m
echo -e "${GREEN}✅ Kiali installed${NC}"
echo ""

# Step 8: Configure Application Namespace
echo -e "${YELLOW}Step 8: Configuring application namespace...${NC}"
kubectl create namespace $NAMESPACE_APP --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE_APP istio-injection=enabled --overwrite
echo -e "${GREEN}✅ Namespace configured with Istio injection${NC}"
echo ""

# Step 9: Apply Istio configurations
echo -e "${YELLOW}Step 9: Applying Istio configurations...${NC}"
kubectl apply -f infrastructure/istio/gateway.yaml -n $NAMESPACE_APP
kubectl apply -f infrastructure/istio/virtualservices/ -n $NAMESPACE_APP
kubectl apply -f infrastructure/istio/destinationrules/ -n $NAMESPACE_APP
kubectl apply -f infrastructure/istio/peerauthentication.yaml -n $NAMESPACE_APP
echo -e "${GREEN}✅ Istio configurations applied${NC}"
echo ""

# Step 10: Verify Installation
echo -e "${YELLOW}Step 10: Verifying installation...${NC}"

echo "Istio System Pods:"
kubectl get pods -n $NAMESPACE_ISTIO

echo ""
echo "Istio Services:"
kubectl get svc -n $NAMESPACE_ISTIO

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""

# Get Istio Ingress Gateway IP
INGRESS_IP=$(kubectl get svc istio-ingressgateway -n $NAMESPACE_ISTIO -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                Installation Summary                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Istio Ingress Gateway:${NC} $INGRESS_IP"
echo ""
echo -e "${YELLOW}Dashboard Access Instructions:${NC}"
echo ""
echo -e "${GREEN}1. Kiali (Service Mesh Dashboard):${NC}"
echo "   kubectl port-forward -n $NAMESPACE_ISTIO svc/kiali 20001:20001"
echo "   Then open: http://localhost:20001"
echo ""
echo -e "${GREEN}2. Grafana (Metrics & Dashboards):${NC}"
echo "   kubectl port-forward -n $NAMESPACE_ISTIO svc/grafana 3000:80"
echo "   Then open: http://localhost:3000"
echo "   Username: admin"
echo "   Password: $GRAFANA_PASSWORD"
echo ""
echo -e "${GREEN}3. Prometheus (Metrics Database):${NC}"
echo "   kubectl port-forward -n $NAMESPACE_ISTIO svc/prometheus-server 9090:80"
echo "   Then open: http://localhost:9090"
echo ""
echo -e "${GREEN}4. Jaeger (Distributed Tracing):${NC}"
echo "   kubectl port-forward -n $NAMESPACE_ISTIO svc/jaeger-query 16686:16686"
echo "   Then open: http://localhost:16686"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy your application with Helm"
echo "2. Verify sidecar injection: kubectl get pods -n $NAMESPACE_APP"
echo "3. Access dashboards to monitor traffic"
echo ""
echo -e "${GREEN}Installation completed successfully! 🎉${NC}"
