#!/bin/bash

# Script to import custom Grafana dashboards
# Restaurant Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NAMESPACE="istio-system"
DASHBOARD_DIR="infrastructure/grafana/dashboards"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Importing Grafana Dashboards                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Grafana is running
if ! kubectl get pod -n $NAMESPACE -l app.kubernetes.io/name=grafana | grep -q Running; then
    echo -e "${RED}❌ Grafana is not running in namespace $NAMESPACE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Grafana is running${NC}"
echo ""

# Get Grafana pod name
GRAFANA_POD=$(kubectl get pod -n $NAMESPACE -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}')
echo -e "${BLUE}Grafana Pod: $GRAFANA_POD${NC}"
echo ""

# Get Grafana admin password
GRAFANA_PASSWORD=$(kubectl get secret --namespace $NAMESPACE grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
echo -e "${YELLOW}Grafana Password: $GRAFANA_PASSWORD${NC}"
echo ""

# Start port-forward in background
echo -e "${YELLOW}Starting port-forward to Grafana...${NC}"
kubectl port-forward -n $NAMESPACE svc/grafana 3000:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Function to cleanup on exit
cleanup() {
    if [ ! -z "$PF_PID" ]; then
        kill $PF_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo -e "${GREEN}✅ Port-forward established${NC}"
echo ""

# Import dashboards using Grafana API
import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)

    echo -e "${CYAN}Importing: $dashboard_name${NC}"

    # Read dashboard JSON
    DASHBOARD_JSON=$(cat "$dashboard_file")

    # Create payload
    PAYLOAD=$(cat <<EOF
{
  "dashboard": $DASHBOARD_JSON,
  "overwrite": true,
  "message": "Imported by script"
}
EOF
)

    # Import via API
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "admin:$GRAFANA_PASSWORD" \
        -d "$PAYLOAD" \
        http://localhost:3000/api/dashboards/db)

    # Check response
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        echo -e "${GREEN}   ✅ Successfully imported: $dashboard_name${NC}"
        # Extract dashboard URL
        DASHBOARD_URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
        echo -e "${BLUE}   📊 URL: http://localhost:3000$DASHBOARD_URL${NC}"
    else
        echo -e "${RED}   ❌ Failed to import: $dashboard_name${NC}"
        echo -e "${YELLOW}   Response: $RESPONSE${NC}"
    fi
    echo ""
}

# Import all dashboards
echo -e "${YELLOW}Importing dashboards...${NC}"
echo ""

if [ -d "$DASHBOARD_DIR" ]; then
    for dashboard_file in "$DASHBOARD_DIR"/*.json; do
        if [ -f "$dashboard_file" ]; then
            import_dashboard "$dashboard_file"
        fi
    done
else
    echo -e "${RED}❌ Dashboard directory not found: $DASHBOARD_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Dashboard Import Complete!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 Access Grafana Dashboards:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}URL:${NC}       http://localhost:3000"
echo -e "${CYAN}Username:${NC}  admin"
echo -e "${CYAN}Password:${NC}  $GRAFANA_PASSWORD"
echo ""
echo -e "${YELLOW}Custom Dashboards Imported:${NC}"
echo "  1. Restaurant Management - Metrics Dashboard"
echo "  2. Restaurant Management - Logs Dashboard"
echo "  3. Restaurant Management - Traces Dashboard"
echo ""
echo -e "${YELLOW}Pre-loaded Istio Dashboards:${NC}"
echo "  4. Istio Mesh Dashboard"
echo "  5. Istio Service Dashboard"
echo "  6. Istio Workload Dashboard"
echo "  7. Istio Performance Dashboard"
echo "  8. Istio Control Plane Dashboard"
echo ""
echo -e "${GREEN}🎉 All dashboards ready to use!${NC}"
