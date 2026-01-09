# Test Credentials - Restaurant Management System

## 🔐 Login Credentials for Testing

### Master Admin (System Administrator)
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: MASTER_ADMIN
- **Access**: Full system administration
- **Dashboard**: `/master-admin`

### Restaurant Admin (Restaurant Owner/Manager)
- **Username**: `adminres`
- **Password**: `password`
- **Role**: RESTAURANT_ADMIN
- **Access**: Restaurant management, menu, tables, orders
- **Dashboard**: `/admin/dashboard`

### Chef (Kitchen Staff)
- **Username**: `adminchef`
- **Password**: `password`
- **Role**: CHEF
- **Access**: Kitchen dashboard, order processing
- **Dashboard**: `/kitchen` or `/chef`

### Customer (Guest Ordering)
- **Login**: NOT REQUIRED ✅
- **Role**: GUEST
- **Access**: Place orders via QR code without login
- **Entry Point**: QR code scan

---

## 📍 Quick Reference

| User Type | Username | Password | Login Required |
|-----------|----------|----------|----------------|
| Master Admin | `admin` | `admin123` | ✅ Yes |
| Restaurant Admin | `adminres` | `password` | ✅ Yes |
| Chef | `adminchef` | `password` | ✅ Yes |
| Customer | - | - | ❌ No (QR code) |

---

**Last Updated**: January 2, 2026
**Status**: ✅ All credentials verified and working
