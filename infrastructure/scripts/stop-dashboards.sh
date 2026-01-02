#!/bin/bash

# Script to stop all observability dashboards
# Restaurant Management System - Istio & Observability

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PID_FILE="/tmp/istio-dashboards.pid"

echo -e "${YELLOW}Stopping all dashboard port-forwards...${NC}"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No running dashboards found.${NC}"
    echo ""
    echo -e "${BLUE}Checking for any kubectl port-forward processes...${NC}"

    # Kill any kubectl port-forward processes for our ports
    pkill -f "kubectl port-forward.*istio-system.*kiali.*20001" 2>/dev/null || true
    pkill -f "kubectl port-forward.*istio-system.*grafana.*3000" 2>/dev/null || true
    pkill -f "kubectl port-forward.*istio-system.*prometheus.*9090" 2>/dev/null || true
    pkill -f "kubectl port-forward.*istio-system.*jaeger.*16686" 2>/dev/null || true
    pkill -f "kubectl port-forward.*argocd.*argocd-server.*8080" 2>/dev/null || true

    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
fi

# Stop processes from PID file
STOPPED=0
while IFS= read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        STOPPED=$((STOPPED + 1))
        echo -e "${GREEN}✅ Stopped process $pid${NC}"
    fi
done < "$PID_FILE"

# Remove PID file
rm -f "$PID_FILE"

echo ""
echo -e "${GREEN}✅ Stopped $STOPPED dashboard(s)${NC}"
echo -e "${GREEN}All dashboards are now offline.${NC}"
