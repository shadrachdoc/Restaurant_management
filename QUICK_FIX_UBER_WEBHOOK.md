# 🔧 Quick Fix: Uber Webhook "failed to register OAuth client" Error

## ❌ The Problem

You're getting **"2 UNKNOWN: failed to register OAuth client"** because you selected "OAuth" in the webhook configuration dialog.

## ✅ The Solution

**OAuth is NOT for webhook registration!** OAuth is for YOU to call Uber's API.

---

## 📋 Correct Webhook Configuration

### In Uber Developer Dashboard:

1. Go to https://developer.uber.com/
2. Navigate to your application
3. Click "Add Webhook" or "Webhooks" section

### Choose ONE of these options:

#### Option 1: No Authentication (RECOMMENDED)
Simply enter:
- **Webhook URL**: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`
- **Authentication**: Select "None" or leave empty

Our service will still verify the `X-Uber-Signature` header that Uber sends.

#### Option 2: Basic Authentication
- **Webhook URL**: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`
- **Authentication Type**: Basic Auth
- **Username**: `uber-webhook`
- **Password**: `secure-password-123`

---

## ⚠️ DO NOT Use These Options:

❌ **OAuth** - This requires US to provide a token endpoint, which is NOT needed for webhooks
❌ **OAuth Client Credentials** - Same as above

---

## 🧪 Test After Configuration

Once you configure the webhook with "No Authentication" or "Basic Auth", test it:

```bash
# Test GET endpoint
curl https://restaurant.corpv3.com/api/v1/webhooks/uber-eats/test

# Test POST endpoint (simulates Uber sending webhook)
curl -X POST https://restaurant.corpv3.com/api/v1/webhooks/uber-eats \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","data":{}}'
```

Both should return success responses.

---

## 📖 Understanding OAuth vs Webhooks

### OAuth (YOU → Uber)
**Purpose**: You call Uber's API to get order data, update status, etc.

**Your Credentials**:
- Client ID: `V29RkSpTL1w-GpKbXsUWMWXmiOIwfcrM`
- Client Secret: `m4a4DRDfkgtoPDTh9JVI0RHx-5J7nAJ9x4pntgSU`
- Token URL: `https://sandbox-login.uber.com/oauth/v2/token`

**Usage**: Making API calls FROM your system TO Uber
```python
# Example: You calling Uber's API
response = requests.post("https://sandbox-login.uber.com/oauth/v2/token", data={
    "client_id": "V29RkSpTL1w-GpKbXsUWMWXmiOIwfcrM",
    "client_secret": "m4a4DRDfkgtoPDTh9JVI0RHx-5J7nAJ9x4pntgSU",
    "grant_type": "client_credentials",
    "scope": "eats.store"
})
token = response.json()["access_token"]

# Now use token to call Uber API
orders = requests.get("https://api.uber.com/v1/eats/stores/STORE_ID/orders",
    headers={"Authorization": f"Bearer {token}"})
```

### Webhooks (Uber → YOU)
**Purpose**: Uber sends events to your server (new order, cancellation, etc.)

**Authentication**: Uber proves it's really them via:
1. **X-Uber-Signature header** (HMAC-SHA256 of request body)
2. **Optional Basic Auth** (username/password you provide)

**Usage**: Uber calling YOUR webhook
```http
POST https://restaurant.corpv3.com/api/v1/webhooks/uber-eats
Headers:
  X-Uber-Signature: abc123...
  Content-Type: application/json

Body:
{
  "event_type": "orders.notification",
  "order_id": "xyz-789",
  "restaurant_id": "store-123"
}
```

---

## 🎯 Summary

| Component | Authentication Method |
|-----------|----------------------|
| **Webhook Registration** | None or Basic Auth |
| **Webhook Delivery** | X-Uber-Signature header |
| **Your API Calls to Uber** | OAuth 2.0 Client Credentials |

**For webhook setup, DO NOT use OAuth!**

---

**Quick Action**: Go back to Uber dashboard, delete the failed webhook, and add a new one with "No Authentication".

