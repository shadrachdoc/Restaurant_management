#!/bin/bash

# Script to start all observability dashboards
# Restaurant Management System - Istio & Observability

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# PID file to track background processes
PID_FILE="/tmp/istio-dashboards.pid"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all port-forwards...${NC}"
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    echo -e "${GREEN}✅ All dashboards stopped${NC}"
    exit 0
}

# Trap CTRL+C and other termination signals
trap cleanup SIGINT SIGTERM EXIT

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Starting Observability Dashboards & ArgoCD            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check if istio-system namespace exists
if ! kubectl get namespace istio-system &> /dev/null; then
    echo -e "${RED}❌ istio-system namespace not found. Please install Istio first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting port-forwards...${NC}"
echo ""

# Clear old PID file
rm -f "$PID_FILE"

# Start Kiali port-forward
echo -e "${CYAN}1. Starting Kiali (Service Mesh Dashboard)...${NC}"
kubectl port-forward -n istio-system svc/kiali 20001:20001 > /dev/null 2>&1 &
KIALI_PID=$!
echo "$KIALI_PID" >> "$PID_FILE"
sleep 2

if kill -0 "$KIALI_PID" 2>/dev/null; then
    echo -e "${GREEN}   ✅ Kiali running on http://localhost:20001${NC}"
else
    echo -e "${RED}   ❌ Failed to start Kiali${NC}"
fi
echo ""

# Start Grafana port-forward
echo -e "${CYAN}2. Starting Grafana (Metrics & Dashboards)...${NC}"
kubectl port-forward -n istio-system svc/grafana 3000:80 > /dev/null 2>&1 &
GRAFANA_PID=$!
echo "$GRAFANA_PID" >> "$PID_FILE"
sleep 2

if kill -0 "$GRAFANA_PID" 2>/dev/null; then
    echo -e "${GREEN}   ✅ Grafana running on http://localhost:3000${NC}"
    echo -e "${YELLOW}   📝 Username: admin${NC}"
    echo -e "${YELLOW}   📝 Password: changeme123${NC}"
else
    echo -e "${RED}   ❌ Failed to start Grafana${NC}"
fi
echo ""

# Start Prometheus port-forward
echo -e "${CYAN}3. Starting Prometheus (Metrics Database)...${NC}"
kubectl port-forward -n istio-system svc/prometheus-server 9090:80 > /dev/null 2>&1 &
PROMETHEUS_PID=$!
echo "$PROMETHEUS_PID" >> "$PID_FILE"
sleep 2

if kill -0 "$PROMETHEUS_PID" 2>/dev/null; then
    echo -e "${GREEN}   ✅ Prometheus running on http://localhost:9090${NC}"
else
    echo -e "${RED}   ❌ Failed to start Prometheus${NC}"
fi
echo ""

# Optional: Start Jaeger if available
if kubectl get svc jaeger-query -n istio-system &> /dev/null; then
    echo -e "${CYAN}4. Starting Jaeger (Distributed Tracing)...${NC}"
    kubectl port-forward -n istio-system svc/jaeger-query 16686:16686 > /dev/null 2>&1 &
    JAEGER_PID=$!
    echo "$JAEGER_PID" >> "$PID_FILE"
    sleep 2

    if kill -0 "$JAEGER_PID" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Jaeger running on http://localhost:16686${NC}"
    else
        echo -e "${RED}   ❌ Failed to start Jaeger${NC}"
    fi
    echo ""
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              All Dashboards are Running!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 Dashboard URLs:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}1. Kiali (Service Mesh):${NC}      http://localhost:20001"
echo -e "${CYAN}2. Grafana (Dashboards):${NC}      http://localhost:3000  (admin / changeme123)"
echo -e "${CYAN}3. Prometheus (Metrics):${NC}      http://localhost:9090"
if kubectl get svc jaeger-query -n istio-system &> /dev/null; then
    echo -e "${CYAN}4. Jaeger (Tracing):${NC}          http://localhost:16686"
fi
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}💡 Quick Tips:${NC}"
echo "   • All dashboards will open in your browser"
echo "   • Keep this terminal window open"
echo "   • Press CTRL+C to stop all dashboards"
echo ""

echo -e "${YELLOW}🔍 What to check:${NC}"
echo "   • Kiali:      Service topology and traffic flow"
echo "   • Grafana:    Pre-loaded Istio dashboards"
echo "   • Prometheus: Raw metrics and PromQL queries"
echo ""

# Function to open URLs in browser (works on Linux, macOS, WSL)
open_browser() {
    local url=$1
    if command -v xdg-open &> /dev/null; then
        xdg-open "$url" &> /dev/null &
    elif command -v open &> /dev/null; then
        open "$url" &> /dev/null &
    elif command -v wslview &> /dev/null; then
        wslview "$url" &> /dev/null &
    fi
}

# Ask if user wants to auto-open browsers
read -p "$(echo -e ${YELLOW}Do you want to open all dashboards in your browser? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}Opening dashboards in browser...${NC}"
    sleep 2
    open_browser "http://localhost:20001"
    sleep 1
    open_browser "http://localhost:3000"
    sleep 1
    open_browser "http://localhost:9090"
    if kubectl get svc jaeger-query -n istio-system &> /dev/null; then
        sleep 1
        open_browser "http://localhost:16686"
    fi
    echo -e "${GREEN}✅ Dashboards opened${NC}"
    echo ""
fi

echo -e "${GREEN}✨ Dashboards are ready! Press CTRL+C to stop all port-forwards.${NC}"
echo ""

# Keep script running and display status every 30 seconds
while true; do
    sleep 30

    # Check if all processes are still running
    RUNNING=0
    TOTAL=0
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            TOTAL=$((TOTAL + 1))
            if kill -0 "$pid" 2>/dev/null; then
                RUNNING=$((RUNNING + 1))
            fi
        done < "$PID_FILE"
    fi

    echo -e "${BLUE}[$(date '+%H:%M:%S')] Status: ${RUNNING}/${TOTAL} dashboards running${NC}"

    # If any process died, exit
    if [ "$RUNNING" -lt "$TOTAL" ]; then
        echo -e "${RED}⚠️  Some dashboards stopped unexpectedly. Exiting...${NC}"
        cleanup
    fi
done
