# Restaurant Management System - Test Credentials

## Created: 2025-12-20

### System Access Credentials

All accounts have been created and tested successfully. Use these credentials to access different pages/roles in the application.

---

## 1. Admin Account (Primary)
**Page/Role:** System Administration / Master Admin Dashboard

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `password` |
| **Email** | admin@restaurant.com |
| **Role** | master_admin |
| **Phone** | +1234567890 |
| **User ID** | fbd91e54-a091-4d36-9e3e-db62e05aa5ce |

**Permissions:**
- Full system access
- Manage all restaurants
- Manage all users
- System configuration
- Analytics and reporting

---

## 2. Chef Account
**Page/Role:** Kitchen Management / Chef Dashboard

| Field | Value |
|-------|-------|
| **Username** | `adminchef1` |
| **Password** | `password` |
| **Email** | chef@restaurant.com |
| **Role** | chef |
| **Phone** | +1234567891 |
| **User ID** | ed5cec07-63df-4ae9-8397-e11af02d945b |

**Permissions:**
- View incoming orders
- Update order status
- Manage kitchen operations
- View menu items
- Kitchen analytics

---

## 3. Restaurant Admin Account
**Page/Role:** Restaurant Management / Restaurant Dashboard

| Field | Value |
|-------|-------|
| **Username** | `adminres` |
| **Password** | `password` |
| **Email** | restaurant@restaurant.com |
| **Role** | restaurant_admin |
| **Phone** | +1234567892 |
| **User ID** | 4f9a03d6-a890-4462-a5ef-e3758963b0b6 |

**Permissions:**
- Manage restaurant profile
- Manage menu items
- Manage tables
- View orders
- Staff management
- Restaurant analytics
- QR code generation

---

## Login Test Results

All accounts tested successfully:

```bash
✅ Admin Login: master_admin - admin (PRIMARY)
✅ Chef Login: chef - adminchef1
✅ Restaurant Admin Login: restaurant_admin - adminres
```

**Note:** The `admin` account was recreated with the correct password. Old admin account from 2025-12-19 has been removed.

---

## API Endpoints for Testing

### Authentication
```bash
# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"masteradmin","password":"password"}'

# Login via API Gateway
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"masteradmin","password":"password"}'
```

### Using Access Token
```bash
# Get user profile
curl -X GET http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Available Roles

The system supports the following roles:

1. **master_admin** - System-wide administrator
2. **restaurant_admin** - Restaurant manager
3. **chef** - Kitchen staff
4. **customer** - End users/customers

---

## Notes

- All accounts are active but not verified
- Default password for all accounts: `password`
- For production, ensure passwords are changed and email verification is enabled
- Access tokens expire in 30 minutes (configurable in settings)
- Refresh tokens expire in 7 days (configurable in settings)

---

## Frontend Access

**Local Development:**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Auth Service: http://localhost:8001
- Restaurant Service: http://localhost:8003

**API Documentation:**
- Auth API Docs: http://localhost:8001/docs
- Restaurant API Docs: http://localhost:8003/docs
- API Gateway Docs: http://localhost:8000/docs

---

## Security Recommendations

⚠️ **Important for Production:**

1. Change all default passwords immediately
2. Enable email verification
3. Implement 2FA for admin accounts
4. Use strong password policies
5. Enable rate limiting
6. Monitor authentication logs
7. Set up proper RBAC (Role-Based Access Control)
8. Use HTTPS in production
9. Implement session management
10. Regular security audits

---

**Document Status:** ✅ Verified and Working
**Last Updated:** 2025-12-20
**Environment:** Kubernetes Development Cluster
