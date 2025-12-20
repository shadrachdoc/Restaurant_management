# Restaurant Management System - Postman Testing Guide

## 📋 Table of Contents

1. [Setup Instructions](#setup-instructions)
2. [Import Postman Collection](#import-postman-collection)
3. [Environment Variables](#environment-variables)
4. [Testing Workflow](#testing-workflow)
5. [API Endpoints by Service](#api-endpoints-by-service)
6. [Common Issues](#common-issues)

---

## 🚀 Setup Instructions

### **Step 1: Install Postman**

Download and install Postman from:
```
https://www.postman.com/downloads/
```

### **Step 2: Start Port Forwarding**

Before testing, ensure all services are accessible:

```bash
# Start port forwards in separate terminals or background
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/auth-service -n restaurant-system 8001:8001 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &
```

### **Step 3: Verify Services**

Test that services are running:

```bash
# API Gateway
curl http://localhost:8001/health

# Auth Service
curl http://localhost:8001/health

# Restaurant Service
curl http://localhost:8003/health

# Order Service
curl http://localhost:8004/health
```

---

## 📥 Import Postman Collection

### **Method 1: Import from File**

1. Open Postman
2. Click **"Import"** button (top left)
3. Click **"Upload Files"**
4. Select `Restaurant-Management-API.postman_collection.json`
5. Click **"Import"**

### **Method 2: Import from URL**

1. Open Postman
2. Click **"Import"** button
3. Select **"Link"** tab
4. Paste the raw GitHub URL (if hosted)
5. Click **"Continue"** → **"Import"**

### **Method 3: Drag and Drop**

1. Open Postman
2. Drag `Restaurant-Management-API.postman_collection.json` into Postman window
3. Collection will be imported automatically

---

## 🔧 Environment Variables

### **Create Postman Environment**

1. Click the **"Environments"** icon (left sidebar)
2. Click **"+"** to create new environment
3. Name it: `Restaurant System - Local`
4. Add these variables:

| Variable Name | Initial Value | Current Value |
|--------------|---------------|---------------|
| `base_url` | `http://localhost:8001` | `http://localhost:8001` |
| `auth_url` | `http://localhost:8001` | `http://localhost:8001` |
| `restaurant_url` | `http://localhost:8003` | `http://localhost:8003` |
| `order_url` | `http://localhost:8004` | `http://localhost:8004` |
| `access_token` | _(leave empty)_ | _(auto-filled after login)_ |
| `restaurant_id` | _(leave empty)_ | _(auto-filled)_ |
| `table_id` | _(leave empty)_ | _(auto-filled)_ |
| `order_id` | _(leave empty)_ | _(auto-filled)_ |
| `session_token` | _(leave empty)_ | _(auto-filled)_ |
| `menu_item_id` | _(leave empty)_ | _(auto-filled)_ |

5. Click **"Save"**
6. Select this environment from the dropdown (top right)

---

## 📝 Testing Workflow

### **Complete Test Flow (Step by Step)**

#### **Phase 1: Authentication**

1. **Login as Admin**
   - Folder: `Authentication`
   - Request: `Login - Admin`
   - Expected: 200 OK, access_token saved automatically
   - ✅ Token will be stored in environment variable

2. **Get Current User**
   - Folder: `Authentication`
   - Request: `Get Current User`
   - Expected: 200 OK, user details returned

#### **Phase 2: Restaurant Management**

3. **List Restaurants**
   - Folder: `Restaurant Service`
   - Request: `List All Restaurants`
   - Expected: 200 OK, array of restaurants
   - ✅ First restaurant_id saved automatically

4. **Create Restaurant**
   - Folder: `Restaurant Service`
   - Request: `Create Restaurant`
   - Expected: 201 Created
   - Edit JSON body with your restaurant details

5. **Get Restaurant by ID**
   - Folder: `Restaurant Service`
   - Request: `Get Restaurant by ID`
   - Expected: 200 OK
   - Uses `{{restaurant_id}}` from environment

6. **Update Restaurant**
   - Folder: `Restaurant Service`
   - Request: `Update Restaurant`
   - Expected: 200 OK

#### **Phase 3: Table Management**

7. **List Tables**
   - Folder: `Restaurant Service > Tables`
   - Request: `List Tables for Restaurant`
   - Expected: 200 OK
   - ✅ First table_id saved automatically

8. **Create Table**
   - Folder: `Restaurant Service > Tables`
   - Request: `Create Table`
   - Expected: 201 Created

#### **Phase 4: Menu Management**

9. **List Menu Items**
   - Folder: `Restaurant Service > Menu`
   - Request: `List Menu Items`
   - Expected: 200 OK
   - ✅ First menu_item_id saved automatically

10. **Create Menu Item**
    - Folder: `Restaurant Service > Menu`
    - Request: `Create Menu Item`
    - Expected: 201 Created

#### **Phase 5: Online Orders (NEW)**

11. **Create Table Session**
    - Folder: `Order Service > Sessions`
    - Request: `Create Table Session`
    - Expected: 201 Created
    - ✅ session_token saved automatically
    - **NO AUTH REQUIRED** (Public endpoint)

12. **Join Session**
    - Folder: `Order Service > Sessions`
    - Request: `Join Table Session`
    - Expected: 200 OK

13. **Add Items to Session**
    - Folder: `Order Service > Sessions`
    - Request: `Add Item to Session`
    - Expected: 200 OK

14. **Get Session Details**
    - Folder: `Order Service > Sessions`
    - Request: `Get Session`
    - Expected: 200 OK

15. **Create Order**
    - Folder: `Order Service > Orders`
    - Request: `Create Order`
    - Expected: 201 Created
    - ✅ order_id saved automatically
    - **NO AUTH REQUIRED** (Public endpoint)

16. **List Orders**
    - Folder: `Order Service > Orders`
    - Request: `List Orders for Restaurant`
    - Expected: 200 OK
    - **AUTH REQUIRED**

17. **Get Order by ID**
    - Folder: `Order Service > Orders`
    - Request: `Get Order by ID`
    - Expected: 200 OK

18. **Update Order Status**
    - Folder: `Order Service > Orders`
    - Request: `Update Order Status`
    - Expected: 200 OK
    - Test status flow: PENDING → CONFIRMED → PREPARING → READY → SERVED → COMPLETED

19. **Cancel Order**
    - Folder: `Order Service > Orders`
    - Request: `Cancel Order`
    - Expected: 200 OK

#### **Phase 6: Assistance Requests**

20. **Create Assistance Request**
    - Folder: `Order Service > Assistance`
    - Request: `Request Assistance`
    - Expected: 201 Created
    - **NO AUTH REQUIRED** (Public endpoint)

21. **List Assistance Requests**
    - Folder: `Order Service > Assistance`
    - Request: `List Assistance Requests`
    - Expected: 200 OK
    - **AUTH REQUIRED**

22. **Resolve Assistance Request**
    - Folder: `Order Service > Assistance`
    - Request: `Resolve Assistance Request`
    - Expected: 200 OK

---

## 🗂️ API Endpoints by Service

### **1. Authentication Service**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/signup` | Register new user | ❌ No |
| POST | `/api/v1/auth/login` | Login user | ❌ No |
| POST | `/api/v1/auth/logout` | Logout user | ✅ Yes |
| GET | `/api/v1/users/me` | Get current user | ✅ Yes |
| PATCH | `/api/v1/users/me` | Update current user | ✅ Yes |
| PATCH | `/api/v1/users/me/restaurant` | Link user to restaurant | ✅ Yes |

### **2. Restaurant Service**

#### Restaurants
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/restaurants` | List all restaurants | ✅ Yes |
| POST | `/api/v1/restaurants` | Create restaurant | ✅ Yes |
| GET | `/api/v1/restaurants/{id}` | Get restaurant | ✅ Yes |
| PUT | `/api/v1/restaurants/{id}` | Update restaurant | ✅ Yes |
| DELETE | `/api/v1/restaurants/{id}` | Delete restaurant | ✅ Yes |

#### Tables
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/restaurants/{id}/tables` | List tables | ✅ Yes |
| POST | `/api/v1/restaurants/{id}/tables` | Create table | ✅ Yes |
| GET | `/api/v1/tables/{id}` | Get table | ✅ Yes |
| PUT | `/api/v1/tables/{id}` | Update table | ✅ Yes |
| DELETE | `/api/v1/tables/{id}` | Delete table | ✅ Yes |

#### Menu Items
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/restaurants/{id}/menu` | List menu items | ✅ Yes |
| POST | `/api/v1/restaurants/{id}/menu` | Create menu item | ✅ Yes |
| GET | `/api/v1/menu/{id}` | Get menu item | ✅ Yes |
| PUT | `/api/v1/menu/{id}` | Update menu item | ✅ Yes |
| DELETE | `/api/v1/menu/{id}` | Delete menu item | ✅ Yes |

### **3. Order Service (NEW)**

#### Orders
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/orders` | Create order | ❌ No (Public) |
| GET | `/api/v1/restaurants/{id}/orders` | List orders | ✅ Yes |
| GET | `/api/v1/orders/{id}` | Get order | ❌ No (Public) |
| PATCH | `/api/v1/orders/{id}/status` | Update status | ✅ Yes |
| DELETE | `/api/v1/orders/{id}` | Cancel order | ❌ No (Public) |

#### Table Sessions (Collaborative Ordering)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/sessions` | Create session | ❌ No (Public) |
| POST | `/api/v1/sessions/{token}/join` | Join session | ❌ No (Public) |
| POST | `/api/v1/sessions/{token}/items` | Add item | ❌ No (Public) |
| GET | `/api/v1/sessions/{token}` | Get session | ❌ No (Public) |
| POST | `/api/v1/sessions/{token}/submit` | Submit order | ❌ No (Public) |
| DELETE | `/api/v1/sessions/{token}` | Close session | ❌ No (Public) |

#### Assistance Requests
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/assistance` | Request help | ❌ No (Public) |
| GET | `/api/v1/restaurants/{id}/assistance` | List requests | ✅ Yes |
| GET | `/api/v1/assistance/{id}` | Get request | ✅ Yes |
| PATCH | `/api/v1/assistance/{id}/resolve` | Resolve request | ✅ Yes |
| DELETE | `/api/v1/assistance/{id}` | Delete request | ✅ Yes |

---

## 🔐 Authorization Setup

### **Automatic Token Management**

The Postman collection includes **pre-request scripts** that automatically:
- Extract `access_token` from login response
- Store token in environment variable
- Add `Authorization: Bearer {token}` header to protected requests

### **Manual Token Setup** (if auto-setup fails)

1. Run the **"Login - Admin"** request
2. Copy the `access_token` from response
3. Go to **Environment variables**
4. Paste token into `access_token` variable
5. Save environment

### **Headers for Protected Endpoints**

Protected endpoints automatically include:
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

---

## 📊 Response Auto-Capture

The collection includes **test scripts** that automatically capture:

- `access_token` from login response
- `restaurant_id` from restaurant creation/listing
- `table_id` from table creation/listing
- `menu_item_id` from menu item creation/listing
- `order_id` from order creation
- `session_token` from session creation
- `assistance_id` from assistance request creation

These values are used in subsequent requests automatically!

---

## 🧪 Test Examples

### **Example 1: Complete Order Flow**

**Run requests in this order:**

1. **Login - Admin**
   ```json
   POST /api/v1/auth/login
   Body: {"username": "admin", "password": "password"}
   ```

2. **List Restaurants**
   ```json
   GET /api/v1/restaurants
   → Captures first restaurant_id
   ```

3. **List Tables**
   ```json
   GET /api/v1/restaurants/{{restaurant_id}}/tables
   → Captures first table_id
   ```

4. **Create Table Session** (No Auth)
   ```json
   POST /api/v1/sessions
   Body: {
     "restaurant_id": "{{restaurant_id}}",
     "table_id": "{{table_id}}",
     "participant_name": "John Doe"
   }
   → Captures session_token
   ```

5. **Add Items to Session** (No Auth)
   ```json
   POST /api/v1/sessions/{{session_token}}/items
   Body: {
     "menu_item_id": "{{menu_item_id}}",
     "quantity": 2,
     "special_requests": "No onions",
     "contributor_name": "John Doe"
   }
   ```

6. **Submit Session Order** (No Auth)
   ```json
   POST /api/v1/sessions/{{session_token}}/submit
   ```

7. **View Orders** (Auth Required)
   ```json
   GET /api/v1/restaurants/{{restaurant_id}}/orders
   ```

8. **Update Order Status** (Auth Required)
   ```json
   PATCH /api/v1/orders/{{order_id}}/status
   Body: {"status": "CONFIRMED"}
   ```

### **Example 2: Customer Assistance Flow**

1. **Request Waiter** (No Auth)
   ```json
   POST /api/v1/assistance
   Body: {
     "restaurant_id": "{{restaurant_id}}",
     "table_id": "{{table_id}}",
     "request_type": "waiter",
     "message": "Need water please"
   }
   ```

2. **Staff Views Requests** (Auth Required)
   ```json
   GET /api/v1/restaurants/{{restaurant_id}}/assistance?resolved=false
   ```

3. **Resolve Request** (Auth Required)
   ```json
   PATCH /api/v1/assistance/{{assistance_id}}/resolve
   Body: {"resolved_by": "{{user_id}}"}
   ```

---

## 🎯 Testing Checklist

### **Authentication ✓**
- [ ] Login with admin credentials
- [ ] Login with chef credentials
- [ ] Login with restaurant admin credentials
- [ ] Get current user details
- [ ] Logout

### **Restaurant Management ✓**
- [ ] List all restaurants
- [ ] Create new restaurant
- [ ] Get restaurant by ID
- [ ] Update restaurant details
- [ ] Delete restaurant

### **Table Management ✓**
- [ ] List tables for restaurant
- [ ] Create new table
- [ ] Get table by ID
- [ ] Update table details
- [ ] Delete table

### **Menu Management ✓**
- [ ] List menu items
- [ ] Create menu item
- [ ] Get menu item by ID
- [ ] Update menu item
- [ ] Delete menu item

### **Order Management ✓**
- [ ] Create order (public)
- [ ] List orders (staff)
- [ ] Get order details
- [ ] Update order status through flow
- [ ] Cancel order

### **Table Sessions ✓**
- [ ] Create session
- [ ] Join session
- [ ] Add items to session
- [ ] Get session details
- [ ] Submit session order
- [ ] Close session

### **Assistance ✓**
- [ ] Request assistance (public)
- [ ] List assistance requests (staff)
- [ ] Resolve assistance request
- [ ] Delete assistance request

---

## ⚠️ Common Issues

### **Issue 1: "Unauthorized" Error**

**Problem:** Getting 401 Unauthorized on protected endpoints

**Solution:**
1. Ensure you've logged in first
2. Check `access_token` is set in environment
3. Verify Authorization header is included
4. Token may have expired - login again

### **Issue 2: "Connection Refused"**

**Problem:** Cannot connect to service

**Solution:**
1. Verify port forwarding is running:
   ```bash
   ps aux | grep port-forward
   ```
2. Restart port forwarding if needed
3. Check pod status:
   ```bash
   kubectl get pods -n restaurant-system
   ```

### **Issue 3: "Not Found" - 404 Error**

**Problem:** Endpoint returns 404

**Solution:**
1. Check the URL is correct
2. Verify service is running
3. Check API Gateway routing
4. View service logs:
   ```bash
   kubectl logs -n restaurant-system deployment/api-gateway
   ```

### **Issue 4: Variables Not Auto-Filling**

**Problem:** {{variable}} not being replaced

**Solution:**
1. Ensure environment is selected (top right dropdown)
2. Check variable name spelling
3. Run the request that sets the variable first
4. Manually set variable in environment if needed

### **Issue 5: "Invalid JSON" Error**

**Problem:** Request body validation fails

**Solution:**
1. Check JSON format is valid
2. Ensure all required fields are included
3. Verify data types match (UUID, string, number, etc.)
4. Check for trailing commas

---

## 📚 Additional Resources

### **View API Documentation**

- **Auth Service:** http://localhost:8001/docs
- **Restaurant Service:** http://localhost:8003/docs
- **Order Service:** http://localhost:8004/docs

### **Database Access**

```bash
kubectl exec -it postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db
```

### **View Logs**

```bash
# Order Service
kubectl logs -f -n restaurant-system deployment/order-service

# API Gateway
kubectl logs -f -n restaurant-system deployment/api-gateway
```

---

## 🎓 Postman Tips

### **1. Use Collections Runner**

Test entire collection at once:
1. Click on collection name
2. Click **"Run"** button
3. Select requests to run
4. Click **"Run Restaurant Management API"**
5. View results

### **2. Save Responses as Examples**

1. Run a request
2. Click **"Save Response"**
3. Click **"Save as Example"**
4. Examples help document expected responses

### **3. Use Pre-request Scripts**

Add before each request:
```javascript
// Log request details
console.log("Making request to:", pm.request.url);

// Set timestamp
pm.environment.set("timestamp", new Date().toISOString());
```

### **4. Use Tests for Validation**

Add to test tab:
```javascript
// Check status code
pm.test("Status is 200", function() {
    pm.response.to.have.status(200);
});

// Validate response structure
pm.test("Response has data", function() {
    pm.expect(pm.response.json()).to.have.property("data");
});
```

---

## 🚀 Quick Start Commands

```bash
# 1. Start all port forwards
kubectl port-forward svc/api-gateway -n restaurant-system 8001:8000 &
kubectl port-forward svc/restaurant-service -n restaurant-system 8003:8003 &
kubectl port-forward svc/order-service -n restaurant-system 8004:8004 &

# 2. Import collection into Postman
# File: Restaurant-Management-API.postman_collection.json

# 3. Create environment with these variables:
# - base_url: http://localhost:8001
# - restaurant_url: http://localhost:8003
# - order_url: http://localhost:8004

# 4. Run "Login - Admin" request first

# 5. Start testing other endpoints!
```

---

**Happy Testing! 🎉**

For issues or questions, check the troubleshooting section or view service logs.
