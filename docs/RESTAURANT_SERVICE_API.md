# Restaurant Service API Documentation

Complete API reference for the Restaurant Service.

**Base URL**: `http://localhost:8003/api/v1`

## Table of Contents

1. [Restaurant Management](#restaurant-management)
2. [Menu Items](#menu-items)
3. [Table Management](#table-management)
4. [Feedback](#feedback)

---

## Restaurant Management

### Create Restaurant

Create a new restaurant.

**Endpoint**: `POST /restaurants`

**Request Body**:
```json
{
  "name": "The Amazing Restaurant",
  "description": "Best food in town",
  "email": "contact@amazing.com",
  "phone": "+1234567890",
  "address": "123 Main St, City",
  "website": "https://amazing.com",
  "theme_color": "#FF5733",
  "pricing_plan": "premium",
  "max_tables": 50
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "name": "The Amazing Restaurant",
  "subscription_status": "trial",
  "pricing_plan": "premium",
  "is_active": true,
  "created_at": "2025-12-03T10:00:00Z"
}
```

---

### List All Restaurants

Get all restaurants with optional filtering.

**Endpoint**: `GET /restaurants`

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (default: 100)
- `is_active` (bool): Filter by active status

**Response**: `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Restaurant 1",
    "is_active": true
  }
]
```

---

### Get Restaurant by ID

Get specific restaurant details.

**Endpoint**: `GET /restaurants/{restaurant_id}`

**Response**: `200 OK`

---

### Update Restaurant

Update restaurant details.

**Endpoint**: `PUT /restaurants/{restaurant_id}`

**Request Body**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "theme_color": "#000000"
}
```

**Response**: `200 OK`

---

### Update Restaurant Branding

Update logos, banners, events, and advertisements.

**Endpoint**: `PATCH /restaurants/{restaurant_id}/branding`

**Request Body**:
```json
{
  "logo_url": "https://cdn.example.com/logo.png",
  "theme_color": "#FF5733",
  "banner_images": [
    "https://cdn.example.com/banner1.jpg",
    "https://cdn.example.com/banner2.jpg"
  ],
  "upcoming_events": [
    {
      "title": "Live Music Night",
      "date": "2025-12-15",
      "description": "Jazz band performance"
    }
  ],
  "advertisements": [
    {
      "title": "Happy Hour",
      "content": "50% off drinks 5-7 PM"
    }
  ]
}
```

**Response**: `200 OK`

---

### Delete Restaurant

Delete a restaurant (Master Admin only).

**Endpoint**: `DELETE /restaurants/{restaurant_id}`

**Response**: `200 OK`
```json
{
  "message": "Restaurant deleted successfully"
}
```

---

### Toggle Restaurant Status

Activate/deactivate restaurant.

**Endpoint**: `PATCH /restaurants/{restaurant_id}/toggle-status`

**Response**: `200 OK`

---

### Get Restaurant Analytics

Get statistics and analytics.

**Endpoint**: `GET /restaurants/{restaurant_id}/analytics`

**Response**: `200 OK`
```json
{
  "total_menu_items": 45,
  "total_tables": 20,
  "available_tables": 15,
  "occupied_tables": 5,
  "total_feedback": 120,
  "average_rating": 4.5,
  "menu_items_by_category": {
    "appetizer": 10,
    "main_course": 20,
    "dessert": 8,
    "beverage": 7
  }
}
```

---

## Menu Items

### Create Menu Item

Add a new menu item.

**Endpoint**: `POST /restaurants/{restaurant_id}/menu-items`

**Request Body**:
```json
{
  "name": "Margherita Pizza",
  "description": "Classic Italian pizza",
  "category": "main_course",
  "price": 12.99,
  "image_url": "https://cdn.example.com/pizza.jpg",
  "is_vegetarian": true,
  "is_vegan": false,
  "is_gluten_free": false,
  "preparation_time": 15,
  "calories": 800,
  "ingredients": ["tomato", "mozzarella", "basil"],
  "allergens": ["dairy", "gluten"],
  "display_order": 1
}
```

**Response**: `201 Created`

---

### List Menu Items

Get all menu items with filters.

**Endpoint**: `GET /restaurants/{restaurant_id}/menu-items`

**Query Parameters**:
- `category` (MenuItemCategory): Filter by category
- `is_available` (bool): Filter by availability
- `is_vegetarian` (bool): Vegetarian items only
- `is_vegan` (bool): Vegan items only
- `is_gluten_free` (bool): Gluten-free items only
- `skip` (int): Pagination offset
- `limit` (int): Items per page

**Response**: `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Margherita Pizza",
    "category": "main_course",
    "price": 12.99,
    "is_available": true,
    "is_vegetarian": true
  }
]
```

---

### Get Menu Item by ID

Get specific menu item.

**Endpoint**: `GET /restaurants/{restaurant_id}/menu-items/{item_id}`

**Response**: `200 OK`

---

### Update Menu Item

Update menu item details.

**Endpoint**: `PUT /restaurants/{restaurant_id}/menu-items/{item_id}`

**Request Body**:
```json
{
  "price": 13.99,
  "is_available": true,
  "description": "Updated description"
}
```

**Response**: `200 OK`

---

### Delete Menu Item

Remove a menu item.

**Endpoint**: `DELETE /restaurants/{restaurant_id}/menu-items/{item_id}`

**Response**: `200 OK`
```json
{
  "message": "Menu item deleted successfully"
}
```

---

### Toggle Menu Item Availability

Make item available/unavailable.

**Endpoint**: `PATCH /restaurants/{restaurant_id}/menu-items/{item_id}/toggle-availability`

**Response**: `200 OK`

---

### Get Menu Items by Category

Get all items in a specific category.

**Endpoint**: `GET /restaurants/{restaurant_id}/menu-items/category/{category}`

**Category Values**:
- `appetizer`
- `main_course`
- `dessert`
- `beverage`
- `side_dish`
- `special`

**Response**: `200 OK`

---

## Table Management

### Create Table

Add a new table.

**Endpoint**: `POST /restaurants/{restaurant_id}/tables`

**Request Body**:
```json
{
  "table_number": "T-01",
  "seat_count": 4,
  "floor": "Ground",
  "section": "Window Side"
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "table_number": "T-01",
  "seat_count": 4,
  "status": "available",
  "qr_code_url": "data:image/png;base64,iVBORw0KG...",
  "qr_code_data": "unique-token",
  "created_at": "2025-12-03T10:00:00Z"
}
```

---

### List Tables

Get all tables with filters.

**Endpoint**: `GET /restaurants/{restaurant_id}/tables`

**Query Parameters**:
- `status` (TableStatus): Filter by status
- `floor` (string): Filter by floor
- `section` (string): Filter by section
- `skip` (int): Pagination offset
- `limit` (int): Items per page

**Table Status Values**:
- `available`
- `occupied`
- `reserved`
- `cleaning`

**Response**: `200 OK`

---

### Get Table by ID

Get specific table.

**Endpoint**: `GET /restaurants/{restaurant_id}/tables/{table_id}`

**Response**: `200 OK`

---

### Update Table

Update table details.

**Endpoint**: `PUT /restaurants/{restaurant_id}/tables/{table_id}`

**Request Body**:
```json
{
  "table_number": "T-02",
  "seat_count": 6,
  "status": "occupied",
  "floor": "First Floor"
}
```

**Response**: `200 OK`

---

### Delete Table

Remove a table.

**Endpoint**: `DELETE /restaurants/{restaurant_id}/tables/{table_id}`

**Response**: `200 OK`

---

### Update Table Status

Change table status.

**Endpoint**: `PATCH /restaurants/{restaurant_id}/tables/{table_id}/status?new_status=occupied`

**Query Parameters**:
- `new_status` (TableStatus): New status value

**Response**: `200 OK`

---

### Regenerate QR Code

Generate new QR code for a table.

**Endpoint**: `POST /restaurants/{restaurant_id}/tables/{table_id}/regenerate-qr`

**Response**: `200 OK`
```json
{
  "table_id": "uuid",
  "table_number": "T-01",
  "qr_code_url": "data:image/png;base64,...",
  "qr_code_data": "new-unique-token"
}
```

---

### Get Table QR Code

Get existing QR code for a table.

**Endpoint**: `GET /restaurants/{restaurant_id}/tables/{table_id}/qr-code`

**Response**: `200 OK`

---

## Feedback

### Submit Feedback

Submit customer feedback.

**Endpoint**: `POST /restaurants/{restaurant_id}/feedback`

**Request Body**:
```json
{
  "rating": 5,
  "comment": "Excellent food and service!",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "table_id": "uuid"
}
```

**Response**: `201 Created`

---

### List Feedback

Get all feedback with filters.

**Endpoint**: `GET /restaurants/{restaurant_id}/feedback`

**Query Parameters**:
- `min_rating` (int): Minimum rating (1-5)
- `max_rating` (int): Maximum rating (1-5)
- `days` (int): Feedback from last N days
- `skip` (int): Pagination offset
- `limit` (int): Items per page

**Response**: `200 OK`

---

### Get Feedback by ID

Get specific feedback.

**Endpoint**: `GET /restaurants/{restaurant_id}/feedback/{feedback_id}`

**Response**: `200 OK`

---

### Delete Feedback

Remove feedback (Admin only).

**Endpoint**: `DELETE /restaurants/{restaurant_id}/feedback/{feedback_id}`

**Response**: `200 OK`

---

### Get Feedback Summary

Get feedback statistics.

**Endpoint**: `GET /restaurants/{restaurant_id}/feedback/stats/summary?days=30`

**Query Parameters**:
- `days` (int): Period in days (default: 30)

**Response**: `200 OK`
```json
{
  "total_feedback": 120,
  "average_rating": 4.5,
  "rating_distribution": {
    "1": 2,
    "2": 5,
    "3": 15,
    "4": 38,
    "5": 60
  },
  "period_days": 30,
  "five_star_percentage": 50.0,
  "four_plus_percentage": 81.7
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation error",
  "detail": "Invalid field value"
}
```

### 401 Unauthorized
```json
{
  "error": "Not authenticated",
  "detail": "Missing or invalid token"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions",
  "detail": "User does not have required role"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

---

## Testing the API

### Using cURL

```bash
# Create a restaurant
curl -X POST http://localhost:8003/api/v1/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "theme_color": "#FF5733",
    "pricing_plan": "basic"
  }'

# List restaurants
curl http://localhost:8003/api/v1/restaurants

# Create menu item
curl -X POST http://localhost:8003/api/v1/restaurants/{restaurant_id}/menu-items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pizza",
    "category": "main_course",
    "price": 12.99
  }'
```

### Using Swagger UI

Access interactive API documentation at:
http://localhost:8003/docs

---

For more information, see:
- [Main README](../README.md)
- [Getting Started](GETTING_STARTED.md)
- [Kubernetes Deployment](KUBERNETES.md)
