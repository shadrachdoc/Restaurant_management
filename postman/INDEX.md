# Postman Collections Index

This directory contains all Postman collections and environments for the Restaurant Management System.

## Collections Overview

### 1. **Restaurant_Load_Test.postman_collection.json** (NEW - Load Testing)
**Purpose:** Generate bulk test data - 150 online orders + 100 table orders

**Use Cases:**
- Load testing and performance testing
- Populating analytics dashboards with realistic data
- Testing ML prediction algorithms with large datasets
- Simulating real-world traffic patterns

**How to Use:**
- See [README.md](./README.md) for detailed instructions
- Run Setup first to load menu items
- Use Collection Runner with iterations (150 for online, 100 for table)
- Creates unique customers, realistic orders, varied items

**Key Features:**
- Auto-generates unique customer emails/phones
- Random item selection from actual menu
- Realistic delivery addresses
- Special instructions variety
- No manual data entry needed

---

### 2. **Restaurant_Management_System.postman_collection.json** (Manual Testing)
**Purpose:** Comprehensive API testing for all endpoints

**Use Cases:**
- Manual endpoint testing during development
- Verifying API functionality
- Testing specific scenarios
- Debugging issues

**Endpoints Covered:**
- Authentication (Register, Login, Logout)
- Restaurant Management (CRUD)
- Menu Management (Items, Categories)
- Order Management (Create, Update, Status)
- Customer Management
- Analytics Endpoints
- ML Prediction Endpoints

**How to Use:**
- Import collection
- Set environment (Restaurant_Management_Environment or Restaurant_Local)
- Run individual requests or folders
- Variables auto-populate from responses

---

### 3. **Restaurant-Management-API.postman_collection.json** (Original Collection)
**Purpose:** Legacy collection for basic API testing

**Status:** Maintained for backward compatibility

**Use Cases:**
- Quick API checks
- Basic endpoint verification
- Reference for API structure

---

## Environments

### 1. **Restaurant_Local.postman_environment.json** (Load Testing)
- Base URL: `http://localhost:8000`
- Restaurant ID: Chai Kadai (`73332393-3c58-47c1-b58e-6d2ab59e96bb`)
- Used with: Restaurant_Load_Test collection
- Contains: Dynamic variables for order generation

### 2. **Restaurant_Management_Environment.postman_environment.json** (Manual Testing)
- Base URL: `http://localhost:8000`
- Restaurant ID: Configurable
- Used with: Restaurant_Management_System collection
- Contains: Auth tokens, user IDs, test data

### 3. **Restaurant-System-Local.postman_environment.json** (Original)
- Base URL: `http://localhost:8000`
- Used with: Original Restaurant-Management-API collection
- Status: Legacy support

---

## Quick Start Guides

### For Load Testing (Generate 250 Orders)
```
1. Import: Restaurant_Load_Test.postman_collection.json
2. Import: Restaurant_Local.postman_environment.json
3. Select "Restaurant Local Environment"
4. Run "Setup - Get Menu Items" once
5. Collection Runner → 150 iterations (Online orders)
6. Collection Runner → 100 iterations (Table orders)
7. Check database for 250 orders + 150 customers
```

### For Manual API Testing
```
1. Import: Restaurant_Management_System.postman_collection.json
2. Import: Restaurant_Management_Environment.postman_environment.json
3. Select environment
4. Run "Auth" folder to login
5. Test individual endpoints
```

### For Quick Endpoint Check
```
1. Import: Restaurant-Management-API.postman_collection.json
2. Import: Restaurant-System-Local.postman_environment.json
3. Run specific requests
```

---

## Documentation

- **[README.md](./README.md)** - Detailed load testing guide
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Comprehensive testing documentation

---

## Common Workflows

### 1. Testing New Features
**Collection:** Restaurant_Management_System
1. Create new request in appropriate folder
2. Add Pre-request Scripts for dynamic data
3. Add Tests for assertions
4. Run and verify

### 2. Performance Testing
**Collection:** Restaurant_Load_Test
1. Adjust iterations in Collection Runner
2. Monitor response times
3. Check server logs for errors
4. Analyze database performance

### 3. Analytics Testing
**Collection:** Restaurant_Load_Test (generate data) + Restaurant_Management_System (test endpoints)
1. Generate 250+ orders with load test
2. Use manual collection to call analytics endpoints
3. Verify data accuracy
4. Test chart rendering

### 4. ML Prediction Testing
**Collection:** Restaurant_Load_Test (historical data) + Restaurant_Management_System (predictions)
1. Generate orders with time spread (90+ days)
2. Call prediction endpoints with various periods
3. Verify confidence intervals
4. Test cache performance

---

## Environment Variables Reference

### Common Variables (All Environments)
- `base_url` - API base URL
- `restaurant_id` - Target restaurant UUID
- `access_token` - JWT authentication token

### Load Test Specific
- `menu_items` - Cached menu items (JSON array)
- `customer_email` - Generated customer email
- `customer_password` - Generated password
- `customer_name` - Random customer name
- `order_items` - Selected items for order
- `delivery_address` - Random address
- `table_number` - Random table ID

### Manual Test Specific
- `admin_token` - Admin JWT token
- `chef_token` - Chef JWT token
- `customer_token` - Customer JWT token
- `order_id` - Last created order ID
- `menu_item_id` - Last created menu item ID

---

## Tips & Best Practices

### Load Testing
1. **Always run Setup first** to populate menu_items
2. **Monitor system resources** during high iterations
3. **Use delays** (50-100ms) to avoid overwhelming the server
4. **Check logs** after each run for errors
5. **Verify data** in database after completion

### Manual Testing
1. **Update environment variables** before testing
2. **Check Pre-request Scripts** for dynamic data generation
3. **Review Test assertions** to understand expected behavior
4. **Use Console** to debug variable values
5. **Save responses** for reference

### General
1. **Keep collections updated** with new endpoints
2. **Use folders** to organize related requests
3. **Add descriptions** to requests for clarity
4. **Share collections** with team via Git
5. **Version control** environments separately

---

## Troubleshooting

### Collection Runner Errors
- **Menu items not found:** Run Setup request first
- **Authentication failed:** Check token expiration, re-login
- **Order creation failed:** Verify restaurant_id and menu items
- **Slow execution:** Increase delay, reduce iterations

### Variable Issues
- **Undefined variables:** Check environment is selected
- **Stale tokens:** Re-run auth requests
- **Wrong restaurant data:** Update restaurant_id in environment

### Performance Issues
- **Timeouts:** Increase request timeout in settings
- **Memory errors:** Disable "Save Responses" in runner
- **Slow responses:** Check server logs, database queries

---

## File Structure
```
postman/
├── INDEX.md                                          # This file
├── README.md                                         # Load testing guide
├── TESTING_GUIDE.md                                  # Comprehensive testing docs
│
├── Collections/
│   ├── Restaurant_Load_Test.postman_collection.json           # Load testing (NEW)
│   ├── Restaurant_Management_System.postman_collection.json   # Manual testing
│   └── Restaurant-Management-API.postman_collection.json      # Legacy
│
└── Environments/
    ├── Restaurant_Local.postman_environment.json              # Load testing env
    ├── Restaurant_Management_Environment.postman_environment.json  # Manual testing env
    └── Restaurant-System-Local.postman_environment.json       # Legacy env
```

---

## Contributing

When adding new endpoints:

1. Add to **Restaurant_Management_System** collection
2. Organize in appropriate folder
3. Add Pre-request Scripts for setup
4. Add Tests for validation
5. Update environment variables if needed
6. Document in comments

---

## Support

- **Issues:** Check Postman Console for detailed error logs
- **Questions:** Review Pre-request Scripts and Tests
- **Updates:** Keep collections synced with API changes
- **Docs:** Refer to README.md and TESTING_GUIDE.md

---

**Last Updated:** December 27, 2025
**Collections:** 3
**Environments:** 3
**Total Requests:** 50+
