# 🎉 Backend Services Are Running!

## ✅ Status

All backend services are UP and running:

- ✅ **PostgreSQL**: localhost:5432
- ✅ **Redis**: localhost:6379
- ✅ **Auth Service**: http://localhost:8001
- ✅ **Restaurant Service**: http://localhost:8003
- ✅ **Frontend**: http://localhost:3001

---

## 🔗 Service URLs

### Auth Service
- **Health Check**: http://localhost:8001/health
- **API Docs**: http://localhost:8001/docs
- **Base URL**: http://localhost:8001

### Restaurant Service
- **Health Check**: http://localhost:8003/health
- **API Docs**: http://localhost:8003/docs
- **Base URL**: http://localhost:8003

### Frontend
- **Web App**: http://localhost:3001
- **Admin**: http://localhost:3001/admin
- **Tables**: http://localhost:3001/admin/tables

---

## 🧪 Test the System

### Step 1: Create an Account

Open your browser and go to: http://localhost:3001/signup

Fill in:
- **Full Name**: Test Admin
- **Email**: admin@test.com
- **Username**: testadmin
- **Password**: Password123!
- **Role**: Restaurant Admin

Click **"Create Account"**

### Step 2: Login

Go to: http://localhost:3001/login

Login with:
- **Username**: testadmin
- **Password**: Password123!

You'll be redirected to: http://localhost:3001/admin

### Step 3: Create Your Restaurant

1. Click **"Restaurant"** in the sidebar
2. Click **"Edit Details"**
3. Fill in:
   - Restaurant Name: "My Test Restaurant"
   - Description: "Delicious food"
   - Cuisine Type: "Italian"
   - Address: "123 Main St"
   - Phone: "555-1234"
4. Click **"Save Changes"**

### Step 4: Create Tables with QR Codes

1. Click **"Tables"** in the sidebar
2. Click **"Add Table"** button
3. Fill in:
   - Table Number: "T1"
   - Seat Count: 4
   - Floor: "Ground Floor"
   - Section: "Window"
4. Click **"Create Table"**

**✅ QR Code will AUTO-GENERATE!**

Repeat for Tables T2, T3, T4, T5...

### Step 5: View QR Code

1. Find the table card
2. See the small QR code preview
3. Click **"View QR"** button
4. Large QR code appears (256x256px)
5. **Right-click** → **Save Image** or take screenshot
6. Print and place at physical table

### Step 6: Add Menu Items

1. Click **"Menu"** in sidebar
2. Click **"Add Menu Item"**
3. Fill in:
   - Name: "Margherita Pizza"
   - Description: "Classic pizza"
   - Price: 12.99
   - Category: "Pizza"
   - Preparation Time: 15
   - Check "Vegetarian"
4. Click **"Add Item"**

Add more items...

### Step 7: Test QR Code Flow

#### Option A: Simulate QR Scan (Desktop)

1. Get your table ID from the Tables page
2. Open new tab with URL:
   ```
   http://localhost:3001/table/{TABLE_ID}?restaurant={RESTAURANT_ID}&token=test
   ```

#### Option B: Real QR Scan (Mobile)

1. Print the QR code
2. Open phone camera
3. Scan QR code
4. Browser opens automatically

### Step 8: Order as Customer

After scanning QR:

1. **Landing Page** appears showing:
   - Restaurant name
   - Table number
   - Welcome message

2. Click **"View Menu & Start Ordering"**

3. **Menu Page** shows:
   - Table banner at top: "🍽️ Table T1"
   - All menu items
   - Dietary filters

4. Add items to cart:
   - Click "Add to Cart"
   - See cart at bottom
   - Adjust quantities

5. Click **"Checkout"**

---

## 📊 API Endpoints Available

### Auth Service (Port 8001)

```
POST   /api/v1/auth/signup       - Create account
POST   /api/v1/auth/login        - Login
POST   /api/v1/auth/logout       - Logout
POST   /api/v1/auth/refresh      - Refresh token
GET    /api/v1/users/me          - Get current user
```

### Restaurant Service (Port 8003)

```
# Restaurants
GET    /api/v1/restaurants             - List restaurants
POST   /api/v1/restaurants             - Create restaurant
GET    /api/v1/restaurants/{id}        - Get restaurant
PUT    /api/v1/restaurants/{id}        - Update restaurant

# Menu Items
GET    /api/v1/restaurants/{id}/menu-items              - List menu
POST   /api/v1/restaurants/{id}/menu-items              - Create item
GET    /api/v1/restaurants/{id}/menu-items/{item_id}    - Get item
PUT    /api/v1/restaurants/{id}/menu-items/{item_id}    - Update item
DELETE /api/v1/restaurants/{id}/menu-items/{item_id}    - Delete item

# Tables (with QR Codes!)
GET    /api/v1/restaurants/{id}/tables               - List tables
POST   /api/v1/restaurants/{id}/tables               - Create table + QR
GET    /api/v1/restaurants/{id}/tables/{table_id}    - Get table
PUT    /api/v1/restaurants/{id}/tables/{table_id}    - Update table
DELETE /api/v1/restaurants/{id}/tables/{table_id}    - Delete table
POST   /api/v1/restaurants/{id}/tables/{table_id}/regenerate-qr  - New QR
PATCH  /api/v1/restaurants/{id}/tables/{table_id}/status         - Update status

# Feedback
GET    /api/v1/restaurants/{id}/feedback           - List feedback
POST   /api/v1/restaurants/{id}/feedback           - Submit feedback
GET    /api/v1/restaurants/{id}/feedback/{fb_id}   - Get feedback
DELETE /api/v1/restaurants/{id}/feedback/{fb_id}   - Delete feedback
```

---

## 🔧 Manage Services

### Check Status

```bash
# Check if services are running
curl http://localhost:8001/health
curl http://localhost:8003/health

# Check database
docker ps | grep restaurant-postgres

# Check logs
docker logs restaurant-postgres
```

### Stop Services

```bash
# Stop backend services
pkill -f "uvicorn.*8001"
pkill -f "uvicorn.*8003"

# Stop databases
docker stop restaurant-postgres restaurant-redis
```

### Restart Services

```bash
# Start databases
docker start restaurant-postgres restaurant-redis

# Start services
cd /home/shadrach/Restaurant_management
./start-auth-service.sh &
./start-restaurant-service.sh &
```

---

## 🐛 Troubleshooting

### Frontend can't connect to backend

1. Check if services are running:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8003/health
   ```

2. Check frontend .env file:
   ```bash
   cat /home/shadrach/Restaurant_management/frontend/.env
   ```
   
   Should contain:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000
   ```

3. Note: Frontend expects API Gateway on port 8000, but we're running services directly on 8001/8003

**FIX**: Update frontend .env:
```bash
cd /home/shadrach/Restaurant_management/frontend
cat > .env << 'ENVEOF'
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
ENVEOF
```

Then restart frontend:
```bash
# Kill current frontend
pkill -f "vite"

# Restart
npm run dev &
```

### Login fails

1. Make sure Auth Service is running on port 8001
2. Check browser console for errors
3. Try creating account first at /signup

### QR Code doesn't scan

1. Make sure QR code was generated (check table card)
2. QR URL format: `http://localhost:3001/table/{tableId}?restaurant={restaurantId}&token={token}`
3. Test by opening URL manually in browser

---

## ✅ Success Checklist

After following all steps, you should have:

- [x] Backend services running (8001, 8003)
- [x] Frontend running (3001)
- [x] User account created
- [ ] Restaurant created
- [ ] Tables created with QR codes
- [ ] Menu items added
- [ ] QR code printed/tested
- [ ] Complete order flow tested

---

## 🎯 Next Steps

1. **Create your restaurant data** (Steps 3-6 above)
2. **Test QR code workflow** (Steps 7-8)
3. **Add Kitchen Interface** (when Order Service is implemented)
4. **Deploy to production** (when ready)

---

## 📝 Quick Reference

**Frontend**: http://localhost:3001  
**Auth API**: http://localhost:8001/docs  
**Restaurant API**: http://localhost:8003/docs  

**Test Credentials**:
- Username: testadmin
- Password: Password123!

**QR Code Flow**:
```
Scan QR → Landing Page → Menu (with table banner) → Cart → Order
```

---

🎉 **Everything is set up and ready to test!**
