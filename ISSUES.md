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

## Summary Table

| Issue | Severity | Component | Status | Date Resolved |
|-------|----------|-----------|--------|---------------|
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

---

**Last Updated**: January 6, 2026
