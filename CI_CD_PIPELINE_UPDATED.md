# CI/CD Pipeline Updates

## ✅ Changes Made to `.github/workflows/ci-cd-istio.yml`

### 1. Fixed Docker Hub Authentication
**Problem**: Secret names didn't match
**Fix**: Changed from `DOCKER_USERNAME` / `DOCKER_PASSWORD` to `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`

```yaml
# Before:
username: ${{ secrets.DOCKER_USERNAME }}
password: ${{ secrets.DOCKER_PASSWORD }}

# After:
username: ${{ secrets.DOCKERHUB_USERNAME }}
password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### 2. Added Missing Services
Added build steps for services that were missing from the pipeline:

- ✅ **Customer Service** - New
- ✅ **Kitchen Service** - New
- ✅ **Integration Service** - New (Uber Eats/delivery platforms)

### 3. Removed Non-Existent Service
- ❌ **Menu Service** - Removed (directory doesn't exist)

### 4. Standardized Image Naming
Changed from inconsistent `restaurant-*` prefixes to clean service names:

| Old Name | New Name |
|----------|----------|
| `restaurant-api-gateway` | `api-gateway` |
| `restaurant-order-service` | `order-service` |
| `restaurant-auth-service` | `auth-service` |
| `restaurant-notification-service` | `notification-service` |
| `restaurant-frontend` | `frontend` |
| `restaurant-service` | `restaurant-service` ✓ (kept) |

## 📋 Complete Service List in Pipeline

The pipeline now builds and pushes these Docker images:

1. **api-gateway** - Main API gateway with Istio routing
2. **order-service** - Order management and analytics
3. **restaurant-service** - Restaurant and menu management
4. **auth-service** - Authentication and user management
5. **customer-service** - Customer management
6. **kitchen-service** - Kitchen display system
7. **integration-service** - Third-party integrations (Uber Eats, Just Eat, etc.)
8. **notification-service** - Notifications (email, SMS, push)
9. **frontend** - React frontend application

## 🔧 Image Tag Format

All images are tagged with:
- **Short SHA**: `shadrach85/<service>:<7-char-sha>`
- **Latest**: `shadrach85/<service>:latest`

Example:
```
shadrach85/integration-service:a1b2c3d
shadrach85/integration-service:latest
```

## 📊 Pipeline Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Build Job                                           │
│  - Checkout code                                        │
│  - Setup Docker Buildx                                  │
│  - Login to Docker Hub (DOCKERHUB_USERNAME/TOKEN)       │
│  - Generate image tags (short SHA)                      │
│  - Build & push 9 services in parallel                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. Deploy Infrastructure Job                           │
│  - Install Istio (if not exists)                        │
│  - Install Helm charts:                                 │
│    * Prometheus (metrics)                               │
│    * Grafana (dashboards)                               │
│    * Loki (logs)                                        │
│    * Jaeger (tracing)                                   │
│    * Kiali (service mesh visualization)                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. Deploy Application Job                              │
│  - Create namespace with istio-injection=enabled        │
│  - Apply Istio Gateway                                  │
│  - Apply VirtualServices                                │
│  - Apply DestinationRules                               │
│  - Apply mTLS Policy                                    │
│  - Deploy via Helm with new image tags                  │
│  - Verify sidecar injection (2 containers per pod)      │
│  - Wait for rollouts                                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. Smoke Tests Job                                     │
│  - Get Istio Ingress IP                                 │
│  - Health checks (/health, /api/v1/health)              │
│  - Check metrics availability (Prometheus)              │
│  - Print deployment summary                             │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  5. Notify Job                                          │
│  - Send deployment status notification                  │
│  - Exit with error if smoke tests failed               │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Trigger Conditions

Pipeline runs on:
- **Push** to `main` or `developer` branches
- **Pull Request** to `main` branch

Infrastructure and application deployment only runs on:
- `main` branch
- `developer` branch

## 🔐 Required GitHub Secrets

Ensure these secrets are configured in your GitHub repository:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub username | `shadrach85` |
| `DOCKERHUB_TOKEN` | Docker Hub access token | `dckr_pat_xxx...` |
| `KUBECONFIG` | Kubernetes cluster config | base64 encoded kubeconfig |

## 📝 Service Dockerfiles

All services have Dockerfiles at:
```
services/
├── api-gateway/Dockerfile
├── auth-service/Dockerfile
├── customer-service/Dockerfile
├── integration-service/Dockerfile
├── kitchen-service/Dockerfile
├── notification-service/Dockerfile
├── order-service/Dockerfile
└── restaurant-service/Dockerfile

frontend/Dockerfile
```

## ⚠️ Important Notes

### Integration Service
The new **integration-service** handles third-party delivery platform integrations:
- Uber Eats webhooks
- Just Eat integration (future)
- DoorDash integration (future)
- Generic webhook receiver with signature verification

### Image Name Changes
If you update the pipeline image names, you must also update:
1. **Kubernetes deployments** in `infrastructure/kubernetes/`
2. **Helm values** in `infrastructure/helm/`
3. **ArgoCD image updater** annotations

### Build Caching
Only API Gateway uses build cache to speed up builds:
```yaml
cache-from: type=registry,ref=shadrach85/api-gateway:buildcache
cache-to: type=registry,ref=shadrach85/api-gateway:buildcache,mode=max
```

Consider adding caching for other services to improve build times.

## 🐛 Troubleshooting

### Build Fails with "Username and password required"
**Cause**: GitHub secrets not configured or wrong names
**Fix**: Ensure `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets exist

### Service Not Building
**Cause**: Missing Dockerfile or wrong context path
**Fix**: Verify Dockerfile exists at `services/<service>/Dockerfile`

### Image Not Updating in Cluster
**Cause**: Using `imagePullPolicy: IfNotPresent` with same tag
**Fix**: Pipeline uses unique SHA tags, update deployments to use new tag

### Namespace Issues
**Cause**: Pipeline expects `restaurant-management` namespace
**Fix**: Current system uses `restaurant-system` - update pipeline or rename namespace

## 📈 Next Steps

### 1. Align Namespace
Current mismatch:
- Pipeline deploys to: `restaurant-management`
- Actual namespace: `restaurant-system`

**Action**: Update pipeline line 234 to use `restaurant-system`

### 2. Add Build Caching
Add build cache to all services for faster builds:
```yaml
cache-from: type=registry,ref=${{ env.DOCKER_USERNAME }}/<service>:buildcache
cache-to: type=registry,ref=${{ env.DOCKER_USERNAME }}/<service>:buildcache,mode=max
```

### 3. Multi-Architecture Builds
Support ARM64 for M1/M2 Macs:
```yaml
platforms: linux/amd64,linux/arm64
```

### 4. ArgoCD Image Updater
Configure ArgoCD to auto-update image tags when new builds complete.

## ✅ Summary

**Fixed**:
- ✅ Docker Hub authentication
- ✅ Added integration-service
- ✅ Added customer-service
- ✅ Added kitchen-service
- ✅ Removed non-existent menu-service
- ✅ Standardized image names

**Services in Pipeline**: 9 total (8 backend + 1 frontend)

**Ready for**: `git push origin developer`

---

**Last Updated**: 2026-01-13
**Pipeline File**: `.github/workflows/ci-cd-istio.yml`

