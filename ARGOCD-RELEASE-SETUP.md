# ArgoCD Release Setup Guide

Guide for configuring ArgoCD to work with the versioned release system.

---

## Overview

We now have **two ArgoCD applications** for different environments:

| Application | Namespace | Tracks Branch | Image Tags | Purpose |
|------------|-----------|---------------|------------|---------|
| `restaurant-system-dev` | `restaurant-system-dev` | `developer` | `latest` | Development/Testing |
| `restaurant-system-prod` | `restaurant-system` | `main` | `v1.2.3` | Production Releases |

---

## Current State

Your current ArgoCD application (`restaurant-system`) tracks the `developer` branch. We'll:
1. Rename it to `restaurant-system-prod` tracking `main` branch
2. Create `restaurant-system-dev` tracking `developer` branch

---

## Setup Instructions

### Option 1: Update Existing Application (Recommended)

Since you're currently using `restaurant-system` for development, let's keep it and add a production one:

```bash
# 1. Apply the production ArgoCD application
kubectl apply -f infrastructure/argocd/application.yaml

# 2. (Optional) Apply the development ArgoCD application
kubectl apply -f infrastructure/argocd/application-dev.yaml

# 3. Verify applications created
kubectl get applications -n argocd
```

Expected output:
```
NAME                      SYNC STATUS   HEALTH STATUS
restaurant-system-prod    Synced        Healthy
restaurant-system-dev     Synced        Healthy  (if applied)
```

### Option 2: Start Fresh

If you want to delete the old application and start fresh:

```bash
# 1. Delete old application
kubectl delete application restaurant-system -n argocd

# 2. Apply new production application
kubectl apply -f infrastructure/argocd/application.yaml

# 3. (Optional) Apply development application
kubectl apply -f infrastructure/argocd/application-dev.yaml
```

---

## For Now: Single Environment Setup

Since you only have `developer` and `main` branches, you can start with just **one** ArgoCD application:

### Production Setup (Recommended)

Use the existing namespace with versioned releases:

```bash
# Apply production ArgoCD app (tracks main branch with version tags)
kubectl apply -f infrastructure/argocd/application.yaml
```

**Workflow**:
1. Develop on `developer` branch → builds with `latest` tag
2. When ready for release → merge to `main` → create tag `v1.2.0`
3. ArgoCD deploys version `v1.2.0` to `restaurant-system` namespace

### Development + Production Setup

If you want separate environments:

```bash
# Apply both applications
kubectl apply -f infrastructure/argocd/application.yaml       # Production
kubectl apply -f infrastructure/argocd/application-dev.yaml   # Development
```

**Workflow**:
1. Develop on `developer` branch → ArgoCD deploys to `restaurant-system-dev` with `latest`
2. Release to `main` + tag → ArgoCD deploys to `restaurant-system` with `v1.2.0`

---

## Verification

### Check ArgoCD Applications

```bash
# List applications
kubectl get applications -n argocd

# Check specific application
kubectl describe application restaurant-system-prod -n argocd

# Check sync status
kubectl get application restaurant-system-prod -n argocd -o jsonpath='{.status.sync.status}'
```

### Check Deployed Image Versions

```bash
# Production namespace
kubectl get pods -n restaurant-system \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# Development namespace (if using dev app)
kubectl get pods -n restaurant-system-dev \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

Expected output (after release v1.0.0):
```
# Production
auth-service-xxx    shadrachdoc/auth-service:v1.0.0
order-service-xxx   shadrachdoc/order-service:v1.0.0
...

# Development
auth-service-xxx    shadrachdoc/auth-service:latest
order-service-xxx   shadrachdoc/order-service:latest
...
```

### Access ArgoCD UI

```bash
# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8081:443

# Login to UI
https://localhost:8081
```

In the UI, you'll see:
- **Application Name**: restaurant-system-prod
- **Sync Status**: Synced
- **Health**: Healthy
- **Images**: Shows `v1.0.0` tags (instead of commit SHA)

---

## Creating Your First Release

Now that ArgoCD is configured, create your first release:

### Step 1: Prepare Code

```bash
# Ensure developer branch is up to date
git checkout developer
git pull origin developer

# Merge to main
git checkout main
git merge developer
git push origin main
```

### Step 2: Create Release Tag

```bash
# Create v1.0.0 tag
git tag -a v1.0.0 -m "Release v1.0.0: Initial production release"

# Push tag (triggers release workflow)
git push origin v1.0.0
```

### Step 3: Monitor Release

```bash
# Watch GitHub Actions
https://github.com/shadrachdoc/Restaurant_management/actions

# Watch ArgoCD sync
kubectl get application restaurant-system-prod -n argocd -w

# Watch pods update
kubectl get pods -n restaurant-system -w
```

### Step 4: Verify

```bash
# Check deployed version
kubectl get pods -n restaurant-system \
  -o jsonpath='{.items[0].spec.containers[0].image}'

# Expected: shadrachdoc/auth-service:v1.0.0
```

---

## How It Works

### Development Workflow

```
Developer → Push to developer branch
     ↓
GitHub Actions CI/CD
     ↓
Build images with 'latest' tag
     ↓
Push to DockerHub
     ↓
Update deployments (developer branch)
     ↓
ArgoCD (restaurant-system-dev) detects changes
     ↓
Deploys latest to dev namespace
```

### Release Workflow

```
Developer → Merge to main → Create tag v1.2.0
     ↓
GitHub Actions Release Workflow
     ↓
Build images with 'v1.2.0', 'latest', commit SHA tags
     ↓
Push to DockerHub
     ↓
Update deployments (main branch) with v1.2.0
     ↓
Generate changelog + Create GitHub Release
     ↓
ArgoCD (restaurant-system-prod) detects changes
     ↓
Deploys v1.2.0 to production namespace
```

---

## Troubleshooting

### ArgoCD Not Syncing After Release

**Problem**: Created tag but ArgoCD still shows old version

**Solution**:
```bash
# Check if deployment manifests were updated
git log -1 infrastructure/kubernetes/

# Force sync
kubectl patch application restaurant-system-prod -n argocd \
  --type merge -p '{"operation":{"initiatedBy":{"automated":false},"sync":{"revision":"main"}}}'

# Or use ArgoCD UI: Click "Sync" button
```

### Wrong Image Tag in Pods

**Problem**: Pods show `latest` instead of `v1.0.0`

**Solution**:
```bash
# Check deployment manifest in main branch
git checkout main
grep "image:" infrastructure/kubernetes/auth-service-deployment.yaml

# Should show: shadrachdoc/auth-service:v1.0.0
# If not, release workflow may have failed

# Check release workflow logs
https://github.com/shadrachdoc/Restaurant_management/actions
```

### Multiple Applications Conflict

**Problem**: Both dev and prod trying to use same namespace

**Solution**:
- Production uses: `restaurant-system` namespace
- Development uses: `restaurant-system-dev` namespace
- They don't conflict!

If you want them in the same namespace (not recommended):
```bash
# Delete dev application
kubectl delete application restaurant-system-dev -n argocd
```

---

## Recommended Setup (For Your Case)

Since you have a single KIND cluster, I recommend:

**Option A: Production Only** (Simpler)
```bash
# Apply only production app
kubectl apply -f infrastructure/argocd/application.yaml

# Workflow:
# - Develop on 'developer' branch (test locally with build-and-deploy.sh)
# - Release to 'main' branch + tag for ArgoCD deployment
```

**Option B: Separate Namespaces** (Better isolation)
```bash
# Apply both apps
kubectl apply -f infrastructure/argocd/application.yaml
kubectl apply -f infrastructure/argocd/application-dev.yaml

# Workflow:
# - ArgoCD deploys 'developer' to restaurant-system-dev (latest tags)
# - ArgoCD deploys 'main' releases to restaurant-system (version tags)
```

I recommend **Option A** for now, then add **Option B** when you need better environment separation.

---

## Quick Commands

```bash
# Apply production ArgoCD app
kubectl apply -f infrastructure/argocd/application.yaml

# Create first release
git checkout main
git merge developer
git tag -a v1.0.0 -m "Release v1.0.0: Initial release"
git push origin main --tags

# Watch deployment
kubectl get pods -n restaurant-system -w

# Check version
kubectl get pods -n restaurant-system \
  -o jsonpath='{.items[0].spec.containers[0].image}'
```

---

**Next Step**: Create your first release with `v1.0.0` tag!

See [RELEASE.md](RELEASE.md) for detailed release instructions.

---

**Last Updated**: 2025-12-23
**Document Owner**: DevOps Team
