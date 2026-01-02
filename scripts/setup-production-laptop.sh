#!/bin/bash

##############################################################################
# Production Laptop Setup Script
# This script sets up the production environment on a new laptop
##############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
PROD_DOMAIN="${PROD_DOMAIN:-prod.corpv3.com}"  # Update with your production domain
PROD_NAMESPACE="restaurant-prod"
KIND_CLUSTER_NAME="restaurant-prod-cluster"
ISTIO_VERSION="1.20.1"

##############################################################################
# Helper Functions
##############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_prerequisites() {
    log_step "Checking prerequisites..."

    # Check if running on Ubuntu
    if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release; then
        log_warn "This script is designed for Ubuntu. Your OS might not be supported."
        read -p "Continue anyway? (yes/no): " continue
        if [ "$continue" != "yes" ]; then
            exit 0
        fi
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        log_info "Install Docker with: sudo apt-get update && sudo apt-get install -y docker.io"
        exit 1
    fi

    # Check if kind is installed
    if ! command -v kind &> /dev/null; then
        log_warn "kind not found."
        read -p "Install kind? (yes/no): " install_kind
        if [ "$install_kind" == "yes" ]; then
            install_kind_cli
        else
            log_error "kind is required. Exiting."
            exit 1
        fi
    fi

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_warn "kubectl not found."
        read -p "Install kubectl? (yes/no): " install_kubectl
        if [ "$install_kubectl" == "yes" ]; then
            install_kubectl_cli
        else
            log_error "kubectl is required. Exiting."
            exit 1
        fi
    fi

    # Check if Helm is installed
    if ! command -v helm &> /dev/null; then
        log_warn "Helm not found."
        read -p "Install Helm? (yes/no): " install_helm
        if [ "$install_helm" == "yes" ]; then
            install_helm_cli
        else
            log_error "Helm is required. Exiting."
            exit 1
        fi
    fi

    log_info "Prerequisites check passed."
}

install_kind_cli() {
    log_info "Installing kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
    log_info "kind installed successfully."
}

install_kubectl_cli() {
    log_info "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/kubectl
    log_info "kubectl installed successfully."
}

install_helm_cli() {
    log_info "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    log_info "Helm installed successfully."
}

create_kind_cluster() {
    log_step "Creating kind cluster..."

    # Check if cluster already exists
    if kind get clusters | grep -q "^${KIND_CLUSTER_NAME}$"; then
        log_warn "Cluster '${KIND_CLUSTER_NAME}' already exists."
        read -p "Delete and recreate? (yes/no): " recreate
        if [ "$recreate" == "yes" ]; then
            kind delete cluster --name "$KIND_CLUSTER_NAME"
        else
            log_info "Using existing cluster."
            return
        fi
    fi

    # Create kind cluster configuration
    cat > /tmp/kind-config-prod.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${KIND_CLUSTER_NAME}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF

    # Create cluster
    log_info "Creating cluster with configuration..."
    kind create cluster --config /tmp/kind-config-prod.yaml

    # Wait for cluster to be ready
    log_info "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s

    log_info "Kind cluster created successfully."
}

install_istio() {
    log_step "Installing Istio..."

    # Check if istioctl is installed
    if ! command -v istioctl &> /dev/null; then
        log_info "Downloading istioctl..."
        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
        cd istio-${ISTIO_VERSION}
        sudo cp bin/istioctl /usr/local/bin/
        cd ..
        rm -rf istio-${ISTIO_VERSION}
    fi

    # Install Istio
    log_info "Installing Istio with production profile..."
    istioctl install --set profile=production -y

    # Enable automatic sidecar injection for production namespace
    log_info "Waiting for namespace creation..."

    log_info "Istio installed successfully."
}

create_namespace() {
    log_step "Creating production namespace..."

    if kubectl get namespace "$PROD_NAMESPACE" &> /dev/null; then
        log_info "Namespace '$PROD_NAMESPACE' already exists."
    else
        kubectl create namespace "$PROD_NAMESPACE"
        log_info "Namespace created."
    fi

    # Enable Istio sidecar injection
    kubectl label namespace "$PROD_NAMESPACE" istio-injection=enabled --overwrite

    log_info "Namespace configured successfully."
}

setup_ingress_nginx() {
    log_step "Setting up Nginx Ingress Controller..."

    # Install nginx ingress
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

    # Wait for ingress controller to be ready
    log_info "Waiting for ingress controller to be ready..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s

    log_info "Nginx Ingress Controller installed successfully."
}

install_monitoring() {
    log_step "Installing monitoring stack..."

    # Add Prometheus Helm repo
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update

    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Install Prometheus
    log_info "Installing Prometheus..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set grafana.adminPassword=admin \
        --wait \
        --timeout 10m

    log_info "Monitoring stack installed successfully."
    log_info "Grafana credentials: admin / admin (change on first login)"
}

create_secrets() {
    log_step "Creating production secrets..."

    log_warn "IMPORTANT: You need to create production secrets manually!"
    echo ""
    log_info "Required secrets:"
    echo "  1. JWT Secret Key (different from dev)"
    echo "  2. Database passwords (different from dev)"
    echo "  3. Any external API keys"
    echo ""
    log_info "Example commands to create secrets:"
    echo ""
    echo "  # JWT Secret"
    echo "  kubectl create secret generic jwt-secret \\"
    echo "    --from-literal=secret-key=\$(openssl rand -hex 32) \\"
    echo "    -n $PROD_NAMESPACE"
    echo ""
    echo "  # Database passwords"
    echo "  kubectl create secret generic db-passwords \\"
    echo "    --from-literal=auth-db-password=\$(openssl rand -base64 24) \\"
    echo "    --from-literal=restaurant-db-password=\$(openssl rand -base64 24) \\"
    echo "    -n $PROD_NAMESPACE"
    echo ""
    read -p "Press Enter to continue after creating secrets..."
}

configure_dns() {
    log_step "Configuring DNS..."

    # Get the node IP
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

    echo ""
    log_info "Production environment is running on IP: $NODE_IP"
    log_info "Please configure your DNS to point to this IP:"
    echo ""
    echo "  Domain: $PROD_DOMAIN"
    echo "  Type: A Record"
    echo "  Value: $NODE_IP"
    echo ""
    log_warn "If using /etc/hosts for testing, add:"
    echo "  $NODE_IP $PROD_DOMAIN"
    echo ""
    read -p "Press Enter after configuring DNS..."
}

print_summary() {
    echo ""
    echo "=============================================="
    log_info "Production Environment Setup Complete!"
    echo "=============================================="
    echo ""
    log_info "Cluster: $KIND_CLUSTER_NAME"
    log_info "Namespace: $PROD_NAMESPACE"
    log_info "Domain: $PROD_DOMAIN"
    echo ""
    log_info "Next steps:"
    echo "  1. Transfer deployment files from dev laptop"
    echo "  2. Create production secrets (see above)"
    echo "  3. Deploy using: ./scripts/deploy-production.sh <version>"
    echo ""
    log_info "Useful commands:"
    echo "  # Check cluster status"
    echo "  kubectl get nodes"
    echo "  kubectl get pods -n $PROD_NAMESPACE"
    echo ""
    echo "  # Access Grafana (monitoring)"
    echo "  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo "  # Then open: http://localhost:3000 (admin/admin)"
    echo ""
    echo "  # View logs"
    echo "  kubectl logs -n $PROD_NAMESPACE -l app=<service-name> -f"
    echo ""
    echo "  # Switch to this cluster"
    echo "  kubectl config use-context kind-$KIND_CLUSTER_NAME"
    echo ""
    echo "=============================================="
}

##############################################################################
# Main Execution
##############################################################################

main() {
    log_info "=== Production Laptop Setup Script ==="
    echo ""

    # Confirm setup
    log_warn "This script will set up the production environment."
    log_warn "Domain: $PROD_DOMAIN"
    log_warn "Cluster: $KIND_CLUSTER_NAME"
    echo ""
    read -p "Continue with setup? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Setup cancelled."
        exit 0
    fi

    check_prerequisites
    create_kind_cluster
    install_istio
    create_namespace
    setup_ingress_nginx
    install_monitoring
    create_secrets
    configure_dns
    print_summary

    log_info "Production laptop setup completed successfully!"
}

# Run main function
main
