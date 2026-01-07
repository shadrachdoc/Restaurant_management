#!/bin/bash

##############################################################################
# Production Rollback Script
# This script rolls back production deployments to previous versions
##############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROD_NAMESPACE="restaurant-prod"
KIND_CLUSTER_NAME="restaurant-prod-cluster"

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

    # Set kubectl context to production cluster
    if ! kubectl config use-context "kind-${KIND_CLUSTER_NAME}" &> /dev/null; then
        log_error "Cannot switch to production cluster context."
        log_error "Is the production cluster running?"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace "$PROD_NAMESPACE" &> /dev/null; then
        log_error "Production namespace '$PROD_NAMESPACE' not found."
        exit 1
    fi

    log_info "Prerequisites check passed."
}

show_deployment_history() {
    log_info "Deployment history:"
    echo ""

    DEPLOYMENTS=("frontend" "api-gateway" "auth-service" "restaurant-service")

    for deployment in "${DEPLOYMENTS[@]}"; do
        echo "=== $deployment ==="
        kubectl rollout history deployment/"$deployment" -n "$PROD_NAMESPACE"
        echo ""
    done
}

get_current_revision() {
    local deployment=$1
    kubectl get deployment "$deployment" -n "$PROD_NAMESPACE" \
        -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}'
}

show_revision_details() {
    local deployment=$1
    local revision=$2

    log_info "Details for $deployment revision $revision:"
    kubectl rollout history deployment/"$deployment" -n "$PROD_NAMESPACE" --revision="$revision"
}

confirm_rollback() {
    local deployment=$1
    local target_revision=$2

    log_warn "You are about to rollback $deployment in PRODUCTION"
    log_warn "Target revision: $target_revision"
    echo ""

    # Show what we're rolling back to
    show_revision_details "$deployment" "$target_revision"

    echo ""
    read -p "Confirm rollback? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Rollback cancelled."
        exit 0
    fi
}

rollback_deployment() {
    local deployment=$1
    local target_revision=$2

    log_info "Rolling back $deployment to revision $target_revision..."

    if [ -z "$target_revision" ]; then
        # Rollback to previous revision
        kubectl rollout undo deployment/"$deployment" -n "$PROD_NAMESPACE"
    else
        # Rollback to specific revision
        kubectl rollout undo deployment/"$deployment" -n "$PROD_NAMESPACE" --to-revision="$target_revision"
    fi

    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    if ! kubectl rollout status deployment/"$deployment" -n "$PROD_NAMESPACE" --timeout=5m; then
        log_error "Rollback failed for $deployment"
        return 1
    fi

    log_info "$deployment rolled back successfully."
}

rollback_all_services() {
    log_info "Rolling back all services to previous version..."

    DEPLOYMENTS=("frontend" "api-gateway" "auth-service" "restaurant-service")
    FAILED_ROLLBACKS=()

    for deployment in "${DEPLOYMENTS[@]}"; do
        log_info "Rolling back $deployment..."

        if ! rollback_deployment "$deployment" ""; then
            FAILED_ROLLBACKS+=("$deployment")
        fi
    done

    if [ ${#FAILED_ROLLBACKS[@]} -gt 0 ]; then
        log_error "Rollback failed for: ${FAILED_ROLLBACKS[*]}"
        return 1
    fi

    log_info "All services rolled back successfully."
}

verify_rollback() {
    log_info "Verifying rollback..."

    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n "$PROD_NAMESPACE"

    # Verify all pods are running
    NOT_RUNNING=$(kubectl get pods -n "$PROD_NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [ "$NOT_RUNNING" -gt 0 ]; then
        log_warn "Warning: $NOT_RUNNING pod(s) are not in Running state"
        log_warn "Please investigate"
        return 1
    fi

    log_info "Rollback verification complete."
}

record_rollback() {
    log_info "Recording rollback..."

    DEPLOY_LOG="PRODUCTION_DEPLOYMENTS.md"
    ROLLBACK_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    ROLLED_BACK_BY=$(git config user.name || echo "Unknown")

    if [ ! -f "$DEPLOY_LOG" ]; then
        log_warn "Deployment log not found. Skipping recording."
        return
    fi

    # Add rollback entry
    cat >> "$DEPLOY_LOG" << EOF
### ROLLBACK - $ROLLBACK_DATE
- **Rolled back by**: $ROLLED_BACK_BY
- **Reason**: Manual rollback via script
- **Status**: Successful
- **Deployments rolled back**:
  - frontend
  - api-gateway
  - auth-service
  - restaurant-service

EOF

    log_info "Rollback recorded in $DEPLOY_LOG"
}

interactive_mode() {
    log_info "=== Interactive Rollback Mode ==="
    echo ""

    # Show deployment history
    show_deployment_history

    # Ask what to rollback
    echo "Options:"
    echo "  1. Rollback all services to previous version"
    echo "  2. Rollback specific service to specific revision"
    echo "  3. Cancel"
    echo ""
    read -p "Select option (1-3): " option

    case $option in
        1)
            confirm_rollback "all services" "previous"
            rollback_all_services
            verify_rollback
            record_rollback
            ;;
        2)
            echo ""
            read -p "Enter deployment name (frontend/api-gateway/auth-service/restaurant-service): " deployment
            read -p "Enter target revision number: " revision

            if [ -z "$deployment" ] || [ -z "$revision" ]; then
                log_error "Invalid input"
                exit 1
            fi

            confirm_rollback "$deployment" "$revision"
            rollback_deployment "$deployment" "$revision"
            verify_rollback
            record_rollback
            ;;
        3)
            log_info "Cancelled."
            exit 0
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
}

emergency_rollback() {
    log_warn "=== EMERGENCY ROLLBACK MODE ==="
    log_warn "This will immediately rollback ALL services to previous version"
    log_warn "Use this if production is completely broken"
    echo ""
    read -p "Are you absolutely sure? (YES/no): " confirm

    if [ "$confirm" != "YES" ]; then
        log_info "Emergency rollback cancelled."
        exit 0
    fi

    log_info "Executing emergency rollback..."
    rollback_all_services
    verify_rollback
    record_rollback

    log_warn "Emergency rollback complete!"
    log_warn "Please investigate the root cause before redeploying."
}

print_summary() {
    echo ""
    echo "=============================================="
    log_info "Rollback Summary"
    echo "=============================================="
    log_info "Environment: Production"
    log_info "Namespace: $PROD_NAMESPACE"
    log_info "Status: SUCCESS"
    echo "=============================================="
    echo ""
    log_info "Next steps:"
    echo "  1. Verify application functionality"
    echo "  2. Investigate what went wrong with the previous deployment"
    echo "  3. Fix issues before attempting new deployment"
    echo "  4. Update CHANGELOG.md with rollback information"
    echo ""
    log_info "Check pod status:"
    echo "  kubectl get pods -n $PROD_NAMESPACE"
    echo ""
    log_info "View logs:"
    echo "  kubectl logs -n $PROD_NAMESPACE -l app=<service-name> -f"
    echo ""
}

show_help() {
    cat << EOF
Production Rollback Script

Usage:
  $0 [options]

Options:
  --emergency     Emergency rollback (rolls back all services immediately)
  --help          Show this help message

Interactive Mode (default):
  Run without arguments to enter interactive mode where you can choose
  what to rollback and to which revision.

Examples:
  # Interactive mode
  $0

  # Emergency rollback (no confirmation)
  $0 --emergency

EOF
}

##############################################################################
# Main Execution
##############################################################################

main() {
    # Parse arguments
    case "${1:-}" in
        --emergency)
            check_prerequisites
            emergency_rollback
            print_summary
            ;;
        --help)
            show_help
            exit 0
            ;;
        "")
            check_prerequisites
            interactive_mode
            print_summary
            ;;
        *)
            log_error "Invalid argument: $1"
            show_help
            exit 1
            ;;
    esac

    log_info "Rollback completed successfully!"
}

# Run main function
main "$@"
