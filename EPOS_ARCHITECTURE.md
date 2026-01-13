# EPOS (Electronic Point of Sale) System Architecture
## SaaS Restaurant Management with Offline-First Capability

---

## Executive Summary

This document outlines a comprehensive **EPOS system** integrated with the existing Restaurant Management SaaS platform. The system is designed as a **hybrid cloud/offline solution** that works seamlessly with or without internet connectivity, supports multiple operating systems (Windows, Linux, Android), and integrates with standard POS hardware including barcode scanners, receipt printers, and cash drawers.

### Key Requirements Addressed

✅ **Dual Mode Operation**: Full restaurant management + EPOS, or EPOS-only mode
✅ **Offline-First Architecture**: Works without internet, syncs when available
✅ **Multi-OS Support**: Windows, Linux (Ubuntu/Debian), Android tablets
✅ **Hardware Integration**: Barcode scanners, thermal printers, cash drawers, card readers
✅ **SaaS Model**: Multi-tenant architecture with subscription-based pricing
✅ **Real-time Sync**: Background synchronization with conflict resolution

---

## Technology Stack

### Backend Services (Cloud)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Core Services** | FastAPI (Python 3.11+) | Existing microservices + new EPOS services |
| **Database** | PostgreSQL 15+ | Persistent data storage |
| **Cache Layer** | Redis 7+ | Session management, real-time data |
| **Message Queue** | RabbitMQ | Async task processing, sync queue |
| **API Gateway** | FastAPI + Istio | Request routing, auth, rate limiting |
| **Search Engine** | Elasticsearch 8+ | Product search, analytics |
| **Object Storage** | MinIO / S3 | Receipts, product images, backups |
| **Orchestration** | Kubernetes (Kind/K3s) | Container management |
| **Service Mesh** | Istio | Traffic management, security |

### EPOS Client Applications (Edge/Offline)

| Platform | Technology Stack | Justification |
|----------|-----------------|---------------|
| **Windows Desktop** | Electron + React + TypeScript | Native Windows experience, hardware support |
| **Linux Desktop** | Electron + React + TypeScript | Same codebase as Windows, cross-platform |
| **Android Tablet** | React Native + TypeScript | Touch-optimized, mobile hardware support |
| **Web (Optional)** | React PWA + TypeScript | Browser-based backup, limited offline |

### Local Database (Offline Storage)

| Platform | Database | Sync Strategy |
|----------|---------|---------------|
| **Windows/Linux** | SQLite 3.40+ | Embedded database, file-based |
| **Android** | SQLite (via React Native SQLite) | Native Android storage |
| **Web** | IndexedDB + Dexie.js | Browser storage API |

### Synchronization Engine

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Sync Protocol** | WebSocket (Socket.io) + REST | Real-time bidirectional sync |
| **Conflict Resolution** | CRDT (Conflict-free Replicated Data Types) | Automatic merge strategy |
| **Offline Queue** | IndexedDB / SQLite | Store operations while offline |
| **Background Sync** | Service Workers (Web), Background Services (Desktop/Mobile) | Automatic sync when online |

### Hardware Integration Layer

| Hardware Type | Integration Method | Libraries/SDKs |
|--------------|-------------------|----------------|
| **Barcode Scanner** | HID USB / Bluetooth SPP | node-hid, Web Bluetooth API |
| **Thermal Printer** | ESC/POS protocol | node-thermal-printer, escpos-buffer |
| **Cash Drawer** | RJ11/RJ12 via printer | Triggered by printer commands |
| **Card Reader** | Stripe Terminal SDK / Square SDK | stripe-terminal-js, square-web-sdk |
| **Touch Screen** | Native touch events | React touch handlers |
| **Customer Display** | Serial/USB display | node-serialport |

### Payment Gateway Integration

| Provider | SDK/API | Use Case |
|----------|---------|----------|
| **Stripe Terminal** | stripe-terminal-js | Card payments (EMV, NFC) |
| **Square POS** | square-pos-sdk | Integrated payments |
| **PayPal Zettle** | zettle-sdk | Mobile card reader |
| **Cash** | Manual entry | No integration needed |
| **Mobile Wallets** | Apple Pay / Google Pay | NFC tap-to-pay |

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLOUD INFRASTRUCTURE                             │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Kubernetes Cluster (K8s)                      │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ API Gateway  │  │ Auth Service │  │ Restaurant   │          │   │
│  │  │  (Istio VS)  │  │   (JWT)      │  │   Service    │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ EPOS Service │  │ Inventory    │  │ Payment      │          │   │
│  │  │  (NEW)       │  │ Service(NEW) │  │ Service(NEW) │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ Sync Service │  │ Receipt      │  │ Analytics    │          │   │
│  │  │  (NEW)       │  │ Service(NEW) │  │ Service      │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                                    │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ PostgreSQL   │  │ Redis Cluster│  │ RabbitMQ     │          │   │
│  │  │ (Primary DB) │  │ (Cache/Sync) │  │ (Msg Queue)  │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐                             │   │
│  │  │ Elasticsearch│  │ MinIO (S3)   │                             │   │
│  │  │ (Search)     │  │ (Files)      │                             │   │
│  │  └──────────────┘  └──────────────┘                             │   │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
                        WebSocket + REST API (HTTPS)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EDGE / CLIENT LAYER                               │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │  Windows EPOS Client │  │  Linux EPOS Client   │                     │
│  │  (Electron + React)  │  │  (Electron + React)  │                     │
│  │                      │  │                      │                     │
│  │  ┌────────────────┐ │  │  ┌────────────────┐ │                     │
│  │  │ Local SQLite   │ │  │  │ Local SQLite   │ │                     │
│  │  │ (Offline DB)   │ │  │  │ (Offline DB)   │ │                     │
│  │  └────────────────┘ │  │  └────────────────┘ │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │ Android EPOS Client  │  │  Web PWA (Optional)  │                     │
│  │ (React Native)       │  │  (React + IndexedDB) │                     │
│  │                      │  │                      │                     │
│  │  ┌────────────────┐ │  │  ┌────────────────┐ │                     │
│  │  │ SQLite DB      │ │  │  │ IndexedDB      │ │                     │
│  │  │ (Offline)      │ │  │  │ (Offline)      │ │                     │
│  │  └────────────────┘ │  │  └────────────────┘ │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Hardware Integration Layer                    │   │
│  │                                                                   │   │
│  │  [Barcode Scanner] [Thermal Printer] [Cash Drawer]              │   │
│  │  [Card Reader]     [Customer Display] [Touch Screen]            │   │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Dual Mode Architecture

### Mode 1: Full Restaurant Management + EPOS

**Target Users**: Restaurants, cafes, bars, food trucks

**Features Enabled**:
- ✅ Table management & QR ordering
- ✅ Kitchen display system (KDS)
- ✅ Staff management (waiters, chefs, cashiers)
- ✅ EPOS for counter/takeaway orders
- ✅ Inventory management
- ✅ Menu management with images
- ✅ Customer loyalty programs
- ✅ Analytics & forecasting
- ✅ Multi-location support

**Pricing**: $99/month per location

### Mode 2: EPOS Only

**Target Users**: Retail stores, supermarkets, pharmacies, liquor stores, convenience stores

**Features Enabled**:
- ✅ EPOS terminal for sales
- ✅ Product catalog management
- ✅ Barcode scanning
- ✅ Inventory tracking
- ✅ Sales analytics
- ✅ Receipt printing
- ✅ Payment processing

**Features Disabled**:
- ❌ Table management
- ❌ Kitchen display
- ❌ QR ordering
- ❌ Menu categories (replaced with product categories)

**Pricing**: $49/month per location

---

## Offline-First Architecture

### Design Principles

1. **Local-First**: All operations work on local database first
2. **Eventual Consistency**: Sync with cloud when available
3. **Conflict Resolution**: Automatic merge with timestamp priority
4. **Queue-Based Sync**: Failed operations retry automatically
5. **Delta Sync**: Only sync changes, not full dataset

### Offline Capabilities

| Operation | Offline Support | Notes |
|-----------|----------------|-------|
| View products | ✅ Full | Cached locally |
| Add to cart | ✅ Full | Stored in local DB |
| Complete sale | ✅ Full | Queued for sync |
| Print receipt | ✅ Full | Local printer access |
| Inventory check | ✅ Limited | Last synced values |
| Product search | ✅ Full | Local search index |
| Sales reports | ✅ Limited | Local data only |
| Payment (card) | ⚠️ Requires internet | Stripe/Square needs connection |
| Payment (cash) | ✅ Full | No internet needed |
| Cloud backup | ❌ No | Requires internet |

### Sync Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Synchronization Flow                        │
└─────────────────────────────────────────────────────────────────┘

1. OFFLINE MODE
   ┌────────────────┐
   │ User Action    │ → Barcode scan, add to cart, checkout
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Local SQLite   │ → Save transaction with status: "pending_sync"
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Sync Queue     │ → Add to outbound sync queue
   └────────────────┘

2. INTERNET RESTORED
   ┌────────────────┐
   │ Network Check  │ → Detect internet connection
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Background Sync│ → WebSocket connection established
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Sync Engine    │ → Process sync queue (FIFO)
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Cloud API      │ → POST transactions to cloud
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Response       │ → Update local DB with cloud IDs
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Conflict?      │ → Check for conflicts (e.g., inventory)
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Resolve        │ → Apply merge strategy
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Confirm Sync   │ → Mark as "synced" in local DB
   └────────────────┘

3. CONTINUOUS SYNC (ONLINE MODE)
   ┌────────────────┐
   │ WebSocket Open │ → Real-time bidirectional sync
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Cloud Changes  │ → Receive product updates, price changes
   └────────────────┘
           ↓
   ┌────────────────┐
   │ Update Local   │ → Merge into local SQLite
   └────────────────┘
```

### Conflict Resolution Rules

| Conflict Type | Resolution Strategy |
|--------------|---------------------|
| **Product Price Change** | Cloud wins (always use latest price) |
| **Inventory Adjustment** | Sum all changes (additive) |
| **Product Deleted** | Cloud wins (mark as inactive locally) |
| **Transaction Duplicate** | Deduplicate by transaction_id |
| **User Permission Change** | Cloud wins (security first) |
| **Settings Update** | Last-write-wins with timestamp |

### Sync Data Model

```sql
-- Local Sync Queue Table (SQLite)
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50) NOT NULL,  -- 'transaction', 'product', 'inventory'
    entity_id VARCHAR(36) NOT NULL,
    operation VARCHAR(20) NOT NULL,     -- 'create', 'update', 'delete'
    payload TEXT NOT NULL,              -- JSON data
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'syncing', 'synced', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    error_message TEXT
);

-- Sync Status Tracking
CREATE TABLE sync_metadata (
    id INTEGER PRIMARY KEY,
    last_full_sync TIMESTAMP,
    last_incremental_sync TIMESTAMP,
    pending_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    cloud_connection_status VARCHAR(20) -- 'online', 'offline', 'syncing'
);
```

---

## Admin Dashboard Configuration

### Restaurant Admin Settings

```
┌─────────────────────────────────────────────────────────────┐
│                    EPOS Configuration Panel                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Operation Mode                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ○ Full Restaurant Management + EPOS                        │
│     Includes: Tables, Kitchen, QR Ordering, EPOS            │
│                                                              │
│  ○ EPOS Only (Retail Mode)                                  │
│     Includes: Product Sales, Inventory, Analytics           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Synchronization Settings                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Sync Mode:                                                  │
│  ☑ Automatic Sync (Recommended)                             │
│    Syncs automatically when internet is available           │
│                                                              │
│  ☐ Manual Sync Only                                         │
│    Requires manual sync button click                        │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Sync Frequency: [Every 5 minutes ▼]                        │
│                                                              │
│  Sync During: ☑ Business Hours  ☑ After Hours              │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Current Status: 🟢 Connected | Last Sync: 2 mins ago       │
│                                                              │
│  Pending Operations: 3 transactions, 1 inventory update     │
│                                                              │
│  [Sync Now] [View Sync Log] [Clear Failed Items]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Offline Mode Settings                                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ☑ Allow Offline Sales                                      │
│    Continue selling even without internet                   │
│                                                              │
│  ☑ Cache Product Images (requires 500MB+ storage)          │
│                                                              │
│  ☐ Require Internet for Card Payments                      │
│    Block card payments when offline (cash only)             │
│                                                              │
│  ☑ Show Offline Indicator                                  │
│    Display banner when not connected                        │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Storage Used: 340MB / 2GB                                  │
│  Cached Products: 1,247 items                               │
│  Pending Transactions: 3                                    │
│                                                              │
│  [Clear Cache] [Export Offline Data]                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Hardware Configuration                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Barcode Scanner:                                           │
│  Connected: ✅ Honeywell Voyager 1200g                      │
│  [Configure] [Test Scan]                                    │
│                                                              │
│  Receipt Printer:                                           │
│  Connected: ✅ Epson TM-T20III (IP: 192.168.1.50)          │
│  [Configure] [Print Test]                                   │
│                                                              │
│  Cash Drawer:                                               │
│  Connected: ✅ via Printer (RJ12)                           │
│  [Configure] [Test Open]                                    │
│                                                              │
│  Card Reader:                                               │
│  Connected: ✅ Stripe Terminal S700                         │
│  [Configure] [Test Payment]                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-OS Support Strategy

### Windows Desktop Application

**Technology**: Electron 28+ + React 18+ + TypeScript 5+

**Features**:
- Native Windows installer (.exe, .msi)
- System tray integration
- Auto-update mechanism
- USB device detection (barcode scanners, printers)
- Windows printer API integration
- File system access for local database
- Offline notifications

**Distribution**:
- Direct download from dashboard
- Windows Store (optional)
- Auto-update via Squirrel.Windows

**System Requirements**:
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 500MB disk space
- USB 2.0+ ports

### Linux Desktop Application

**Technology**: Electron 28+ + React 18+ + TypeScript 5+

**Supported Distros**:
- Ubuntu 20.04+
- Debian 11+
- Fedora 35+
- Linux Mint 20+

**Features**:
- AppImage (universal format)
- .deb package (Debian/Ubuntu)
- .rpm package (Fedora/RHEL)
- CUPS printer integration
- udev rules for hardware access
- SystemD service for background sync

**Distribution**:
- Direct download from dashboard
- Snap Store
- Flathub (optional)

**System Requirements**:
- Linux kernel 5.4+
- 4GB RAM minimum
- 500MB disk space
- USB 2.0+ ports

### Android Tablet Application

**Technology**: React Native 0.73+ + TypeScript 5+

**Features**:
- Touch-optimized UI (finger-friendly buttons)
- Portrait & landscape mode support
- Bluetooth barcode scanner pairing
- Mobile printer support (Bluetooth/WiFi)
- Cash drawer via Bluetooth relay
- Stripe Terminal Mobile SDK
- Background sync service
- Offline-first architecture

**Distribution**:
- Google Play Store
- Direct APK download (sideload)

**System Requirements**:
- Android 9.0 (Pie) or higher
- 3GB RAM minimum
- 1GB storage
- Bluetooth 4.0+
- Camera (for barcode scanning)

**Supported Devices**:
- Samsung Galaxy Tab A/S series
- Lenovo Tab M/P series
- Generic Android tablets (9-13 inches)

### Web PWA (Progressive Web App) - Optional

**Technology**: React 18+ + TypeScript + Service Workers

**Features**:
- Install as desktop app (Chrome, Edge)
- Offline mode via Service Workers
- IndexedDB for local storage
- Limited hardware support (browser limitations)
- Best for backup/secondary terminal

**Limitations**:
- ⚠️ Limited USB device access (WebUSB API)
- ⚠️ Bluetooth support varies by browser
- ⚠️ Printer access via WebUSB or Cloud Print
- ⚠️ Less reliable offline mode

**Use Case**: Emergency backup terminal, management view

---

## Hardware Integration

### Barcode Scanner Integration

```typescript
// Unified Barcode Scanner API (Cross-Platform)

interface BarcodeScanner {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  onScan(callback: (barcode: string, type: string) => void): void;
}

// Windows/Linux: USB HID Scanner
class USBBarcodeScanner implements BarcodeScanner {
  private device: HID.HID;

  async connect() {
    // node-hid library
    const devices = HID.devices();
    this.device = new HID.HID(vendorId, productId);
  }

  onScan(callback) {
    this.device.on('data', (data) => {
      const barcode = this.parseHIDData(data);
      callback(barcode, 'EAN13');
    });
  }
}

// Android: Camera Scanner
class CameraBarcodeScanner implements BarcodeScanner {
  async connect() {
    // Request camera permission
    // Initialize ML Kit Barcode Scanner
  }

  onScan(callback) {
    // Process camera frames
    // Detect barcode using ML Kit
    // Return scanned code
  }
}

// Android: Bluetooth Scanner
class BluetoothBarcodeScanner implements BarcodeScanner {
  private device: BluetoothDevice;

  async connect() {
    // React Native Bluetooth Classic
    this.device = await BluetoothSerial.connect(address);
  }

  onScan(callback) {
    this.device.on('data', (data) => {
      callback(data.toString(), 'EAN13');
    });
  }
}
```

### Thermal Printer Integration

```typescript
// Unified Printer API (ESC/POS Protocol)

interface ThermalPrinter {
  connect(): Promise<void>;
  print(receipt: Receipt): Promise<void>;
  openCashDrawer(): Promise<void>;
}

// Windows/Linux: Network Printer
class NetworkPrinter implements ThermalPrinter {
  private socket: net.Socket;

  async connect() {
    this.socket = net.connect({
      host: '192.168.1.50',
      port: 9100  // ESC/POS port
    });
  }

  async print(receipt: Receipt) {
    const escpos = require('escpos-buffer');
    const buffer = escpos()
      .text(receipt.header)
      .text('----------------------------')
      .table(receipt.items)
      .text(`TOTAL: $${receipt.total}`)
      .cut()
      .encode();

    this.socket.write(buffer);
  }

  async openCashDrawer() {
    // ESC/POS cash drawer kick command
    const kickCommand = Buffer.from([0x1B, 0x70, 0x00, 0x19, 0xFA]);
    this.socket.write(kickCommand);
  }
}

// Android: Bluetooth Printer
class BluetoothPrinter implements ThermalPrinter {
  private device: BluetoothDevice;

  async connect() {
    this.device = await BluetoothManager.connect(address);
  }

  async print(receipt: Receipt) {
    // Use React Native Bluetooth Serial
    // Send ESC/POS commands via Bluetooth
  }
}
```

### Card Reader Integration

```typescript
// Payment Terminal Integration

interface CardReader {
  initialize(): Promise<void>;
  processPayment(amount: number): Promise<PaymentResult>;
  cancelPayment(): Promise<void>;
}

// Stripe Terminal
class StripeTerminal implements CardReader {
  private terminal: StripeTerminalSDK;

  async initialize() {
    this.terminal = await StripeTerminal.create({
      onUnexpectedReaderDisconnect: () => {
        // Handle disconnect
      }
    });
  }

  async processPayment(amount: number) {
    const paymentIntent = await createPaymentIntent(amount);
    const result = await this.terminal.collectPaymentMethod(paymentIntent);
    const confirmed = await this.terminal.processPayment(result);
    return confirmed;
  }
}

// Square Terminal
class SquareTerminal implements CardReader {
  private api: SquareSDK;

  async initialize() {
    this.api = new SquareSDK({
      accessToken: process.env.SQUARE_ACCESS_TOKEN
    });
  }

  async processPayment(amount: number) {
    const checkout = await this.api.terminal.createTerminalCheckout({
      amount: { amount, currency: 'USD' },
      device_id: 'device_xxx'
    });
    return checkout;
  }
}
```

---

## Database Schema for EPOS

### Local SQLite Schema (Client-Side)

```sql
-- Terminal Configuration
CREATE TABLE terminal_config (
    id INTEGER PRIMARY KEY,
    terminal_id TEXT UNIQUE NOT NULL,
    location_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    terminal_name TEXT,
    device_info TEXT,  -- JSON: OS, version, hardware
    sync_enabled BOOLEAN DEFAULT 1,
    sync_frequency_minutes INTEGER DEFAULT 5,
    offline_mode BOOLEAN DEFAULT 0,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products (Cached from Cloud)
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    sku TEXT UNIQUE,
    barcode TEXT,
    name TEXT NOT NULL,
    description TEXT,
    category_id TEXT,
    price REAL NOT NULL,
    cost_price REAL,
    tax_rate REAL DEFAULT 0,
    current_stock REAL DEFAULT 0,
    image_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);

-- Transactions (Pending Sync)
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    transaction_number TEXT UNIQUE NOT NULL,
    terminal_id TEXT NOT NULL,
    location_id TEXT NOT NULL,

    customer_name TEXT,
    customer_phone TEXT,

    subtotal REAL NOT NULL,
    tax REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    total REAL NOT NULL,

    payment_method TEXT,  -- 'cash', 'card', 'mobile'
    payment_status TEXT DEFAULT 'completed',

    cashier_id TEXT,
    cashier_name TEXT,

    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'synced', 'failed'
    cloud_id TEXT,  -- ID from cloud after sync

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE INDEX idx_transactions_sync_status ON transactions(sync_status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- Transaction Items
CREATE TABLE transaction_items (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    sku TEXT,
    barcode TEXT,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    tax_rate REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    subtotal REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

-- Sync Queue
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,  -- 'transaction', 'inventory'
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,  -- 'create', 'update', 'delete'
    payload TEXT NOT NULL,  -- JSON
    sync_status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    error_message TEXT
);

-- Local Inventory Adjustments
CREATE TABLE inventory_adjustments (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    adjustment_type TEXT NOT NULL,  -- 'sale', 'return', 'manual'
    quantity REAL NOT NULL,
    reference_id TEXT,  -- Transaction ID
    notes TEXT,
    sync_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);
```

### Cloud PostgreSQL Schema (Server-Side)

```sql
-- EPOS Terminals
CREATE TABLE epos_terminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    location_id UUID NOT NULL,
    terminal_number VARCHAR(50) UNIQUE NOT NULL,
    terminal_name VARCHAR(255),
    device_info JSONB,  -- OS, version, MAC address, etc.
    is_active BOOLEAN DEFAULT true,
    last_seen_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_epos_terminals_tenant ON epos_terminals(tenant_id);
CREATE INDEX idx_epos_terminals_location ON epos_terminals(location_id);

-- EPOS Transactions
CREATE TABLE epos_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    terminal_id UUID REFERENCES epos_terminals(id),
    location_id UUID NOT NULL,

    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    client_id VARCHAR(36),  -- Local ID from EPOS client

    customer_id UUID,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),

    subtotal DECIMAL(10, 2) NOT NULL,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,

    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'completed',
    payment_reference VARCHAR(255),

    cashier_id UUID,
    cashier_name VARCHAR(255),

    metadata JSONB,  -- Additional data
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP,

    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_epos_transactions_tenant ON epos_transactions(tenant_id);
CREATE INDEX idx_epos_transactions_terminal ON epos_transactions(terminal_id);
CREATE INDEX idx_epos_transactions_created_at ON epos_transactions(created_at DESC);
CREATE INDEX idx_epos_transactions_client_id ON epos_transactions(client_id);

-- EPOS Transaction Items
CREATE TABLE epos_transaction_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES epos_transactions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    barcode VARCHAR(100),
    quantity DECIMAL(10, 3) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    subtotal DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_epos_transaction_items_transaction ON epos_transaction_items(transaction_id);
CREATE INDEX idx_epos_transaction_items_product ON epos_transaction_items(product_id);

-- Products (Enhanced for EPOS)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    location_id UUID,

    sku VARCHAR(100) UNIQUE NOT NULL,
    barcode VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID,

    cost_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) DEFAULT 0,

    current_stock DECIMAL(10, 3) DEFAULT 0,
    min_stock DECIMAL(10, 3) DEFAULT 0,
    max_stock DECIMAL(10, 3),
    reorder_point DECIMAL(10, 3),
    unit_of_measure VARCHAR(20),

    track_inventory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    is_synced BOOLEAN DEFAULT true,

    image_url TEXT,
    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_location ON products(location_id);
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_sku ON products(sku);

-- Sync Log (Audit Trail)
CREATE TABLE sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    terminal_id UUID REFERENCES epos_terminals(id),

    sync_type VARCHAR(50),  -- 'full', 'incremental', 'manual'
    entity_type VARCHAR(50),  -- 'transaction', 'inventory', 'product'
    entity_count INTEGER,

    status VARCHAR(20),  -- 'success', 'partial', 'failed'
    error_message TEXT,

    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER
);

CREATE INDEX idx_sync_log_tenant ON sync_log(tenant_id);
CREATE INDEX idx_sync_log_terminal ON sync_log(terminal_id);
CREATE INDEX idx_sync_log_started_at ON sync_log(started_at DESC);
```

---

## New Microservices Required

### 1. EPOS Service (Port 8010)

**Responsibilities**:
- Terminal registration & authentication
- Transaction management (create, void, refund)
- Cart operations
- Receipt generation
- Hardware configuration

**Endpoints**:
```
POST   /api/v1/epos/terminals/register
GET    /api/v1/epos/terminals/{id}
POST   /api/v1/epos/transactions
GET    /api/v1/epos/transactions/{id}
POST   /api/v1/epos/transactions/{id}/void
POST   /api/v1/epos/transactions/{id}/refund
GET    /api/v1/epos/transactions
```

**Database**: `epos_db` (PostgreSQL)

**Resources**:
- CPU: 500m-1000m
- Memory: 512Mi-1Gi
- Replicas: 2-3

### 2. Inventory Service (Port 8011)

**Responsibilities**:
- Product catalog management
- Stock tracking & adjustments
- Low stock alerts
- Barcode management
- Supplier management
- Purchase orders

**Endpoints**:
```
POST   /api/v1/inventory/products
GET    /api/v1/inventory/products
GET    /api/v1/inventory/products/search?q={query}
GET    /api/v1/inventory/products/barcode/{barcode}
POST   /api/v1/inventory/stock/adjust
GET    /api/v1/inventory/stock/low-stock
POST   /api/v1/inventory/purchase-orders
```

**Database**: `inventory_db` (PostgreSQL)

**Resources**:
- CPU: 300m-500m
- Memory: 512Mi-1Gi
- Replicas: 2

### 3. Sync Service (Port 8012) - NEW

**Responsibilities**:
- Manage sync sessions
- Conflict resolution
- Delta sync calculation
- Queue management
- Offline data reconciliation

**Endpoints**:
```
POST   /api/v1/sync/register-terminal
POST   /api/v1/sync/push        # Client pushes data to cloud
GET    /api/v1/sync/pull        # Client pulls updates from cloud
POST   /api/v1/sync/conflicts/resolve
GET    /api/v1/sync/status
WS     /ws/sync                 # WebSocket for real-time sync
```

**Database**: `sync_db` (PostgreSQL) + Redis (queue)

**Resources**:
- CPU: 500m-1000m
- Memory: 1Gi-2Gi
- Replicas: 2-3

### 4. Payment Service (Port 8013)

**Responsibilities**:
- Payment gateway integration (Stripe, Square, PayPal)
- Payment processing
- Refund handling
- Split payments
- Payment method management

**Endpoints**:
```
POST   /api/v1/payments/process
POST   /api/v1/payments/refund
GET    /api/v1/payments/{id}
POST   /api/v1/payments/split
GET    /api/v1/payments/methods
```

**Database**: `payment_db` (PostgreSQL)

**Resources**:
- CPU: 500m-1000m
- Memory: 512Mi-1Gi
- Replicas: 3 (critical service)

### 5. Receipt Service (Port 8014)

**Responsibilities**:
- Receipt generation (ESC/POS format)
- Receipt storage
- Print queue management
- Email receipts
- PDF generation

**Endpoints**:
```
POST   /api/v1/receipts/generate
GET    /api/v1/receipts/{id}
POST   /api/v1/receipts/{id}/print
POST   /api/v1/receipts/{id}/email
GET    /api/v1/receipts/{id}/pdf
```

**Database**: `receipt_db` (PostgreSQL) + MinIO (S3)

**Resources**:
- CPU: 200m-300m
- Memory: 256Mi-512Mi
- Replicas: 2

---

## Infrastructure Requirements

### Additional Kubernetes Resources

```yaml
# Total New Infrastructure

Services: 5 new microservices
  - epos-service (2-3 replicas)
  - inventory-service (2 replicas)
  - sync-service (2-3 replicas)
  - payment-service (3 replicas)
  - receipt-service (2 replicas)

Total Pods: 12-14 additional pods

Databases:
  - PostgreSQL: 5 new databases (epos_db, inventory_db, sync_db, payment_db, receipt_db)
  - Redis: Enhanced cluster for sync queues

Storage:
  - PersistentVolume: 50GB (product images, receipts, backups)
  - Object Storage (MinIO/S3): 100GB (receipts, documents)

Resources Required:
  - CPU: 3-5 cores
  - Memory: 6-10 GB
  - Storage: 150GB total

Networking:
  - Additional Istio VirtualServices for new services
  - WebSocket support in Istio Gateway
  - Network policies for service isolation
```

### Kubernetes Deployment Example

```yaml
# epos-service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: epos-service
  namespace: restaurant-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: epos-service
  template:
    metadata:
      labels:
        app: epos-service
    spec:
      containers:
      - name: epos-service
        image: shadrach85/epos-service:latest
        ports:
        - containerPort: 8010
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: epos-db-secret
              key: database_url
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: SYNC_SERVICE_URL
          value: "http://sync-service:8012"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8010
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8010
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: epos-service
  namespace: restaurant-system
spec:
  selector:
    app: epos-service
  ports:
  - port: 8010
    targetPort: 8010
  type: ClusterIP
```

---

## Security Considerations

### PCI DSS Compliance

| Requirement | Implementation |
|------------|----------------|
| **Never store full card numbers** | Use Stripe/Square tokenization |
| **TLS 1.3 encryption** | All API communication encrypted |
| **Access control** | Role-based permissions (cashier, manager, admin) |
| **Audit logging** | All transactions logged with timestamps |
| **Session timeouts** | Auto-logout after inactivity |
| **Data encryption at rest** | PostgreSQL encryption, encrypted SQLite |

### Offline Security

| Threat | Mitigation |
|--------|-----------|
| **Terminal theft** | Encrypted local database, remote wipe capability |
| **Unauthorized access** | PIN/password protection, biometric on Android |
| **Data tampering** | Checksum validation before sync |
| **Replay attacks** | Transaction IDs with timestamps |

---

## SaaS Subscription Model

### Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Retail EPOS Only** | $49/month | EPOS terminal, inventory, basic analytics, 1 location |
| **Restaurant Full Stack** | $99/month | All restaurant features + EPOS, 1 location |
| **Multi-Location** | $199/month | 3 locations, centralized inventory, advanced analytics |
| **Enterprise** | Custom | Unlimited locations, white-label, dedicated support |

### Add-Ons

| Feature | Price |
|---------|-------|
| Additional terminal | +$15/month |
| Advanced analytics | +$29/month |
| Loyalty program | +$39/month |
| Mobile app (customer) | +$49/month |

---

## Deployment Timeline

### Phase 1: Foundation (Months 1-2)
- ✅ Design EPOS client architecture
- ✅ Setup development environment
- ✅ Implement offline-first database layer
- ✅ Build basic EPOS service
- ✅ Create Electron app shell

### Phase 2: Core EPOS (Months 3-4)
- ✅ Product catalog management
- ✅ Barcode scanning integration
- ✅ Transaction flow (cart, checkout)
- ✅ Cash payment support
- ✅ Receipt generation
- ✅ Thermal printer integration

### Phase 3: Sync & Offline (Months 5-6)
- ✅ Sync service implementation
- ✅ Conflict resolution logic
- ✅ Background sync workers
- ✅ Offline queue management
- ✅ Admin dashboard for sync settings

### Phase 4: Payment Integration (Month 7)
- ✅ Stripe Terminal SDK integration
- ✅ Square reader support
- ✅ Card payment processing
- ✅ Payment reconciliation

### Phase 5: Multi-OS Support (Months 8-9)
- ✅ Android React Native app
- ✅ Linux AppImage distribution
- ✅ Hardware testing on all platforms
- ✅ Cross-platform bug fixes

### Phase 6: Analytics & Polish (Month 10)
- ✅ Sales analytics dashboard
- ✅ Inventory reports
- ✅ Cashier performance metrics
- ✅ ML-based forecasting

### Phase 7: Beta Testing (Month 11)
- ✅ 10-20 pilot customers
- ✅ Hardware compatibility testing
- ✅ Performance optimization
- ✅ Bug fixes & iterations

### Phase 8: Production Launch (Month 12)
- ✅ Public release
- ✅ Marketing & sales
- ✅ Customer onboarding
- ✅ 24/7 support setup

---

## Cost Estimation

### Development Costs

| Resource | Duration | Cost |
|----------|----------|------|
| Backend Developer (Senior) | 10 months | $120,000 |
| Frontend Developer (Senior) | 10 months | $110,000 |
| Mobile Developer | 4 months | $40,000 |
| DevOps Engineer | 6 months | $60,000 |
| QA Engineer | 8 months | $50,000 |
| **Total Development** | | **$380,000** |

### Infrastructure Costs (Monthly)

| Tier | Users | Cost |
|------|-------|------|
| Small (1-10 locations) | | $300-500 |
| Medium (11-50 locations) | | $1,000-2,000 |
| Large (51-200 locations) | | $4,000-8,000 |
| Enterprise (200+ locations) | | $10,000+ |

### Hardware Costs (Per Terminal)

| Hardware | Cost Range |
|----------|------------|
| Windows PC / Tablet | $300-800 |
| Linux PC (Raspberry Pi 4) | $100-200 |
| Android Tablet | $200-500 |
| Barcode Scanner | $50-200 |
| Thermal Printer | $150-400 |
| Cash Drawer | $80-150 |
| Card Reader | $50-300 |
| **Total per terminal** | **$930-2,550** |

---

## Monitoring & Observability

### Metrics to Track

**Business Metrics**:
- Transactions per hour/day
- Average transaction value
- Payment method distribution
- Top-selling products
- Stock turnover rate

**Technical Metrics**:
- API response time (<100ms target)
- Database query latency
- Sync success rate (>99%)
- Offline transaction queue depth
- Hardware connection uptime

**Alerts**:
- Low stock warnings
- Failed sync operations
- Payment gateway errors
- Terminal offline > 24 hours
- Disk space < 10%

### Observability Stack

| Component | Technology |
|-----------|-----------|
| Metrics | Prometheus + Grafana |
| Logging | Loki + Grafana |
| Tracing | Jaeger |
| Alerts | Alertmanager |
| Uptime | UptimeRobot |

---

## Conclusion

This EPOS architecture provides a **robust, scalable, offline-first solution** that works seamlessly across Windows, Linux, and Android platforms. The dual-mode approach (Full Restaurant vs EPOS-Only) allows you to target both hospitality and retail markets with a single platform.

### Key Advantages

✅ **Offline-First**: Never lose a sale due to internet outage
✅ **Multi-OS**: Works on any platform, any hardware
✅ **SaaS Model**: Recurring revenue with tiered pricing
✅ **Hardware Agnostic**: Supports standard POS peripherals
✅ **Scalable**: From single store to enterprise chains
✅ **Modern Stack**: Electron, React, TypeScript, FastAPI

### Next Steps

1. **Review & Approve**: Stakeholder sign-off on architecture
2. **Setup Infrastructure**: Provision Kubernetes resources
3. **Hire Team**: Backend, frontend, mobile developers
4. **Sprint Planning**: Break down into 2-week sprints
5. **Begin Phase 1**: Start with offline database layer
