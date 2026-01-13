# Integration Service Deployment Guide

## ✅ Current Status

The integration service is **deployed and running** but **not yet visible in ArgoCD** because the files haven't been committed to Git.

---

## 📋 Why Not Visible in ArgoCD?

Your ArgoCD configuration (`infrastructure/argocd/application.yaml`) tracks the `developer` branch from your GitHub repository:

```yaml
source:
  repoURL: https://github.com/shadrachdoc/Restaurant_management.git
  targetRevision: developer  # Track developer branch
  path: infrastructure/kubernetes
```

**ArgoCD watches:**
- Repository: `github.com/shadrachdoc/Restaurant_management`
- Branch: `developer`
- Path: `infrastructure/kubernetes`

**Current situation:**
- ✅ Integration service is deployed manually via `kubectl`
- ✅ Deployment files exist locally in `infrastructure/kubernetes/`
- ❌ Files are NOT committed to Git yet
- ❌ ArgoCD cannot see uncommitted files

---

## 🚀 To Make Integration Service Visible in ArgoCD

### Step 1: Commit Integration Service Files

```bash
cd /home/shadrach/Restaurant_management

# Add integration service files
git add services/integration-service/
git add infrastructure/kubernetes/integration-service-deployment.yaml
git add infrastructure/kubernetes/integration-secrets.yaml

# Update API Gateway (with integration routing)
git add services/api-gateway/app/main.py

# Update Istio VirtualService (with webhook routes)
git add infrastructure/istio/virtualservices/api-gateway-vs.yaml

# Commit
git commit -m "Add integration service for Uber Eats and third-party delivery platforms"
```

### Step 2: Push to Developer Branch

```bash
git push origin developer
```

### Step 3: ArgoCD Will Auto-Sync

ArgoCD has automated sync enabled:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

Within **1-2 minutes** after push:
- ArgoCD will detect the new files
- Integration service will appear in ArgoCD UI
- ArgoCD will sync the state

---

## 🔧 Architecture Overview

### Service Mesh & Helm

✅ **Using Istio Service Mesh**: All routing configured via Istio VirtualService
✅ **Using Kubernetes Manifests**: Direct YAML in `infrastructure/kubernetes/` (not Helm charts for apps)
✅ **Using ArgoCD**: GitOps continuous deployment from `developer` branch

### Integration Service Stack

```
┌─────────────────────────────────────────────┐
│  Internet (Uber Eats / Just Eat / DoorDash) │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Istio Ingress Gateway                       │
│  restaurant.corpv3.com                       │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼───────┐    ┌───────▼──────────────┐
│  /api/v1/*    │    │ /api/v1/webhooks/*   │
│               │    │ /api/v1/integrations/*│
│  API Gateway  │    │                       │
│  Port: 8000   │    │ Integration Service  │
└───────┬───────┘    │  Port: 8015          │
        │            └───────┬───────────────┘
        │                    │
        └────────┬───────────┘
                 │
        ┌────────▼─────────┐
        │  Order Service   │
        │  Port: 8002      │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  PostgreSQL DB   │
        └──────────────────┘
```

---

## 📁 Files Created

### 1. Integration Service Application
```
services/integration-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with webhook handlers
│   ├── routes/              # Future: route modules
│   ├── services/            # Future: business logic
│   └── models/              # Future: data models
├── requirements.txt
└── Dockerfile
```

**Key Features:**
- Webhook endpoint: `/api/v1/webhooks/uber-eats`
- OAuth callback: `/api/v1/integrations/uber-eats/callback`
- Basic Auth support (optional)
- Uber signature verification (X-Uber-Signature header)
- Multi-platform ready (Uber Eats, Just Eat, DoorDash, etc.)

### 2. Kubernetes Deployment
```
infrastructure/kubernetes/
├── integration-service-deployment.yaml  # Deployment + Service
└── integration-secrets.yaml             # OAuth credentials
```

**Deployment Specs:**
- **Replicas**: 2
- **Port**: 8015
- **Resources**: 256Mi-512Mi RAM, 200m-500m CPU
- **Health Checks**: Liveness & Readiness probes on `/health`
- **Istio**: Sidecar auto-injected

**Secrets:**
- `uber_client_secret`: Uber OAuth client secret
- `webhook_username`: Basic Auth username
- `webhook_password`: Basic Auth password

### 3. API Gateway Updates
```
services/api-gateway/app/main.py
```

**Added Routing:**
```python
INTEGRATION_SERVICE_URL = "http://integration-service:8015"

if path.startswith("api/v1/webhooks/") or path.startswith("api/v1/integrations/"):
    target_url = f"{INTEGRATION_SERVICE_URL}/{path}"
```

### 4. Istio VirtualService Updates
```
infrastructure/istio/virtualservices/api-gateway-vs.yaml
```

**Route Order (CRITICAL):**
```yaml
http:
  # 1. Webhooks (most specific)
  - match:
      - uri:
          prefix: "/api/v1/webhooks/"
    route:
      - destination:
          host: integration-service
          port: 8015

  # 2. Integrations (specific)
  - match:
      - uri:
          prefix: "/api/v1/integrations/"
    route:
      - destination:
          host: integration-service
          port: 8015

  # 3. API routes (generic)
  - match:
      - uri:
          prefix: "/api/v1/"
    route:
      - destination:
          host: api-gateway
          port: 8000
```

---

## 🔍 Verify Deployment

### Check Integration Service Pods
```bash
kubectl get pods -n restaurant-system -l app=integration-service
```

Expected output:
```
NAME                                  READY   STATUS    RESTARTS   AGE
integration-service-xxxxxxxxx-xxxxx   2/2     Running   0          5m
integration-service-xxxxxxxxx-xxxxx   2/2     Running   0          5m
```

### Check Service
```bash
kubectl get svc -n restaurant-system integration-service
```

Expected output:
```
NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
integration-service   ClusterIP   10.96.212.170   <none>        8015/TCP   10m
```

### Test Webhook Endpoint
```bash
curl https://restaurant.corpv3.com/api/v1/webhooks/uber-eats/test
```

Expected response:
```json
{
  "status": "ok",
  "message": "Webhook endpoint is accessible",
  "webhook_url": "https://restaurant.corpv3.com/api/v1/webhooks/uber-eats"
}
```

### Check ArgoCD Status (After Git Push)
```bash
# Get ArgoCD UI URL
kubectl get svc -n argocd argocd-server

# Or check via CLI
argocd app get restaurant-system
```

---

## 🎯 Uber Webhook Configuration

### Option 1: No Authentication (Recommended)

In Uber Developer Dashboard:
- **Webhook URL**: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`
- **Authentication**: None

Uber will send `X-Uber-Signature` header which we verify automatically.

### Option 2: Basic Authentication

- **Webhook URL**: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`
- **Authentication Type**: Basic Auth
- **Username**: `uber-webhook`
- **Password**: `secure-password-123`

**⚠️ DO NOT use OAuth authentication** for webhook registration. OAuth is for YOU to call Uber's API, not for webhook delivery.

---

## 🔐 Secrets Management

### Current Setup
Secrets stored in Kubernetes secret: `integration-secrets`

```bash
# View secret (base64 encoded)
kubectl get secret integration-secrets -n restaurant-system -o yaml

# Decode secret
kubectl get secret integration-secrets -n restaurant-system -o jsonpath='{.data.uber_client_secret}' | base64 -d
```

### Production Best Practices

For production, use external secret management:
- **Sealed Secrets**: Encrypt secrets for Git
- **External Secrets Operator**: Sync from Vault/AWS Secrets Manager
- **SOPS**: Encrypt YAML files with age/PGP

---

## 📊 Monitoring & Logging

### View Integration Service Logs
```bash
# All logs
kubectl logs -n restaurant-system -l app=integration-service --tail=100 -f

# Specific pod
kubectl logs -n restaurant-system integration-service-xxxxxxxxx-xxxxx -c integration-service -f
```

### Check Webhook Events
```bash
# Filter for webhook events
kubectl logs -n restaurant-system -l app=integration-service | grep "webhook"

# Check Uber signature verification
kubectl logs -n restaurant-system -l app=integration-service | grep "signature"
```

### Istio Metrics
```bash
# Check request metrics
kubectl exec -n istio-system $(kubectl get pod -n istio-system -l app=istio-ingressgateway -o jsonpath='{.items[0].metadata.name}') -- curl localhost:15000/stats | grep integration
```

---

## 🐛 Troubleshooting

### Integration Service Not in ArgoCD

**Problem**: Service deployed but not visible in ArgoCD UI

**Solution**: Files not committed to Git
```bash
git status  # Check uncommitted files
git add infrastructure/kubernetes/integration-service-deployment.yaml
git commit -m "Add integration service"
git push origin developer
```

Wait 1-2 minutes for ArgoCD to sync.

### Webhook Returns 404

**Problem**: `curl https://restaurant.corpv3.com/api/v1/webhooks/uber-eats` returns 404

**Checklist**:
1. API Gateway routing updated? Check logs:
   ```bash
   kubectl logs -n restaurant-system -l app=api-gateway | grep "INTEGRATION_SERVICE"
   ```

2. Istio VirtualService applied?
   ```bash
   kubectl get virtualservice api-gateway -n restaurant-system -o yaml | grep webhooks
   ```

3. Integration service running?
   ```bash
   kubectl get pods -n restaurant-system -l app=integration-service
   ```

### Uber Signature Verification Fails

**Problem**: Webhook receives requests but signature is invalid

**Solution**: Check client secret matches Uber dashboard
```bash
# View current secret
kubectl get secret integration-secrets -n restaurant-system -o jsonpath='{.data.uber_client_secret}' | base64 -d

# Update if needed
kubectl create secret generic integration-secrets -n restaurant-system \
  --from-literal=uber_client_secret='YOUR-UBER-CLIENT-SECRET' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/integration-service -n restaurant-system
```

---

## 🚦 Next Steps

### 1. Commit to Git (Required for ArgoCD)
```bash
git add services/integration-service/
git add infrastructure/kubernetes/integration-service-deployment.yaml
git add infrastructure/kubernetes/integration-secrets.yaml
git add services/api-gateway/app/main.py
git add infrastructure/istio/virtualservices/api-gateway-vs.yaml
git commit -m "Add Uber Eats integration service with service mesh support"
git push origin developer
```

### 2. Configure Uber Webhook
- Go to https://developer.uber.com/
- Configure webhook with: `https://restaurant.corpv3.com/api/v1/webhooks/uber-eats`
- Use "No Authentication" or "Basic Auth" (NOT OAuth)

### 3. Get Store ID
- Log into Uber Eats Manager: https://restaurant.uber.com/
- Find your restaurant's Store ID
- Add to integration service configuration

### 4. Implement Order Processing
- Update `services/integration-service/app/main.py`
- Add database models for external orders
- Implement order synchronization logic
- Update chef dashboard to show Uber orders

### 5. Add More Platforms
- Just Eat integration
- DoorDash integration
- Generic platform adapter pattern

---

## 📚 Documentation

See also:
- [UBER_WEBHOOK_CONFIG.md](scripts/UBER_WEBHOOK_CONFIG.md) - Uber webhook setup guide
- [UBER_EATS_INTEGRATION.md](UBER_EATS_INTEGRATION.md) - Complete integration guide
- [EPOS_ARCHITECTURE.md](EPOS_ARCHITECTURE.md) - EPOS system design

---

**Last Updated**: 2026-01-13
**Integration Service Version**: v1.0
**Status**: Deployed (Not in Git/ArgoCD yet)

