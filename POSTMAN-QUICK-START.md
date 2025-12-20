# Postman Quick Start Guide - 5 Minutes Setup

## 📥 Step 1: Import Collection (1 minute)

1. Open **Postman**
2. Click **"Import"** button (top left)
3. Drag and drop these 2 files into Postman:
   - `Restaurant-Management-API.postman_collection.json`
   - `Restaurant-System-Local.postman_environment.json`
4. Click **"Import"**

✅ **Done!** You should see:
- Collection: "Restaurant Management System API" in left sidebar
- Environment: "Restaurant System - Local" in top-right dropdown

---

## ⚙️ Step 2: Select Environment (10 seconds)

1. Click the environment dropdown (top right)
2. Select **"Restaurant System - Local"**
3. Environment is now active (you'll see a checkmark ✓)

---

## 🚀 Step 3: Start Port Forwarding (30 seconds)

Open terminal and run:

```bash
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
```

---

## 🧪 Step 4: Run Your First Request (30 seconds)

### Test 1: Check Services are Running

1. In Postman, expand **"Health Checks"** folder
2. Click **"Order Service Health"**
3. Click **"Send"**
4. ✅ You should get: `{"status":"healthy","service":"order-service"}`

### Test 2: Login

1. Expand **"1. Authentication"** folder
2. Click **"Login - Admin"**
3. Click **"Send"**
4. ✅ You should get: HTTP 200 with `access_token`
5. 🎯 Token is **automatically saved** to environment!

---

## 🎯 Step 5: Run Complete Test Flow (3 minutes)

**Follow these requests in order:**

| # | Folder | Request | What It Does |
|---|--------|---------|-------------|
| 1 | Authentication | **Login - Admin** | Get access token |
| 2 | Restaurant Service > Restaurants | **List All Restaurants** | Get restaurants (saves first ID) |
| 3 | Restaurant Service > Tables | **List Tables for Restaurant** | Get tables (saves first ID) |
| 4 | Restaurant Service > Menu Items | **List Menu Items** | Get menu (saves first ID) |
| 5 | Order Service > Sessions | **Create Table Session** | Start collaborative session |
| 6 | Order Service > Sessions | **Add Item to Session** | Add items to order |
| 7 | Order Service > Sessions | **Submit Session Order** | Submit the order |
| 8 | Order Service > Orders | **List Orders for Restaurant** | View all orders |
| 9 | Order Service > Orders | **Update Order Status - CONFIRMED** | Change order status |
| 10 | Order Service > Assistance | **Request Assistance - Waiter** | Customer requests help |

**Just click each request and press "Send"!**

All variables (restaurant_id, table_id, etc.) are captured automatically! ✨

---

## 🎨 Understanding the Collection Structure

```
Restaurant Management System API/
├── 1. Authentication/              ← Login, signup, logout
│   ├── Login - Admin              ✅ START HERE
│   ├── Login - Chef
│   └── Get Current User
│
├── 2. Restaurant Service/
│   ├── Restaurants/               ← Manage restaurants
│   ├── Tables/                    ← Manage tables
│   └── Menu Items/                ← Manage menu
│
├── 3. Order Service (Online Orders)/  ← NEW!
│   ├── Orders/                    ← Create & manage orders
│   ├── Table Sessions/            ← Collaborative ordering
│   └── Assistance Requests/       ← Customer help requests
│
└── Health Checks/                 ← Test service availability
```

---

## 🔑 Auto-Captured Variables

The collection **automatically captures** these variables:

| Variable | Captured From | Used In |
|----------|---------------|---------|
| `access_token` | Login response | All authenticated requests |
| `user_id` | Login response | Assistance resolution |
| `restaurant_id` | Restaurant list/create | All restaurant operations |
| `table_id` | Table list/create | Orders, sessions |
| `menu_item_id` | Menu list/create | Order items |
| `order_id` | Order creation | Order updates |
| `session_token` | Session creation | Session operations |
| `assistance_id` | Assistance request | Resolve assistance |

**You don't need to copy/paste IDs manually!** 🎉

---

## 🎯 Common Test Scenarios

### Scenario 1: Customer Places Order

```
1. Create Table Session (Public - no auth)
2. Add Item to Session (Public - no auth)
3. Submit Session Order (Public - no auth)
```

### Scenario 2: Kitchen Processes Order

```
1. Login - Chef
2. List Orders for Restaurant
3. Update Order Status - CONFIRMED
4. Update Order Status - PREPARING
5. Update Order Status - READY
6. Update Order Status - SERVED
7. Update Order Status - COMPLETED
```

### Scenario 3: Customer Needs Help

```
1. Request Assistance - Waiter (Public - no auth)
2. Login - Admin/Chef
3. List Assistance Requests
4. Resolve Assistance Request
```

---

## 🔍 View Environment Variables

1. Click the **eye icon** 👁️ next to environment dropdown
2. See all variables and their current values
3. You can manually edit values if needed

---

## 📊 Collection Features

### ✅ Automatic Token Management
- Login response automatically saves `access_token`
- Protected endpoints automatically use the token
- No manual header setup needed!

### ✅ Auto-Variable Capture
- IDs automatically saved from responses
- Variables used in subsequent requests
- No copy/paste needed!

### ✅ Test Scripts Included
- Status code validation
- Response structure checks
- Console logging for debugging

### ✅ Pre-Request Scripts
- Automatic logging
- Variable validation
- Request debugging

---

## 🎓 Pro Tips

### Tip 1: Run Multiple Requests at Once

1. Click on the **collection name**
2. Click **"Run"** button
3. Select requests to run
4. Click **"Run Restaurant Management API"**
5. Watch all requests execute in sequence!

### Tip 2: Save Example Responses

1. Run a request
2. Click **"Save Response"**
3. Click **"Save as Example"**
4. Examples show expected responses!

### Tip 3: Use Console for Debugging

1. Open Postman Console (bottom left icon)
2. See all requests/responses
3. View auto-captured variable values
4. Debug any issues

### Tip 4: Duplicate Requests

1. Right-click any request
2. Click **"Duplicate"**
3. Modify for custom tests
4. Keep original intact!

---

## ⚠️ Troubleshooting

### ❌ "Could not get response" Error

**Fix:** Start port forwarding
```bash
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
```

### ❌ "Unauthorized" Error

**Fix:** Login first
1. Run **"Login - Admin"** request
2. Token will be saved automatically
3. Try your request again

### ❌ Variables showing as {{variable_name}}

**Fix:** Select environment
1. Top-right dropdown
2. Select **"Restaurant System - Local"**
3. Variables will now resolve

### ❌ "Not Found" - Need Restaurant/Table IDs

**Fix:** Run setup requests first
1. **List All Restaurants** (captures restaurant_id)
2. **List Tables for Restaurant** (captures table_id)
3. **List Menu Items** (captures menu_item_id)
4. Now other requests will work!

---

## 📚 Full Documentation

For detailed API documentation, see:
- **POSTMAN.md** - Complete testing guide
- **STARTUP.md** - Service URLs and credentials
- Swagger UI: http://localhost:8004/docs

---

## 🚀 You're Ready!

1. ✅ Collection imported
2. ✅ Environment selected
3. ✅ Port forwarding running
4. ✅ First request tested

**Now start testing!** Click **"Login - Admin"** and work your way through the folders! 🎉

---

**Need Help?**
- Check **POSTMAN.md** for detailed guide
- View service logs: `kubectl logs -f -n restaurant-system deployment/order-service`
- Check pod status: `kubectl get pods -n restaurant-system`
