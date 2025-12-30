#!/bin/bash

##############################################################################
# Production Deployment Script
# This script deploys a specific release version to the production environment
##############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
PROD_DOMAIN="${PROD_DOMAIN:-prod.corpv3.com}"  # Update with your production domain
PROD_NAMESPACE="restaurant-prod"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-shadrach001}"
KIND_CLUSTER_NAME="restaurant-prod-cluster"

# Script arguments
VERSION="${1}"
DRY_RUN="${2:-false}"

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

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check if kind is available
    if ! command -v kind &> /dev/null; then
        log_error "kind not found. Please install kind."
        exit 1
    fi

    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        log_error "docker not found. Please install docker."
        exit 1
    fi

    # Check if cluster exists
    if ! kind get clusters | grep -q "^${KIND_CLUSTER_NAME}$"; then
        log_error "Production cluster '${KIND_CLUSTER_NAME}' not found."
        log_error "Please run setup-production-laptop.sh first."
        exit 1
    fi

    log_info "Prerequisites check passed."
}

validate_version() {
    if [ -z "$VERSION" ]; then
        log_error "Usage: $0 <version> [dry-run]"
        log_error "Example: $0 v1.0.0"
        log_error "Example: $0 v1.0.0 dry-run"
        exit 1
    fi

    # Validate version format (vMAJOR.MINOR.PATCH)
    if ! [[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format. Expected: vMAJOR.MINOR.PATCH (e.g., v1.0.0)"
        exit 1
    fi

    log_info "Deploying version: $VERSION"
}

confirm_deployment() {
    if [ "$DRY_RUN" == "dry-run" ]; then
        log_warn "DRY RUN MODE - No actual changes will be made"
        return
    fi

    log_warn "You are about to deploy version $VERSION to PRODUCTION"
    log_warn "Domain: $PROD_DOMAIN"
    log_warn "Cluster: $KIND_CLUSTER_NAME"
    log_warn "Namespace: $PROD_NAMESPACE"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Deployment cancelled."
        exit 0
    fi
}

pull_docker_images() {
    log_info "Pulling Docker images for version $VERSION..."

    SERVICES=(
        "restaurant-frontend"
        "restaurant_management_api-gateway"
        "restaurant_management_auth-service"
        "restaurant_management_restaurant-service"
    )

    for service in "${SERVICES[@]}"; do
        IMAGE="${DOCKER_REGISTRY}/${service}:${VERSION}"
        log_info "Pulling $IMAGE..."

        if [ "$DRY_RUN" != "dry-run" ]; then
            if ! docker pull "$IMAGE"; then
                log_error "Failed to pull image: $IMAGE"
                log_error "Make sure the version $VERSION has been built and pushed to registry."
                exit 1
            fi
        else
            log_info "[DRY RUN] Would pull: $IMAGE"
        fi
    done

    log_info "All images pulled successfully."
}

load_images_to_kind() {
    log_info "Loading images into kind cluster..."

    SERVICES=(
        "restaurant-frontend"
        "restaurant_management_api-gateway"
        "restaurant_management_auth-service"
        "restaurant_management_restaurant-service"
    )

    for service in "${SERVICES[@]}"; do
        IMAGE="${DOCKER_REGISTRY}/${service}:${VERSION}"
        log_info "Loading $IMAGE into kind cluster..."

        if [ "$DRY_RUN" != "dry-run" ]; then
            kind load docker-image "$IMAGE" --name "$KIND_CLUSTER_NAME"
        else
            log_info "[DRY RUN] Would load: $IMAGE"
        fi
    done

    log_info "All images loaded into kind cluster."
}

update_deployments() {
    log_info "Updating deployments to version $VERSION..."

    # Set kubectl context to production cluster
    kubectl config use-context "kind-${KIND_CLUSTER_NAME}"

    # Update frontend deployment
    log_info "Updating frontend..."
    if [ "$DRY_RUN" != "dry-run" ]; then
        kubectl set image deployment/frontend \
            frontend="${DOCKER_REGISTRY}/restaurant-frontend:${VERSION}" \
            -n "$PROD_NAMESPACE"
    else
        log_info "[DRY RUN] Would update frontend to ${VERSION}"
    fi

    # Update API gateway deployment
    log_info "Updating API gateway..."
    if [ "$DRY_RUN" != "dry-run" ]; then
        kubectl set image deployment/api-gateway \
            api-gateway="${DOCKER_REGISTRY}/restaurant_management_api-gateway:${VERSION}" \
            -n "$PROD_NAMESPACE"
    else
        log_info "[DRY RUN] Would update api-gateway to ${VERSION}"
    fi

    # Update auth service deployment
    log_info "Updating auth service..."
    if [ "$DRY_RUN" != "dry-run" ]; then
        kubectl set image deployment/auth-service \
            auth-service="${DOCKER_REGISTRY}/restaurant_management_auth-service:${VERSION}" \
            -n "$PROD_NAMESPACE"
    else
        log_info "[DRY RUN] Would update auth-service to ${VERSION}"
    fi

    # Update restaurant service deployment
    log_info "Updating restaurant service..."
    if [ "$DRY_RUN" != "dry-run" ]; then
        kubectl set image deployment/restaurant-service \
            restaurant-service="${DOCKER_REGISTRY}/restaurant_management_restaurant-service:${VERSION}" \
            -n "$PROD_NAMESPACE"
    else
        log_info "[DRY RUN] Would update restaurant-service to ${VERSION}"
    fi

    log_info "All deployments updated."
}

wait_for_rollout() {
    if [ "$DRY_RUN" == "dry-run" ]; then
        log_info "[DRY RUN] Would wait for rollout to complete"
        return
    fi

    log_info "Waiting for rollout to complete..."

    DEPLOYMENTS=("frontend" "api-gateway" "auth-service" "restaurant-service")

    for deployment in "${DEPLOYMENTS[@]}"; do
        log_info "Waiting for $deployment rollout..."
        if ! kubectl rollout status deployment/"$deployment" -n "$PROD_NAMESPACE" --timeout=5m; then
            log_error "Rollout failed for $deployment"
            log_error "Run './scripts/rollback-production.sh' to rollback"
            exit 1
        fi
    done

    log_info "All deployments rolled out successfully."
}

verify_deployment() {
    if [ "$DRY_RUN" == "dry-run" ]; then
        log_info "[DRY RUN] Would verify deployment"
        return
    fi

    log_info "Verifying deployment..."

    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n "$PROD_NAMESPACE"

    # Verify all pods are running
    NOT_RUNNING=$(kubectl get pods -n "$PROD_NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [ "$NOT_RUNNING" -gt 0 ]; then
        log_warn "Warning: $NOT_RUNNING pod(s) are not in Running state"
        log_warn "Please investigate before continuing"
    fi

    # Check services
    log_info "Checking services..."
    kubectl get svc -n "$PROD_NAMESPACE"

    log_info "Deployment verification complete."
}

tag_deployment() {
    if [ "$DRY_RUN" == "dry-run" ]; then
        log_info "[DRY RUN] Would create git tag: prod-${VERSION}"
        return
    fi

    log_info "Creating deployment tag..."

    # Create git tag for production deployment
    DEPLOY_TAG="prod-${VERSION}"
    DEPLOY_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

    if git tag -a "$DEPLOY_TAG" -m "Production deployment of $VERSION on $DEPLOY_DATE"; then
        log_info "Created tag: $DEPLOY_TAG"
        log_info "Push tag with: git push origin $DEPLOY_TAG"
    else
        log_warn "Failed to create git tag (may already exist)"
    fi
}

record_deployment() {
    if [ "$DRY_RUN" == "dry-run" ]; then
        log_info "[DRY RUN] Would record deployment in CHANGELOG.md"
        return
    fi

    log_info "Recording deployment..."

    # Add entry to deployment log
    DEPLOY_LOG="PRODUCTION_DEPLOYMENTS.md"
    DEPLOY_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    DEPLOYED_BY=$(git config user.name || echo "Unknown")

    if [ ! -f "$DEPLOY_LOG" ]; then
        cat > "$DEPLOY_LOG" << EOF
# Production Deployment History

This file tracks all production deployments.

## Deployments

EOF
    fi

    # Add deployment entry
    cat >> "$DEPLOY_LOG" << EOF
### $VERSION - $DEPLOY_DATE
- **Deployed by**: $DEPLOYED_BY
- **Domain**: $PROD_DOMAIN
- **Status**: Successful
- **Components**:
  - Frontend: ${DOCKER_REGISTRY}/restaurant-frontend:${VERSION}
  - API Gateway: ${DOCKER_REGISTRY}/restaurant_management_api-gateway:${VERSION}
  - Auth Service: ${DOCKER_REGISTRY}/restaurant_management_auth-service:${VERSION}
  - Restaurant Service: ${DOCKER_REGISTRY}/restaurant_management_restaurant-service:${VERSION}

EOF

    log_info "Deployment recorded in $DEPLOY_LOG"
}

print_summary() {
    echo ""
    echo "=============================================="
    log_info "Deployment Summary"
    echo "=============================================="
    log_info "Version: $VERSION"
    log_info "Environment: Production"
    log_info "Domain: https://$PROD_DOMAIN"
    log_info "Namespace: $PROD_NAMESPACE"
    log_info "Status: SUCCESS"
    echo "=============================================="
    echo ""
    log_info "Next steps:"
    echo "  1. Test application at https://$PROD_DOMAIN"
    echo "  2. Monitor logs: kubectl logs -n $PROD_NAMESPACE -l app=<service-name> -f"
    echo "  3. Check metrics in Grafana"
    echo "  4. If issues occur, rollback with: ./scripts/rollback-production.sh"
    echo ""
}

##############################################################################
# Main Execution
##############################################################################

main() {
    log_info "=== Production Deployment Script ==="

    validate_version
    check_prerequisites
    confirm_deployment
    pull_docker_images
    load_images_to_kind
    update_deployments
    wait_for_rollout
    verify_deployment
    tag_deployment
    record_deployment
    print_summary

    log_info "Production deployment completed successfully!"
}

# Run main function
main
