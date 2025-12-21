# Ingress Setup - Complete Guide ✅

## 🎉 Ingress is Configured and Working!

Your Restaurant Management System now has **NGINX Ingress** configured. Here's how to use it.

---

## 🌐 Available URLs

All services are accessible via these domain names:

| Service | Domain | Port (via port-forward) |
|---------|--------|------------------------|
| **Frontend UI** | `http://restaurant.local` | :8080 |
| **API Gateway** | `http://api.restaurant.local` | :8080 |
| **Order Service** | `http://orders.restaurant.local` | :8080 |
| **Restaurant Service** | `http://restaurants.restaurant.local` | :8080 |
| **Auth Service** | `http://auth.restaurant.local` | :8080 |

---

## 🔧 Setup (One-Time)

### Step 1: Add Hosts Entries

Add these lines to `/etc/hosts`:

```bash
sudo nano /etc/hosts
```

Add at the end:
```
127.0.0.1 restaurant.local
127.0.0.1 api.restaurant.local
127.0.0.1 orders.restaurant.local
127.0.0.1 restaurants.restaurant.local
127.0.0.1 auth.restaurant.local
```

**Or use this command:**
```bash
echo "127.0.0.1 restaurant.local api.restaurant.local orders.restaurant.local restaurants.restaurant.local auth.restaurant.local" | sudo tee -a /etc/hosts
```

### Step 2: Port Forward to Ingress (Required for KIND)

Since we're using KIND (local cluster), we need one port-forward to the Ingress controller:

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
```

**That's it!** Just ONE port-forward instead of many!

---

## 🚀 How to Access Services

### Before Ingress (Multiple Port Forwards):
```bash
kubectl port-forward svc/frontend -n restaurant-system 3000:80 &
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &
kubectl port-forward svc/auth-service -n restaurant-system 8001:8001 &

# Access: http://localhost:3000, http://localhost:8001, etc.
```

### After Ingress (ONE Port Forward):
```bash
# Just ONE command!
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80

# Access everything via domains:
http://restaurant.local:8080
http://api.restaurant.local:8080
http://orders.restaurant.local:8080
```

**Benefits:**
- ✅ Only 1 port-forward needed (instead of 5+)
- ✅ Clean domain names
- ✅ Production-like setup
- ✅ Easier to manage

---

## 🧪 Testing

After setup (hosts added + port-forward running):

### Test 1: Frontend
```bash
curl http://restaurant.local:8080
# Should return HTML

# Or open in browser:
open http://restaurant.local:8080
```

### Test 2: API Gateway
```bash
curl http://api.restaurant.local:8080/health
# Output: {"status":"healthy","service":"api-gateway"}
```

### Test 3: Order Service
```bash
curl http://orders.restaurant.local:8080/health
# Output: {"status":"healthy","service":"order-service"}
```

### Test 4: Login API
```bash
curl -X POST http://api.restaurant.local:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
# Should return access_token
```

### Test 5: API Documentation
```bash
# Open in browser:
open http://orders.restaurant.local:8080/docs
open http://restaurants.restaurant.local:8080/docs
open http://auth.restaurant.local:8080/docs
```

---

## 📱 Browser Access

### Main Application
```
http://restaurant.local:8080
```

Login with:
- Username: `admin`
- Password: `password`

### API Documentation
```
http://orders.restaurant.local:8080/docs
http://restaurants.restaurant.local:8080/docs
http://api.restaurant.local:8080/docs
```

---

## 🔄 Daily Workflow

### Start Working:
```bash
# 1. Start the Ingress port-forward
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80

# 2. Access your app
open http://restaurant.local:8080
```

### Stop Working:
```bash
# Just kill the port-forward (Ctrl+C)
# Or:
pkill -f "port-forward.*ingress-nginx"
```

---

## 📊 Architecture

```
        Browser (http://restaurant.local:8080)
                        ↓
        Port Forward (localhost:8080 → Ingress)
                        ↓
        ┌───────────────────────────────┐
        │  NGINX Ingress Controller     │
        │  (restaurant-cluster-worker)  │
        └──────────────┬────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
    ┌────────┐   ┌─────────┐   ┌─────────┐
    │Frontend│   │   API   │   │  Order  │
    │  :80   │   │ Gateway │   │ Service │
    │        │   │  :8000  │   │  :8004  │
    └────────┘   └─────────┘   └─────────┘
```

---

## 🔧 Update Postman

Update your Postman environment variables:

| Variable | New Value |
|----------|-----------|
| `base_url` | `http://api.restaurant.local:8080` |
| `auth_url` | `http://api.restaurant.local:8080` |
| `restaurant_url` | `http://restaurants.restaurant.local:8080` |
| `order_url` | `http://orders.restaurant.local:8080` |

---

## 🛠️ Kubernetes Commands

### Check Ingress Status
```bash
kubectl get ingress -n restaurant-system
kubectl get pods -n ingress-nginx
```

### View Ingress Controller Logs
```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller -f
```

### Restart Ingress Controller
```bash
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
```

### Check All Pods
```bash
kubectl get pods -n restaurant-system -o wide
```

---

## ⚠️ Troubleshooting

### Issue 1: "curl: (7) Failed to connect"

**Problem:** Can't access services

**Solution:**
```bash
# 1. Check port-forward is running
ps aux | grep "port-forward.*ingress"

# 2. Restart port-forward
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80

# 3. Test with curl
curl -H "Host: api.restaurant.local" http://localhost:8080/health
```

### Issue 2: "Could not resolve host"

**Problem:** Domain names not resolving

**Solution:**
```bash
# Check /etc/hosts entries
cat /etc/hosts | grep restaurant.local

# Should show:
# 127.0.0.1 restaurant.local api.restaurant.local ...

# If missing, add them:
echo "127.0.0.1 restaurant.local api.restaurant.local orders.restaurant.local restaurants.restaurant.local auth.restaurant.local" | sudo tee -a /etc/hosts
```

### Issue 3: Ingress Controller Not Running

**Problem:** Ingress pod is not ready

**Solution:**
```bash
# Check pod status
kubectl get pods -n ingress-nginx

# View logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Restart if needed
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx
```

### Issue 4: Services Still Crashing

**Problem:** Backend services crashing

**Solution:**
```bash
# Check which node they're on (should be restaurant-cluster-worker)
kubectl get pods -n restaurant-system -o wide

# If on worker2, they'll fail due to DNS issues
# Pods should be on: restaurant-cluster-worker

# Check logs
kubectl logs -n restaurant-system deployment/order-service
```

---

## 📝 Quick Reference

### Single Command Start
```bash
# Start Ingress port-forward in background
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 &

# Access your app
open http://restaurant.local:8080
```

### Test All Services
```bash
# Test frontend
curl -I http://restaurant.local:8080

# Test API Gateway
curl http://api.restaurant.local:8080/health

# Test Order Service  
curl http://orders.restaurant.local:8080/health

# Test Restaurant Service
curl http://restaurants.restaurant.local:8080/health

# Test Auth Service
curl http://auth.restaurant.local:8080/health
```

### Stop All
```bash
# Kill port-forward
pkill -f "port-forward.*ingress"
```

---

## 🎯 Complete Example Workflow

### Morning Setup:
```bash
# 1. Start port-forward
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 &

# 2. Open frontend
open http://restaurant.local:8080

# 3. Open API docs
open http://orders.restaurant.local:8080/docs

# 4. Test API
curl -X POST http://api.restaurant.local:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Evening Cleanup:
```bash
# Stop port-forward
pkill -f "port-forward.*ingress"
```

---

## 💡 Pro Tips

1. **Add to your shell profile** (`.bashrc` or `.zshrc`):
   ```bash
   alias ingress-start='kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80'
   alias ingress-stop='pkill -f "port-forward.*ingress"'
   ```

2. **Bookmark in browser:**
   - http://restaurant.local:8080
   - http://orders.restaurant.local:8080/docs
   - http://api.restaurant.local:8080/health

3. **Use tmux/screen** to keep port-forward running:
   ```bash
   tmux new -s ingress
   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
   # Detach: Ctrl+B then D
   ```

---

## 🎉 Summary

**✅ Ingress Configured and Working!**

**What you have:**
- ✅ NGINX Ingress Controller running
- ✅ 5 domain names configured
- ✅ All services accessible via one port-forward
- ✅ Production-like setup
- ✅ Clean URLs

**To use:**
1. Add hosts entries to `/etc/hosts` (one-time)
2. Run: `kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80`
3. Access: `http://restaurant.local:8080`

**That's it!** Much simpler than multiple port-forwards! 🚀

---

## 📚 Related Documentation

- **STARTUP.md** - All service URLs and credentials
- **POSTMAN.md** - Complete API testing guide
- **POSTMAN-QUICK-START.md** - 5-minute Postman setup

---

**Happy Developing!** 🎉
