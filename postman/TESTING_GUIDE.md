# Restaurant Management System - Complete Testing Guide

## Overview
This guide provides step-by-step instructions for testing the entire Restaurant Management System using Postman.

## Prerequisites
- Postman installed (Download from: https://www.postman.com/downloads/)
- System deployed and accessible at: https://restaurant.corpv3.com
- Test credentials available

## Setup

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button (top left)
3. Select the following files:
   - `Restaurant_Management_System.postman_collection.json`
   - `Restaurant_Management_Environment.postman_environment.json`
4. Select the **Restaurant Management - Production** environment from the dropdown

### 2. Test Credentials

**Master Admin:**
- Username: `admin`
- Password: `password`
- Role: `MASTER_ADMIN`
- Can: Manage all users, create restaurants, assign users to restaurants

**Restaurant Admin:**
- Username: `adminres`
- Password: `password`
- Role: `RESTAURANT_ADMIN`
- Can: Manage their restaurant, menu, tables, orders, staff

**Chef:**
- Username: `adminchef`
- Password: `password`
- Role: `CHEF`
- Can: View and update order statuses in kitchen

## Complete Testing Journey

### Phase 1: Authentication & User Management (Master Admin)

#### Step 1: Login as Master Admin
```
Request: POST /api/v1/auth/login
Body:
{
    "username": "admin",
    "password": "password"
}
```
**Expected**: 200 OK with access_token and user details
**Auto-saved**: access_token, refresh_token, user_id

#### Step 2: List All Users
```
Request: GET /api/v1/auth/users
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of all users
**Validates**: Master admin can view all users in the system

#### Step 3: Create a New User
```
Request: POST /api/v1/auth/signup
Body:
{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "password123",
    "full_name": "Test User",
    "role": "RESTAURANT_ADMIN",
    "restaurant_id": null
}
```
**Expected**: 201 Created with user details
**Validates**: New users can be created

#### Step 4: Get User by ID
```
Request: GET /api/v1/auth/users/{{test_user_id}}
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with user details
**Validates**: Individual user lookup works

#### Step 5: Update User (Assign Restaurant)
```
Request: PUT /api/v1/auth/users/{{test_user_id}}
Body:
{
    "full_name": "Updated Test User",
    "role": "RESTAURANT_ADMIN",
    "restaurant_id": "{{restaurant_id}}",
    "is_active": true
}
```
**Expected**: 200 OK with updated user
**Validates**: Users can be updated and assigned to restaurants

### Phase 2: Restaurant Management

#### Step 6: List All Restaurants
```
Request: GET /api/v1/restaurants
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of restaurants
**Auto-saved**: restaurant_id, restaurant_slug

#### Step 7: Create New Restaurant
```
Request: POST /api/v1/restaurants
Body:
{
    "name": "Test Restaurant",
    "description": "A test restaurant for API testing",
    "address": "123 Test Street, Test City",
    "phone": "1234567890",
    "email": "test@restaurant.com",
    "website": "https://testrestaurant.com",
    "theme_color": "#3B82F6",
    "max_tables": 20
}
```
**Expected**: 201 Created with restaurant details
**Auto-saved**: new_restaurant_id
**Validates**: Master admin can create new restaurants

#### Step 8: Get Restaurant Details
```
Request: GET /api/v1/restaurants/{{restaurant_id}}
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with full restaurant details
**Validates**: Restaurant data retrieval

#### Step 9: Update Restaurant
```
Request: PUT /api/v1/restaurants/{{restaurant_id}}
Body:
{
    "name": "Updated Restaurant Name",
    "description": "Updated description",
    "phone": "9876543210"
}
```
**Expected**: 200 OK with updated restaurant
**Validates**: Restaurant information can be updated

### Phase 3: Menu Management (Restaurant Admin)

#### Step 10: Login as Restaurant Admin
```
Request: POST /api/v1/auth/login
Body:
{
    "username": "adminres",
    "password": "password"
}
```
**Expected**: 200 OK
**Auto-saved**: restaurant_admin_token, restaurant_id

#### Step 11: List Menu Items
```
Request: GET /api/v1/restaurants/{{restaurant_id}}/menu-items
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of menu items
**Auto-saved**: menu_item_id
**Validates**: Restaurant admin can view their menu

#### Step 12: Create Menu Item
```
Request: POST /api/v1/restaurants/{{restaurant_id}}/menu-items
Body:
{
    "name": "Margherita Pizza",
    "description": "Classic Italian pizza with tomato and mozzarella",
    "price": 12.99,
    "category": "Pizza",
    "is_vegetarian": true,
    "is_available": true,
    "preparation_time": 15
}
```
**Expected**: 201 Created
**Validates**: Menu items can be added

#### Step 13: Update Menu Item
```
Request: PUT /api/v1/restaurants/{{restaurant_id}}/menu-items/{{menu_item_id}}
Body:
{
    "name": "Deluxe Margherita Pizza",
    "price": 14.99,
    "is_available": true
}
```
**Expected**: 200 OK
**Validates**: Menu items can be updated

### Phase 4: Table Management

#### Step 14: List Tables
```
Request: GET /api/v1/restaurants/{{restaurant_id}}/tables
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of tables
**Auto-saved**: table_id

#### Step 15: Create Table
```
Request: POST /api/v1/restaurants/{{restaurant_id}}/tables
Body:
{
    "table_number": "T10",
    "capacity": 4,
    "location": "Main Hall"
}
```
**Expected**: 201 Created
**Validates**: Tables can be added to restaurant

#### Step 16: Get Table QR Code
```
Request: GET /api/v1/restaurants/{{restaurant_id}}/tables/{{table_id}}/qr-code
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with QR code data
**Validates**: QR codes are generated for tables

### Phase 5: Order Management

#### Step 17: Create Order (Customer - No Auth)
```
Request: POST /api/v1/orders
Body:
{
    "restaurant_id": "{{restaurant_id}}",
    "table_id": "{{table_id}}",
    "customer_name": "John Doe",
    "customer_phone": "1234567890",
    "items": [
        {
            "menu_item_id": "{{menu_item_id}}",
            "quantity": 2,
            "special_instructions": "Extra cheese"
        }
    ]
}
```
**Expected**: 201 Created with order details
**Auto-saved**: order_id
**Validates**: Customers can place orders without authentication

#### Step 18: List Orders (Restaurant Admin)
```
Request: GET /api/v1/restaurants/{{restaurant_id}}/orders
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of orders
**Validates**: Restaurant admin can view all orders

#### Step 19: Update Order Status (Chef)
```
Request: PATCH /api/v1/orders/{{order_id}}/status
Auth: Bearer {{access_token}}
Body:
{
    "status": "preparing"
}
```
**Expected**: 200 OK
**Validates**: Order status can be updated

### Phase 6: Feedback Management

#### Step 20: Submit Feedback (Customer)
```
Request: POST /api/v1/restaurants/{{restaurant_id}}/feedback
Body:
{
    "customer_name": "Jane Smith",
    "rating": 5,
    "comment": "Excellent food and service!",
    "order_id": "{{order_id}}"
}
```
**Expected**: 201 Created
**Validates**: Customers can submit feedback

#### Step 21: List Feedback (Restaurant Admin)
```
Request: GET /api/v1/restaurants/{{restaurant_id}}/feedback
Auth: Bearer {{access_token}}
```
**Expected**: 200 OK with array of feedback
**Validates**: Restaurant admin can view customer feedback

## Testing Workflows

### Workflow 1: Complete User Onboarding
1. Master admin creates restaurant (Step 7)
2. Master admin creates user (Step 3)
3. Master admin assigns user to restaurant (Step 5)
4. New user logs in and manages their restaurant

### Workflow 2: Customer Order Journey
1. Customer scans QR code (table_id)
2. Customer views menu (Step 11)
3. Customer places order (Step 17)
4. Chef receives order notification
5. Chef updates order status (Step 19)
6. Customer receives order
7. Customer submits feedback (Step 20)

### Workflow 3: Restaurant Setup
1. Create restaurant (Step 7)
2. Add menu items (Step 12)
3. Create tables (Step 15)
4. Generate QR codes (Step 16)
5. Assign staff (Step 5)

## Validation Checklist

### Authentication
- [ ] Master admin can login
- [ ] Restaurant admin can login
- [ ] Chef can login
- [ ] Invalid credentials are rejected
- [ ] JWT tokens are properly generated
- [ ] Refresh token works

### User Management (Master Admin Only)
- [ ] Can list all users
- [ ] Can create new users
- [ ] Can update user details
- [ ] Can assign users to restaurants
- [ ] Can change user roles
- [ ] Can delete users
- [ ] Non-master admin cannot access user management

### Restaurant Management
- [ ] Can list restaurants
- [ ] Can create restaurants
- [ ] Can update restaurant details
- [ ] Can view restaurant analytics
- [ ] Restaurant slug is unique

### Menu Management
- [ ] Can add menu items
- [ ] Can update menu items
- [ ] Can toggle item availability
- [ ] Can upload item images
- [ ] Items are categorized correctly

### Table Management
- [ ] Can create tables
- [ ] Can update table status
- [ ] QR codes are generated
- [ ] QR codes contain correct data

### Order Management
- [ ] Customers can place orders without auth
- [ ] Orders include all required details
- [ ] Order status can be updated
- [ ] Real-time updates work
- [ ] Order history is maintained

### Feedback Management
- [ ] Customers can submit feedback
- [ ] Ratings are validated (1-5)
- [ ] Restaurant admin can view feedback
- [ ] Feedback statistics are calculated

## Error Cases to Test

### Authentication Errors
- Login with invalid credentials → 401
- Access protected route without token → 401
- Use expired token → 401
- Non-admin user access admin endpoint → 403

### Validation Errors
- Create user with existing username → 400
- Create restaurant without required fields → 422
- Invalid email format → 422
- Negative menu item price → 422

### Authorization Errors
- Restaurant admin access another restaurant → 403
- Chef modify user details → 403
- Customer access admin endpoints → 401/403

## Performance Testing

### Load Testing Scenarios
1. **Concurrent Orders**: 100 simultaneous order creations
2. **Menu Browsing**: 1000 menu item list requests
3. **Order Status Updates**: Real-time updates for 50 orders
4. **User Creation**: Batch create 100 users

### Expected Response Times
- Authentication: < 500ms
- List endpoints: < 1000ms
- Create operations: < 1500ms
- Update operations: < 1000ms
- Real-time updates: < 2000ms

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Ensure you're logged in (Step 1 or Step 10)
- Check access_token is saved in environment
- Verify Bearer token is in Authorization header

**403 Forbidden**
- Check user role matches endpoint requirements
- Master admin endpoints require MASTER_ADMIN role
- Restaurant-specific endpoints require restaurant_id match

**404 Not Found**
- Verify resource IDs are saved in environment
- Check if resource was created successfully
- Ensure correct restaurant_id is used

**422 Unprocessable Entity**
- Check request body matches schema
- Verify all required fields are present
- Validate data types (strings, numbers, UUIDs)

## Environment Variables Reference

| Variable | Description | Set By |
|----------|-------------|--------|
| base_url | API base URL | Manual |
| access_token | JWT access token | Login response |
| refresh_token | JWT refresh token | Login response |
| user_id | Current user ID | Login response |
| user_role | Current user role | Login response |
| restaurant_id | Active restaurant ID | Restaurant list/login |
| restaurant_slug | Restaurant URL slug | Restaurant list |
| table_id | Active table ID | Table list |
| menu_item_id | Active menu item ID | Menu list |
| order_id | Active order ID | Order creation |
| test_user_id | Test user ID | User list |

## Next Steps

1. **Run Collection**: Use Postman Collection Runner to execute all requests sequentially
2. **Automated Testing**: Set up Newman for CI/CD integration
3. **Monitor**: Track response times and error rates
4. **Document**: Update this guide with any new endpoints or workflows

## Support

For issues or questions:
- Check application logs: `kubectl logs -n restaurant-system -l app=<service-name>`
- Review API documentation: `/docs` endpoint
- Contact: development team
