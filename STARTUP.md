# Restaurant Management System - Startup Guide

## 🚀 Quick Start

This guide contains all commands, URLs, and credentials needed to run and test the Restaurant Management System.

---

## 📋 Prerequisites

- KIND cluster running: `restaurant-cluster`
- Kubernetes namespace: `restaurant-system`
- All Docker images built and loaded into KIND

---

## 🔌 Port Forwarding Commands

Run these commands in separate terminal windows to access services locally:

### **1. Frontend UI**
```bash
kubectl port-forward svc/frontend -n restaurant-system 3000:80
```

### **2. API Gateway**
```bash
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000
```

### **3. Auth Service**
```bash
kubectl port-forward svc/auth-service -n restaurant-system 8001:8001
```

### **4. Restaurant Service**
```bash
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003
```

### **5. Order Service** (NEW)
```bash
kubectl port-forward svc/order-service -n restaurant-system 8004:8004
```

### **6. PostgreSQL Database**
```bash
kubectl port-forward svc/postgres-service -n restaurant-system 5432:5432
```

### **7. ArgoCD**
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### **All-in-One Port Forward Script**
```bash
#!/bin/bash
kubectl port-forward svc/frontend -n restaurant-system 3000:80 &
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/auth-service -n restaurant-system 8001:8001 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

echo "All port forwards started!"
echo "Use 'pkill -f port-forward' to stop all port forwards"
```

---

## 🌐 UI Access URLs

### **Main Application**
```
http://localhost:3000
```

### **Login Page**
```
http://localhost:3000/login
```

### **Customer Online Ordering (No Login Required)**
```
http://localhost:3000/menu/4bbfc1c9-670d-4899-afc9-44795055c27c/fe4547dd-7d99-4b9d-a460-0ece0ef921ab
```
*Replace restaurant_id and table_id with actual IDs from your database*

### **Customer Pages**
- Menu: `http://localhost:3000/customer/menu`
- Checkout: `http://localhost:3000/customer/checkout`
- Order Tracking: `http://localhost:3000/customer/orders`
- Customer Login: `http://localhost:3000/customer-login`

### **ArgoCD Dashboard**
```
http://localhost:8080
```

---

## 🔐 Test Credentials

### **Staff Users**

#### **Master Admin**
```
Username: admin
Password: password
Role: master_admin
User ID: fbd91e54-a091-4d36-9e3e-db62e05aa5ce
Dashboard: http://localhost:3000/master-admin
```

#### **Restaurant Admin**
```
Username: adminres
Password: password
Role: restaurant_admin
User ID: 4f9a03d6-a890-4462-a5ef-e3758963b0b6
Dashboard: http://localhost:3000/admin
```

#### **Chef/Kitchen Staff**
```
Username: adminchef1
Password: password
Role: chef
User ID: ed5cec07-63df-4ae9-8397-e11af02d945b
Dashboard: http://localhost:3000/kitchen
```

### **ArgoCD**
```
Username: admin
Password: (Get with command below)
```

**Get ArgoCD Password:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

### **PostgreSQL Database**
```
Host: localhost (or postgres-service inside cluster)
Port: 5432
Database: restaurant_db
Username: restaurant_admin
Password: restaurant_pass_2024
```

**Connection String:**
```
postgresql://restaurant_admin:restaurant_pass_2024@localhost:5432/restaurant_db
```

---

## 🔗 API Service URLs

### **Internal Kubernetes URLs** (Inside Cluster)
```
auth-service:          http://auth-service.restaurant-system.svc.cluster.local:8001
restaurant-service:    http://restaurant-service.restaurant-system.svc.cluster.local:8003
order-service:         http://order-service.restaurant-system.svc.cluster.local:8004
api-gateway:           http://api-gateway.restaurant-system.svc.cluster.local:8000
postgres:              postgresql://postgres-service.restaurant-system.svc.cluster.local:5432
redis:                 redis://redis-service.restaurant-system.svc.cluster.local:6379
```

### **External Access URLs** (via Port Forward)
```
Frontend:              http://localhost:3000
API Gateway:           http://localhost:8001
Auth Service:          http://localhost:8001
Restaurant Service:    http://localhost:8003
Order Service:         http://localhost:8004
PostgreSQL:            postgresql://localhost:5432
ArgoCD:                http://localhost:8080
```

---

## 📚 API Documentation (Swagger UI)

### **Auth Service**
```
http://localhost:8001/docs
```

### **Restaurant Service**
```
http://localhost:8003/docs
```

### **Order Service** (NEW)
```
http://localhost:8004/docs
```

### **API Gateway**
```
http://localhost:8001/docs
```

---

## 🧪 API Testing Examples

### **1. Health Checks**

#### Auth Service
```bash
curl http://localhost:8001/health
```

#### Restaurant Service
```bash
curl http://localhost:8003/health
```

#### Order Service
```bash
curl http://localhost:8004/health
```

#### API Gateway
```bash
curl http://localhost:8001/health
```

---

### **2. Authentication**

#### Login
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

#### Get Access Token (from database)
```bash
TOKEN=$(kubectl exec -n restaurant-system postgres-0 -- \
  psql -U restaurant_admin -d restaurant_db -t -c \
  "SELECT access_token FROM tokens WHERE user_id = 'fbd91e54-a091-4d36-9e3e-db62e05aa5ce' LIMIT 1" \
  2>/dev/null | tr -d ' ')
echo $TOKEN
```

---

### **3. Restaurant Management**

#### List Restaurants
```bash
curl -X GET http://localhost:8001/api/v1/restaurants \
  -H "Authorization: Bearer $TOKEN"
```

#### Create Restaurant
```bash
curl -X POST http://localhost:8001/api/v1/restaurants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "address": "123 Main St",
    "phone": "555-1234",
    "email": "test@restaurant.com"
  }'
```

#### Get Restaurant by ID
```bash
RESTAURANT_ID="4bbfc1c9-670d-4899-afc9-44795055c27c"
curl -X GET http://localhost:8001/api/v1/restaurants/$RESTAURANT_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

### **4. Online Orders** (NEW)

#### Create Table Session (No Auth Required)
```bash
curl -X POST http://localhost:8004/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "4bbfc1c9-670d-4899-afc9-44795055c27c",
    "table_id": "fe4547dd-7d99-4b9d-a460-0ece0ef921ab",
    "participant_name": "John Doe"
  }'
```

#### Create Order (Public)
```bash
curl -X POST http://localhost:8004/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "4bbfc1c9-670d-4899-afc9-44795055c27c",
    "table_id": "fe4547dd-7d99-4b9d-a460-0ece0ef921ab",
    "items": [
      {
        "menu_item_id": "item-uuid-here",
        "quantity": 2,
        "special_requests": "No onions"
      }
    ],
    "special_instructions": "Table near window"
  }'
```

#### List Orders for Restaurant
```bash
RESTAURANT_ID="4bbfc1c9-670d-4899-afc9-44795055c27c"
curl -X GET "http://localhost:8004/api/v1/restaurants/$RESTAURANT_ID/orders" \
  -H "Authorization: Bearer $TOKEN"
```

#### Update Order Status
```bash
ORDER_ID="order-uuid-here"
curl -X PATCH http://localhost:8004/api/v1/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "CONFIRMED"
  }'
```

**Order Status Flow:**
```
PENDING → CONFIRMED → PREPARING → READY → SERVED → COMPLETED
```

#### Request Assistance (No Auth)
```bash
curl -X POST http://localhost:8004/api/v1/assistance \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "4bbfc1c9-670d-4899-afc9-44795055c27c",
    "table_id": "fe4547dd-7d99-4b9d-a460-0ece0ef921ab",
    "request_type": "waiter",
    "message": "Need water please"
  }'
```

**Assistance Request Types:**
- `waiter` - Call waiter
- `bill` - Request bill
- `complaint` - Report issue
- `other` - Other requests

---

### **5. Via API Gateway**

All endpoints can also be accessed through the API Gateway:

```bash
# Auth endpoints
curl http://localhost:8001/api/v1/auth/login

# Restaurant endpoints
curl http://localhost:8001/api/v1/restaurants

# Order endpoints
curl http://localhost:8001/api/v1/orders
curl http://localhost:8001/api/v1/sessions
curl http://localhost:8001/api/v1/assistance
```

---

## 🗄️ Database Access

### **Connect to PostgreSQL**
```bash
kubectl exec -it postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db
```

### **Common Database Queries**

#### List all users
```sql
SELECT id, username, email, role FROM users;
```

#### List all restaurants
```sql
SELECT id, name, address, phone FROM restaurants;
```

#### List all tables
```sql
SELECT id, table_number, restaurant_id, seats FROM tables;
```

#### List all orders
```sql
SELECT id, order_number, status, total_amount, created_at FROM orders ORDER BY created_at DESC LIMIT 10;
```

#### List all table sessions
```sql
SELECT id, session_token, is_active, is_locked, created_at FROM table_sessions ORDER BY created_at DESC;
```

#### Get order with items
```sql
SELECT
    o.order_number,
    o.status,
    o.total_amount,
    oi.menu_item_name,
    oi.quantity,
    oi.unit_price
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
ORDER BY o.created_at DESC;
```

---

## 🛠️ Useful Kubernetes Commands

### **Check Pod Status**
```bash
kubectl get pods -n restaurant-system
```

### **Check Service Status**
```bash
kubectl get svc -n restaurant-system
```

### **View Pod Logs**
```bash
# Frontend
kubectl logs -f -n restaurant-system deployment/frontend

# API Gateway
kubectl logs -f -n restaurant-system deployment/api-gateway

# Auth Service
kubectl logs -f -n restaurant-system deployment/auth-service

# Restaurant Service
kubectl logs -f -n restaurant-system deployment/restaurant-service

# Order Service
kubectl logs -f -n restaurant-system deployment/order-service

# PostgreSQL
kubectl logs -f -n restaurant-system postgres-0
```

### **Restart Deployments**
```bash
kubectl rollout restart deployment/frontend -n restaurant-system
kubectl rollout restart deployment/api-gateway -n restaurant-system
kubectl rollout restart deployment/auth-service -n restaurant-system
kubectl rollout restart deployment/restaurant-service -n restaurant-system
kubectl rollout restart deployment/order-service -n restaurant-system
```

### **Delete All Port Forwards**
```bash
pkill -f "port-forward"
```

---

## 🎯 Testing Workflow

### **Complete Test Flow**

1. **Start Port Forwards**
```bash
kubectl port-forward svc/frontend -n restaurant-system 3000:80 &
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
```

2. **Access UI**
```
Open browser: http://localhost:3000
```

3. **Login as Admin**
```
Username: admin
Password: password
```

4. **Test Restaurant Management**
- Create restaurant
- Add tables
- Add menu items

5. **Test Online Ordering**
```
Open: http://localhost:3000/menu/{restaurant_id}/{table_id}
```

6. **Test Order Flow**
- Browse menu
- Add items to cart
- Place order
- Track order status

7. **Test Kitchen Dashboard**
```
Login as: adminchef1 / password
Open: http://localhost:3000/kitchen
```

8. **View Orders**
- See pending orders
- Update order status
- Complete orders

---

## 🔍 Troubleshooting

### **Pod Not Running**
```bash
kubectl describe pod -n restaurant-system <pod-name>
kubectl logs -n restaurant-system <pod-name>
```

### **Service Not Accessible**
```bash
# Check if service exists
kubectl get svc -n restaurant-system

# Check endpoints
kubectl get endpoints -n restaurant-system
```

### **Database Connection Issues**
```bash
# Test database connection
kubectl exec -n restaurant-system postgres-0 -- psql -U restaurant_admin -d restaurant_db -c "SELECT 1"
```

### **Port Forward Not Working**
```bash
# Kill all port forwards and restart
pkill -f "port-forward"

# Start fresh
kubectl port-forward svc/frontend -n restaurant-system 3000:80
```

### **Frontend Not Loading**
```bash
# Check frontend pod
kubectl get pods -n restaurant-system | grep frontend

# View logs
kubectl logs -n restaurant-system deployment/frontend
```

---

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│                    http://localhost:3000                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                             │
│                    http://localhost:8001                     │
└──────┬───────────┬──────────────┬──────────────┬────────────┘
       │           │              │              │
       ▼           ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
│   AUTH   │ │RESTAURANT│ │  ORDER   │ │   FUTURE: POS    │
│ :8001    │ │ :8003    │ │ :8004    │ │     :8005        │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────────────┘
     │            │            │
     └────────────┴────────────┴─────────────┐
                                              ▼
                                    ┌──────────────────┐
                                    │   PostgreSQL     │
                                    │     :5432        │
                                    └──────────────────┘
```

---

## 🎉 Quick Start Summary

**Minimum commands to get started:**

```bash
# 1. Start port forwards
kubectl port-forward svc/frontend -n restaurant-system 3000:80 &
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &

# 2. Open browser
open http://localhost:3000

# 3. Login
# Username: admin
# Password: password

# 4. Start testing!
```

---

## 📝 Notes

- All services are running on **worker2** node due to DNS issues on worker node
- Database password: `restaurant_pass_2024`
- JWT secrets are placeholders - change in production
- Order service is PUBLIC - no authentication required for customers
- Session tokens expire after 4 hours

---

**Last Updated:** 2025-12-20
**Version:** 1.0.0
**Status:** ✅ All Services Running
