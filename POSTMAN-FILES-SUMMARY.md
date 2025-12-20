# 📦 Postman Files - Complete Package

## Files Created

✅ **3 Files Ready to Use:**

1. **Restaurant-Management-API.postman_collection.json**
   - Complete API collection with 50+ requests
   - Organized into folders by service
   - Auto-captures tokens and IDs
   - Includes test scripts

2. **Restaurant-System-Local.postman_environment.json**
   - Pre-configured environment variables
   - All service URLs set
   - Auto-filling variables for IDs

3. **POSTMAN.md**
   - Detailed testing guide (10+ pages)
   - Step-by-step workflows
   - Troubleshooting section
   - Testing checklist

4. **POSTMAN-QUICK-START.md**
   - 5-minute setup guide
   - Quick reference
   - Pro tips

---

## 📂 Collection Contents

### Total Requests: **52**

#### 1. Authentication (6 requests)
- Login - Admin
- Login - Chef  
- Login - Restaurant Admin
- Get Current User
- Signup - New User
- Logout

#### 2. Restaurant Service (11 requests)

**Restaurants (5)**
- List All Restaurants
- Create Restaurant
- Get Restaurant by ID
- Update Restaurant
- Delete Restaurant

**Tables (2)**
- List Tables for Restaurant
- Create Table

**Menu Items (2)**
- List Menu Items
- Create Menu Item

#### 3. Order Service - NEW! (31 requests)

**Orders (10)**
- Create Order (Public)
- List Orders for Restaurant
- Get Order by ID
- Update Order Status x6 (PENDING → COMPLETED)
- Cancel Order

**Table Sessions (6)**
- Create Table Session
- Join Table Session
- Add Item to Session
- Get Session Details
- Submit Session Order
- Close Session

**Assistance Requests (7)**
- Request Assistance - Waiter
- Request Assistance - Bill
- Request Assistance - Complaint
- List Assistance Requests
- Get Assistance Request
- Resolve Assistance Request

#### 4. Health Checks (4 requests)
- API Gateway Health
- Auth Service Health
- Restaurant Service Health
- Order Service Health

---

## 🎯 Auto-Captured Variables

The collection automatically captures **14 variables**:

| Variable | Type | Purpose |
|----------|------|---------|
| `base_url` | Static | API Gateway URL |
| `auth_url` | Static | Auth Service URL |
| `restaurant_url` | Static | Restaurant Service URL |
| `order_url` | Static | Order Service URL |
| `access_token` | Auto | JWT token from login |
| `user_id` | Auto | Current user ID |
| `restaurant_id` | Auto | Selected restaurant |
| `table_id` | Auto | Selected table |
| `menu_item_id` | Auto | Selected menu item |
| `order_id` | Auto | Created order |
| `order_number` | Auto | Order number |
| `session_token` | Auto | Table session token |
| `session_id` | Auto | Session ID |
| `assistance_id` | Auto | Assistance request ID |

---

## 🔐 Authentication

### Public Endpoints (No Auth Required)
✅ Create Order
✅ Get Order by ID
✅ Create Table Session
✅ Join Session
✅ Add Item to Session
✅ Get Session
✅ Submit Order
✅ Close Session
✅ Request Assistance
✅ Cancel Order
✅ All Health Checks

### Protected Endpoints (Auth Required)
🔒 All Restaurant Management
🔒 All Menu Management
🔒 List Orders (Staff)
🔒 Update Order Status (Staff)
🔒 List Assistance Requests (Staff)
🔒 Resolve Assistance (Staff)

---

## 📊 Order Status Flow

Test the complete order lifecycle:

```
PENDING
   ↓ (Update Status - CONFIRMED)
CONFIRMED
   ↓ (Update Status - PREPARING)
PREPARING
   ↓ (Update Status - READY)
READY
   ↓ (Update Status - SERVED)
SERVED
   ↓ (Update Status - COMPLETED)
COMPLETED ✓
```

Each status has its own request in the collection!

---

## 🎨 Collection Organization

```
Restaurant Management System API/
│
├── 📁 1. Authentication
│   ├── Login - Admin ⭐ START HERE
│   ├── Login - Chef
│   ├── Login - Restaurant Admin
│   ├── Get Current User
│   ├── Signup - New User
│   └── Logout
│
├── 📁 2. Restaurant Service
│   ├── 📁 Restaurants
│   │   ├── List All Restaurants
│   │   ├── Create Restaurant
│   │   ├── Get Restaurant by ID
│   │   ├── Update Restaurant
│   │   └── Delete Restaurant
│   │
│   ├── 📁 Tables
│   │   ├── List Tables for Restaurant
│   │   └── Create Table
│   │
│   └── 📁 Menu Items
│       ├── List Menu Items
│       └── Create Menu Item
│
├── 📁 3. Order Service (Online Orders) ⭐ NEW!
│   ├── 📁 Orders
│   │   ├── Create Order (Public)
│   │   ├── List Orders for Restaurant
│   │   ├── Get Order by ID
│   │   ├── Update Order Status - CONFIRMED
│   │   ├── Update Order Status - PREPARING
│   │   ├── Update Order Status - READY
│   │   ├── Update Order Status - SERVED
│   │   ├── Update Order Status - COMPLETED
│   │   └── Cancel Order
│   │
│   ├── 📁 Table Sessions (Collaborative Ordering)
│   │   ├── Create Table Session
│   │   ├── Join Table Session
│   │   ├── Add Item to Session
│   │   ├── Get Session Details
│   │   ├── Submit Session Order
│   │   └── Close Session
│   │
│   └── 📁 Assistance Requests
│       ├── Request Assistance - Waiter
│       ├── Request Assistance - Bill
│       ├── Request Assistance - Complaint
│       ├── List Assistance Requests
│       ├── Get Assistance Request
│       └── Resolve Assistance Request
│
└── 📁 Health Checks
    ├── API Gateway Health
    ├── Auth Service Health
    ├── Restaurant Service Health
    └── Order Service Health
```

---

## 🚀 Quick Import Instructions

### Method 1: Drag & Drop (Easiest)
1. Open Postman
2. Drag both JSON files into Postman window
3. Done! ✅

### Method 2: Import Button
1. Click "Import" in Postman
2. Click "Upload Files"
3. Select both JSON files
4. Click "Import"
5. Done! ✅

---

## 🧪 Recommended Test Order

### Beginner Flow (5 minutes)
```
1. Login - Admin
2. List All Restaurants
3. Create Table Session
4. Request Assistance - Waiter
5. List Assistance Requests
```

### Complete Order Flow (10 minutes)
```
1. Login - Admin
2. List All Restaurants
3. List Tables for Restaurant
4. List Menu Items
5. Create Table Session
6. Add Item to Session
7. Submit Session Order
8. List Orders for Restaurant
9. Update Order Status (all steps)
10. Request Assistance - Bill
```

### Full System Test (15 minutes)
```
Run all 52 requests using Collection Runner!
```

---

## 📋 Testing Checklist

Use this to verify your testing:

### Authentication ✓
- [ ] Login as Admin
- [ ] Login as Chef
- [ ] Login as Restaurant Admin
- [ ] Get current user
- [ ] Create new user
- [ ] Logout

### Restaurant Management ✓
- [ ] List restaurants
- [ ] Create restaurant
- [ ] Update restaurant
- [ ] List tables
- [ ] Create table
- [ ] List menu items

### Order Management (NEW) ✓
- [ ] Create order (public)
- [ ] List orders (staff)
- [ ] Update status through full flow
- [ ] Cancel order

### Table Sessions (NEW) ✓
- [ ] Create session
- [ ] Join session
- [ ] Add items
- [ ] Submit order

### Assistance (NEW) ✓
- [ ] Request waiter
- [ ] Request bill
- [ ] Submit complaint
- [ ] Staff views requests
- [ ] Resolve request

### Health Checks ✓
- [ ] All services healthy

---

## 💡 Pro Features

### ✨ Automatic Token Management
- Login once
- Token saved automatically
- Used in all subsequent requests
- No manual copying!

### ✨ Smart Variable Capture
- IDs captured from responses
- Automatically used in next requests
- Seamless workflow

### ✨ Test Scripts Included
- Validates responses
- Checks status codes
- Logs to console
- Saves variables

### ✨ Pre-Request Scripts
- Request logging
- Variable debugging
- Timestamp tracking

---

## 🎓 Learning Resources

1. **POSTMAN-QUICK-START.md** - Start here! (5 min read)
2. **POSTMAN.md** - Complete guide (20 min read)
3. **STARTUP.md** - Service details and credentials
4. **Swagger UI** - Interactive API docs
   - http://localhost:8004/docs (Order Service)
   - http://localhost:8003/docs (Restaurant Service)
   - http://localhost:8001/docs (Auth Service)

---

## 🎉 You're All Set!

**What you have:**
- ✅ 52 pre-configured API requests
- ✅ Auto-capturing environment
- ✅ Complete documentation
- ✅ Testing workflows
- ✅ Troubleshooting guides

**Next steps:**
1. Import the 2 JSON files
2. Select environment
3. Start port forwarding
4. Click "Login - Admin"
5. Start testing! 🚀

---

**Happy Testing!** 🎉

For questions, check POSTMAN.md or STARTUP.md
