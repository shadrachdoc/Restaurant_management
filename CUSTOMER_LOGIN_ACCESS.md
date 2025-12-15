# Customer Login Page - Quick Access Guide

## ✅ What's Been Built

### Backend (Customer Service)
- ✅ Customer registration API
- ✅ Customer login API  
- ✅ Guest checkout API
- ✅ JWT token authentication
- ✅ Multi-tenant isolation (customers per restaurant)

### Frontend
- ✅ Customer login/register page
- ✅ Beautiful UI with tabs
- ✅ Restaurant selection dropdown
- ✅ Guest checkout option

---

## 🚀 How to Access the Customer Login Page

### Step 1: Start the Customer Service Backend

Open a new terminal and run:

```bash
cd /home/shadrach/Restaurant_management

# Start Customer Service on port 8007
cd services/customer-service
uvicorn app.main:app --reload --port 8007
```

### Step 2: Start the Frontend (if not already running)

In another terminal:

```bash
cd /home/shadrach/Restaurant_management/frontend
npm run dev
```

### Step 3: Access the Login Page

Open your browser and go to:

```
http://localhost:5173/customer-login
```

---

## 📝 How to Test

### Create a Restaurant First

Before customers can login, you need at least one restaurant with a slug.

1. **Login as Restaurant Admin or Master Admin**
   - Go to: `http://localhost:5173/login`
   - Login with your admin credentials

2. **Create a Restaurant** (if you haven't already)
   - Go to Admin Dashboard
   - Create a new restaurant
   - The system will auto-generate a slug (e.g., "Pizza Palace" → "pizza-palace")

### Test Customer Registration

1. Go to: `http://localhost:5173/customer-login`
2. Click the **"Register"** tab
3. Fill in the form:
   - **Restaurant**: Select from dropdown
   - **First Name**: John
   - **Last Name**: Doe
   - **Email**: john@example.com
   - **Phone**: +1234567890
   - **Password**: Test1234!
4. Click **"Create Account"**

### Test Customer Login

1. Go to: `http://localhost:5173/customer-login`
2. Click the **"Login"** tab
3. Fill in the form:
   - **Restaurant**: Select your restaurant
   - **Email**: john@example.com
   - **Password**: Test1234!
4. Click **"Login"**

### Test Guest Checkout

1. Go to: `http://localhost:5173/customer-login`
2. Click **"Continue as Guest"**
3. (This will redirect to guest order page - to be built next)

---

## 🔍 Verify It's Working

### Check Backend Logs

You should see in the Customer Service terminal:

```
INFO:customer-service:Customer registered: john@example.com for restaurant abc-123
INFO:customer-service:Customer logged in: john@example.com for restaurant abc-123
```

### Check Browser Console

After successful login:
1. Open Developer Tools (F12)
2. Go to **Console** tab
3. Type: `localStorage.getItem('customer_access_token')`
4. You should see a JWT token

### Check Database

```bash
psql -U restaurant_admin -d restaurant_db -c "SELECT * FROM customers;"
```

You should see your customer record.

---

## 🎨 Features

### Login Page
- ✅ Email & password authentication
- ✅ Restaurant selection dropdown
- ✅ Form validation
- ✅ Loading states
- ✅ Error messages via toast
- ✅ JWT token storage

### Registration Page
- ✅ First name, last name, email, phone
- ✅ Password validation (min 8 chars)
- ✅ Marketing opt-in checkbox
- ✅ Auto-login after registration
- ✅ Duplicate email detection

### Guest Checkout
- ✅ Button to continue without account
- ✅ Quick ordering for first-time users

---

## 🔐 How Authentication Works

### Registration Flow
```
1. Customer fills registration form
   ↓
2. POST /api/v1/customers/register
   ↓
3. Backend creates customer record
   ↓
4. Backend generates JWT tokens (access + refresh)
   ↓
5. Frontend stores tokens in localStorage
   ↓
6. Redirect to menu page
```

### Login Flow
```
1. Customer enters email + password
   ↓
2. POST /api/v1/customers/login
   ↓
3. Backend verifies credentials
   ↓
4. Backend generates JWT tokens
   ↓
5. Frontend stores tokens
   ↓
6. Redirect to menu page
```

### Token Storage
```javascript
localStorage.setItem('customer_access_token', 'eyJhbGc...');
localStorage.setItem('customer_refresh_token', 'eyJhbGc...');
localStorage.setItem('customer', JSON.stringify({
  id: "uuid",
  email: "john@example.com",
  first_name: "John",
  restaurant_id: "uuid"
}));
```

---

## 🛠️ Troubleshooting

### "Failed to load restaurants"
**Problem**: Restaurant Service not running
**Solution**: 
```bash
cd services/restaurant-service
uvicorn app.main:app --reload --port 8003
```

### "Customer with this email already exists"
**Problem**: Trying to register with existing email for same restaurant
**Solution**: 
- Use a different email
- OR login instead
- OR use different restaurant

### "Restaurant 'xyz' not found"
**Problem**: Restaurant doesn't exist or is inactive
**Solution**:
- Create restaurant via admin panel
- Ensure restaurant has `is_active = true`
- Check restaurant has a slug

### "Invalid email or password"
**Problem**: Wrong credentials
**Solution**:
- Double-check email and password
- Ensure you selected correct restaurant
- Password is case-sensitive

### Network Error
**Problem**: Customer Service not running on port 8007
**Solution**:
```bash
cd services/customer-service
uvicorn app.main:app --reload --port 8007
```

---

## 📊 Database Schema

### Customers Table

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    restaurant_id UUID NOT NULL,  -- Tenant isolation
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255),  -- Nullable for guests
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    default_delivery_address VARCHAR(500),
    loyalty_points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    accepts_marketing BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(restaurant_id, email),  -- Same email OK in different restaurants
    UNIQUE(restaurant_id, phone_number)
);
```

---

## 🚀 Next Steps

Now that customer login works, you can:

1. **Build Menu Page** - Show restaurant menu with cart
2. **Build Checkout Page** - Place orders
3. **Build Order Tracking** - Track order status
4. **Build Order History** - See past orders
5. **Add Subdomain Support** - `pizza-palace.yourapp.com` routing

---

## 📞 API Endpoints

### Customer Service (Port 8007)

```
POST   /api/v1/customers/register
POST   /api/v1/customers/login
POST   /api/v1/customers/guest-checkout
GET    /api/v1/customers/me (requires JWT)
PUT    /api/v1/customers/me (requires JWT)
GET    /health
```

### Example API Call (curl)

```bash
# Register
curl -X POST http://localhost:8007/api/v1/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_slug": "pizza-palace",
    "email": "test@example.com",
    "phone_number": "+1234567890",
    "password": "Test1234!",
    "first_name": "Test",
    "last_name": "User",
    "accepts_marketing": false
  }'

# Login
curl -X POST http://localhost:8007/api/v1/customers/login \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_slug": "pizza-palace",
    "email": "test@example.com",
    "password": "Test1234!"
  }'
```

---

## ✅ Summary

**URL**: `http://localhost:5173/customer-login`

**Services Required**:
- ✅ Customer Service (port 8007)
- ✅ Restaurant Service (port 8003)
- ✅ Frontend (port 5173)
- ✅ PostgreSQL (running)

**Features**:
- ✅ Login
- ✅ Registration
- ✅ Guest checkout button
- ✅ Multi-tenant (per restaurant)
- ✅ JWT authentication

Ready to use! 🎉
