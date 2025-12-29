# Point of Sale (POS) System Architecture

## Executive Summary

This document outlines the architecture for adding a Point of Sale (POS) system to the existing Restaurant Management SaaS platform. The POS will support:
- **Restaurants**: Full restaurant features + POS for counter orders
- **Retail Stores**: Supermarkets, off-license shops, convenience stores (POS-only mode)

## Business Model

### Subscription Tiers

1. **Restaurant Full Stack** ($99/month)
   - Complete restaurant management (tables, kitchen, QR ordering, analytics)
   - Integrated POS for counter/takeaway orders
   - Staff management for waiters, chefs, cashiers

2. **Retail POS Only** ($49/month)
   - POS terminal for retail sales
   - Inventory management
   - Sales analytics and reporting
   - No table management, no kitchen display, no QR ordering

3. **Enterprise** (Custom pricing)
   - Multiple locations
   - Centralized inventory across stores
   - Advanced analytics and forecasting

## System Architecture

### New Microservices Required

```
Current Services:
├── auth-service (8001)
├── restaurant-service (8003)
├── customer-service (8004)
├── order-service (8002)
└── api-gateway (8000)

New Services Needed:
├── pos-service (8005)          # Core POS operations
├── inventory-service (8006)    # Stock management
├── payment-service (8007)      # Payment processing
├── receipt-service (8008)      # Receipt generation & printing
└── analytics-service (8009)    # Business intelligence
```

### Infrastructure Requirements

#### Kubernetes Pods/Deployments

```yaml
Additional Pods Needed:

1. pos-service
   - Replicas: 2-3 (for high availability)
   - Resources:
     - CPU: 500m-1000m
     - Memory: 512Mi-1Gi
   - Purpose: Handle POS transactions, cart management, checkout

2. inventory-service
   - Replicas: 2
   - Resources:
     - CPU: 300m-500m
     - Memory: 512Mi-1Gi
   - Purpose: Stock tracking, reorder alerts, supplier management

3. payment-service
   - Replicas: 3 (critical service)
   - Resources:
     - CPU: 500m-1000m
     - Memory: 512Mi-1Gi
   - Purpose: Payment gateway integration (Stripe, PayPal, Square)

4. receipt-service
   - Replicas: 2
   - Resources:
     - CPU: 200m-300m
     - Memory: 256Mi-512Mi
   - Purpose: Receipt generation, thermal printer integration

5. analytics-service
   - Replicas: 2
   - Resources:
     - CPU: 1000m-2000m
     - Memory: 1Gi-2Gi
   - Purpose: Real-time analytics, ML predictions, reports

6. redis-cache (NEW)
   - Replicas: 1 (with persistence)
   - Resources:
     - CPU: 200m-500m
     - Memory: 512Mi-1Gi
   - Purpose: Session management, cart caching, real-time inventory

7. elasticsearch (OPTIONAL for large deployments)
   - Replicas: 3 (cluster)
   - Resources:
     - CPU: 1000m-2000m per node
     - Memory: 2Gi-4Gi per node
   - Purpose: Product search, analytics, audit logs
```

#### Total Additional Infrastructure

**Minimum Setup (Small-Medium Business):**
- 5 new microservices = 12 additional pods (with replicas)
- 1 Redis cache = 1 pod
- Total: ~13 new pods
- Additional CPU: 4-8 cores
- Additional Memory: 6-12 GB
- Additional Storage: 50-100 GB (for receipts, images, analytics)

**Enterprise Setup (High Traffic):**
- Same services with more replicas = 20-25 pods
- Elasticsearch cluster = 3 pods
- Total: ~23-28 new pods
- Additional CPU: 15-25 cores
- Additional Memory: 20-40 GB
- Additional Storage: 500GB-1TB

## Database Schema

### New Tables Required

```sql
-- POS Service Database (pos_db)

-- Business locations (for multi-store support)
CREATE TABLE business_locations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'restaurant', 'retail', 'both'
    address TEXT,
    phone VARCHAR(20),
    tax_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- POS Terminals/Registers
CREATE TABLE pos_terminals (
    id UUID PRIMARY KEY,
    location_id UUID REFERENCES business_locations(id),
    terminal_number VARCHAR(20) UNIQUE NOT NULL,
    terminal_name VARCHAR(100),
    device_id VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- POS Transactions
CREATE TABLE pos_transactions (
    id UUID PRIMARY KEY,
    terminal_id UUID REFERENCES pos_terminals(id),
    location_id UUID REFERENCES business_locations(id),
    transaction_number VARCHAR(50) UNIQUE NOT NULL,

    -- Customer info (optional for retail)
    customer_id UUID,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),

    -- Transaction details
    subtotal DECIMAL(10, 2) NOT NULL,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,

    -- Payment
    payment_method VARCHAR(50), -- 'cash', 'card', 'mobile', 'split'
    payment_status VARCHAR(20), -- 'pending', 'completed', 'failed', 'refunded'

    -- Metadata
    cashier_id UUID,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Transaction Items
CREATE TABLE transaction_items (
    id UUID PRIMARY KEY,
    transaction_id UUID REFERENCES pos_transactions(id),
    product_id UUID,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    quantity DECIMAL(10, 3) NOT NULL, -- Support for weight-based items
    unit_price DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    subtotal DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inventory Database (inventory_db)

-- Product Categories
CREATE TABLE product_categories (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES product_categories(id),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products/Items
CREATE TABLE products (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    location_id UUID REFERENCES business_locations(id),

    -- Product info
    sku VARCHAR(100) UNIQUE NOT NULL,
    barcode VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES product_categories(id),

    -- Pricing
    cost_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) DEFAULT 0,

    -- Inventory
    current_stock DECIMAL(10, 3) DEFAULT 0,
    min_stock DECIMAL(10, 3) DEFAULT 0,
    max_stock DECIMAL(10, 3),
    reorder_point DECIMAL(10, 3),
    unit_of_measure VARCHAR(20), -- 'piece', 'kg', 'liter', 'box'

    -- Tracking
    track_inventory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,

    -- Image
    image_url TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stock Movements
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    location_id UUID REFERENCES business_locations(id),

    movement_type VARCHAR(50), -- 'sale', 'purchase', 'adjustment', 'return', 'transfer'
    quantity DECIMAL(10, 3) NOT NULL,
    reference_id UUID, -- Transaction ID or Purchase Order ID

    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Suppliers
CREATE TABLE suppliers (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Purchase Orders
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    location_id UUID REFERENCES business_locations(id),
    supplier_id UUID REFERENCES suppliers(id),

    po_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20), -- 'draft', 'sent', 'received', 'cancelled'

    subtotal DECIMAL(10, 2),
    tax DECIMAL(10, 2),
    total DECIMAL(10, 2),

    notes TEXT,
    ordered_date DATE,
    expected_date DATE,
    received_date DATE,

    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payment Database (payment_db)

-- Payment Transactions
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    transaction_id UUID, -- Reference to pos_transaction

    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),

    -- Gateway info
    gateway_provider VARCHAR(50), -- 'stripe', 'square', 'paypal'
    gateway_transaction_id VARCHAR(255),
    gateway_response TEXT,

    status VARCHAR(20), -- 'pending', 'completed', 'failed', 'refunded'

    -- Card details (tokenized)
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20),

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Receipts Database (receipt_db)

-- Generated Receipts
CREATE TABLE receipts (
    id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    location_id UUID,

    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    receipt_type VARCHAR(20), -- 'sale', 'refund', 'void'

    -- Receipt data (JSON for flexibility)
    receipt_data JSONB NOT NULL,

    -- Printing
    print_count INT DEFAULT 0,
    last_printed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### POS Service (8005)

```
POST   /api/v1/pos/terminals/register          # Register new POS terminal
GET    /api/v1/pos/terminals/{id}              # Get terminal info
POST   /api/v1/pos/transactions/start          # Start new transaction
POST   /api/v1/pos/transactions/{id}/add-item  # Add item to cart
DELETE /api/v1/pos/transactions/{id}/item/{itemId}  # Remove item
POST   /api/v1/pos/transactions/{id}/checkout  # Complete checkout
POST   /api/v1/pos/transactions/{id}/void      # Void transaction
GET    /api/v1/pos/transactions/{id}           # Get transaction details
GET    /api/v1/pos/transactions                # List transactions (with filters)
POST   /api/v1/pos/transactions/{id}/refund    # Process refund
```

### Inventory Service (8006)

```
# Products
POST   /api/v1/inventory/products              # Create product
GET    /api/v1/inventory/products              # List products
GET    /api/v1/inventory/products/{id}         # Get product
PUT    /api/v1/inventory/products/{id}         # Update product
DELETE /api/v1/inventory/products/{id}         # Delete product
GET    /api/v1/inventory/products/search       # Search by name/SKU/barcode
POST   /api/v1/inventory/products/bulk-import  # Import from CSV/Excel

# Stock Management
GET    /api/v1/inventory/stock/levels          # Get stock levels
POST   /api/v1/inventory/stock/adjust          # Manual stock adjustment
GET    /api/v1/inventory/stock/movements       # Stock movement history
GET    /api/v1/inventory/stock/low-stock       # Products below reorder point

# Suppliers & Purchase Orders
POST   /api/v1/inventory/suppliers             # Create supplier
GET    /api/v1/inventory/suppliers             # List suppliers
POST   /api/v1/inventory/purchase-orders       # Create PO
PUT    /api/v1/inventory/purchase-orders/{id}/receive  # Mark as received
```

### Payment Service (8007)

```
POST   /api/v1/payments/process                # Process payment
POST   /api/v1/payments/refund                 # Process refund
GET    /api/v1/payments/{id}                   # Get payment status
POST   /api/v1/payments/split                  # Split payment (cash + card)
GET    /api/v1/payments/methods                # Get available payment methods
```

### Receipt Service (8008)

```
POST   /api/v1/receipts/generate               # Generate receipt
GET    /api/v1/receipts/{id}                   # Get receipt
POST   /api/v1/receipts/{id}/print             # Print receipt
POST   /api/v1/receipts/{id}/email             # Email receipt
GET    /api/v1/receipts/{id}/pdf               # Download PDF
```

### Analytics Service (8009)

```
GET    /api/v1/analytics/sales/daily           # Daily sales report
GET    /api/v1/analytics/sales/summary         # Sales summary
GET    /api/v1/analytics/products/top-selling  # Best selling products
GET    /api/v1/analytics/products/slow-moving  # Slow moving items
GET    /api/v1/analytics/inventory/value       # Inventory valuation
GET    /api/v1/analytics/cashier/performance   # Cashier performance
GET    /api/v1/analytics/forecast              # ML-based sales forecast
```

## Frontend Components

### New Pages Required

```
frontend/src/pages/
├── POS/
│   ├── POSTerminal.jsx              # Main POS interface (cashier view)
│   ├── QuickSale.jsx                # Quick sale for retail
│   ├── TransactionHistory.jsx       # View past transactions
│   ├── EndOfDay.jsx                 # Cash drawer reconciliation
│   └── RefundPage.jsx               # Process refunds
│
├── Inventory/
│   ├── ProductList.jsx              # Product catalog
│   ├── ProductForm.jsx              # Add/Edit product
│   ├── StockAdjustment.jsx          # Manual stock adjustments
│   ├── PurchaseOrders.jsx           # PO management
│   ├── LowStockAlert.jsx            # Reorder alerts
│   └── BulkImport.jsx               # CSV/Excel import
│
├── Payment/
│   ├── PaymentMethods.jsx           # Configure payment gateways
│   └── PaymentHistory.jsx           # Transaction logs
│
└── Analytics/
    ├── SalesDashboard.jsx           # Sales overview
    ├── InventoryReports.jsx         # Stock reports
    ├── FinancialReports.jsx         # P&L, margins
    └── ForecastingDashboard.jsx     # ML predictions
```

### POS Terminal UI Features

**Main Screen Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Logo        Terminal #1        Cashier: John    [X] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Product Search:  [_________________] [Scan]       │
│                                                     │
│  Categories: [All] [Food] [Drinks] [Retail] ...    │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Current Cart                                │   │
│  │ ─────────────────────────────────────────── │   │
│  │ 1. Coca Cola 500ml      x2    $4.00        │   │
│  │ 2. Bread                x1    $2.50        │   │
│  │ 3. Milk 1L              x1    $3.99        │   │
│  │                                             │   │
│  │                         Subtotal:  $10.49   │   │
│  │                         Tax (10%): $1.05    │   │
│  │                         ───────────────────  │   │
│  │                         TOTAL:     $11.54   │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [Clear Cart]  [Hold]  [Recall]     [CHECKOUT] ►   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Hardware Integration

### Supported Hardware

1. **Barcode Scanners**
   - USB barcode scanners (HID mode)
   - Wireless Bluetooth scanners
   - Mobile camera-based scanning

2. **Receipt Printers**
   - Thermal printers (ESC/POS protocol)
   - Network printers (IP-based)
   - Bluetooth printers for mobile POS

3. **Cash Drawers**
   - Connected via receipt printer (RJ11/RJ12)
   - Automatic opening on cash transactions

4. **Card Readers**
   - Stripe Terminal
   - Square Reader
   - PayPal Zettle
   - Generic EMV readers

5. **Customer Display (Optional)**
   - Secondary screen showing total
   - Pole displays

6. **Tablets/Touch Screens**
   - iPad/Android tablets
   - Windows touch-screen PCs
   - Dedicated POS terminals

## Deployment Strategy

### Phase 1: Core POS (Month 1-2)
- Deploy pos-service, inventory-service
- Basic product management
- Simple checkout flow
- Cash and manual card entry

### Phase 2: Payment Integration (Month 3)
- Deploy payment-service
- Integrate Stripe/Square
- Digital payment methods
- Receipt generation

### Phase 3: Advanced Inventory (Month 4)
- Stock tracking and alerts
- Purchase order management
- Multi-location stock transfer

### Phase 4: Analytics & Intelligence (Month 5-6)
- Deploy analytics-service
- Real-time dashboards
- ML-based forecasting
- Business intelligence reports

## Cost Estimation

### Infrastructure Costs (Monthly)

**Small Business (1-3 locations):**
- Additional Kubernetes nodes: $150-250
- Database storage: $50-100
- Redis cache: $30-50
- Load balancer: $20-30
- **Total: ~$250-430/month**

**Medium Business (4-10 locations):**
- Additional Kubernetes nodes: $400-600
- Database storage: $150-250
- Redis cluster: $100-150
- Elasticsearch (optional): $200-300
- **Total: ~$850-1,300/month**

**Enterprise (10+ locations):**
- Dedicated cluster: $1,500-3,000
- High-availability databases: $500-1,000
- Advanced caching & search: $500-800
- **Total: ~$2,500-4,800/month**

### Development Costs

**Estimated Timeline: 5-6 months**

1. Backend development: 3 months
2. Frontend development: 2 months
3. Hardware integration: 1 month
4. Testing & deployment: 1 month

**Team Required:**
- 2 Backend developers
- 2 Frontend developers
- 1 DevOps engineer
- 1 QA engineer

## Security Considerations

### PCI DSS Compliance

1. **Never store card data**
   - Use tokenization via Stripe/Square
   - Only store last 4 digits for reference

2. **Encryption**
   - TLS 1.3 for all API communication
   - Encrypt sensitive data at rest
   - Secure key management (HashiCorp Vault)

3. **Access Control**
   - Role-based permissions (cashier, manager, admin)
   - Audit logs for all transactions
   - Session timeouts for POS terminals

4. **Network Security**
   - Firewall rules for POS terminals
   - VPN for remote locations
   - Intrusion detection

## Multi-Tenancy & Isolation

### Tenant Separation

```python
# Each tenant gets:
- Dedicated database schema (logical separation)
- Isolated product catalogs
- Separate payment accounts
- Independent analytics

# Shared infrastructure:
- Kubernetes pods (with resource limits)
- Redis cache (with key prefixes)
- Load balancers
- Gateway services
```

### Resource Limits per Tenant

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-{tenant_id}-quota
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    persistentvolumeclaims: "10"
```

## Offline Mode Support

### Sync Architecture

**For Remote/Rural Locations:**

1. **Local SQLite Cache**
   - Store product catalog offline
   - Queue transactions locally
   - Sync when connection restored

2. **Progressive Web App (PWA)**
   - Service workers for offline caching
   - Background sync API
   - IndexedDB for local storage

3. **Conflict Resolution**
   - Last-write-wins for product updates
   - Timestamp-based merging
   - Manual review for stock discrepancies

## Monitoring & Alerts

### Key Metrics to Track

```
# Business Metrics
- Transactions per hour
- Average transaction value
- Payment success rate
- Top-selling products
- Stock-out frequency

# Technical Metrics
- API response time (<100ms)
- Database query performance
- Cache hit rate (>90%)
- Service uptime (99.9%)
- Error rate (<0.1%)

# Alerts
- Low stock warnings
- Failed payment notifications
- System downtime alerts
- Unusual transaction patterns (fraud)
```

## Migration Path

### For Existing Restaurant Customers

1. **Auto-provision POS terminal**
   - Create default terminal for each restaurant
   - Sync menu items to product catalog
   - Enable counter orders through POS

2. **Gradual rollout**
   - Beta testing with 5-10 customers
   - Collect feedback and iterate
   - Full rollout after validation

3. **Training & Support**
   - Video tutorials
   - Live onboarding sessions
   - 24/7 chat support

## Conclusion

This POS system will transform your platform into a comprehensive business management solution suitable for both hospitality and retail sectors. The modular architecture allows you to:

1. **Offer tiered pricing** based on feature access
2. **Scale independently** - retail stores don't pay for restaurant features
3. **Expand market** - target supermarkets, pharmacies, liquor stores, etc.
4. **Cross-sell opportunities** - retail customers might later add online ordering

**Next Steps:**
1. Review and approve this architecture
2. Set up development environment for new services
3. Create detailed sprint plans
4. Begin with Phase 1 implementation
