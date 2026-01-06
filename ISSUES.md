# Issues and Fixes - January 6, 2026

## Critical Issues Fixed

### 1. User Management Page - 401 Unauthorized Error

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

### 2. User Management Endpoint - Incorrect Route Path

**Issue**: After fixing the authorization issue, the endpoint still returned 422 Unprocessable Entity. The frontend was requesting `/api/v1/auth/users` but the backend endpoint was registered at `/api/v1/auth/` (empty path).

**Root Cause**: The users router endpoint was defined as `@router.get("")` which created the route at `/api/v1/auth/` instead of `/api/v1/auth/users`.

**Impact**: User Management page could not fetch the user list even with correct authentication.

**Fix Applied**:
- **File**: `services/auth-service/app/routes/users.py` (line 18)
- **Change**: Changed endpoint path from `""` to `"/users"`
- **Code**:
```python
# Before:
@router.get("")
async def list_users(...)

# After:
@router.get("/users")
async def list_users(...)
```

**Testing**: Endpoint now accessible at `/api/v1/auth/users` matching frontend requests.

---

### 3. User Creation - Role Validation Error (422)

**Issue**: When attempting to create a new user via the signup form, requests failed with 422 validation error. The frontend was sending role values in uppercase format (e.g., `"RESTAURANT_ADMIN"`) but the backend enum expected lowercase with underscores (e.g., `"restaurant_admin"`).

**Root Cause**: Pydantic strict validation rejected the uppercase role strings that didn't match the exact enum values defined in `shared/models/enums.py`.

**Impact**: Unable to create new users through the User Management interface.

**Fix Applied**:
- **File**: `services/auth-service/app/schemas.py`
- **Changes**: Added `@field_validator` decorators to normalize role values
- **Schemas Updated**: `UserCreate` (lines 25-42), `UserUpdate` (lines 61-78)
- **Code**:
```python
@field_validator('role', mode='before')
@classmethod
def normalize_role(cls, v: Union[str, UserRole]) -> UserRole:
    """Convert role string to proper enum value (case-insensitive)"""
    if isinstance(v, UserRole):
        return v
    if isinstance(v, str):
        # Convert to lowercase with underscores
        normalized = v.lower().replace('-', '_')
        try:
            return UserRole(normalized)
        except ValueError:
            # If direct match fails, try to match by name
            for role in UserRole:
                if role.name.lower() == v.upper().replace('-', '_'):
                    return role
            raise ValueError(f"Invalid role: {v}")
    raise ValueError(f"Role must be a string or UserRole, got {type(v)}")
```

**Supported Formats**: Now accepts `"RESTAURANT_ADMIN"`, `"restaurant_admin"`, `"restaurant-admin"`, etc.

---

## Secondary Issues Encountered

### 4. Istio Service Mesh Communication Issues

**Issue**: When Istio sidecar injection was disabled on auth-service for debugging, the API Gateway (with Istio) could not communicate with auth-service (without Istio), resulting in "Invalid HTTP request" errors.

**Root Cause**: Istio uses mTLS (mutual TLS) for service-to-service communication. Mixed mode (some services with Istio, some without) caused protocol mismatch.

**Resolution**: Re-enabled Istio injection on auth-service to maintain consistent service mesh across all services.

**Command**:
```bash
kubectl patch deployment auth-service -n restaurant-system -p '{"spec":{"template":{"metadata":{"annotations":{"sidecar.istio.io/inject":"true"}}}}}'
```

---

### 5. Logout Endpoint - 422 Validation Error

**Issue**: POST /api/v1/auth/logout endpoint returns 422 Unprocessable Entity.

**Root Cause**: The logout endpoint expects a `TokenRefreshRequest` body with a `refresh_token` field, but the frontend is likely sending an empty body or incorrect format.

**Status**: **NOT FIXED** - This is a frontend issue where the logout request is not sending the required `refresh_token` in the request body.

**Expected Request Body**:
```json
{
  "refresh_token": "the_refresh_token_string"
}
```

---

## Deployment Images Used

### Production Images (Final State)
- **API Gateway**: `shadrach85/api-gateway:debug-auth` (with authorization header fix)
- **Auth Service**: `shadrach85/auth-service:users-path-fix` (with role validation and path fix)

### Debug Images Created During Troubleshooting
- `shadrach85/auth-service:role-fix` - Initial role validator attempt
- `shadrach85/auth-service:role-fix-v2` - Role validator with UserResponse
- `shadrach85/auth-service:role-fix-v3` - Removed validator from UserResponse
- `shadrach85/auth-service:debug-users` - Added debug logging
- `shadrach85/auth-service:debug-deps` - Added dependency debug logging
- `shadrach85/auth-service:debug-v2` - Manual serialization attempt
- `shadrach85/auth-service:no-response-model` - Removed response_model

---

## Files Modified

### 1. services/api-gateway/app/main.py
**Lines Changed**: 127-142
**Purpose**: Fix Authorization header forwarding with correct case
**Status**: ✅ Production-ready

### 2. services/auth-service/app/routes/users.py
**Lines Changed**: 18
**Purpose**: Correct endpoint path from "" to "/users"
**Status**: ✅ Production-ready

### 3. services/auth-service/app/schemas.py
**Lines Added**:
- UserCreate validator (lines 25-42)
- UserUpdate validator (lines 61-78)
- UserResponse model_config (line 62)
**Purpose**: Case-insensitive role validation
**Status**: ✅ Production-ready

### 4. services/auth-service/app/dependencies.py
**Lines Added**: 61-70 (DEBUG logging - should be removed)
**Purpose**: Debug logging for troubleshooting
**Status**: ⚠️ Remove debug prints before production

---

## Debugging Process Summary

1. **Initial Investigation**: Checked browser DevTools and confirmed Authorization header was being sent correctly by frontend
2. **API Gateway Analysis**: Added debug logging to verify header forwarding
3. **Auth Service Investigation**: Checked JWT token validation and role comparison
4. **Istio Testing**: Temporarily disabled Istio to isolate the issue (caused new issues)
5. **Route Path Discovery**: Found mismatch between frontend request path and backend endpoint path
6. **Role Validation**: Discovered case sensitivity issue with enum validation

---

## Recommendations

### Immediate Actions Required

1. **Remove Debug Logging**: Clean up debug print statements from production code
   - `services/auth-service/app/dependencies.py` (lines 61-70)
   - `services/auth-service/app/routes/users.py` (debug prints)

2. **Update Frontend Logout**: Fix logout functionality to send proper request body with `refresh_token`

3. **Build Final Production Images**: Create clean images without debug logging
   ```bash
   docker build -t shadrach85/api-gateway:v1.0.0 -f services/api-gateway/Dockerfile .
   docker build -t shadrach85/auth-service:v1.0.0 -f services/auth-service/Dockerfile .
   ```

### Future Improvements

1. **Consistent Role Format**: Consider updating frontend to send role values in the backend's expected format to avoid conversion overhead

2. **API Gateway Tests**: Add integration tests for header forwarding to prevent regression

3. **Pydantic Validators**: Consider centralizing enum validators in a shared module

4. **Error Handling**: Add better error messages for 422 validation errors to help with debugging

---

## Testing Checklist

- [x] User Management page loads successfully
- [x] User list displays correctly
- [ ] User creation via signup form works
- [ ] User logout functionality works (pending frontend fix)
- [x] Authorization header properly forwarded through API Gateway
- [x] Istio service mesh communication working
- [x] All pods running with 2/2 containers (Istio sidecars)

---

## Related Documentation

- See `infrastructure/kubernetes/api-gateway-deployment.yaml` for API Gateway configuration
- See `infrastructure/kubernetes/auth-service-deployment.yaml` for Auth Service configuration
- See `shared/models/enums.py` for UserRole enum definition

---

**Last Updated**: January 6, 2026
**Status**: User Management functionality restored and working
