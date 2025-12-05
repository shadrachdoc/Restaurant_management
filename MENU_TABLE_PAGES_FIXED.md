# Menu & Table Pages Loading Issue - FIXED

## Problem Identified

The menu and table management pages were showing the sidebar but had infinite loading for the main content.

### Root Cause
- Frontend was using a **single axios instance** calling port 8001 for ALL API endpoints
- Port 8001 = **Auth Service** (only has `/api/v1/auth/*` endpoints)
- Port 8003 = **Restaurant Service** (has `/api/v1/restaurants/*`, menu, table endpoints)
- When frontend tried to fetch restaurants/menus/tables from port 8001, it got 404 errors
- This caused the infinite loading state in the UI

## Solution Implemented

### Updated File: `frontend/src/services/api.js`

Completely rewrote the API configuration to support **multiple microservices**:

#### Before (WRONG):
```javascript
// Single axios instance calling port 8001 for everything
const API_BASE_URL = 'http://localhost:8001';
const api = axios.create({ baseURL: API_BASE_URL });

// All APIs used the same instance
export const authAPI = { login: () => api.post(...) };
export const restaurantAPI = { list: () => api.get(...) };  // ❌ Wrong port!
export const menuAPI = { list: () => api.get(...) };        // ❌ Wrong port!
```

#### After (CORRECT):
```javascript
// Separate axios instances for each service
const AUTH_SERVICE_URL = 'http://localhost:8001';
const RESTAURANT_SERVICE_URL = 'http://localhost:8003';

const authApi = axios.create({ baseURL: AUTH_SERVICE_URL });
const restaurantApi = axios.create({ baseURL: RESTAURANT_SERVICE_URL });

// Auth endpoints use authApi (port 8001)
export const authAPI = {
  login: (credentials) => authApi.post('/api/v1/auth/login', credentials),
  signup: (userData) => authApi.post('/api/v1/auth/signup', userData),
  logout: () => authApi.post('/api/v1/auth/logout'),
  // ...
};

// Restaurant endpoints use restaurantApi (port 8003)
export const restaurantAPI = {
  list: (params) => restaurantApi.get('/api/v1/restaurants', { params }),
  create: (data) => restaurantApi.post('/api/v1/restaurants', data),
  update: (id, data) => restaurantApi.put(`/api/v1/restaurants/${id}`, data),
  // ...
};

// Menu endpoints use restaurantApi (port 8003)
export const menuAPI = {
  list: (restaurantId, params) =>
    restaurantApi.get(`/api/v1/restaurants/${restaurantId}/menu-items`, { params }),
  create: (restaurantId, data) =>
    restaurantApi.post(`/api/v1/restaurants/${restaurantId}/menu-items`, data),
  // ...
};

// Table endpoints use restaurantApi (port 8003)
export const tableAPI = {
  list: (restaurantId, params) =>
    restaurantApi.get(`/api/v1/restaurants/${restaurantId}/tables`, { params }),
  create: (restaurantId, data) =>
    restaurantApi.post(`/api/v1/restaurants/${restaurantId}/tables`, data),
  // ...
};

// Feedback endpoints use restaurantApi (port 8003)
export const feedbackAPI = {
  list: (restaurantId, params) =>
    restaurantApi.get(`/api/v1/restaurants/${restaurantId}/feedback`, { params }),
  create: (restaurantId, data) =>
    restaurantApi.post(`/api/v1/restaurants/${restaurantId}/feedback`, data),
  // ...
};
```

### Key Improvements

1. **Service Separation**:
   - Auth operations → `authApi` → Port 8001
   - Restaurant/Menu/Table/Feedback operations → `restaurantApi` → Port 8003

2. **Shared Interceptors**:
   - Created `addInterceptors()` helper function
   - Both axios instances get the same interceptors:
     - Request interceptor: Adds JWT token from localStorage
     - Response interceptor: Handles 401 errors with automatic token refresh

3. **Token Refresh Logic**:
   ```javascript
   // Response interceptor handles token refresh
   instance.interceptors.response.use(
     (response) => response,
     async (error) => {
       if (error.response?.status === 401 && !originalRequest._retry) {
         originalRequest._retry = true;
         const refreshToken = localStorage.getItem('refresh_token');
         if (refreshToken) {
           const response = await axios.post(`${AUTH_SERVICE_URL}/api/v1/auth/refresh`, {
             refresh_token: refreshToken,
           });
           const { access_token } = response.data;
           localStorage.setItem('access_token', access_token);
           originalRequest.headers.Authorization = `Bearer ${access_token}`;
           return instance(originalRequest);
         }
       }
       // If refresh fails, clear storage and redirect to login
       localStorage.clear();
       window.location.href = '/login';
       return Promise.reject(error);
     }
   );
   ```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Port 3001)                    │
│                                                              │
│  ┌──────────────┐              ┌─────────────────────────┐ │
│  │   authApi    │              │    restaurantApi        │ │
│  │ (port 8001)  │              │    (port 8003)          │ │
│  └──────┬───────┘              └───────┬─────────────────┘ │
└─────────┼─────────────────────────────┼────────────────────┘
          │                              │
          │                              │
          ▼                              ▼
┌──────────────────────┐    ┌────────────────────────────────┐
│  Auth Service        │    │  Restaurant Service            │
│  (Port 8001)         │    │  (Port 8003)                   │
│                      │    │                                │
│  • /auth/login       │    │  • /restaurants                │
│  • /auth/signup      │    │  • /restaurants/:id/menu-items │
│  • /auth/logout      │    │  • /restaurants/:id/tables     │
│  • /auth/refresh     │    │  • /restaurants/:id/feedback   │
│  • /users/me         │    │  • /restaurants/:id/analytics  │
└──────────────────────┘    └────────────────────────────────┘
```

## What Now Works

After this fix, the following pages should now load correctly:

✅ **Restaurant Management**
- Create restaurant
- List restaurants
- Update restaurant details
- Toggle restaurant status
- View restaurant analytics

✅ **Menu Management**
- Add menu items
- Edit menu items
- Toggle item availability
- Delete menu items

✅ **Table Management**
- Create tables
- Update table status (Available, Occupied, Reserved)
- Generate QR codes
- Regenerate QR codes

✅ **Feedback Management**
- View feedback
- Create feedback
- Get feedback summary/stats

## Testing the Fix

### 1. Frontend Should Auto-Reload
Vite has Hot Module Replacement (HMR), so the changes should be live immediately. If not:
```bash
# Check if frontend is running
curl http://localhost:3001

# If needed, restart frontend
cd /home/shadrach/Restaurant_management/frontend
npm run dev
```

### 2. Test Menu Page
1. Login to the application
2. Create or select a restaurant
3. Navigate to "Menu Management"
4. Page should load (not infinite loading)
5. Try adding a menu item

### 3. Test Table Page
1. Navigate to "Table Management"
2. Page should load with table list
3. Try creating a new table
4. Try generating a QR code

### 4. Verify API Calls in Browser DevTools
Open Browser DevTools → Network tab:
- Auth requests should go to `http://localhost:8001/api/v1/auth/*`
- Restaurant requests should go to `http://localhost:8003/api/v1/restaurants/*`
- All requests should get 200 OK (except expected errors)

## Current Service Status

All services are running and healthy:

```bash
# Check services
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8003/health  # Restaurant Service
curl http://localhost:3001         # Frontend
```

**Output:**
```
✓ Auth Service (8001) - {"status":"healthy","service":"auth-service"}
✓ Restaurant Service (8003) - {"status":"healthy","service":"restaurant-service"}
✓ Frontend (3001) - Serving React App
```

## Summary

✅ **Root Cause Fixed**: Frontend API was calling wrong service (auth instead of restaurant)
✅ **Solution Implemented**: Separate axios instances for each microservice
✅ **Auth Token Handling**: Interceptors add JWT to all requests automatically
✅ **Token Refresh**: Automatic refresh on 401 errors
✅ **All Services Running**: Auth (8001), Restaurant (8003), Frontend (3001)
✅ **Vite HMR Active**: Changes should be live without restart

**The menu and table pages should now work correctly. Try navigating to them in the browser!**
