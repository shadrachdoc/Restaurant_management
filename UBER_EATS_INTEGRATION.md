# Uber Eats Integration Guide
## Restaurant Management System - Third-Party Order Integration

---

## 📋 Overview

This guide explains how to integrate Uber Eats orders into your Restaurant Management System so that:
- ✅ Chef Dashboard shows Uber Eats orders alongside regular orders
- ✅ Restaurant Admin can view and manage all orders (dine-in, online, Uber Eats)
- ✅ Order status updates sync between systems
- ✅ Kitchen Display System (KDS) shows all order types

---

## 🎯 What You'll Achieve

### Before Integration
```
Chef Dashboard:
├── Dine-in orders (TABLE)
└── Online orders (ONLINE)

Restaurant Admin:
├── Dine-in orders
└── Online orders
```

### After Integration
```
Chef Dashboard:
├── Dine-in orders (TABLE)
├── Online orders (ONLINE)
└── Uber Eats orders (UBER_EATS) ← NEW

Restaurant Admin:
├── All orders unified view
├── Filter by source (Dine-in / Online / Uber Eats)
└── Real-time status updates
```

---

## 🔑 Step 1: Uber Eats API Setup

### 1.1 Access Developer Portal

You already have an account at: https://developer.uber.com/

Navigate to:
1. **Developer Portal**: https://developer.uber.com/
2. **Eats Integration**: https://developer.uber.com/docs/eats/introduction

### 1.2 Create an App

1. Go to **Dashboard** → **Apps**
2. Click **Create New App**
3. Fill in details:
   - **App Name**: `Restaurant Management System - [Your Restaurant Name]`
   - **Type**: Select **Uber Eats**
   - **Environment**: Start with **Sandbox** (testing), later switch to **Production**

### 1.3 Get API Credentials

After creating the app, you'll receive:

```
Client ID:       [Your Client ID]
Client Secret:   [Your Client Secret]
Server Token:    [Your Server Token]
Store ID:        [Your Restaurant Store ID]
```

**⚠️ IMPORTANT**: Keep these credentials secure!

### 1.4 Required Scopes (Permissions)

Enable these scopes for your app:
- ✅ `eats.store.orders.read` - Read orders
- ✅ `eats.store.orders.write` - Update order status
- ✅ `eats.store` - Access store information
- ✅ `eats.store.status.write` - Update store status (open/closed)

### 1.5 Webhook Setup

Configure webhooks to receive real-time order notifications:

**Webhook URL**: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`

**Events to subscribe**:
- ✅ `orders.notification` - New order received
- ✅ `orders.cancel` - Order cancelled
- ✅ `orders.status_update` - Status changed

---

## 📊 Step 2: Database Schema Changes

### 2.1 Update Order Type Enum

Add new order type for Uber Eats:

```sql
-- Connect to database
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db

-- Add UBER_EATS to order type enum
ALTER TYPE ordertype ADD VALUE IF NOT EXISTS 'UBER_EATS';

-- Verify
SELECT unnest(enum_range(NULL::ordertype));
-- Should show: TABLE, ONLINE, UBER_EATS
```

### 2.2 Add Uber Eats Metadata to Orders Table

```sql
-- Add columns for third-party integration
ALTER TABLE orders ADD COLUMN IF NOT EXISTS external_order_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS external_source VARCHAR(50); -- 'UBER_EATS', 'DOORDASH', etc.
ALTER TABLE orders ADD COLUMN IF NOT EXISTS external_metadata JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS external_status VARCHAR(50);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_external_order_id ON orders(external_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_external_source ON orders(external_source);
CREATE INDEX IF NOT EXISTS idx_orders_source_status ON orders(external_source, status);

-- Example of what external_metadata will store:
/*
{
  "uber_order_id": "abc123-xyz789",
  "customer_info": {
    "name": "John Doe",
    "phone": "+1234567890"
  },
  "delivery_info": {
    "address": "123 Main St",
    "instructions": "Ring doorbell"
  },
  "estimated_pickup_time": "2026-01-13T12:30:00Z",
  "courier_name": "Jane Driver",
  "delivery_fee": 3.99
}
*/
```

### 2.3 Create Uber Eats Integration Settings Table

```sql
-- Store API credentials and configuration
CREATE TABLE IF NOT EXISTS uber_eats_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,

    -- API Credentials
    client_id VARCHAR(255) NOT NULL,
    client_secret_encrypted TEXT NOT NULL,  -- Encrypted!
    server_token_encrypted TEXT NOT NULL,   -- Encrypted!
    store_id VARCHAR(255) NOT NULL,

    -- Configuration
    is_enabled BOOLEAN DEFAULT true,
    auto_accept_orders BOOLEAN DEFAULT false,
    environment VARCHAR(20) DEFAULT 'sandbox',  -- 'sandbox' or 'production'

    -- Webhook
    webhook_secret VARCHAR(255),

    -- Settings
    default_prep_time_minutes INTEGER DEFAULT 20,
    auto_status_sync BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_sync_at TIMESTAMP,

    UNIQUE(restaurant_id)
);

-- Create index
CREATE INDEX idx_uber_config_restaurant ON uber_eats_config(restaurant_id);
```

### 2.4 Create Order Status Mapping Table

Map internal statuses to Uber Eats statuses:

```sql
CREATE TABLE IF NOT EXISTS order_status_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    internal_status VARCHAR(50) NOT NULL,
    external_source VARCHAR(50) NOT NULL,
    external_status VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(internal_status, external_source)
);

-- Insert mappings
INSERT INTO order_status_mapping (internal_status, external_source, external_status, description) VALUES
    ('PENDING', 'UBER_EATS', 'created', 'Order placed, awaiting restaurant acceptance'),
    ('CONFIRMED', 'UBER_EATS', 'accepted', 'Restaurant accepted the order'),
    ('PREPARING', 'UBER_EATS', 'preparing', 'Order is being prepared'),
    ('READY', 'UBER_EATS', 'ready_for_pickup', 'Order ready for courier pickup'),
    ('SERVED', 'UBER_EATS', 'picked_up', 'Courier picked up the order'),
    ('COMPLETED', 'UBER_EATS', 'delivered', 'Order delivered to customer'),
    ('CANCELLED', 'UBER_EATS', 'cancelled', 'Order was cancelled')
ON CONFLICT (internal_status, external_source) DO NOTHING;
```

---

## 🏗️ Step 3: Architecture Changes

### 3.1 New Microservice: Integration Service

Create a new service to handle third-party integrations:

```
services/
└── integration-service/          ← NEW SERVICE
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── config.py
    │   ├── routes/
    │   │   ├── uber_eats.py      # Uber Eats endpoints
    │   │   ├── webhooks.py        # Webhook handlers
    │   │   └── admin.py           # Admin configuration
    │   ├── services/
    │   │   ├── uber_eats_client.py  # Uber API client
    │   │   ├── order_sync.py        # Order synchronization
    │   │   └── status_mapper.py     # Status mapping logic
    │   └── models/
    │       └── uber_order.py        # Uber order models
    ├── requirements.txt
    └── Dockerfile
```

### 3.2 Service Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Uber Eats → Your System                      │
└─────────────────────────────────────────────────────────────────┘

1. New Order Flow:
   Uber Eats API
        ↓ (webhook)
   Integration Service (Port 8015)
        ↓ (validate & transform)
   Order Service (Port 8002)
        ↓ (create order with type=UBER_EATS)
   PostgreSQL Database
        ↓ (real-time sync)
   Chef Dashboard & Admin Panel

2. Status Update Flow:
   Chef marks order as "READY"
        ↓
   Frontend → API Gateway
        ↓
   Order Service (update status)
        ↓
   Integration Service (detect status change)
        ↓
   Uber Eats API (sync status)
```

---

## 🔧 Step 4: Integration Service Implementation

### 4.1 Main Service File

**File**: `services/integration-service/app/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routes import uber_eats, webhooks, admin
from .services.uber_eats_client import UberEatsClient
from shared.config.settings import settings
from shared.utils.logger import setup_logger

logger = setup_logger("integration-service", settings.log_level, settings.log_format)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Integration Service...")
    # Initialize Uber Eats client
    app.state.uber_client = UberEatsClient()
    yield
    logger.info("Shutting down Integration Service...")

app = FastAPI(
    title="Restaurant Management - Integration Service",
    description="Third-party integration service (Uber Eats, DoorDash, etc.)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(uber_eats.router, prefix="/api/v1/integrations/uber-eats", tags=["Uber Eats"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(admin.router, prefix="/api/v1/integrations/admin", tags=["Admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "integration-service"}
```

### 4.2 Uber Eats Client

**File**: `services/integration-service/app/services/uber_eats_client.py`

```python
import httpx
import hmac
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel

class UberEatsClient:
    """Client for Uber Eats API"""

    def __init__(self, client_id: str, client_secret: str, server_token: str, store_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.server_token = server_token
        self.store_id = store_id
        self.base_url = "https://api.uber.com"  # Production
        # For sandbox: "https://api-sandbox.uber.com"

    async def get_orders(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get recent orders from Uber Eats
        Docs: https://developer.uber.com/docs/eats/references/api/v1/get-stores-storeid-orders
        """
        url = f"{self.base_url}/v1/eats/stores/{self.store_id}/orders"
        headers = {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }
        params = {"limit": limit, "offset": offset}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_order(self, order_id: str) -> Dict:
        """
        Get specific order details
        """
        url = f"{self.base_url}/v1/eats/stores/{self.store_id}/orders/{order_id}"
        headers = {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def accept_order(self, order_id: str, estimated_prep_time: int = 20) -> Dict:
        """
        Accept an order
        """
        url = f"{self.base_url}/v1/eats/stores/{self.store_id}/orders/{order_id}/accept_pos_order"
        headers = {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "reason": "ACCEPTED",
            "estimated_ready_for_pickup_at": self._calculate_pickup_time(estimated_prep_time)
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def deny_order(self, order_id: str, reason: str = "OUT_OF_ITEMS") -> Dict:
        """
        Deny/reject an order
        Reasons: OUT_OF_ITEMS, STORE_CLOSED, TOO_BUSY, etc.
        """
        url = f"{self.base_url}/v1/eats/stores/{self.store_id}/orders/{order_id}/deny_pos_order"
        headers = {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }
        payload = {"reason": reason}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def update_order_status(self, order_id: str, status: str) -> Dict:
        """
        Update order status
        Statuses: created, accepted, preparing, ready_for_pickup, picked_up, delivered, cancelled
        """
        url = f"{self.base_url}/v1/eats/stores/{self.store_id}/orders/{order_id}/status"
        headers = {
            "Authorization": f"Bearer {self.server_token}",
            "Content-Type": "application/json"
        }
        payload = {"status": status}

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def verify_webhook_signature(self, payload: str, signature: str, webhook_secret: str) -> bool:
        """
        Verify webhook signature for security
        """
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)

    def _calculate_pickup_time(self, prep_minutes: int) -> str:
        """Calculate estimated pickup time"""
        from datetime import datetime, timedelta
        pickup_time = datetime.utcnow() + timedelta(minutes=prep_minutes)
        return pickup_time.isoformat() + "Z"
```

### 4.3 Webhook Handler

**File**: `services/integration-service/app/routes/webhooks.py`

```python
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import json
from ..services.uber_eats_client import UberEatsClient
from ..services.order_sync import OrderSyncService

router = APIRouter()

@router.post("/uber-eats")
async def uber_eats_webhook(
    request: Request,
    x_uber_signature: Optional[str] = Header(None)
):
    """
    Handle incoming webhooks from Uber Eats

    Events:
    - orders.notification: New order placed
    - orders.cancel: Order cancelled
    - orders.status_update: Status changed
    """

    # Get raw body for signature verification
    body = await request.body()
    payload = json.loads(body.decode())

    # Verify signature (security)
    webhook_secret = "YOUR_WEBHOOK_SECRET"  # From database
    uber_client = UberEatsClient(...)

    if not uber_client.verify_webhook_signature(body.decode(), x_uber_signature, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Extract event details
    event_type = payload.get("event_type")
    order_data = payload.get("order")

    # Route to appropriate handler
    sync_service = OrderSyncService()

    if event_type == "orders.notification":
        # New order received
        await sync_service.create_order_from_uber(order_data)

    elif event_type == "orders.cancel":
        # Order cancelled
        await sync_service.cancel_uber_order(order_data["id"])

    elif event_type == "orders.status_update":
        # Status changed
        await sync_service.update_uber_order_status(order_data["id"], order_data["status"])

    return {"status": "processed"}
```

### 4.4 Order Synchronization Service

**File**: `services/integration-service/app/services/order_sync.py`

```python
from typing import Dict
import httpx
from uuid import uuid4

class OrderSyncService:
    """Synchronize orders between Uber Eats and internal system"""

    def __init__(self):
        self.order_service_url = "http://order-service:8002"

    async def create_order_from_uber(self, uber_order: Dict):
        """
        Transform Uber order to internal format and create in database
        """

        # Transform Uber order format to internal format
        internal_order = {
            "id": str(uuid4()),
            "restaurant_id": uber_order["store"]["id"],  # Map to your restaurant ID
            "order_number": f"UE-{uber_order['id'][:8]}",
            "order_type": "UBER_EATS",
            "status": "PENDING",

            # Customer info
            "customer_name": uber_order.get("eater", {}).get("first_name", "Uber Customer"),
            "customer_phone": uber_order.get("eater", {}).get("phone_number"),

            # Delivery info
            "delivery_address": self._format_address(uber_order.get("delivery")),
            "special_instructions": uber_order.get("special_instructions", ""),

            # Items
            "items": self._transform_items(uber_order["cart"]["items"]),

            # Pricing
            "subtotal": uber_order["payment"]["charges"]["total"] / 100,  # Convert cents to dollars
            "tax": uber_order["payment"]["charges"]["tax"] / 100,
            "total": uber_order["payment"]["charges"]["total_with_tip"] / 100,

            # Uber-specific metadata
            "external_order_id": uber_order["id"],
            "external_source": "UBER_EATS",
            "external_metadata": {
                "uber_order_id": uber_order["id"],
                "estimated_pickup_time": uber_order["estimated_ready_for_pickup_at"],
                "delivery_fee": uber_order["payment"]["charges"]["delivery_fee"] / 100,
                "customer_tip": uber_order["payment"]["charges"]["tip"] / 100,
                "courier_info": uber_order.get("courier", {})
            }
        }

        # Send to order service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.order_service_url}/api/v1/orders",
                json=internal_order
            )
            response.raise_for_status()
            return response.json()

    def _transform_items(self, uber_items: list) -> list:
        """Transform Uber Eats items to internal format"""
        items = []
        for item in uber_items:
            items.append({
                "menu_item_id": self._map_uber_item_to_internal(item["id"]),
                "menu_item_name": item["title"],
                "quantity": item["quantity"],
                "unit_price": item["price"] / 100,
                "special_requests": item.get("special_requests", ""),
                "customizations": item.get("selected_modifier_groups", [])
            })
        return items

    def _map_uber_item_to_internal(self, uber_item_id: str) -> str:
        """
        Map Uber Eats item ID to internal menu item ID
        You'll need a mapping table for this
        """
        # Query database for mapping
        # For now, return placeholder
        return str(uuid4())

    def _format_address(self, delivery_info: Dict) -> str:
        """Format delivery address"""
        if not delivery_info:
            return ""

        addr = delivery_info.get("location", {})
        return f"{addr.get('address')}, {addr.get('city')}, {addr.get('state')} {addr.get('postal_code')}"
```

---

## 🎨 Step 5: Frontend Changes

### 5.1 Update Order Type Display

**File**: `frontend/src/components/OrderCard.jsx`

```javascript
const getOrderTypeStyle = (orderType) => {
  switch(orderType) {
    case 'TABLE':
      return {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        icon: '🍽️',
        label: 'Dine-in'
      };
    case 'ONLINE':
      return {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: '🌐',
        label: 'Online'
      };
    case 'UBER_EATS':  // NEW
      return {
        bg: 'bg-black',
        text: 'text-white',
        icon: '🚗',
        label: 'Uber Eats'
      };
    default:
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        icon: '📦',
        label: 'Other'
      };
  }
};
```

### 5.2 Chef Dashboard - Order List with Uber Eats

**File**: `frontend/src/pages/Chef/OrderList.jsx`

```javascript
// Add filter for order source
const [sourceFilter, setSourceFilter] = useState('ALL');

const filteredOrders = orders.filter(order => {
  if (sourceFilter === 'ALL') return true;
  return order.order_type === sourceFilter;
});

return (
  <div>
    {/* Filter buttons */}
    <div className="flex gap-2 mb-4">
      <button
        onClick={() => setSourceFilter('ALL')}
        className={`px-4 py-2 rounded ${sourceFilter === 'ALL' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
      >
        All Orders
      </button>
      <button
        onClick={() => setSourceFilter('TABLE')}
        className={`px-4 py-2 rounded ${sourceFilter === 'TABLE' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
      >
        🍽️ Dine-in
      </button>
      <button
        onClick={() => setSourceFilter('ONLINE')}
        className={`px-4 py-2 rounded ${sourceFilter === 'ONLINE' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
      >
        🌐 Online
      </button>
      <button
        onClick={() => setSourceFilter('UBER_EATS')}
        className={`px-4 py-2 rounded ${sourceFilter === 'UBER_EATS' ? 'bg-black text-white' : 'bg-gray-200'}`}
      >
        🚗 Uber Eats
      </button>
    </div>

    {/* Order cards */}
    {filteredOrders.map(order => (
      <OrderCard key={order.id} order={order} />
    ))}
  </div>
);
```

### 5.3 Admin Configuration Page

**File**: `frontend/src/pages/Admin/IntegrationSettings.jsx`

```javascript
import React, { useState } from 'react';
import { integrationAPI } from '../../services/api';

export default function IntegrationSettings() {
  const [uberConfig, setUberConfig] = useState({
    client_id: '',
    client_secret: '',
    server_token: '',
    store_id: '',
    is_enabled: false,
    auto_accept_orders: false,
    default_prep_time_minutes: 20
  });

  const handleSave = async () => {
    await integrationAPI.updateUberEatsConfig(uberConfig);
    alert('Configuration saved!');
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Uber Eats Integration</h1>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Client ID</label>
          <input
            type="text"
            value={uberConfig.client_id}
            onChange={(e) => setUberConfig({...uberConfig, client_id: e.target.value})}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Client Secret</label>
          <input
            type="password"
            value={uberConfig.client_secret}
            onChange={(e) => setUberConfig({...uberConfig, client_secret: e.target.value})}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Server Token</label>
          <input
            type="password"
            value={uberConfig.server_token}
            onChange={(e) => setUberConfig({...uberConfig, server_token: e.target.value})}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Store ID</label>
          <input
            type="text"
            value={uberConfig.store_id}
            onChange={(e) => setUberConfig({...uberConfig, store_id: e.target.value})}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            checked={uberConfig.is_enabled}
            onChange={(e) => setUberConfig({...uberConfig, is_enabled: e.target.checked})}
            className="mr-2"
          />
          <label>Enable Uber Eats Integration</label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            checked={uberConfig.auto_accept_orders}
            onChange={(e) => setUberConfig({...uberConfig, auto_accept_orders: e.target.checked})}
            className="mr-2"
          />
          <label>Auto-accept orders</label>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Default Prep Time (minutes)</label>
          <input
            type="number"
            value={uberConfig.default_prep_time_minutes}
            onChange={(e) => setUberConfig({...uberConfig, default_prep_time_minutes: parseInt(e.target.value)})}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <button
          onClick={handleSave}
          className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
}
```

---

## 🚀 Step 6: Deployment

### 6.1 Add Integration Service to Kubernetes

**File**: `infrastructure/kubernetes/integration-service-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: integration-service
  namespace: restaurant-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: integration-service
  template:
    metadata:
      labels:
        app: integration-service
    spec:
      containers:
      - name: integration-service
        image: shadrach85/integration-service:latest
        ports:
        - containerPort: 8015
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: restaurant-config
              key: DATABASE_URL
        - name: ORDER_SERVICE_URL
          value: "http://order-service:8002"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: integration-service
  namespace: restaurant-system
spec:
  selector:
    app: integration-service
  ports:
  - port: 8015
    targetPort: 8015
  type: ClusterIP
```

### 6.2 Update API Gateway Routes

**File**: `infrastructure/istio/virtualservices/api-gateway-vs.yaml`

Add integration service routes:

```yaml
- match:
    - uri:
        prefix: "/api/v1/integrations/"
  route:
    - destination:
        host: integration-service
        port:
          number: 8015

- match:
    - uri:
        prefix: "/api/v1/webhooks/"
  route:
    - destination:
        host: integration-service
        port:
          number: 8015
```

---

## 📝 Step 7: Configuration Checklist

### Required Information from Uber

- [ ] Client ID
- [ ] Client Secret
- [ ] Server Token
- [ ] Store ID
- [ ] Webhook Secret

### Database Changes

- [ ] Add UBER_EATS to ordertype enum
- [ ] Add external_order_id, external_source, external_metadata columns
- [ ] Create uber_eats_config table
- [ ] Create order_status_mapping table
- [ ] Create indexes

### Services

- [ ] Create integration-service
- [ ] Update order-service to handle UBER_EATS type
- [ ] Deploy to Kubernetes

### Frontend

- [ ] Update OrderCard component
- [ ] Add filter buttons to Chef Dashboard
- [ ] Create Integration Settings page in Admin panel
- [ ] Add Uber Eats icon/branding

---

## 🧪 Step 8: Testing

### 8.1 Sandbox Testing

Use Uber's sandbox environment for testing:

```bash
# Test webhook endpoint
curl -X POST https://restaurant.corpv3.com/api/v1/webhooks/uber-eats \
  -H "Content-Type: application/json" \
  -H "X-Uber-Signature: test_signature" \
  -d '{
    "event_type": "orders.notification",
    "order": {
      "id": "test_order_123",
      "store": {"id": "your_store_id"},
      "eater": {"first_name": "Test", "phone_number": "+1234567890"},
      "cart": {"items": []},
      "payment": {"charges": {"total": 2500}}
    }
  }'
```

### 8.2 Verify Order Appears in Chef Dashboard

1. Go to `https://restaurant.corpv3.com/chef/orders`
2. Look for order with Uber Eats icon (🚗)
3. Verify all details are correct

### 8.3 Test Status Updates

1. Mark order as "PREPARING" in dashboard
2. Verify Uber Eats API receives status update
3. Check Uber Eats dashboard for status change

---

## 🔐 Step 9: Security Best Practices

### 9.1 Encrypt Credentials

Never store API keys in plain text:

```python
from cryptography.fernet import Fernet

# Generate encryption key (store securely in Kubernetes secret)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt credentials before storing
encrypted_secret = cipher.encrypt(client_secret.encode())

# Decrypt when needed
decrypted_secret = cipher.decrypt(encrypted_secret).decode()
```

### 9.2 Webhook Signature Verification

Always verify webhook signatures to prevent spoofing.

### 9.3 Rate Limiting

Add rate limits to webhook endpoint to prevent abuse.

---

## 📊 Step 10: Monitoring & Analytics

### 10.1 Track Uber Eats Orders Separately

```sql
-- Daily Uber Eats orders
SELECT
  DATE(created_at) as date,
  COUNT(*) as uber_orders,
  SUM(total) as uber_revenue
FROM orders
WHERE external_source = 'UBER_EATS'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 10.2 Dashboard Metrics

Add to analytics dashboard:
- Uber Eats orders today
- Uber Eats revenue
- Average delivery time
- Most popular items on Uber Eats

---

## 🚀 Next Steps After Setup

### Phase 1: Basic Integration (Week 1-2)
1. Complete API setup
2. Create integration service
3. Handle webhook for new orders
4. Display in chef dashboard

### Phase 2: Status Sync (Week 3)
1. Implement bidirectional status sync
2. Add auto-accept option
3. Handle cancellations

### Phase 3: Advanced Features (Week 4+)
1. Menu sync (update Uber menu when you update yours)
2. Inventory sync (mark items out of stock)
3. Analytics dashboard
4. Multi-location support

---

## 📞 Getting Help

### Uber Eats Support
- **Documentation**: https://developer.uber.com/docs/eats
- **Support**: https://developer.uber.com/support
- **Community**: https://community.uber.com/

### Testing Resources
- **Sandbox Environment**: https://api-sandbox.uber.com
- **Postman Collection**: Available in Uber Developer Portal

---

## ✅ Summary

Once complete, you'll have:
- ✅ Uber Eats orders appear automatically in chef dashboard
- ✅ Restaurant admin sees all order types in one place
- ✅ Status updates sync between systems
- ✅ Unified kitchen workflow
- ✅ Comprehensive analytics across all channels

---

**Next Action**: Share your Uber API credentials (Client ID, Secret, Token, Store ID) and I'll help you implement the integration service!

**Last Updated**: 2026-01-13
**Version**: 1.0.0
