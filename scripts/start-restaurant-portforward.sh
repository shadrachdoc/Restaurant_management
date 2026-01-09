#!/bin/bash

# Port-forward script for Restaurant Management System
# Quick access to all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# PID file
PID_FILE="/tmp/restaurant-portforward.pid"

# Cleanup function
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
    echo -e "${GREEN}✅ All port-forwards stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Restaurant Management System - Port Forward   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not installed${NC}"
    exit 1
fi

# Check cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check namespace
if ! kubectl get namespace restaurant-system &> /dev/null; then
    echo -e "${RED}❌ restaurant-system namespace not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting port-forwards...${NC}"
echo ""

rm -f "$PID_FILE"

# 1. Frontend (port 3000)
echo -e "${CYAN}1. Starting Frontend...${NC}"
kubectl port-forward -n restaurant-system svc/frontend 3000:80 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ Frontend on http://localhost:3000${NC}"
echo ""

# 2. API Gateway (port 8000)
echo -e "${CYAN}2. Starting API Gateway...${NC}"
kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ API Gateway on http://localhost:8000${NC}"
echo -e "${GREEN}   ✅ API Docs on http://localhost:8000/docs${NC}"
echo ""

# 3. Auth Service (port 8001)
echo -e "${CYAN}3. Starting Auth Service...${NC}"
kubectl port-forward -n restaurant-system svc/auth-service 8001:8001 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ Auth Service on http://localhost:8001${NC}"
echo ""

# 4. Restaurant Service (port 8003)
echo -e "${CYAN}4. Starting Restaurant Service...${NC}"
kubectl port-forward -n restaurant-system svc/restaurant-service 8003:8003 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ Restaurant Service on http://localhost:8003${NC}"
echo ""

# 5. Order Service (port 8004)
echo -e "${CYAN}5. Starting Order Service...${NC}"
kubectl port-forward -n restaurant-system svc/order-service 8004:8004 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ Order Service on http://localhost:8004${NC}"
echo ""

# 6. Customer Service (port 8007) - if exists
if kubectl get svc customer-service -n restaurant-system &> /dev/null; then
    echo -e "${CYAN}6. Starting Customer Service...${NC}"
    kubectl port-forward -n restaurant-system svc/customer-service 8007:8007 > /dev/null 2>&1 &
    echo $! >> "$PID_FILE"
    sleep 2
    echo -e "${GREEN}   ✅ Customer Service on http://localhost:8007${NC}"
    echo ""
fi

# 7. PostgreSQL (port 5432)
echo -e "${CYAN}7. Starting PostgreSQL...${NC}"
kubectl port-forward -n restaurant-system svc/postgres-service 5432:5432 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ PostgreSQL on localhost:5432${NC}"
echo ""

# 8. Redis (port 6379)
echo -e "${CYAN}8. Starting Redis...${NC}"
kubectl port-forward -n restaurant-system svc/redis-service 6379:6379 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ Redis on localhost:6379${NC}"
echo ""

# 9. RabbitMQ (ports 5672, 15672)
echo -e "${CYAN}9. Starting RabbitMQ...${NC}"
kubectl port-forward -n restaurant-system svc/rabbitmq-service 15672:15672 5672:5672 > /dev/null 2>&1 &
echo $! >> "$PID_FILE"
sleep 2
echo -e "${GREEN}   ✅ RabbitMQ Management on http://localhost:15672${NC}"
echo -e "${GREEN}   ✅ RabbitMQ AMQP on localhost:5672${NC}"
echo ""

# 10. ArgoCD (port 8080)
if kubectl get svc argocd-server -n argocd &> /dev/null; then
    echo -e "${CYAN}10. Starting ArgoCD...${NC}"
    kubectl port-forward -n argocd svc/argocd-server 8080:80 > /dev/null 2>&1 &
    echo $! >> "$PID_FILE"
    sleep 2
    echo -e "${GREEN}   ✅ ArgoCD on http://localhost:8080 (redirects to HTTPS)${NC}"

    # Get ArgoCD password
    ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null || echo "")
    if [ -n "$ARGOCD_PASS" ]; then
        echo -e "${YELLOW}   📝 Username: admin${NC}"
        echo -e "${YELLOW}   📝 Password: ${ARGOCD_PASS}${NC}"
    fi
    echo ""
fi

# 11. Grafana (port 3001)
if kubectl get svc grafana -n istio-system &> /dev/null; then
    echo -e "${CYAN}11. Starting Grafana...${NC}"
    kubectl port-forward -n istio-system svc/grafana 3001:80 > /dev/null 2>&1 &
    echo $! >> "$PID_FILE"
    sleep 2
    echo -e "${GREEN}   ✅ Grafana on http://localhost:3001${NC}"
    echo -e "${YELLOW}   📝 Username: admin${NC}"
    echo -e "${YELLOW}   📝 Password: changeme123${NC}"
    echo ""
fi

echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         All Port-Forwards are Running!            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}📊 Service URLs:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Frontend:          http://localhost:3000"
echo -e "API Gateway:       http://localhost:8000"
echo -e "API Docs:          http://localhost:8000/docs"
echo -e "Auth Service:      http://localhost:8001"
echo -e "Restaurant Svc:    http://localhost:8003"
echo -e "Order Service:     http://localhost:8004"
if kubectl get svc customer-service -n restaurant-system &> /dev/null; then
    echo -e "Customer Service:  http://localhost:8007"
fi
echo -e "RabbitMQ Console:  http://localhost:15672 (guest/guest)"
if kubectl get svc argocd-server -n argocd &> /dev/null; then
    ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null || echo "admin")
    echo -e "ArgoCD:            http://localhost:8080 (admin / ${ARGOCD_PASS})"
fi
if kubectl get svc grafana -n istio-system &> /dev/null; then
    echo -e "Grafana:           http://localhost:3001 (admin / changeme123)"
fi
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}💡 Test Credentials:${NC}"
echo "   Master Admin:      admin / admin123"
echo "   Restaurant Admin:  adminres / password"
echo "   Chef:              adminchef / password"
echo ""

echo -e "${YELLOW}🔍 Useful Commands:${NC}"
echo "   Check pods:        kubectl get pods -n restaurant-system"
echo "   View logs:         kubectl logs -f <pod-name> -n restaurant-system"
echo "   Restart service:   kubectl rollout restart deployment/<name> -n restaurant-system"
echo ""

echo -e "${GREEN}✨ All services ready! Press CTRL+C to stop all port-forwards.${NC}"
echo ""

# Keep running and monitor
while true; do
    sleep 30
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
    echo -e "${CYAN}[$(date '+%H:%M:%S')] Status: ${RUNNING}/${TOTAL} port-forwards running${NC}"

    if [ "$RUNNING" -lt "$TOTAL" ]; then
        echo -e "${RED}⚠️  Some port-forwards stopped. Exiting...${NC}"
        cleanup
    fi
done
