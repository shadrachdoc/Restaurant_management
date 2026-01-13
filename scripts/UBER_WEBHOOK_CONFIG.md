# Uber Eats Webhook Configuration

## ✅ Webhook Endpoint is Ready!

Your integration service is now deployed and accessible. You can configure the Uber Eats webhook now.

---

## 📋 Uber Developer Dashboard Configuration

### Step 1: Go to Webhook Configuration

1. Visit: https://developer.uber.com/
2. Navigate to your application
3. Click "Add Webhook" or "Configure Webhooks"

### Step 2: Enter These Exact Values

**IMPORTANT**: When configuring the webhook in Uber dashboard, you have TWO options:

#### Option 1: No Authentication (Recommended for Testing)
| Field | Value |
|-------|-------|
| **Webhook URL** | `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats` |
| **Authentication** | None (or skip auth fields) |

Uber will still send `X-Uber-Signature` header for verification.

#### Option 2: Basic Authentication
| Field | Value |
|-------|-------|
| **Webhook URL** | `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats` |
| **Authentication Type** | Basic Auth |
| **Username** | `uber-webhook` |
| **Password** | `your-secure-password-here` |

⚠️ **DO NOT use OAuth authentication** - OAuth is for YOU to authenticate TO Uber when making API calls, not for webhook registration.

---

### Your Uber OAuth Credentials (For API Calls)

These credentials are for making API calls TO Uber (not for webhooks):

| Field | Value |
|-------|-------|
| **Client ID** | `V29RkSpTL1w-GpKbXsUWMWXmiOIwfcrM` |
| **Client Secret** | `m4a4DRDfkgtoPDTh9JVI0RHx-5J7nAJ9x4pntgSU` |
| **Token URL** | `https://sandbox-login.uber.com/oauth/v2/token` |
| **Scope** | `eats.store eats.store.orders.read eats.store.orders.write eats.store.status.write` |
| **Environment** | Sandbox |

---

## ✅ Endpoint Verification

All endpoints are working and tested:

### Test Endpoint (GET)
```bash
curl https://restaurant.corpv3.com/api/v1/webhooks/uber-eats/test
```
**Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint is accessible",
  "webhook_url": "https://restaurant.corpv3.com/api/v1/webhooks/uber-eats"
}
```

### Webhook Endpoint (POST)
```bash
curl -X POST https://restaurant.corpv3.com/api/v1/webhooks/uber-eats \
  -H "Content-Type: application/json" \
  -d '{"event_type":"orders.notification","data":{}}'
```
**Response:**
```json
{
  "status": "success",
  "message": "Webhook processed"
}
```

### OAuth Callback (GET)
```bash
curl "https://restaurant.corpv3.com/api/v1/integrations/uber-eats/callback?code=test123"
```
**Response:**
```json
{
  "status": "success",
  "message": "Authorization successful"
}
```

---

## 🔧 What Was Deployed

### 1. Integration Service
- **Port**: 8015
- **Replicas**: 2
- **Status**: Running ✅
- **Location**: `services/integration-service/`

### 2. API Gateway Updated
- **Image**: `shadrach85/api-gateway:uber-integration`
- **Added Routing**: Webhooks and integration endpoints now route to integration-service
- **Status**: Deployed ✅

### 3. Istio Service Mesh
- **VirtualService**: Updated to route `/api/v1/webhooks/` and `/api/v1/integrations/` to integration-service
- **Status**: Configured ✅

---

## 📊 Service Architecture

```
Internet
    ↓
Istio Ingress Gateway (restaurant.corpv3.com)
    ↓
API Gateway (Port 8000)
    ↓
Integration Service (Port 8015) ← Handles Uber Eats webhooks
    ↓
Order Service (Port 8004) ← Will store Uber orders
    ↓
PostgreSQL Database
```

---

## 🔍 Verify Deployment

### Check Integration Service Pods
```bash
kubectl get pods -n restaurant-system -l app=integration-service
```
Expected: 2 pods running

### Check Integration Service Logs
```bash
kubectl logs -n restaurant-system -l app=integration-service --tail=20
```

### Check API Gateway Routing
```bash
kubectl logs -n restaurant-system -l app=api-gateway --tail=20 | grep "INTEGRATION_SERVICE"
```

---

## 🚀 Next Steps After Webhook Registration

### 1. Get Your Store ID
You need to find your restaurant's Store ID from Uber Eats:
- Log into Uber Eats Manager: https://restaurant.uber.com/
- Go to Store Settings
- Copy your Store ID (format: `store-uuid-here`)

### 2. Test Webhook Events
Once webhook is registered, Uber will send these events:
- `orders.notification` - New order
- `orders.cancel` - Order cancelled
- `orders.status_update` - Status changed

### 3. Database Schema Updates
We'll need to update the database to support Uber orders:
```sql
-- Add UBER_EATS to order type enum
ALTER TYPE ordertype ADD VALUE 'UBER_EATS';

-- Add external tracking columns
ALTER TABLE orders ADD COLUMN external_order_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN external_source VARCHAR(50);
ALTER TABLE orders ADD COLUMN external_metadata JSONB;
```

### 4. Frontend Updates
Update chef dashboard to show Uber Eats orders with filters.

---

## 📝 Important Notes

1. **Sandbox Environment**: Currently configured for Uber's sandbox environment
2. **Multi-Platform Ready**: The integration service is designed to support Just Eat, DoorDash, etc.
3. **Service Mesh**: All routing uses Istio service mesh as requested
4. **Helm Compatibility**: All deployments are Helm-compatible

---

## 🛠️ Troubleshooting

### If Webhook Registration Fails

1. **Check endpoint is accessible**:
   ```bash
   curl https://restaurant.corpv3.com/api/v1/webhooks/uber-eats/test
   ```
   Should return `200 OK`

2. **Check integration service logs**:
   ```bash
   kubectl logs -n restaurant-system -l app=integration-service --tail=50
   ```

3. **Verify Uber can reach your domain**:
   - Ensure `restaurant.corpv3.com` is publicly accessible
   - Check firewall rules
   - Verify SSL certificate is valid

4. **Check API Gateway routing**:
   ```bash
   kubectl logs -n restaurant-system -l app=api-gateway | grep "webhooks"
   ```
   Should show: `DEBUG: Routing to INTEGRATION_SERVICE`

---

## 📞 Support

### View Integration Service Status
```bash
kubectl get all -n restaurant-system -l app=integration-service
```

### View API Gateway Status
```bash
kubectl get all -n restaurant-system -l app=api-gateway
```

### View Istio Configuration
```bash
kubectl get virtualservice api-gateway -n restaurant-system -o yaml
```

---

**Last Updated**: 2026-01-13
**Status**: ✅ Ready for webhook registration
**New Pod Tag**: `shadrach85/api-gateway:uber-integration`

