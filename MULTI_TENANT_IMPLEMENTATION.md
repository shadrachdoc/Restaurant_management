# Multi-Tenant SaaS Online Ordering - Implementation Progress

## Architecture Overview

**Approach**: Subdomain-based multi-tenancy
- Each restaurant: `pizza-palace.yourapp.com`
- Tenant isolation: All data scoped by `restaurant_id`
- Microservices: Independent scalable services in Kubernetes

---

## What We've Implemented ✅

### 1. Restaurant Slug System
**Files Modified:**
- `services/restaurant-service/app/models.py` - Added `slug` field
- `services/restaurant-service/app/schemas.py` - Added slug to schemas
- `services/restaurant-service/app/utils/slug.py` - Auto-generate unique slugs
- `services/restaurant-service/app/routes/restaurants.py` - Slug generation on creation

**Features:**
- ✅ Unique slug per restaurant (e.g., "Pizza Palace" → "pizza-palace")
- ✅ Auto-increment if duplicate ("pizza-palace-2", "pizza-palace-3")
- ✅ New API endpoint: `GET /api/v1/restaurants/slug/{slug}`
- ✅ Used for tenant resolution from subdomain

**Example:**
```python
# Creating restaurant
POST /api/v1/restaurants
{
  "name": "Pizza Palace",
  "email": "info@pizzapalace.com"
}
# Auto-generates: slug="pizza-palace"

# Access via subdomain
https://pizza-palace.yourapp.com
# Backend resolves: GET /restaurants/slug/pizza-palace
```

### 2. Customer Service Microservice
**Files Created:**
- `services/customer-service/Dockerfile`
- `services/customer-service/requirements.txt`
- `services/customer-service/app/models.py` - Customer & CustomerSession models
- `services/customer-service/app/schemas.py` - API request/response schemas
- `services/customer-service/app/database.py` - Database connection
- `services/customer-service/app/utils/auth.py` - JWT & password hashing

**Customer Model Features:**
- ✅ Tenant isolation (`restaurant_id` required)
- ✅ Email unique per restaurant (can reuse across restaurants)
- ✅ Guest checkout support (nullable password)
- ✅ Delivery addresses
- ✅ Loyalty points system
- ✅ Marketing preferences

**Database Schema:**
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255),  -- Nullable for guests
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    default_delivery_address VARCHAR(500),
    loyalty_points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    UNIQUE(restaurant_id, email),
    UNIQUE(restaurant_id, phone_number)
);
```

---

## What's Next (Ready to Implement)

### 3. Customer API Routes (Next Task)
**File to Create:** `services/customer-service/app/routes/customers.py`

**Endpoints to Build:**
```python
POST   /api/v1/customers/register          # Register customer
POST   /api/v1/customers/login             # Login
POST   /api/v1/customers/guest-checkout    # Guest checkout
POST   /api/v1/customers/refresh-token     # Refresh JWT
GET    /api/v1/customers/me                # Get profile
PUT    /api/v1/customers/me                # Update profile
POST   /api/v1/customers/change-password   # Change password
GET    /api/v1/customers/me/orders         # Order history
```

### 4. Tenant Middleware
**File to Create:** `shared/middleware/tenant.py`

**Purpose:** Extract restaurant from subdomain/URL
```python
# From subdomain
pizza-palace.yourapp.com → restaurant_id="uuid-123"

# From path
yourapp.com/pizza-palace/menu → restaurant_id="uuid-123"

# From header (mobile apps)
X-Restaurant-Slug: pizza-palace → restaurant_id="uuid-123"
```

### 5. Frontend Components

**Pages to Create:**
```
frontend/src/pages/Customer/
├── RestaurantHome.jsx          # Landing page (branded)
├── Menu.jsx                    # Browse menu + cart
├── Checkout.jsx                # Order placement
├── OrderTracking.jsx           # Track order
├── OrderHistory.jsx            # Past orders
├── CustomerLogin.jsx           # Login modal
└── CustomerRegister.jsx        # Registration modal
```

**Store:**
```javascript
// Cart store (Zustand)
frontend/src/store/cartStore.js
- addItem(menuItem, quantity)
- removeItem(itemId)
- updateQuantity(itemId, quantity)
- clearCart()
- getTotal()
```

### 6. Kubernetes Configuration

**Ingress for Subdomains:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: restaurant-ingress
spec:
  tls:
  - hosts:
    - "*.yourapp.com"
    secretName: wildcard-tls
  rules:
  - host: "*.yourapp.com"
    http:
      paths:
      - path: /
        backend:
          service:
            name: frontend
            port: 3000
```

### 7. Notification System

**When Order Placed:**
1. Notify chef (Kitchen Display)
2. Notify restaurant admin (Dashboard)
3. Email customer confirmation
4. SMS customer (optional)

**Technologies:**
- RabbitMQ for event bus
- Email: SendGrid/SMTP
- SMS: Twilio (future)

---

## Implementation Roadmap

### Week 1: Customer Service & Auth
- [x] Add restaurant slug field
- [x] Create Customer Service structure
- [ ] Build customer registration API
- [ ] Build customer login API
- [ ] Build guest checkout API
- [ ] Add JWT authentication middleware
- [ ] Test customer endpoints

### Week 2: Frontend Online Ordering
- [ ] Create tenant detection utility
- [ ] Build restaurant home page
- [ ] Build menu display + cart
- [ ] Build checkout flow
- [ ] Add customer login/register modals
- [ ] Test end-to-end ordering

### Week 3: Notifications & Polish
- [ ] Implement order notifications
- [ ] Add email confirmations
- [ ] Create order tracking page
- [ ] Add order history
- [ ] Test multi-tenant isolation

### Week 4: Kubernetes & Deployment
- [ ] Configure Ingress for subdomains
- [ ] Setup wildcard SSL
- [ ] Deploy Customer Service
- [ ] Test subdomain routing
- [ ] Performance testing

---

## How It Works (Full Flow)

### 1. Restaurant Setup
```
1. Restaurant Admin signs up
2. Creates restaurant: "Pizza Palace"
3. System generates slug: "pizza-palace"
4. Restaurant accessible at: https://pizza-palace.yourapp.com
5. Admin adds menu items, sets branding
```

### 2. Customer Journey
```
1. Customer visits: https://pizza-palace.yourapp.com
2. Sees branded page (logo, colors, banner)
3. Browses menu, adds to cart
4. At checkout, can:
   a) Continue as guest (name, email, phone)
   b) Register account (save info, loyalty)
   c) Login (if existing customer)
5. Place order
6. Receive order number
7. Track order status in real-time
```

### 3. Order Fulfillment
```
1. Order created → Event published
2. Chef dashboard receives notification
3. Admin dashboard shows new order
4. Customer gets email confirmation
5. Chef updates status: PREPARING → READY
6. Customer sees live status updates
7. Order completed
```

### 4. Tenant Isolation
```
Request: GET https://pizza-palace.yourapp.com/menu
         ↓
Extract slug: "pizza-palace"
         ↓
Lookup restaurant: SELECT * FROM restaurants WHERE slug='pizza-palace'
         ↓
Set context: restaurant_id="abc-123"
         ↓
Filter menu: SELECT * FROM menu_items WHERE restaurant_id='abc-123'
         ↓
Return: Only Pizza Palace's menu items
```

---

## Database Changes Required

### Migration SQL

```sql
-- Add slug to restaurants table
ALTER TABLE restaurants
ADD COLUMN slug VARCHAR(255) UNIQUE NOT NULL;

CREATE INDEX idx_restaurants_slug ON restaurants(slug);

-- Create customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    default_delivery_address VARCHAR(500),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP,
    accepts_marketing BOOLEAN DEFAULT FALSE,
    loyalty_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_order_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_restaurant_email UNIQUE (restaurant_id, email),
    CONSTRAINT uq_restaurant_phone UNIQUE (restaurant_id, phone_number)
);

CREATE INDEX idx_customers_restaurant ON customers(restaurant_id);
CREATE INDEX idx_customers_email ON customers(restaurant_id, email);

-- Add customer_id to orders table
ALTER TABLE orders
ADD COLUMN customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;

CREATE INDEX idx_orders_customer ON orders(customer_id);
```

---

## Testing Checklist

### Backend
- [ ] Create restaurant with slug auto-generation
- [ ] Get restaurant by slug
- [ ] Register customer for restaurant A
- [ ] Same email registers for restaurant B (should work)
- [ ] Login customer with correct credentials
- [ ] Login fails with wrong password
- [ ] Guest checkout creates customer without password
- [ ] JWT token includes restaurant_id
- [ ] Customer can only see their restaurant's data

### Frontend
- [ ] Visit subdomain shows correct restaurant
- [ ] Browse menu filtered by restaurant
- [ ] Add items to cart
- [ ] Cart clears when switching restaurants
- [ ] Guest checkout works
- [ ] Customer registration works
- [ ] Customer login works
- [ ] Order placement creates order
- [ ] Order linked to customer (if logged in)
- [ ] Order tracking works

### Kubernetes
- [ ] Wildcard DNS *.yourapp.com points to cluster
- [ ] Ingress routes subdomains correctly
- [ ] SSL certificate works for subdomains
- [ ] Customer Service deployment healthy
- [ ] Services can communicate
- [ ] Load balancing works

---

## Environment Variables Needed

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/restaurant_db

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Redis
REDIS_URL=redis://redis:6379/0

# Email (future)
SENDGRID_API_KEY=
SMTP_HOST=
SMTP_PORT=

# SMS (future)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# Domain
BASE_DOMAIN=yourapp.com
```

---

## Next Steps

**Immediate (This Week):**
1. Complete customer registration/login API routes
2. Create tenant middleware for request context
3. Build frontend menu + cart components
4. Test guest checkout flow

**Coming Soon:**
1. Order notifications
2. Email confirmations
3. Kubernetes Ingress setup
4. Production deployment

Ready to continue? Let's build the customer API routes next!
