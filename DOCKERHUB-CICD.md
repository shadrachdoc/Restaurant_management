# DockerHub CI/CD Setup

Complete guide for the automated build and deployment pipeline using DockerHub.

---

## Overview

This CI/CD pipeline automatically:
1. **Builds** Docker images when you push code to GitHub
2. **Pushes** images to DockerHub with both `latest` and commit SHA tags
3. **Deploys** via ArgoCD which pulls images from DockerHub

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Developer: git push to developer/main      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  GitHub Actions:                            │
│  1. Build all Docker images                 │
│  2. Push to DockerHub with tags:            │
│     - latest                                │
│     - commit SHA                            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  DockerHub Registry:                        │
│  yourusername/restaurant-frontend:latest    │
│  yourusername/api-gateway:latest            │
│  yourusername/auth-service:latest           │
│  yourusername/restaurant-service:latest     │
│  yourusername/order-service:latest          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  ArgoCD:                                    │
│  1. Detects Git repo changes                │
│  2. Applies Kubernetes manifests            │
│  3. Pulls images from DockerHub             │
│  4. Deploys to cluster (any env)            │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. DockerHub Account
- Sign up at https://hub.docker.com/
- Get your username (you'll need this)

### 2. GitHub Secrets
Already configured in your repository:
- `DOCKERHUB_USERNAME` - Your DockerHub username
- `DOCKERHUB_TOKEN` - DockerHub access token

**To create a DockerHub token:**
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name it `github-actions`
4. Copy the token
5. Add to GitHub: Settings → Secrets → Actions → New repository secret

---

## Setup Instructions

### Step 1: Commit CI/CD Pipeline

The pipeline automatically handles everything - you just need to commit and push:

```bash
# Commit CI/CD pipeline
git add .github/workflows/ci-cd.yml
git commit -m "Update CI/CD to push images to DockerHub and auto-update deployments"

# Push to trigger the pipeline
git push origin developer
```

The pipeline will automatically:
1. Build all Docker images
2. Push images to DockerHub with `latest` and commit SHA tags
3. Update all deployment YAML files to use DockerHub images
4. Change `imagePullPolicy` from `IfNotPresent` to `Always`
5. Commit the deployment changes back to the repository
6. ArgoCD detects the changes and deploys automatically

**Example changes made by pipeline:**
```yaml
# Before
image: restaurant-frontend:latest
imagePullPolicy: IfNotPresent

# After (automatically updated by pipeline)
image: yourusername/restaurant-frontend:latest
imagePullPolicy: Always
```

### Step 2: No manual steps needed!

The pipeline handles everything automatically. Just push your code and watch it deploy.

### Step 2: Verify Pipeline Execution

1. Go to GitHub repository → Actions tab
2. Watch the "Build and Push Docker Images" workflow
3. Pipeline will:
   - Build and push all 5 images to DockerHub
   - Update deployment files with DockerHub image names
   - Commit changes back to repository (with `[skip ci]` to avoid infinite loop)
4. Check your DockerHub account to see the images

### Step 3: ArgoCD Auto-Deployment

ArgoCD will automatically:
1. Detect the Git repository changes (deployment files updated)
2. Apply the new deployment configurations
3. Pull images from DockerHub
4. Deploy to your Kubernetes cluster

---

## Pipeline Details

### Triggered On

- Push to `main` branch
- Push to `developer` branch
- Push to `staging` branch

### Build Process

For each service, the pipeline:
1. Builds the Docker image
2. Tags with two tags:
   - `yourusername/service:latest` - Always points to most recent
   - `yourusername/service:COMMIT_SHA` - Immutable version for rollbacks
3. Pushes both tags to DockerHub
4. Updates Kubernetes deployment files to use DockerHub images
5. Commits deployment changes back to repository (with `[skip ci]` flag)
6. ArgoCD detects changes and deploys automatically

### Services Built

| Service | DockerHub Repository |
|---------|---------------------|
| Frontend | `yourusername/restaurant-frontend` |
| API Gateway | `yourusername/api-gateway` |
| Auth Service | `yourusername/auth-service` |
| Restaurant Service | `yourusername/restaurant-service` |
| Order Service | `yourusername/order-service` |

---

## Image Tagging Strategy

### Latest Tag
```
yourusername/restaurant-frontend:latest
```
- Always updated on every push
- Used by Kubernetes deployments
- Good for development environments

### Commit SHA Tag
```
yourusername/restaurant-frontend:a1b2c3d4e5f6
```
- Immutable - never changes
- Useful for rollbacks
- Good for production environments

### Example: Rolling Back

If you need to rollback to a previous version:

```bash
# Find the commit SHA you want to rollback to
git log --oneline

# Update deployment to use that specific image
kubectl set image deployment/frontend \
  frontend=yourusername/restaurant-frontend:a1b2c3d4e5f6 \
  -n restaurant-system
```

---

## Workflow File Breakdown

### Login to DockerHub
```yaml
- name: Login to DockerHub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### Build and Push (Example)
```yaml
- name: Build and Push Frontend
  uses: docker/build-push-action@v5
  with:
    context: .
    file: frontend/Dockerfile
    push: true
    tags: |
      ${{ secrets.DOCKERHUB_USERNAME }}/restaurant-frontend:latest
      ${{ secrets.DOCKERHUB_USERNAME }}/restaurant-frontend:${{ github.sha }}
```

### Update Deployment Files (Automated)
```yaml
- name: Update Kubernetes Deployments
  run: |
    # Update all deployment files to use DockerHub images
    sed -i "s|image: restaurant-frontend:latest|image: ${{ secrets.DOCKERHUB_USERNAME }}/restaurant-frontend:latest|g" infrastructure/kubernetes/frontend-deployment.yaml
    sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" infrastructure/kubernetes/frontend-deployment.yaml
    # ... (same for all services)
```

### Commit Changes Back to Repo
```yaml
- name: Commit and Push Deployment Updates
  run: |
    git config --global user.name "GitHub Actions Bot"
    git config --global user.email "actions@github.com"
    git add infrastructure/kubernetes/*.yaml

    if git diff --staged --quiet; then
      echo "No changes to commit"
    else
      git commit -m "Update deployments to use DockerHub images [skip ci]"
      git push
    fi
```

**Note**: The `[skip ci]` flag prevents an infinite loop of pipeline triggers.

---

## Deployment Configuration

### imagePullPolicy: Always

```yaml
containers:
- name: frontend
  image: yourusername/restaurant-frontend:latest
  imagePullPolicy: Always  # Always pull from DockerHub
```

**Why `Always`?**
- Ensures Kubernetes always checks DockerHub for latest image
- Critical for development where `latest` tag is constantly updated
- Production can use specific SHA tags with `IfNotPresent`

### Node Affinity (Database Services)

Auth, order, and restaurant services have node affinity configured:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - restaurant-cluster-worker2  # DNS-reliable node
```

---

## Local Development

### Option 1: Use build-and-deploy.sh (Local Images)

For local KIND cluster development, you can still use local images:

```bash
# Build and load into KIND
./build-and-deploy.sh
```

This bypasses DockerHub and loads images directly into KIND.

### Option 2: Pull from DockerHub (Testing CI/CD)

Test the full CI/CD flow locally:

```bash
# Push code to GitHub
git push origin developer

# Wait for pipeline to complete
# ArgoCD will automatically deploy

# Or manually sync ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8081:443
# Login to ArgoCD UI and click "Sync"
```

---

## Environments

### Development (developer branch)
- Pushes to `developer` branch trigger build
- Images tagged with `latest` and commit SHA
- ArgoCD deploys automatically
- Fast iteration cycle

### Staging (staging branch)
- Pushes to `staging` branch trigger build
- Separate environment for testing
- Pre-production validation

### Production (main branch)
- Pushes to `main` branch trigger build
- Should use immutable SHA tags
- Manual approval before deploy (recommended)

---

## Monitoring and Debugging

### Check Pipeline Status

```bash
# View recent workflow runs
gh run list --workflow=ci-cd.yml

# View specific run logs
gh run view RUN_ID --log
```

### Check DockerHub Images

```bash
# List images using Docker CLI
docker search yourusername/restaurant

# Or visit: https://hub.docker.com/u/yourusername
```

### Check ArgoCD Deployment

```bash
# Check application status
kubectl get applications -n argocd

# Check application details
kubectl describe application restaurant-management -n argocd

# View ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### Check Kubernetes Pods

```bash
# View all pods
kubectl get pods -n restaurant-system

# Check image being used
kubectl get pods -n restaurant-system -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# Describe pod to see pull errors
kubectl describe pod <pod-name> -n restaurant-system
```

---

## Troubleshooting

### Pipeline Fails at DockerHub Login

**Error**: `Error: Cannot perform an interactive login from a non TTY device`

**Solution**: Check GitHub secrets are configured correctly
```bash
# In GitHub repo: Settings → Secrets → Actions
# Verify DOCKERHUB_USERNAME and DOCKERHUB_TOKEN exist
```

### Image Pull Errors in Kubernetes

**Error**: `Failed to pull image: unauthorized`

**Solution**: DockerHub images are private, make them public or add image pull secret

**Option 1: Make images public**
1. Go to DockerHub
2. Select repository
3. Settings → Make Public

**Option 2: Add image pull secret**
```bash
# Create secret
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  --docker-email=YOUR_EMAIL \
  -n restaurant-system

# Update deployment to use secret
# Add to deployment YAML:
spec:
  template:
    spec:
      imagePullSecrets:
      - name: dockerhub-secret
```

### ArgoCD Not Pulling New Images

**Problem**: ArgoCD shows "Synced" but pods have old images

**Cause**: `imagePullPolicy: IfNotPresent` and Kubernetes cached old image

**Solution**: Already fixed by using `imagePullPolicy: Always`

**Manual force refresh**:
```bash
# Delete pod to force recreation with new image
kubectl delete pod <pod-name> -n restaurant-system

# Or rollout restart deployment
kubectl rollout restart deployment frontend -n restaurant-system
```

---

## Cost Considerations

### DockerHub Free Tier
- **6 months** image retention
- **1 team** member
- **100 pulls** per 6 hours per IP
- **Unlimited** public repositories
- **1** private repository

### If You Hit Rate Limits

Upgrade to DockerHub Pro ($5/month):
- **Unlimited** pulls
- **Unlimited** private repositories
- **Faster** builds

Or use alternative registries:
- **GitHub Container Registry** (ghcr.io) - Free for public repos
- **Amazon ECR** - First 500MB storage free
- **Google Container Registry** - Integrated with GCP

---

## Best Practices

### 1. Use Semantic Versioning (Future Enhancement)

Instead of just `latest`, use version tags:

```yaml
tags: |
  yourusername/restaurant-frontend:latest
  yourusername/restaurant-frontend:v1.2.3
  yourusername/restaurant-frontend:${{ github.sha }}
```

### 2. Separate Dev and Prod Images

```yaml
# For developer branch
tags: yourusername/restaurant-frontend:dev-latest

# For main branch
tags: yourusername/restaurant-frontend:latest
```

### 3. Add Image Scanning

Add security scanning to pipeline:

```yaml
- name: Scan image for vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: yourusername/restaurant-frontend:latest
```

### 4. Multi-Stage Builds

Already using multi-stage builds in Dockerfiles for smaller images:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
# ... build steps

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

---

## Migration Path

### From Local KIND Images → DockerHub

| Step | Command | Impact |
|------|---------|--------|
| 1. Commit pipeline | `git add .github/workflows/ci-cd.yml && git commit -m "Add DockerHub CI/CD"` | Pipeline ready |
| 2. Push to trigger | `git push origin developer` | Triggers pipeline |
| 3. Wait for build | Check GitHub Actions | Images pushed to DockerHub + deployments updated |
| 4. ArgoCD sync | Automatic | Deploys from DockerHub |

**Rollback**: If issues occur, you can still use local images:
```bash
# Temporarily use local images
kubectl set image deployment/frontend \
  frontend=restaurant-frontend:latest \
  -n restaurant-system

kubectl patch deployment frontend -n restaurant-system \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"frontend","imagePullPolicy":"IfNotPresent"}]}}}}'
```

---

## Summary

**What You Get:**
✅ Automated builds on every push
✅ Images available anywhere (DockerHub)
✅ Works in any Kubernetes environment
✅ Rollback capability with SHA tags
✅ No manual image building/loading
✅ ArgoCD GitOps deployment

**What Changes:**
- Deployments pull from DockerHub instead of local cache
- Pipeline pushes to DockerHub instead of loading to KIND
- Images available publicly (or with pull secret for private)

---

**Next Steps:**
1. Commit the updated pipeline: `git add .github/workflows/ci-cd.yml`
2. Push to trigger: `git push origin developer`
3. Watch the pipeline automatically build, push, and update deployments!

**Questions?** Check [ISSUES.md](ISSUES.md) or GitHub Actions logs.

---

**Last Updated**: 2025-12-23
**Document Owner**: DevOps Team
