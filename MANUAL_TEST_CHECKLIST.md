# Manual Testing Checklist - Restaurant Management System

## Test Environment
- **Frontend URL**: https://restaurant.corpv3.com
- **API URL**: https://restaurant.corpv3.com/api/v1
- **Test Devices**: Desktop (Chrome, Firefox, Safari), Mobile (Android Chrome, iOS Safari)

---

## 1. Authentication & Authorization Tests

### 1.1 Master Admin Login
- [ ] Navigate to `/admin/login`
- [ ] Enter credentials: `admin` / `password`
- [ ] Verify successful login and redirect to admin dashboard
- [ ] Verify master admin menu items are visible
- [ ] Test logout functionality

### 1.2 Restaurant Admin Login
- [ ] Navigate to `/admin/login`
- [ ] Enter credentials: `adminres` / `password1234`
- [ ] Verify successful login
- [ ] Verify restaurant-specific dashboard loads
- [ ] Verify limited access (no master admin features)
- [ ] Test logout functionality

### 1.3 Chef/Staff Login
- [ ] Navigate to `/staff/login`
- [ ] Enter valid chef credentials
- [ ] Verify kitchen/chef dashboard loads
- [ ] Verify order management features available
- [ ] Test logout functionality

### 1.4 Customer Login/Signup
- [ ] Navigate to `/customer-login`
- [ ] Test signup with new email
- [ ] Verify email validation
- [ ] Test login with created account
- [ ] **iPhone Safari**: Test form submission and autocomplete
- [ ] **Android Chrome**: Test form submission
- [ ] Verify redirect to customer menu/orders

### 1.5 Guest Access (No Login)
- [ ] Scan QR code (or navigate to `/menu?restaurant=SLUG&table=ID`)
- [ ] Verify menu loads without login
- [ ] Verify can add items to cart
- [ ] Verify can place order without name (auto-generates Guest-XXXX)

---

## 2. QR Code & Table Order Flow (Mobile Priority)

### 2.1 QR Code Scanning
- [ ] Generate QR code for a table from restaurant admin
- [ ] Scan QR code with **Android Chrome**
- [ ] Verify redirects to `/menu?restaurant=SLUG&table=ID`
- [ ] Scan QR code with **iPhone Safari**
- [ ] Verify correct restaurant and table detected

### 2.2 Public Menu Ordering (Guest - No Login)
- [ ] Navigate via QR code
- [ ] Verify menu items load with images and prices
- [ ] Add multiple items to cart
- [ ] Update quantities in cart
- [ ] Remove items from cart
- [ ] Leave name field **EMPTY** (test guest flow)
- [ ] Leave phone field **EMPTY**
- [ ] Add special instructions
- [ ] Click "Place Order"
- [ ] Verify order succeeds with auto-generated Guest name
- [ ] Verify redirect to `/order/:orderId`

### 2.3 Public Menu Ordering (With Name)
- [ ] Navigate via QR code
- [ ] Add items to cart
- [ ] Enter name: "John Doe"
- [ ] Enter phone: "+1234567890"
- [ ] Place order
- [ ] Verify order created successfully

### 2.4 Order Placement Validation
- [ ] Check backend logs for enum errors (should NOT see `invalid input value for enum ordertype`)
- [ ] Verify `order_type` is sent as `'table'` (lowercase, not 'DINE_IN')
- [ ] Verify order appears in chef dashboard
- [ ] Verify order appears in restaurant admin orders list

---

## 3. Order Tracking (Real-Time Updates)

### 3.1 Mobile Order Tracking (Primary Flow)
- [ ] After placing order, verify redirect to `/order/:orderId`
- [ ] **Android Chrome**: Verify page loads completely
- [ ] **iPhone Safari**: Verify page loads completely
- [ ] Verify order details display correctly:
  - [ ] Order number
  - [ ] Customer name (Guest-XXXX if auto-generated)
  - [ ] Table number
  - [ ] Order items with quantities and prices
  - [ ] Subtotal, tax, total
- [ ] Verify status timeline displays with correct status
- [ ] Verify status icons and colors are correct

### 3.2 Real-Time Status Updates (Keep Page Open)
- [ ] With order tracking page open on mobile
- [ ] In another browser, login as chef
- [ ] Update order status from `pending` → `confirmed`
- [ ] **Within 3 seconds**, verify mobile page updates to "Confirmed" (no page refresh)
- [ ] Update status to `preparing`
- [ ] Verify mobile page updates automatically
- [ ] Update status to `ready`
- [ ] Verify mobile page updates
- [ ] Update status to `served`
- [ ] Verify mobile page updates
- [ ] Verify status timeline highlights correct step
- [ ] Verify "In progress..." text appears on current status

### 3.3 Status Case Sensitivity Check
- [ ] Open browser console on order tracking page
- [ ] Check network tab for `/api/v1/orders/:id` response
- [ ] Verify response contains `"status": "served"` (lowercase)
- [ ] Verify UI displays "Served" correctly (not stuck on previous status)

### 3.4 Action Buttons Visibility (Mobile)
- [ ] Scroll to bottom of order tracking page
- [ ] **Android Chrome**: Verify "Quick Actions" section is visible
- [ ] **iPhone Safari**: Verify "Quick Actions" section is visible
- [ ] Verify buttons are NOT hidden behind bottom browser bar
- [ ] Verify padding allows comfortable scrolling

---

## 4. Generate Receipt & Free Table

### 4.1 Receipt Button Visibility
- [ ] When order status is `pending`: Verify "Generate Receipt" button is **NOT visible**
- [ ] When order status is `confirmed`: Verify button is **NOT visible**
- [ ] When order status is `preparing`: Verify button is **NOT visible**
- [ ] When order status is `ready`: Verify button is **NOT visible**
- [ ] When order status is `served`: Verify "✅ Generate Receipt & Free Table" button **IS visible**
- [ ] When order status is `completed`: Verify button is **NOT visible** (already completed)

### 4.2 Generate Receipt Functionality
- [ ] Mark order as `served` from chef dashboard
- [ ] On mobile order tracking, verify green "Generate Receipt" button appears
- [ ] Click "Generate Receipt & Free Table"
- [ ] Verify confirmation dialog appears
- [ ] Click "Cancel" - verify nothing happens
- [ ] Click button again and confirm
- [ ] Verify loading spinner appears
- [ ] Verify success toast: "Receipt generated! Table is now available."
- [ ] Verify order status updates to `completed`
- [ ] Verify button disappears after completion

### 4.3 Table Status After Receipt
- [ ] Login as restaurant admin
- [ ] Navigate to tables page
- [ ] Verify table status changed from `occupied` to `available`
- [ ] Verify table can be reassigned to new orders

---

## 5. Add More Items to Existing Order

### 5.1 Add Items UI
- [ ] On order tracking page (status NOT `served` or `completed`)
- [ ] Verify "Add More Items" section is visible
- [ ] Click "Show Menu"
- [ ] Verify restaurant menu items load
- [ ] Verify currency symbols display correctly
- [ ] Click "Hide Menu" - verify menu collapses

### 5.2 Adding Items
- [ ] Click "Show Menu"
- [ ] Click "Add" button on a menu item
- [ ] Verify toast appears: "[Item Name] added"
- [ ] Verify item appears in "Items to Add" cart
- [ ] Add same item again
- [ ] Verify quantity increments
- [ ] Add different item
- [ ] Verify both items in cart

### 5.3 Quantity Management
- [ ] Click "-" button to decrease quantity
- [ ] Verify quantity decreases
- [ ] Decrease to 0
- [ ] Verify item is removed from cart
- [ ] Click "+" button
- [ ] Verify quantity increases
- [ ] Verify "Additional Total" calculates correctly

### 5.4 Place Additional Order
- [ ] Add items to cart
- [ ] Verify "Additional Total" displays correct sum
- [ ] Click "Place Additional Order"
- [ ] Verify loading state: "Placing Order..."
- [ ] Verify success toast
- [ ] Verify cart clears
- [ ] Verify menu collapses
- [ ] Verify a **NEW order** was created (check chef dashboard)
- [ ] Verify new order has same table and customer info

---

## 6. Other Action Buttons

### 6.1 Order Again Button
- [ ] Click "🍽️ Order Again"
- [ ] Verify redirects to `/menu?restaurant=SLUG`
- [ ] Verify correct restaurant menu loads
- [ ] Verify can place new order

### 6.2 Print Receipt Button
- [ ] Click "🖨️ Print Receipt"
- [ ] Verify browser print dialog opens
- [ ] Verify print preview shows order details
- [ ] Cancel print dialog

---

## 7. Chef/Kitchen Dashboard

### 7.1 Order Display
- [ ] Login as chef
- [ ] Verify active orders display in cards/list
- [ ] Verify each order shows:
  - [ ] Order number
  - [ ] Table number
  - [ ] Customer name
  - [ ] Order items with quantities
  - [ ] Current status
  - [ ] Timestamp

### 7.2 Status Updates
- [ ] Click "Confirm Order" on pending order
- [ ] Verify status changes to `confirmed`
- [ ] Click "Start Preparing"
- [ ] Verify status changes to `preparing`
- [ ] Click "Mark Ready"
- [ ] Verify status changes to `ready`
- [ ] Click "Mark Served"
- [ ] Verify status changes to `served`
- [ ] Verify order moves to completed section or updates UI

### 7.3 Real-Time Order Arrival
- [ ] Keep chef dashboard open
- [ ] In another browser, place new order via QR code
- [ ] Verify new order appears in chef dashboard within 3 seconds (no refresh)

---

## 8. Restaurant Admin Dashboard

### 8.1 Restaurant Management
- [ ] Login as restaurant admin
- [ ] Navigate to restaurant settings
- [ ] Update restaurant name
- [ ] Update currency symbol
- [ ] Upload logo
- [ ] Update business hours
- [ ] Save changes
- [ ] Verify changes persist after logout/login

### 8.2 Menu Management
- [ ] Navigate to menu items
- [ ] Create new menu item:
  - [ ] Add name, description, price
  - [ ] Upload image
  - [ ] Set category
  - [ ] Mark as available
- [ ] Edit existing menu item
- [ ] Toggle availability (available/unavailable)
- [ ] Verify unavailable items don't show in customer menu
- [ ] Delete menu item

### 8.3 Table Management
- [ ] Navigate to tables page
- [ ] Create new table
- [ ] Assign table number
- [ ] Generate QR code
- [ ] Download QR code
- [ ] Verify QR code works when scanned
- [ ] Edit table
- [ ] Delete table

### 8.4 Orders Management
- [ ] View all orders
- [ ] Filter by status
- [ ] Filter by date range
- [ ] Search by order number
- [ ] Search by customer name
- [ ] View order details
- [ ] Export orders (if available)

---

## 9. Customer Dashboard (Logged In Users)

### 9.1 Order History
- [ ] Login as customer
- [ ] Navigate to `/customer/orders`
- [ ] Verify past orders display
- [ ] Click on an order
- [ ] Verify order details load
- [ ] Verify order tracking works

### 9.2 Profile Management
- [ ] Navigate to profile/settings
- [ ] Update name
- [ ] Update phone
- [ ] Update email
- [ ] Save changes
- [ ] Verify changes persist

---

## 10. Payment Integration (If Implemented)

### 10.1 Online Order Payment
- [ ] Place online order (delivery/pickup)
- [ ] Proceed to checkout
- [ ] Select payment method
- [ ] Enter test card details
- [ ] Complete payment
- [ ] Verify order status updates
- [ ] Verify payment confirmation

### 10.2 Table Order Payment
- [ ] Generate receipt for table order
- [ ] Verify payment options display
- [ ] Process payment
- [ ] Verify receipt generation

---

## 11. Mobile-Specific Tests

### 11.1 Android Chrome
- [ ] Test all QR code flows
- [ ] Test order placement
- [ ] Test order tracking
- [ ] Test button visibility (no buttons hidden)
- [ ] Test scrolling and touch interactions
- [ ] Test landscape and portrait modes
- [ ] Test back button behavior

### 11.2 iPhone Safari
- [ ] **HIGH PRIORITY**: Test login/signup (currently reported as broken)
- [ ] Test form autocomplete
- [ ] Test form submission
- [ ] Test QR code flows
- [ ] Test order placement
- [ ] Test order tracking
- [ ] Test button visibility
- [ ] Test Safari-specific input behaviors
- [ ] Test back navigation

### 11.3 Responsive Design
- [ ] Test on small phone (< 375px width)
- [ ] Test on standard phone (375-414px)
- [ ] Test on large phone (414-480px)
- [ ] Test on tablet (768px+)
- [ ] Verify all content is readable
- [ ] Verify buttons are tappable (min 44px touch target)

---

## 12. Performance & UX

### 12.1 Loading States
- [ ] Verify loading spinners appear during API calls
- [ ] Verify skeleton screens (if implemented)
- [ ] Verify no blank white screens
- [ ] Verify error states display properly

### 12.2 Error Handling
- [ ] Test with network disconnected
- [ ] Verify friendly error messages
- [ ] Test with invalid order ID
- [ ] Verify 404 handling
- [ ] Test with expired session
- [ ] Verify redirect to login

### 12.3 Toast Notifications
- [ ] Verify success toasts appear and auto-dismiss
- [ ] Verify error toasts appear
- [ ] Verify toasts are readable on mobile
- [ ] Verify toasts don't block important UI

---

## 13. Edge Cases & Negative Tests

### 13.1 Empty States
- [ ] Restaurant with no menu items
- [ ] Customer with no orders
- [ ] Chef with no active orders
- [ ] Empty cart checkout attempt

### 13.2 Validation
- [ ] Submit order with empty cart
- [ ] Submit login with empty fields
- [ ] Submit signup with invalid email
- [ ] Submit signup with weak password
- [ ] Place order with negative quantity
- [ ] Place order with extremely large quantity (999+)

### 13.3 Concurrent Actions
- [ ] Have two users order from same table simultaneously
- [ ] Update order status while customer is viewing
- [ ] Delete menu item that's in someone's cart
- [ ] Change table availability while order is being placed

---

## 14. Security Tests

### 14.1 Access Control
- [ ] Try accessing chef dashboard as customer
- [ ] Try accessing admin features as chef
- [ ] Try accessing another restaurant's data
- [ ] Try accessing orders from different restaurant
- [ ] Verify API returns 401/403 appropriately

### 14.2 QR Code Security
- [ ] Try using QR code from different restaurant
- [ ] Try using invalid table ID
- [ ] Try using deleted table's QR code
- [ ] Verify proper error handling

### 14.3 Input Sanitization
- [ ] Enter SQL injection in search fields
- [ ] Enter XSS scripts in text inputs
- [ ] Enter extremely long strings
- [ ] Enter special characters
- [ ] Verify all inputs are sanitized

---

## 15. Browser Compatibility

### 15.1 Desktop Browsers
- [ ] **Chrome** (latest): Full functionality test
- [ ] **Firefox** (latest): Full functionality test
- [ ] **Safari** (latest): Full functionality test
- [ ] **Edge** (latest): Full functionality test

### 15.2 Mobile Browsers
- [ ] **Android Chrome**: Complete flow test
- [ ] **iPhone Safari**: Complete flow test (PRIORITY - currently broken)
- [ ] **Samsung Internet**: Basic flow test
- [ ] **Firefox Mobile**: Basic flow test

---

## 16. Database & Backend Validation

### 16.1 Data Integrity
- [ ] After placing order, check database for correct data
- [ ] Verify `order_type` is stored as lowercase ('table', 'online')
- [ ] Verify `status` is stored as lowercase ('pending', 'served', etc.)
- [ ] Verify timestamps are correct
- [ ] Verify guest names are generated correctly

### 16.2 API Response Validation
- [ ] Check API responses return lowercase enum values
- [ ] Verify currency symbols in responses
- [ ] Verify calculated totals match (subtotal + tax = total)
- [ ] Verify all required fields are present

---

## 17. Known Issues to Verify Fixed

### 17.1 Order Type Enum Error
- [ ] ✅ **FIXED**: Verify no `invalid input value for enum ordertype: "DINE_IN"` errors
- [ ] ✅ Verify orders use `'table'` not `'DINE_IN'`

### 17.2 Status Case Mismatch
- [ ] ✅ **FIXED**: Verify order tracking updates in real-time
- [ ] ✅ Verify status comparisons work with lowercase values
- [ ] ✅ Verify served orders show "Generate Receipt" button

### 17.3 Guest Order Name Requirement
- [ ] ✅ **FIXED**: Verify can place order without entering name
- [ ] ✅ Verify auto-generates Guest-XXXX name

### 17.4 Missing Buttons on Mobile
- [ ] ✅ **FIXED**: Verify action buttons appear on `/order/:orderId` route
- [ ] ✅ Verify buttons visible on Android Chrome
- [ ] ✅ Verify buttons are not hidden by browser UI

### 17.5 Outstanding Issues
- [ ] ❌ **NOT FIXED**: iPhone Safari login/signup issue - needs investigation

---

## Test Summary Template

```
Test Date: ___________
Tester: ___________
Device/Browser: ___________

Total Tests: _____
Passed: _____
Failed: _____
Blocked: _____

Critical Issues:
1.
2.
3.

Medium Issues:
1.
2.

Minor Issues:
1.
2.

Notes:


```

---

## Priority Test Paths (Smoke Test - 15 minutes)

If time is limited, test these critical paths first:

1. **QR Code Order Flow (Mobile)**
   - Scan QR → View Menu → Add Items → Place Order (as guest) → Track Order → Status Updates → Generate Receipt

2. **Chef Order Processing**
   - Login → View Orders → Update Status (pending → confirmed → preparing → ready → served)

3. **Admin Restaurant Setup**
   - Login → Create Menu Item → Create Table → Generate QR Code

4. **Real-Time Updates**
   - Place order on mobile → Keep page open → Update status from chef → Verify mobile updates automatically

5. **iPhone Safari Login** (CRITICAL - currently broken)
   - Test login and signup forms on iPhone Safari

---

## Test Data

### Test Credentials
- Master Admin: `admin` / `password`
- Restaurant Admin: `adminres` / `password1234`
- Chef: (check your database)
- Customer: (create during testing)

### Test Restaurants
- Check existing restaurants in database
- Use slugs in QR code URLs

### Test Menu Items
- Create items with various prices (0.99, 10.00, 25.50)
- Test with and without images
- Test with special characters in names

### Test Tables
- Create tables 1-10 for testing
- Generate QR codes for each

---

## Automation Candidates

Tests that should eventually be automated:
- ✅ Already automated with Playwright: Auth, Orders, Tables, Staff, QR Security
- 🔄 Need automation: Payment flows, Real-time updates, Mobile-specific tests

---

**END OF CHECKLIST**
