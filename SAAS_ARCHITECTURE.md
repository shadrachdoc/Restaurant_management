# Restaurant Management SAAS - System Architecture

## Overview
This is a multi-tenant SAAS application for restaurant management where multiple restaurants can register and manage their operations independently.

## User Hierarchy

### 1. Master Admin (Product Owner)
**Access**: Full system control
**Responsibilities**:
- View all registered restaurants
- Dashboard with consolidated analytics across all restaurants
- Enable/Disable restaurant accounts
- Manage subscriptions and pricing plans
- System-wide configuration

**Dashboard Features**:
- Total restaurants count
- Active/Inactive restaurants
- Total revenue across all restaurants
- Subscription status overview
- Restaurant list with actions (enable/disable/view details)

### 2. Restaurant Admin (Restaurant Owner)
**Access**: Own restaurant only
**Registration**: Public signup (only role available on signup page)
**Responsibilities**:
- Create and manage their restaurant profile
- Create/Delete Chef accounts for their restaurant
- Manage menu items
- Manage tables and QR codes
- View orders and analytics
- Manage restaurant settings

**Dashboard Features**:
- Restaurant analytics (orders, revenue, ratings)
- Quick actions (manage menu, tables, staff)
- Recent orders
- Feedback summary

**User Management**:
- Create Chef accounts (username, password, assign to restaurant)
- Delete Chef accounts
- View list of all staff

### 3. Chef (Restaurant Staff)
**Access**: View orders for their restaurant only
**Creation**: Created by Restaurant Admin (no signup)
**Dashboard**: Simple order management interface

**Features**:
- View all active orders grouped by table
- Order details: Table number, Items, Quantity, Special instructions
- Update order status:
  - **Pending** (New order)
  - **Preparing** (Chef started cooking)
  - **Ready** (Food ready for serving)
  - **Served** (Delivered to customer)
  - **Cancelled** (Order cancelled)
- Filter by status
- Real-time updates (websocket/polling)

**Dashboard Layout**:
```
┌─────────────────────────────────────────────┐
│  Chef Dashboard - [Restaurant Name]         │
│  Logout Button (Top Right)                  │
├─────────────────────────────────────────────┤
│  Filters: [All] [Pending] [Preparing] [Ready]│
├─────────────────────────────────────────────┤
│  Table 1 - Order #123                       │
│  ├─ 2x Burger                               │
│  ├─ 1x Fries                                │
│  └─ Status: [Preparing] [Ready] [Cancel]   │
├─────────────────────────────────────────────┤
│  Table 3 - Order #124                       │
│  ├─ 1x Pizza                                │
│  └─ Status: [Preparing] [Ready] [Cancel]   │
└─────────────────────────────────────────────┘
```

### 4. Customer (Public - No Authentication)
**Access**: View menu and place orders via QR code
**Flow**:
1. Scan QR code on table
2. View restaurant menu (with images, prices, descriptions)
3. Select items with checkboxes
4. Submit order
5. Order sent to kitchen (Chef dashboard)

**Features**:
- No login required
- Menu display with categories
- Item selection with quantity
- Special instructions field
- Order confirmation

## Data Models

### Restaurant
- id (UUID)
- name
- owner_id (Restaurant Admin user ID)
- subscription_status (active/inactive/suspended/trial)
- pricing_plan (basic/premium/enterprise)
- is_active (controlled by Master Admin)
- created_at, updated_at

### User
- id (UUID)
- username
- email
- role (master_admin / restaurant_admin / chef)
- restaurant_id (NULL for master_admin, required for others)
- is_active
- created_at, updated_at

### Order (NEW - Needs to be created)
- id (UUID)
- restaurant_id
- table_id
- order_number (auto-increment per restaurant)
- items (JSONB array)
- status (pending/preparing/ready/served/cancelled)
- special_instructions
- total_amount
- created_at, updated_at

### MenuItem (Existing)
- Already implemented

### Table (Existing)
- Already implemented
- QR code links to public menu page

## Routes Structure

### Public Routes (No Auth)
- `/menu/:restaurant_id/:table_id` - Public menu page
- `/order/:restaurant_id/:table_id` - Place order

### Auth Routes
- `/login` - All users login here
- `/signup` - Only Restaurant Admin signup

### Master Admin Routes
- `/master/dashboard` - All restaurants overview
- `/master/restaurants` - Restaurant management
- `/master/analytics` - System-wide analytics

### Restaurant Admin Routes
- `/admin/dashboard` - Restaurant dashboard
- `/admin/restaurant` - Restaurant profile
- `/admin/menu` - Menu management
- `/admin/tables` - Table management
- `/admin/staff` - Chef management (NEW)
- `/admin/orders` - Order history
- `/admin/feedback` - Customer feedback

### Chef Routes
- `/chef/dashboard` - Order management dashboard
- `/chef/orders` - View and update orders

## Implementation Plan

### Phase 1: Core Fixes (Current)
✅ Fix menu item category dropdown
✅ Fix table QR code column size
✅ Remove Customer/Chef from signup page

### Phase 2: User Management
1. Add Staff Management page for Restaurant Admin
   - Create Chef accounts
   - List all chefs
   - Delete chef accounts
2. Add logout button to all dashboards

### Phase 3: Order System
1. Create Order model and API
2. Create public menu page (QR code destination)
3. Create Chef dashboard for order management
4. Implement order status workflow

### Phase 4: Master Admin
1. Create Master Admin dashboard
2. Restaurant list with enable/disable
3. Consolidated analytics

### Phase 5: Enhancements
1. Real-time order updates (WebSocket)
2. Notifications
3. Print orders
4. Reports and analytics

## Current Status

✅ Restaurant creation working
✅ Menu items working (with category dropdown)
✅ Tables working (QR codes generated)
⏳ Signup page (needs Customer/Chef removal)
⏳ Chef dashboard (needs to be created)
⏳ Staff management (needs to be created)
⏳ Public menu page (needs to be created)
⏳ Order system (needs to be created)
⏳ Master Admin dashboard (needs to be created)

## Next Steps

1. Update SignupPage.jsx - Remove Customer/Chef options
2. Add logout button to DashboardLayout
3. Create StaffManagement.jsx for Restaurant Admin
4. Create ChefDashboard.jsx for Chef role
5. Create Order model and APIs
6. Create public MenuPage.jsx (QR code destination)
7. Create MasterDashboard.jsx for Master Admin
