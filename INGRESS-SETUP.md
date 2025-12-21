# Ingress Setup Guide - No More Port Forwarding! 🎉

## Overview

Ingress has been configured for your Restaurant Management System. You can now access all services using domain names instead of port forwarding!

---

## ✅ What's Configured

### **Ingress Controller**: NGINX Ingress Controller v1.8.1
### **Namespace**: ingress-nginx
### **Ingress Resource**: restaurant-ingress (in restaurant-system namespace)

---

## 🌐 Domain Mappings

All services are accessible via these domains:

| Service | Domain | Description |
|---------|--------|-------------|
| **Frontend UI** | http://restaurant.local | Main web application |
| **API Gateway** | http://api.restaurant.local | All API requests |
| **Order Service** | http://orders.restaurant.local | Online orders API |
| **Restaurant Service** | http://restaurants.restaurant.local | Restaurant management API |
| **Auth Service** | http://auth.restaurant.local | Authentication API |

---

## 🔧 Setup Instructions

### Step 1: Add Hosts Entries

Add these lines to your `/etc/hosts` file:

```bash
sudo nano /etc/hosts
```

Add:
```
127.0.0.1 restaurant.local
127.0.0.1 www.restaurant.local
127.0.0.1 api.restaurant.local
127.0.0.1 orders.restaurant.local
127.0.0.1 restaurants.restaurant.local
127.0.0.1 auth.restaurant.local
```

**Or run this command:**
```bash
echo "127.0.0.1 restaurant.local www.restaurant.local api.restaurant.local orders.restaurant.local restaurants.restaurant.local auth.restaurant.local" | sudo tee -a /etc/hosts
```

### Step 2: Verify Ingress is Running

```bash
kubectl get pods -n ingress-nginx
kubectl get ingress -n restaurant-system
```

You should see:
- ingress-nginx-controller pod in Running state
- restaurant-ingress with all 5 hosts listed

---

## 🚀 Access URLs

### **Frontend (UI)**
```
http://restaurant.local
```
- Login page
- Restaurant dashboard
- Admin panel
- Kitchen view

### **API Gateway**
```
http://api.restaurant.local/health
http://api.restaurant.local/api/v1/auth/login
http://api.restaurant.local/api/v1/restaurants
http://api.restaurant.local/api/v1/orders
```

### **Order Service (Direct)**
```
http://orders.restaurant.local/health
http://orders.restaurant.local/docs
http://orders.restaurant.local/api/v1/orders
http://orders.restaurant.local/api/v1/sessions
http://orders.restaurant.local/api/v1/assistance
```

### **Restaurant Service (Direct)**
```
http://restaurants.restaurant.local/health
http://restaurants.restaurant.local/docs
http://restaurants.restaurant.local/api/v1/restaurants
```

### **Auth Service (Direct)**
```
http://auth.restaurant.local/health
http://auth.restaurant.local/docs
http://auth.restaurant.local/api/v1/auth/login
```

---

## 🧪 Testing

### Test 1: Frontend Access
```bash
curl http://restaurant.local
# Should return HTML page
```

### Test 2: API Gateway Health
```bash
curl http://api.restaurant.local/health
# Should return: {"status":"healthy","service":"api-gateway"}
```

### Test 3: Order Service Health
```bash
curl http://orders.restaurant.local/health
# Should return: {"status":"healthy","service":"order-service"}
```

### Test 4: Login via API Gateway
```bash
curl -X POST http://api.restaurant.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
# Should return access_token
```

### Test 5: Create Order (Public)
```bash
curl -X POST http://orders.restaurant.local/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "your-restaurant-id",
    "table_id": "your-table-id",
    "items": [...]
  }'
```

---

## 📱 Browser Access

Simply open your browser and navigate to:

```
http://restaurant.local
```

**Login with:**
- Username: `admin`
- Password: `password`

---

## 🔄 Benefits Over Port Forwarding

### ✅ **Before (Port Forwarding)**
```bash
# Required multiple terminal windows
kubectl port-forward svc/frontend -n restaurant-system 3000:80 &
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &

# Access via ports
http://localhost:3000
http://localhost:8001
http://localhost:8004
```

### ✅ **After (Ingress)**
```bash
# NO port forwarding needed!
# Just use domain names
http://restaurant.local
http://api.restaurant.local
http://orders.restaurant.local
```

**Advantages:**
- ✅ No background processes to manage
- ✅ No terminal windows to keep open
- ✅ Cleaner URLs (no ports)
- ✅ Production-like setup
- ✅ Easier to remember
- ✅ Better for development and testing

---

## 🔧 Update Postman Collection

Update your Postman environment variables to use new Ingress URLs:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `base_url` | `http://localhost:8001` | `http://api.restaurant.local` |
| `auth_url` | `http://localhost:8001` | `http://api.restaurant.local` |
| `restaurant_url` | `http://localhost:8003` | `http://restaurants.restaurant.local` |
| `order_url` | `http://localhost:8004` | `http://orders.restaurant.local` |

---

## 📊 Architecture

```
                         Browser/Postman
                               |
                               | http://restaurant.local
                               | http://api.restaurant.local
                               | http://orders.restaurant.local
                               ↓
                     ┌─────────────────────┐
                     │  NGINX Ingress      │
                     │  Controller         │
                     │  (Port 80)          │
                     └─────────┬───────────┘
                               |
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │ Frontend │        │   API    │        │  Order   │
    │ Service  │        │ Gateway  │        │ Service  │
    │  :80     │        │  :8000   │        │  :8004   │
    └──────────┘        └──────────┘        └──────────┘
```

---

## 🛠️ Troubleshooting

### Issue 1: "Connection Refused"

**Problem:** Cannot access http://restaurant.local

**Solution:**
```bash
# 1. Check Ingress controller is running
kubectl get pods -n ingress-nginx

# 2. Check /etc/hosts entries exist
cat /etc/hosts | grep restaurant.local

# 3. Restart Ingress controller if needed
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
```

### Issue 2: "404 Not Found"

**Problem:** Page not found when accessing a service

**Solution:**
```bash
# 1. Check Ingress configuration
kubectl get ingress -n restaurant-system restaurant-ingress -o yaml

# 2. Check backend services are running
kubectl get pods -n restaurant-system

# 3. Check service endpoints
kubectl get endpoints -n restaurant-system
```

### Issue 3: Ingress Controller Not Ready

**Problem:** Ingress controller pod is not ready

**Solution:**
```bash
# Check pod status
kubectl get pods -n ingress-nginx

# View logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Delete and recreate if needed
kubectl delete pod -n ingress-nginx -l app.kubernetes.io/component=controller
```

---

## 📝 Kubernetes Commands

### Check Ingress Status
```bash
kubectl get ingress -n restaurant-system
kubectl describe ingress restaurant-ingress -n restaurant-system
```

### View Ingress Controller Logs
```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller -f
```

### Check Ingress Controller Status
```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### Restart Ingress Controller
```bash
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
```

### Delete and Reinstall Ingress
```bash
kubectl delete namespace ingress-nginx
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

---

## 🎯 Complete Test Workflow

### 1. Access Frontend
```bash
# Open browser
open http://restaurant.local

# Or test with curl
curl -I http://restaurant.local
```

### 2. Test API via Ingress
```bash
# Login
curl -X POST http://api.restaurant.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# List restaurants
TOKEN="your-access-token-here"
curl -H "Authorization: Bearer $TOKEN" \
  http://api.restaurant.local/api/v1/restaurants
```

### 3. Test Order Service
```bash
# Create table session (no auth required)
curl -X POST http://orders.restaurant.local/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "restaurant-uuid",
    "table_id": "table-uuid",
    "participant_name": "John Doe"
  }'

# View API documentation
open http://orders.restaurant.local/docs
```

---

## 💡 Pro Tips

1. **Use Ingress for Everything**: No more port forwarding needed!

2. **Bookmark URLs**: Add these to your browser:
   - http://restaurant.local (Frontend)
   - http://api.restaurant.local (API Gateway)
   - http://orders.restaurant.local/docs (Order Service Docs)

3. **Update Postman**: Import the updated collection with Ingress URLs

4. **Production-Ready**: This setup mirrors production Ingress configuration

5. **Easy Testing**: Share URLs with team members (after they update /etc/hosts)

---

## 📚 Related Documentation

- **STARTUP.md** - Service details and credentials
- **POSTMAN.md** - API testing guide
- **POSTMAN-QUICK-START.md** - Quick Postman setup

---

## 🎉 Summary

**You can now access all services via Ingress!**

✅ **No more port forwarding**
✅ **Clean domain names**
✅ **Production-like setup**
✅ **Easier to use and share**

**Main URL:**
```
http://restaurant.local
```

**Happy developing!** 🚀
