# CI/CD Pipeline Setup Guide

## Overview

The Restaurant Management System uses a **build-and-load** CI/CD approach optimized for KIND (Kubernetes in Docker) clusters with ArgoCD for GitOps deployment.

## Architecture

```
┌─────────────────┐
│   GitHub Push   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   GitHub Actions Workflow   │
│  1. Build Docker Images     │
│  2. Load into KIND Cluster  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│      ArgoCD watches Git     │
│  - Auto-detects changes     │
│  - Syncs Kubernetes YAML    │
│  - Restarts deployments     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Kubernetes Deployments    │
│   Pull new images from      │
│   KIND cluster              │
└─────────────────────────────┘
```

## Why This Approach?

### Traditional Registry-Based CI/CD Problems:
- ❌ Requires Docker registry (DockerHub, ECR, GCR)
- ❌ Image push/pull adds latency
- ❌ Registry authentication complexity
- ❌ Costs money for private registries
- ❌ Network bandwidth usage

### Our KIND + ArgoCD Solution:
- ✅ No external registry needed
- ✅ Images loaded directly into KIND nodes
- ✅ Faster deployment (no push/pull)
- ✅ Free and local development friendly
- ✅ ArgoCD handles deployment orchestration
- ✅ GitOps best practices

## Components

### 1. GitHub Actions Workflow
**File:** `.github/workflows/ci-cd.yml`

**Triggers:**
- Push to `main`, `developer`, or `staging` branches
- Pull requests to `main` or `developer`

**Steps:**
1. Checkout code
2. Build all Docker images
3. Load images into existing KIND cluster
4. Notify about ArgoCD sync

**Does NOT:**
- ❌ Create/destroy clusters
- ❌ Apply Kubernetes manifests directly
- ❌ Push images to registries

### 2. ArgoCD Application
**File:** `argocd/application.yaml`

**Configuration:**
- **Source:** Git repository (`infrastructure/kubernetes/` directory)
- **Destination:** `restaurant-system` namespace
- **Sync Policy:** Automated with self-heal
- **Prune:** Enabled (removes deleted resources)

**Features:**
- Auto-sync on Git changes
- Self-healing (restores manual changes)
- Retry on failure (exponential backoff)
- Revision history (last 3 deployments)

### 3. Local Build Script
**File:** `build-and-deploy.sh`

**Usage:**
```bash
./build-and-deploy.sh
```

**What it does:**
1. Verifies KIND cluster exists
2. Builds all Docker images
3. Loads images into KIND
4. Offers deployment options:
   - Wait for ArgoCD auto-sync
   - Manual ArgoCD sync
   - Direct kubectl restart

### 4. Makefile Commands
**File:** `Makefile`

Quick commands for development:

```bash
make help              # Show all commands
make all              # Build, load, restart, verify
make build            # Build all images
make load             # Load all images to KIND
make restart          # Restart all deployments

# Service-specific commands
make quick-frontend   # Build + Load + Restart frontend only
make quick-auth       # Build + Load + Restart auth service
make logs-frontend    # View frontend logs
make status           # Show all pod/service status
```

## Setup Instructions

### 1. Install Prerequisites

```bash
# KIND (if not installed)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# ArgoCD CLI (optional, for manual control)
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

### 2. Verify KIND Cluster

```bash
kind get clusters
# Should show: restaurant-cluster
```

### 3. Deploy ArgoCD Application

```bash
# Apply the ArgoCD application manifest
kubectl apply -f argocd/application.yaml

# Verify application is created
kubectl get applications -n argocd

# Check sync status
kubectl get application restaurant-management -n argocd -o yaml
```

### 4. Configure Auto-Sync (Optional)

ArgoCD auto-sync is already enabled in the manifest. To verify:

```bash
# Check if auto-sync is enabled
kubectl get application restaurant-management -n argocd -o jsonpath='{.spec.syncPolicy.automated}'
```

Should show: `{"allowEmpty":false,"prune":true,"selfHeal":true}`

### 5. Update Git Repository URL

Edit `argocd/application.yaml` and update:

```yaml
source:
  repoURL: https://github.com/YOUR-USERNAME/Restaurant_management.git
```

Then reapply:
```bash
kubectl apply -f argocd/application.yaml
```

## Workflows

### Development Workflow

1. **Make code changes** to services
2. **Commit and push** to `developer` branch
3. **GitHub Actions runs automatically:**
   - Builds new Docker images
   - Loads images into KIND cluster
4. **Two options for deployment:**
   
   **Option A: Automatic (ArgoCD auto-sync enabled)**
   - ArgoCD detects Git changes
   - Automatically syncs and restarts pods
   - New images are pulled from KIND
   
   **Option B: Manual sync**
   - Access ArgoCD UI: https://localhost:8081
   - Click "Sync" on restaurant-management app
   - Or use CLI: `argocd app sync restaurant-management`

5. **Verify deployment:**
   ```bash
   kubectl get pods -n restaurant-system
   make status
   ```

### Production Workflow

1. **Merge `developer` → `main`**
2. **GitHub Actions runs** on main branch
3. **ArgoCD syncs production** changes
4. **Monitor deployment:**
   ```bash
   kubectl get application restaurant-management -n argocd -w
   ```

### Hotfix Workflow

1. **Run local build:**
   ```bash
   ./build-and-deploy.sh
   # Choose option to restart deployments
   ```

2. **Or use Make commands:**
   ```bash
   # Update specific service quickly
   make quick-frontend
   make quick-auth
   ```

3. **Verify and commit changes** when ready

## ArgoCD Management

### Access ArgoCD UI

```bash
# Port forward (if not already running)
kubectl port-forward svc/argocd-server -n argocd 8081:443 &

# Access at: https://localhost:8081
# Username: admin
# Password: myq45CaeIZQNPgkA
```

### View Application Status

```bash
# List all applications
kubectl get applications -n argocd

# Detailed status
kubectl describe application restaurant-management -n argocd

# Sync status
argocd app get restaurant-management
```

### Manual Sync

```bash
# Sync all resources
argocd app sync restaurant-management

# Sync specific resource
argocd app sync restaurant-management --resource deployment:frontend

# Force sync (ignore differences)
argocd app sync restaurant-management --force
```

### Rollback

```bash
# List revisions
argocd app history restaurant-management

# Rollback to previous version
argocd app rollback restaurant-management <revision-id>
```

## Troubleshooting

### Images not updating after build

**Problem:** Pods are running but using old images

**Solution:**
```bash
# Delete pods to force recreation
kubectl delete pods -l app=frontend -n restaurant-system

# Or restart deployments
kubectl rollout restart deployment/frontend -n restaurant-system
```

### ArgoCD not syncing

**Problem:** ArgoCD shows "OutOfSync" but not syncing

**Solution:**
```bash
# Check auto-sync status
kubectl get application restaurant-management -n argocd -o jsonpath='{.spec.syncPolicy}'

# Manually sync
argocd app sync restaurant-management

# Check ArgoCD logs
kubectl logs -n argocd deployment/argocd-application-controller
```

### KIND cluster not found

**Problem:** GitHub Actions or script can't find cluster

**Solution:**
```bash
# Check if cluster exists
kind get clusters

# If missing, create it
kind create cluster --name restaurant-cluster --config infrastructure/kubernetes/kind-config.yaml
```

### Build failures

**Problem:** Docker build fails in GitHub Actions

**Solution:**
```bash
# Test build locally
docker build -f frontend/Dockerfile -t restaurant-frontend:latest .

# Check Dockerfile paths
ls -la frontend/Dockerfile
ls -la services/*/Dockerfile
```

## Best Practices

### 1. Branch Strategy
- **main:** Production-ready code
- **developer:** Development and testing
- **staging:** Pre-production testing
- **feature/*:** Individual features

### 2. Commit Messages
Use conventional commits:
```
feat: add user authentication
fix: resolve database connection issue
docs: update CI/CD documentation
chore: update dependencies
```

### 3. Image Tagging
Currently using `:latest` tag. Consider:
- **Git SHA:** `frontend:${GITHUB_SHA}`
- **Semantic versioning:** `frontend:v1.2.3`
- **Build number:** `frontend:build-123`

### 4. Deployment Verification
Always verify after deployment:
```bash
# Check pod status
kubectl get pods -n restaurant-system

# Check service health
make health

# View logs
make logs-frontend
make logs-auth
```

### 5. Resource Limits
Monitor resource usage:
```bash
kubectl top pods -n restaurant-system
kubectl top nodes
```

## Performance Optimization

### Parallel Builds

GitHub Actions already builds images in parallel. To optimize further:

```yaml
# Add build caching
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### ArgoCD Sync Waves

Add sync waves for ordered deployment:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Database first
    argocd.argoproj.io/sync-wave: "2"  # Services second
    argocd.argoproj.io/sync-wave: "3"  # Frontend last
```

## Monitoring

### GitHub Actions Status

Check workflow runs:
- GitHub → Actions tab
- View logs for each step
- Check build duration

### ArgoCD Metrics

```bash
# Application health
kubectl get application -n argocd

# Sync status
argocd app list

# Resource details
argocd app resources restaurant-management
```

## Security Considerations

### 1. Secrets Management
- Never commit secrets to Git
- Use Kubernetes Secrets
- Consider Sealed Secrets or Vault

### 2. ArgoCD Access
- Change default admin password
- Configure RBAC
- Enable SSO if needed

### 3. Image Security
- Scan images for vulnerabilities
- Use specific image tags (not `:latest` in production)
- Implement image signing

## Next Steps

1. **Add Tests to Pipeline:**
   - Unit tests before build
   - Integration tests after deployment
   - E2E tests on staging

2. **Implement Notifications:**
   - Slack/Discord notifications
   - Email alerts on failures
   - GitHub commit status checks

3. **Add Monitoring:**
   - Prometheus for metrics
   - Grafana for dashboards
   - Alert Manager for alerts

4. **Production Registry:**
   - Consider Docker registry for production
   - Implement image scanning
   - Set up image retention policies

## Summary

This CI/CD setup provides:
- ✅ Fast local development (no registry needed)
- ✅ GitOps with ArgoCD
- ✅ Automated builds on push
- ✅ Flexible deployment options
- ✅ Easy rollback capability
- ✅ Cost-effective (no registry fees)

Perfect for:
- Local Kubernetes development
- KIND-based testing
- Small to medium teams
- Cost-conscious projects

For production at scale, consider adding:
- External Docker registry
- Multi-cluster ArgoCD
- Advanced monitoring
- Security scanning
