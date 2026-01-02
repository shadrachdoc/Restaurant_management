# Restaurant Management System - Test Credentials

## Last Updated: December 29, 2025

### System Access Credentials

All accounts have been created and tested successfully. Use these credentials to access different roles in the application.

**Production URL**: https://restaurant.corpv3.com

---

## 1. Master Admin Account
**Page/Role:** System Administration / Master Admin Dashboard

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `password` |
| **Email** | admin@restaurant.com |
| **Role** | master_admin |
| **Phone** | +1234567890 |

**Access URL**: https://restaurant.corpv3.com/master-admin

**Permissions:**
- Full system access
- Manage all restaurants
- Manage all users (User Management)
- View and generate invoices for all restaurants
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
| **Restaurant** | phalwan Briyani |

**Access URL**: https://restaurant.corpv3.com/kitchen

**Permissions:**
- View incoming orders
- Update order status (Accept/Reject/Complete)
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
| **Restaurant** | phalwan Briyani |

**Access URL**: https://restaurant.corpv3.com/admin

**Permissions:**
- Manage restaurant profile
- Manage menu items
- Manage tables
- View orders
- Staff management
- Restaurant analytics
- QR code generation

---

## Test Restaurant Details

**Restaurant Name**: phalwan Briyani
**Restaurant ID**: `52c0d315-b894-40c6-be52-3416a9d0a1e7`
**Country**: India
**Currency**: INR (₹)
**Billing Fees**:
- Per Table Booking: ₹10.00
- Per Online Booking: ₹15.00
- Billing Enabled: ✅ YES

**Test Data**:
- 8 Menu Items (Chicken Biryani, Mutton Biryani, Veg Biryani, etc.)
- 5 Tables (T1-T5)
- 240 Completed Orders (16 days of test data)

---

## Available Roles

The system supports the following roles:

1. **master_admin** - System-wide administrator
2. **restaurant_admin** - Restaurant manager
3. **chef** - Kitchen staff
4. **customer** - End users/customers

---

## Notes

- All accounts are active
- Default password for all test accounts: `password`
- For production, ensure passwords are changed and email verification is enabled
- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days

---

## Kubernetes Services

**Namespace**: restaurant-system

| Service | Type | Port |
|---------|------|------|
| API Gateway | ClusterIP | 8000 |
| Auth Service | ClusterIP | 8001 |
| Restaurant Service | ClusterIP | 8003 |
| Order Service | ClusterIP | 8004 |
| Customer Service | ClusterIP | 8007 |
| Frontend | ClusterIP | 80 |
| PostgreSQL | ClusterIP | 5432 |
| Redis | ClusterIP | 6379 |
| RabbitMQ | ClusterIP | 5672, 15672 |

---

## API Documentation

**Swagger/OpenAPI Docs** (via port-forward):
```bash
# Port-forward API Gateway
kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000

# Then access:
# - API Gateway Docs: http://localhost:8000/docs
# - Auth API: http://localhost:8000/api/v1/auth/*
# - Restaurant API: http://localhost:8000/api/v1/restaurants/*
# - Order API: http://localhost:8000/api/v1/orders/*
```

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
**Last Updated:** December 29, 2025
**Environment:** Kubernetes Production Cluster (Kind)
**Domain:** https://restaurant.corpv3.com
