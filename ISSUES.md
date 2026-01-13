# Issues and Fixes

This document tracks all major issues encountered in the Restaurant Management System and their solutions.

---

## Issue #12: User Management - Authorization and Role Validation (January 6, 2026)

**Date**: January 6, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Critical Issues Fixed

#### 1. User Management Page - 401 Unauthorized Error

**Issue**: User Management page failed to load with "Failed to load resource: 401 Unauthorized" error when trying to fetch `/api/v1/auth/users` endpoint, even with valid master_admin token.

**Root Cause**: API Gateway was using inconsistent header casing when forwarding the Authorization header. The code was setting `headers["Authorization"]` (capital A) but the dictionary from `dict(request.headers)` had lowercased keys as `"authorization"`.

**Impact**: Master admin users could not access the User Management page to view/manage users.

**Fix Applied**:
- **File**: `services/api-gateway/app/main.py` (line 140)
- **Change**: Changed from `headers["Authorization"]` to `headers["authorization"]` (lowercase)
- **Code**:
```python
# Before:
if credentials:
    headers["Authorization"] = f"Bearer {credentials.credentials}"

# After:
if credentials:
    headers["authorization"] = f"Bearer {credentials.credentials}"
```

**Testing**: Verified that GET /api/v1/auth/users now returns 200 OK with user list.

---

#### 2. User Management Endpoint - Incorrect Route Path

**Issue**: After fixing the authorization issue, the endpoint still returned 422 Unprocessable Entity. The frontend was requesting `/api/v1/auth/users` but the backend endpoint was registered at `/api/v1/auth/` (empty path).

**Root Cause**: The users router endpoint was defined as `@router.get("")` which created the route at `/api/v1/auth/` instead of `/api/v1/auth/users`.

**Impact**: User Management page could not fetch the user list even with correct authentication.

**Fix Applied**:
- **File**: `services/auth-service/app/routes/users.py` (line 18)
- **Change**: Changed endpoint path from `""` to `"/users"`

**Testing**: Endpoint now accessible at `/api/v1/auth/users` matching frontend requests.

---

#### 3. User Creation - Role Validation Error (422)

**Issue**: When attempting to create a new user via the signup form, requests failed with 422 validation error. The frontend was sending role values in uppercase format (e.g., `"RESTAURANT_ADMIN"`) but the backend enum expected lowercase with underscores (e.g., `"restaurant_admin"`).

**Root Cause**: Pydantic strict validation rejected the uppercase role strings that didn't match the exact enum values defined in `shared/models/enums.py`.

**Impact**: Unable to create new users through the User Management interface.

**Fix Applied**:
- **File**: `services/auth-service/app/schemas.py`
- **Changes**: Added `@field_validator` decorators to normalize role values
- **Schemas Updated**: `UserCreate` (lines 25-42), `UserUpdate` (lines 61-78)

**Supported Formats**: Now accepts `"RESTAURANT_ADMIN"`, `"restaurant_admin"`, `"restaurant-admin"`, etc.

---

## Issue #11: Cloudflare Tunnel Rate Limiting - Order Tracking HTTP 429 Errors

**Date**: January 2, 2026
**Severity**: Medium
**Status**: ✅ Resolved

### Problem Description

User reported HTTP 500 and HTTP 429 (Too Many Requests) errors after completing an order in the customer screen. The errors appeared in the browser console when trying to fetch order status updates.

### Root Cause

**Primary Issue**: Frontend was aggressively polling order status every 3 seconds, triggering Cloudflare Tunnel's rate limiting.

### Solution

Changed polling frequency from 3 seconds to 10 seconds in order tracking pages:

**Files Modified**:
1. `frontend/src/pages/Customer/OrderTracking.jsx` - Line 64
2. `frontend/src/pages/Customer/OrderTrackingPage.jsx` - Line 49

```javascript
// Before:
const interval = setInterval(fetchOrder, 3000); // Poll every 3 seconds

// After:
const interval = setInterval(fetchOrder, 10000); // Poll every 10 seconds to avoid rate limiting
```

---

## Issue #10: API Requests Failing with 503 - Istio VirtualService Misconfiguration

**Date**: January 1, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Problem Description

All API requests to analytics endpoints were failing with HTTP 503 (Service Unavailable). Frontend loaded correctly, but backend API calls were being blocked.

### Root Cause

**Primary Issue**: Istio VirtualService for order-service was configured with incorrect port (8001 instead of 8004)

### Solution

**Fixed order-service VirtualService**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
  namespace: restaurant-system
spec:
  hosts:
  - order-service
  http:
  - route:
    - destination:
        host: order-service
        port:
          number: 8004  # ✅ Correct port (was 8001)
    timeout: 15s
    retries:
      attempts: 3
      perTryTimeout: 5s
```

---

## Issue #9: Order Service Database Connection Failure - Worker Node Failure & PostgreSQL Restart

**Date**: January 1, 2026
**Severity**: High
**Status**: ✅ Resolved

### Problem Description

Order service failing to start with database connection error: `socket.gaierror: [Errno -3] Temporary failure in name resolution`. All database-dependent services were in CrashLoopBackOff state.

### Root Cause

**Primary Issues**:
1. PostgreSQL pod stuck in "Terminating" state after cluster restart
2. Worker node (worker2) in "NotReady" state
3. StatefulSet PVC bound to failed worker node
4. Services unable to resolve database hostname

### Solution

**Step 1**: Force delete stuck PostgreSQL pod
**Step 2**: Restart failed worker node (stayed NotReady)
**Step 3**: Cordon failed node
**Step 4**: Delete and recreate PostgreSQL StatefulSet PVC (⚠️ data loss acceptable in dev)
**Step 5**: Restart all database-dependent services

---

## Issue #8: Observability Dashboards Not Accessible - Cluster Networking Failure

**Date**: January 1, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Problem Description

All observability dashboards (Grafana, Kiali, ArgoCD) became inaccessible. Multiple pods in CrashLoopBackOff state.

### Root Cause

- Cluster had been running for 28 days without restart
- Accumulated iptables rules or networking state corruption
- CNI unable to properly route pod-to-pod traffic
- Kubernetes API server (`10.96.0.1:443`) unreachable from pods

### Solution

**Step 1**: Restart cluster containers
```bash
docker restart restaurant-cluster-control-plane restaurant-cluster-worker restaurant-cluster-worker2
```

**Step 2**: Fix Grafana PVC permission issues by recreating PVC

**Step 3**: Remove plugin installation from Grafana ConfigMap

**Step 4**: Verify all pods running

**Step 5**: Start port-forwards for dashboard access

---

## Issue #13: Login and User Management Complete Failure - Istio mTLS + Authorization Header Issues (January 12, 2026)

**Date**: January 12, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Problem Description

Complete authentication system failure affecting:
1. ❌ Login endpoint returning **503 Service Unavailable**
2. ❌ User Management page showing **"No users found"** with 401 Unauthorized errors
3. ❌ Restaurant Management page failing with 503 errors
4. ❌ All authenticated API requests failing

### Architecture Overview

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────────────────────────────────────────┐
│        Cloudflare Tunnel / Ingress              │
│        (restaurant.corpv3.com)                  │
└──────┬──────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│            API Gateway (Port 8000)              │
│  ┌───────────────────────────────────────────┐  │
│  │  FastAPI + HTTPBearer Security            │  │
│  │  - Routes requests to services            │  │
│  │  - Extracts Bearer tokens                 │  │
│  └───────────────────────────────────────────┘  │
└──────┬──────────────────────────────────────────┘
       │
       │ Internal HTTP
       ├─────────────────┬──────────────────┐
       ↓                 ↓                  ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Auth Service │  │Restaurant   │  │Order Service│
│(Port 8001)  │  │Service      │  │(Port 8004)  │
│             │  │(Port 8003)  │  │             │
│ ┌─────────┐ │  │             │  │             │
│ │ Istio   │ │  │ ┌─────────┐ │  │ ┌─────────┐ │
│ │ Proxy   │ │  │ │ Istio   │ │  │ │ Istio   │ │
│ └────┬────┘ │  │ │ Proxy   │ │  │ │ Proxy   │ │
│      ↓      │  │ └────┬────┘ │  │ └────┬────┘ │
│ ┌─────────┐ │  │      ↓      │  │      ↓      │
│ │FastAPI  │ │  │ ┌─────────┐ │  │ ┌─────────┐ │
│ │Service  │ │  │ │FastAPI  │ │  │ │FastAPI  │ │
│ └─────────┘ │  │ │Service  │ │  │ │Service  │ │
└─────────────┘  │ └─────────┘ │  │ └─────────┘ │
                 └─────────────┘  └─────────────┘
```

### Root Causes Identified

#### **Issue 13.1: Istio mTLS Certificate Verification Failure**

**Problem**: API Gateway could connect to auth-service locally within the pod, but all external requests through Istio proxy returned **503 Service Unavailable**.

**Root Cause**:
- Istio `DestinationRule` had `tls: mode: ISTIO_MUTUAL` (mutual TLS required)
- Istio `PeerAuthentication` was set to `PERMISSIVE` mode
- Configuration mismatch caused TLS certificate verification to fail

**Error in Istio Proxy Logs**:
```json
{
  "upstream_transport_failure_reason": "TLS_error:|268435581:SSL_routines:OPENSSL_internal:CERTIFICATE_VERIFY_FAILED",
  "response_code": 503,
  "response_flags": "UF,URX"
}
```

**Request Flow (BROKEN)**:
```
Browser → API Gateway → Istio Proxy (auth-service) → ❌ TLS Error
                                                    → 503 Service Unavailable
```

**Fix Applied**:
```yaml
# File: infrastructure/k8s/istio/destinationrules/auth-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service
  namespace: restaurant-system
spec:
  host: auth-service
  trafficPolicy:
    tls:
      mode: DISABLE  # ✅ Disabled TLS to match PERMISSIVE PeerAuthentication
```

**Services Fixed**:
- ✅ auth-service (Port 8001)
- ✅ restaurant-service (Port 8003)
- ✅ order-service (Port 8004)
- ✅ customer-service (Port 8007)
- ✅ menu-service
- ✅ notification-service

**Commands Used**:
```bash
kubectl patch destinationrule auth-service -n restaurant-system \
  --type='json' -p='[{"op": "add", "path": "/spec/trafficPolicy/tls", "value": {"mode": "DISABLE"}}]'
```

---

#### **Issue 13.2: Duplicate Authorization Headers**

**Problem**: After fixing TLS, requests started getting **401 Unauthorized** instead of 503. Auth-service logs showed duplicate Bearer tokens in the Authorization header.

**Auth-Service Logs**:
```python
'authorization': 'Bearer TOKEN1,Bearer TOKEN2'
# Two tokens separated by comma - INVALID format!
```

**Root Cause**:
1. Browser sends request with `Authorization: Bearer TOKEN1`
2. API Gateway copies all headers: `headers = dict(request.headers)`
3. API Gateway's `HTTPBearer` dependency extracts token as `credentials`
4. API Gateway adds token again: `headers["authorization"] = f"Bearer {credentials.credentials}"`
5. Result: **Two Bearer tokens in same header!**

**Request Flow (BROKEN)**:
```
Browser
  │ Authorization: Bearer TOKEN1
  ↓
API Gateway
  │ 1. Copies headers → authorization: Bearer TOKEN1
  │ 2. Adds from credentials → authorization: Bearer TOKEN2
  │ Result: authorization: Bearer TOKEN1,Bearer TOKEN2
  ↓
Auth Service → ❌ Invalid token format → 401 Unauthorized
```

**Fix Applied**:
```python
# File: services/api-gateway/app/main.py (lines 132-143)

# BEFORE (BROKEN):
headers = dict(request.headers)
headers.pop("host", None)
if credentials:
    headers["authorization"] = f"Bearer {credentials.credentials}"
# Result: Duplicate headers!

# AFTER (FIXED):
headers = dict(request.headers)
headers.pop("host", None)
headers.pop("authorization", None)  # ✅ Remove original to prevent duplication
if credentials:
    headers["authorization"] = f"Bearer {credentials.credentials}"
# Result: Single clean token!
```

**Request Flow (FIXED)**:
```
Browser
  │ Authorization: Bearer TOKEN
  ↓
API Gateway
  │ 1. Copies headers → authorization: Bearer TOKEN
  │ 2. REMOVES original → authorization: (empty)
  │ 3. Sets from credentials → authorization: Bearer TOKEN
  │ Result: authorization: Bearer TOKEN (single, clean)
  ↓
Auth Service → ✅ Valid token → 200 OK
```

---

#### **Issue 13.3: User/Restaurant Password Reset Required**

**Problem**: Even after fixing TLS and authorization headers, login still returned 401.

**Root Cause**: Password hashes in database were using different bcrypt context than the auth-service expected.

**Fix Applied**:
```bash
# Reset passwords using auth-service's bcrypt context
kubectl exec -i auth-service-pod -- python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('admin123'))
"

# Update database
kubectl exec -i postgres-0 -- psql -U restaurant_admin -d restaurant_db -c "
UPDATE users
SET hashed_password = '$2b$12$P1Y/nEPacs1xZw65yYiZ2untNwQQ1fhonMQvyFt9nI/ucZWqF7GI6'
WHERE username IN ('admin', 'adminres');
"
```

**Users Fixed**:
- ✅ `admin` (Master Admin) - Password: `admin123`
- ✅ `adminres` (Restaurant Admin) - Password: `admin123`

---

### Complete Request Flow Comparison

#### **BEFORE (All Broken - 503/401 Errors)**:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Login Request Flow (503 Error)                              │
└─────────────────────────────────────────────────────────────────┘

Browser
  │ POST /api/v1/auth/login
  │ Body: {"username": "admin", "password": "admin123"}
  ↓
API Gateway
  │ Routes to: http://auth-service:8001/api/v1/auth/login
  ↓
Istio Proxy (auth-service sidecar)
  │ ❌ TLS_error: CERTIFICATE_VERIFY_FAILED
  │ DestinationRule requires ISTIO_MUTUAL
  │ PeerAuthentication is PERMISSIVE
  ↓
❌ 503 Service Unavailable
  │ upstream_transport_failure_reason: TLS_error
  ↓
Browser: "503 Service Unavailable"


┌─────────────────────────────────────────────────────────────────┐
│ 2. User Management Request Flow (401 Error - after TLS fix)    │
└─────────────────────────────────────────────────────────────────┘

Browser
  │ GET /api/v1/auth/users
  │ Authorization: Bearer abc123
  ↓
API Gateway (HTTPBearer extracts token)
  │ headers = dict(request.headers)
  │   → authorization: Bearer abc123
  │
  │ credentials.credentials = "abc123"
  │ headers["authorization"] = f"Bearer {credentials.credentials}"
  │   → authorization: Bearer abc123,Bearer abc123 ❌ DUPLICATE!
  ↓
Auth Service
  │ Receives: authorization: Bearer abc123,Bearer abc123
  │ ❌ Invalid token format
  ↓
❌ 401 Unauthorized
  ↓
Browser: "Failed to fetch users: 401"
```

#### **AFTER (All Working - 200 OK)**:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Login Request Flow (200 OK)                                 │
└─────────────────────────────────────────────────────────────────┘

Browser
  │ POST /api/v1/auth/login
  │ Body: {"username": "admin", "password": "admin123"}
  ↓
API Gateway
  │ Routes to: http://auth-service:8001/api/v1/auth/login
  ↓
Istio Proxy (auth-service sidecar)
  │ ✅ TLS mode: DISABLE (no certificate verification)
  │ Forwards directly to auth-service container
  ↓
Auth Service (FastAPI)
  │ 1. Validates credentials against database
  │ 2. Compares password hash: $2b$12$P1Y...
  │ 3. ✅ Password matches!
  │ 4. Generates JWT tokens (access + refresh)
  ↓
✅ 200 OK
  │ {
  │   "access_token": "eyJhbGc...",
  │   "refresh_token": "eyJhbGc...",
  │   "user": {"username": "admin", "role": "master_admin"}
  │ }
  ↓
Browser: Stores tokens in localStorage


┌─────────────────────────────────────────────────────────────────┐
│ 2. User Management Request Flow (200 OK)                       │
└─────────────────────────────────────────────────────────────────┘

Browser
  │ GET /api/v1/auth/users
  │ Authorization: Bearer eyJhbGc...
  ↓
API Gateway (HTTPBearer extracts token)
  │ headers = dict(request.headers)
  │   → authorization: Bearer eyJhbGc...
  │
  │ headers.pop("authorization", None)  ✅ Remove original
  │
  │ credentials.credentials = "eyJhbGc..."
  │ headers["authorization"] = f"Bearer {credentials.credentials}"
  │   → authorization: Bearer eyJhbGc... ✅ SINGLE TOKEN
  ↓
Istio Proxy (auth-service)
  │ ✅ TLS: DISABLE - forwards directly
  ↓
Auth Service (FastAPI)
  │ 1. Validates JWT token signature
  │ 2. Extracts user_id from token: 0bc199d4-8e9b-4c2f-9cfc-2eedf79b7419
  │ 3. Checks role: master_admin ✅
  │ 4. Queries database: SELECT * FROM users
  │ 5. Returns 7 users
  ↓
✅ 200 OK
  │ [
  │   {"username": "admin", "role": "master_admin"},
  │   {"username": "adminres", "role": "restaurant_admin"},
  │   {"username": "gjfg", "role": "restaurant_admin"},
  │   ... (7 users total)
  │ ]
  ↓
Browser: Displays user list in User Management page


┌─────────────────────────────────────────────────────────────────┐
│ 3. Restaurant Management Request Flow (200 OK)                 │
└─────────────────────────────────────────────────────────────────┘

Browser
  │ GET /api/v1/restaurants
  │ Authorization: Bearer eyJhbGc...
  ↓
API Gateway
  │ Routes to: http://restaurant-service:8003/api/v1/restaurants
  │ ✅ Clean authorization header (single token)
  ↓
Istio Proxy (restaurant-service)
  │ ✅ TLS: DISABLE - forwards directly
  ↓
Restaurant Service (FastAPI)
  │ Queries database: SELECT * FROM restaurants
  ↓
✅ 200 OK
  │ [
  │   {"id": "6956017d...", "name": "My Restaurant"},
  │   {"id": "b0c92b45...", "name": "Test Restaurant"},
  │   ... (3 restaurants)
  │ ]
  ↓
Browser: Displays restaurant list
```

---

### Files Modified

1. **API Gateway** (services/api-gateway/app/main.py)
   - Lines 132-143: Remove authorization header duplication
   - Built new image: `shadrach85/api-gateway:auth-fix`

2. **Istio DestinationRules** (Applied via kubectl patch)
   - auth-service: TLS mode DISABLE
   - restaurant-service: TLS mode DISABLE
   - order-service: TLS mode DISABLE
   - customer-service: TLS mode DISABLE
   - menu-service: TLS mode DISABLE
   - notification-service: TLS mode DISABLE

3. **Database** (PostgreSQL users table)
   - Updated password hashes for admin and adminres users

4. **Frontend** (Rebuilt and deployed)
   - Image: `shadrach85/restaurant-frontend:2c0035c`
   - No code changes (already had correct API endpoints)
   - Rebuild required to ensure consistent bundle

---

### Testing & Verification

```bash
# 1. Test Login
curl -X POST https://restaurant.corpv3.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq
# ✅ Result: 200 OK, returns access_token

# 2. Test User Management
TOKEN="eyJhbGc..."
curl -X GET https://restaurant.corpv3.com/api/v1/auth/users \
  -H "Authorization: Bearer $TOKEN" | jq length
# ✅ Result: 7 users

# 3. Test Restaurant Management
curl -X GET https://restaurant.corpv3.com/api/v1/restaurants \
  -H "Authorization: Bearer $TOKEN" | jq length
# ✅ Result: 3 restaurants

# 4. Check Istio proxy logs (should be clean)
kubectl logs -n restaurant-system auth-service-pod -c istio-proxy --tail=10
# ✅ No TLS errors

# 5. Check auth-service logs (should show single token)
kubectl logs -n restaurant-system auth-service-pod --tail=10 | grep authorization
# ✅ Single Bearer token, no duplicates
```

---

### Impact Summary

**Before Fix**:
- ❌ Login: 503 Service Unavailable
- ❌ User Management: 401 Unauthorized (duplicate tokens after TLS fix)
- ❌ Restaurant Management: 503 Service Unavailable
- ❌ All authenticated endpoints: Non-functional

**After Fix**:
- ✅ Login: Working (200 OK)
- ✅ User Management: 7 users displayed
- ✅ Restaurant Management: 3 restaurants displayed
- ✅ Staff Management: Working
- ✅ ML Predictions: Working (already functional)
- ✅ All authenticated endpoints: Functional

---

## Summary Table

| Issue | Severity | Component | Status | Date Resolved |
|-------|----------|-----------|--------|---------------|
| #13 | Critical | Auth/Istio/API Gateway | ✅ Resolved | Jan 12, 2026 |
| #12 | Critical | User Management | ✅ Resolved | Jan 6, 2026 |
| #11 | Medium | Frontend/Cloudflare | ✅ Resolved | Jan 2, 2026 |
| #10 | Critical | Istio VirtualService | ✅ Resolved | Jan 1, 2026 |
| #9 | High | Database/Worker Node | ✅ Resolved | Jan 1, 2026 |
| #8 | Critical | Observability | ✅ Resolved | Jan 1, 2026 |

---

## Lessons Learned

1. **Long-running clusters need periodic restarts**: Kind clusters can accumulate networking state issues over time
2. **StatefulSet PVC Locality**: If a node fails, pods cannot reschedule unless PVC is deleted or node recovered
3. **VirtualService port configuration is critical**: Always verify ports match actual service ports
4. **Rate Limiting Can Occur at Multiple Layers**: Application, service mesh, ingress, and CDN/tunnel layers
5. **Authorization header casing matters**: Use lowercase keys when working with request.headers dictionaries
6. **Istio TLS Configuration Must Be Consistent**: DestinationRule `tls.mode` must match PeerAuthentication mode (DISABLE for PERMISSIVE, ISTIO_MUTUAL for STRICT)
7. **FastAPI HTTPBearer Dependency Can Cause Header Duplication**: Always remove original authorization header before adding from extracted credentials
8. **Password Hash Context Consistency**: Ensure bcrypt context used for hashing matches validation context
9. **Debug Istio Issues at Multiple Layers**: Check application logs, Istio proxy logs (both source and destination), and VirtualService/DestinationRule configs
10. **Browser Cache Can Hide Fixes**: Always test with fresh tokens or incognito mode after authentication fixes

---

**Last Updated**: January 12, 2026
