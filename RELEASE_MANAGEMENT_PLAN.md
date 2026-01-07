# Release Management Plan - Dev/Prod Environment Strategy

**Date Created:** December 30, 2025
**System:** Restaurant Management System
**Environment Architecture:** Dual Laptop Setup with Kind Clusters

---

## Table of Contents
1. [Overview](#overview)
2. [Environment Architecture](#environment-architecture)
3. [Prerequisites](#prerequisites)
4. [Release Workflow](#release-workflow)
5. [Git Branching Strategy](#git-branching-strategy)
6. [Version Tagging Convention](#version-tagging-convention)
7. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
8. [Production Deployment Checklist](#production-deployment-checklist)
9. [Rollback Strategy](#rollback-strategy)
10. [Configuration Management](#configuration-management)
11. [Required Setup on Production Laptop](#required-setup-on-production-laptop)

---

## Overview

### Current Setup (Dev Environment)
- **Location:** Current laptop
- **Cluster:** kind cluster (`restaurant-cluster`)
- **Namespace:** `restaurant-system`
- **Domain:** `restaurant.corpv3.com`
- **Purpose:** Development, testing, and experimentation

### Planned Setup (Prod Environment)
- **Location:** Second Ubuntu laptop
- **Cluster:** kind cluster (new production cluster)
- **Namespace:** `restaurant-production`
- **Domain:** `prod-restaurant.corpv3.com` (or your choice)
- **Purpose:** Stable production releases for end users

### Goals
✅ Separate dev and prod environments
✅ Controlled release process
✅ Easy rollback capability
✅ Automated deployment pipeline
✅ Configuration separation
✅ Version tracking

---

## Environment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│                    Restaurant_management                         │
└─────────────────┬──────────────────────────┬────────────────────┘
                  │                          │
                  │                          │
    ┌─────────────▼──────────────┐  ┌───────▼────────────────────┐
    │   Dev Laptop (Current)     │  │  Prod Laptop (New)         │
    │  ┌──────────────────────┐  │  │  ┌──────────────────────┐  │
    │  │  Kind Cluster        │  │  │  │  Kind Cluster        │  │
    │  │  restaurant-cluster  │  │  │  │  restaurant-prod     │  │
    │  │                      │  │  │  │                      │  │
    │  │  Namespace:          │  │  │  │  Namespace:          │  │
    │  │  restaurant-system   │  │  │  │  restaurant-prod     │  │
    │  │                      │  │  │  │                      │  │
    │  │  Branch: develop     │  │  │  │  Branch: main        │  │
    │  │  Tags: v*-dev        │  │  │  │  Tags: v*            │  │
    │  └──────────────────────┘  │  │  └──────────────────────┘  │
    │                            │  │                            │
    │  Domain:                   │  │  Domain:                   │
    │  restaurant.corpv3.com     │  │  prod.corpv3.com          │
    │                            │  │                            │
    │  Cloudflare Tunnel: Dev    │  │  Cloudflare Tunnel: Prod  │
    └────────────────────────────┘  └────────────────────────────┘
```

---

## Prerequisites

### Required on Production Laptop

1. **Ubuntu Setup**
   - Ubuntu 20.04+ (already installed ✅)
   - Docker installed
   - kubectl installed
   - kind installed ✅
   - git installed
   - Helm installed (for Istio)

2. **Network Access**
   - Internet connectivity
   - Access to GitHub repository
   - Access to Cloudflare for tunnel setup

3. **Tools to Install**
   ```bash
   # Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER

   # kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

   # Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

   # Istio
   curl -L https://istio.io/downloadIstio | sh -
   cd istio-*
   export PATH=$PWD/bin:$PATH
   ```

4. **GitHub Access**
   - SSH key setup for git access
   - Repository clone on prod laptop

5. **Secrets & Credentials**
   - Database passwords (production-specific)
   - JWT secret keys (different from dev)
   - Cloudflare tunnel credentials

---

## Release Workflow

### Development Flow (Dev Laptop)

```
Developer makes changes
       ↓
Commit to feature branch
       ↓
Test locally on dev cluster
       ↓
Create PR to develop branch
       ↓
Merge PR
       ↓
Auto-deploy to dev environment
       ↓
QA testing on dev
       ↓
Create release PR (develop → main)
       ↓
Tag release version
       ↓
Deploy to production laptop
```

### Detailed Steps

#### Step 1: Development (Dev Laptop)
```bash
# Work on feature
git checkout -b feature/my-feature develop
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# Test on dev cluster
docker build ...
kind load ...
kubectl apply ...
```

#### Step 2: Code Review & Merge
```bash
# Create PR on GitHub: feature/my-feature → develop
# After review and approval, merge

# Pull latest develop
git checkout develop
git pull origin develop
```

#### Step 3: Create Release (When Ready for Prod)
```bash
# Ensure develop is stable and tested
# Create release branch
git checkout -b release/v1.2.0 develop

# Update version in files
# - Update package.json versions
# - Update Helm chart versions
# - Update CHANGELOG.md

git add .
git commit -m "chore: bump version to v1.2.0"
git push origin release/v1.2.0

# Create PR: release/v1.2.0 → main
# After approval, merge to main
```

#### Step 4: Tag Release
```bash
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.2.0 -m "Release v1.2.0: User management authentication fixes"
git push origin v1.2.0

# Merge back to develop
git checkout develop
git merge main
git push origin develop
```

#### Step 5: Deploy to Production (Prod Laptop)
```bash
# On production laptop
git fetch --tags
git checkout v1.2.0

# Run production deployment script
./scripts/deploy-production.sh v1.2.0
```

---

## Git Branching Strategy

### Branch Structure

```
main (production)
  ├── v1.0.0 (tag)
  ├── v1.1.0 (tag)
  └── v1.2.0 (tag)

develop (development)
  └── feature/user-auth
  └── feature/order-tracking
  └── bugfix/login-issue

hotfix/critical-bug → main → develop
release/v1.2.0 → main → develop
```

### Branch Purposes

| Branch | Purpose | Protected | Deploy To |
|--------|---------|-----------|-----------|
| `main` | Production-ready code | ✅ Yes | Production laptop |
| `develop` | Integration branch | ✅ Yes | Dev laptop (auto) |
| `feature/*` | New features | No | Dev laptop (manual) |
| `bugfix/*` | Bug fixes | No | Dev laptop (manual) |
| `hotfix/*` | Urgent prod fixes | No | Production (emergency) |
| `release/*` | Release preparation | No | Staging/QA |

### Branch Protection Rules

**main branch:**
- Require pull request reviews (1 approver minimum)
- Require status checks to pass
- No direct commits
- Only merge from `release/*` or `hotfix/*`

**develop branch:**
- Require pull request reviews
- No direct commits
- Merge from `feature/*` and `bugfix/*`

---

## Version Tagging Convention

### Semantic Versioning: `vMAJOR.MINOR.PATCH`

**Format:** `v1.2.3`
- **MAJOR:** Breaking changes (v1 → v2)
- **MINOR:** New features, backward compatible (v1.1 → v1.2)
- **PATCH:** Bug fixes, backward compatible (v1.2.1 → v1.2.2)

### Examples

```
v1.0.0 - Initial production release
v1.1.0 - Added user management features
v1.1.1 - Fixed authentication bug
v1.2.0 - Added order tracking
v2.0.0 - Migrated to microservices (breaking change)
```

### Pre-release Tags (Optional)

```
v1.2.0-rc.1  - Release candidate 1
v1.2.0-beta.1 - Beta version
v1.2.0-alpha.1 - Alpha version
```

### Creating Tags

```bash
# Annotated tag (recommended)
git tag -a v1.2.0 -m "Release v1.2.0: Summary of changes"

# Push tag
git push origin v1.2.0

# List tags
git tag -l

# View tag details
git show v1.2.0

# Delete tag (if mistake)
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0
```

---

## CI/CD Pipeline Setup

### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          ref: ${{ github.ref }}

      - name: Get version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push images
        run: |
          VERSION=${{ steps.version.outputs.VERSION }}

          # Build all services
          docker build -t shadrach001/restaurant-frontend:${VERSION} \
                       -t shadrach001/restaurant-frontend:latest \
                       -f frontend/Dockerfile .
          docker build -t shadrach001/restaurant-auth-service:${VERSION} \
                       -f services/auth-service/Dockerfile .
          docker build -t shadrach001/restaurant-service:${VERSION} \
                       -f services/restaurant-service/Dockerfile .
          docker build -t shadrach001/restaurant-api-gateway:${VERSION} \
                       -f services/api-gateway/Dockerfile .
          docker build -t shadrach001/restaurant-order-service:${VERSION} \
                       -f services/order-service/Dockerfile .
          docker build -t shadrach001/restaurant-customer-service:${VERSION} \
                       -f services/customer-service/Dockerfile .

          # Push to Docker Hub
          docker push shadrach001/restaurant-frontend:${VERSION}
          docker push shadrach001/restaurant-frontend:latest
          docker push shadrach001/restaurant-auth-service:${VERSION}
          docker push shadrach001/restaurant-service:${VERSION}
          docker push shadrach001/restaurant-api-gateway:${VERSION}
          docker push shadrach001/restaurant-order-service:${VERSION}
          docker push shadrach001/restaurant-customer-service:${VERSION}

      - name: Create release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ steps.version.outputs.VERSION }}
          release_name: Release ${{ steps.version.outputs.VERSION }}
          body: |
            Production release ${{ steps.version.outputs.VERSION }}

            ## Changes
            See CHANGELOG.md for details

            ## Deployment
            Pull this version on production laptop and run:
            ```
            git checkout ${{ steps.version.outputs.VERSION }}
            ./scripts/deploy-production.sh ${{ steps.version.outputs.VERSION }}
            ```
          draft: false
          prerelease: false
```

### Option 2: Manual Deployment Script

Create `scripts/deploy-production.sh`:

```bash
#!/bin/bash
set -e

VERSION=${1:-latest}

echo "=========================================="
echo "Production Deployment Script"
echo "Version: $VERSION"
echo "=========================================="

# Verify we're on the right tag
CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "not-on-tag")
if [ "$CURRENT_TAG" != "$VERSION" ]; then
    echo "Error: Not on tag $VERSION. Current: $CURRENT_TAG"
    echo "Run: git checkout $VERSION"
    exit 1
fi

# Confirmation prompt
read -p "Deploy version $VERSION to PRODUCTION? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo "Step 1: Pulling Docker images..."
docker pull shadrach001/restaurant-frontend:$VERSION
docker pull shadrach001/restaurant-auth-service:$VERSION
docker pull shadrach001/restaurant-service:$VERSION
docker pull shadrach001/restaurant-api-gateway:$VERSION
docker pull shadrach001/restaurant-order-service:$VERSION
docker pull shadrach001/restaurant-customer-service:$VERSION

echo "Step 2: Loading images into kind cluster..."
kind load docker-image shadrach001/restaurant-frontend:$VERSION --name restaurant-prod
kind load docker-image shadrach001/restaurant-auth-service:$VERSION --name restaurant-prod
kind load docker-image shadrach001/restaurant-service:$VERSION --name restaurant-prod
kind load docker-image shadrach001/restaurant-api-gateway:$VERSION --name restaurant-prod
kind load docker-image shadrach001/restaurant-order-service:$VERSION --name restaurant-prod
kind load docker-image shadrach001/restaurant-customer-service:$VERSION --name restaurant-prod

echo "Step 3: Updating Kubernetes deployments..."
kubectl set image deployment/frontend frontend=shadrach001/restaurant-frontend:$VERSION -n restaurant-production
kubectl set image deployment/auth-service auth-service=shadrach001/restaurant-auth-service:$VERSION -n restaurant-production
kubectl set image deployment/restaurant-service restaurant-service=shadrach001/restaurant-service:$VERSION -n restaurant-production
kubectl set image deployment/api-gateway api-gateway=shadrach001/restaurant-api-gateway:$VERSION -n restaurant-production
kubectl set image deployment/order-service order-service=shadrach001/restaurant-order-service:$VERSION -n restaurant-production
kubectl set image deployment/customer-service customer-service=shadrach001/restaurant-customer-service:$VERSION -n restaurant-production

echo "Step 4: Waiting for rollouts to complete..."
kubectl rollout status deployment/frontend -n restaurant-production
kubectl rollout status deployment/auth-service -n restaurant-production
kubectl rollout status deployment/restaurant-service -n restaurant-production
kubectl rollout status deployment/api-gateway -n restaurant-production
kubectl rollout status deployment/order-service -n restaurant-production
kubectl rollout status deployment/customer-service -n restaurant-production

echo "Step 5: Verifying deployment..."
kubectl get pods -n restaurant-production

echo "=========================================="
echo "✅ Deployment Complete!"
echo "Version $VERSION is now running in production"
echo "=========================================="
```

Make it executable:
```bash
chmod +x scripts/deploy-production.sh
```

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] All tests passing in dev environment
- [ ] QA approval received
- [ ] Performance testing completed
- [ ] Security scan passed
- [ ] Database migrations prepared (if any)
- [ ] Backup of production database created
- [ ] Release notes prepared
- [ ] Rollback plan documented
- [ ] Stakeholders notified of deployment window

### Deployment Steps

- [ ] Git checkout to release tag
- [ ] Verify tag version matches release
- [ ] Pull Docker images from registry
- [ ] Load images into kind cluster
- [ ] Apply database migrations (if any)
- [ ] Update Kubernetes deployments
- [ ] Wait for all pods to be ready
- [ ] Run smoke tests
- [ ] Verify health endpoints
- [ ] Check logs for errors
- [ ] Test critical user flows

### Post-Deployment

- [ ] Monitor error rates for 15 minutes
- [ ] Check response times
- [ ] Verify all services are communicating
- [ ] Test authentication flows
- [ ] Confirm order processing works
- [ ] Update release documentation
- [ ] Notify stakeholders of successful deployment
- [ ] Tag deployment in monitoring system

### If Issues Occur

- [ ] Check logs: `kubectl logs -n restaurant-production -l app=<service>`
- [ ] Check pod status: `kubectl get pods -n restaurant-production`
- [ ] Check events: `kubectl get events -n restaurant-production --sort-by='.lastTimestamp'`
- [ ] If critical: Execute rollback procedure
- [ ] Document incident for post-mortem

---

## Rollback Strategy

### Quick Rollback Commands

```bash
# Rollback to previous version
VERSION=v1.1.0  # Previous stable version

./scripts/deploy-production.sh $VERSION
```

### Emergency Rollback (If Script Fails)

```bash
# Rollback each deployment individually
kubectl rollout undo deployment/frontend -n restaurant-production
kubectl rollout undo deployment/auth-service -n restaurant-production
kubectl rollout undo deployment/restaurant-service -n restaurant-production
kubectl rollout undo deployment/api-gateway -n restaurant-production
kubectl rollout undo deployment/order-service -n restaurant-production
kubectl rollout undo deployment/customer-service -n restaurant-production

# Verify rollback
kubectl rollout status deployment/frontend -n restaurant-production
```

### Rollback Decision Tree

```
Issue Detected
     ↓
Is it critical? → No → Monitor and plan fix
     ↓ Yes
Can it be hotfixed in < 10 min? → Yes → Apply hotfix
     ↓ No
ROLLBACK IMMEDIATELY
     ↓
Verify rollback successful
     ↓
Investigate root cause
     ↓
Prepare hotfix
     ↓
Test in dev
     ↓
Deploy hotfix as new version
```

---

## Configuration Management

We use **Helm** for managing environment-specific configurations. The Helm chart is located at `helm/restaurant-system/`.

### Environment-Specific Configs

**Dev Environment** (`helm/restaurant-system/values.yaml`):
```yaml
# Default values - used for development
namespace: restaurant-system

# Dev-friendly image settings
imagePullPolicy: IfNotPresent

# Lower replica counts for laptop
apiGateway:
  replicaCount: 1
  image:
    repository: shadrach85/restaurant_management_api-gateway
    tag: latest  # Use latest in dev for faster iteration

# Dev resource limits (laptop-friendly)
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

# Dev config
config:
  environment: "development"
  logLevel: "DEBUG"  # Verbose logging in dev

# Dev secrets (not secure - for dev only!)
secrets:
  jwtSecretKey: "dev-secret-key-change-in-prod"
```

**Production Environment** (`helm/restaurant-system/values-prod.yaml`):
```yaml
# Production overrides - use with -f values-prod.yaml
namespace: restaurant-prod

# Strict image policy in production
imagePullPolicy: IfNotPresent

# Higher replica counts for HA
apiGateway:
  replicaCount: 2
  image:
    repository: shadrach001/restaurant_management_api-gateway
    tag: "REPLACE_WITH_VERSION"  # Specific version tags in prod
  autoscaling:
    enabled: true  # Enable autoscaling in prod
    minReplicas: 2
    maxReplicas: 5

# Production resource limits (more resources)
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

# Production config
config:
  environment: "production"
  logLevel: "INFO"  # Less verbose in prod

# Production secrets (MUST be changed!)
secrets:
  jwtSecretKey: "REPLACE_WITH_PRODUCTION_SECRET"
  postgresPassword: "REPLACE_WITH_PRODUCTION_SECRET"
```

### Deploying with Helm

**Development** (on dev laptop):
```bash
# Deploy with default values
helm upgrade restaurant-system helm/restaurant-system \
  --install \
  --namespace restaurant-system \
  --create-namespace \
  --wait

# Or use explicit dev values
helm upgrade restaurant-system helm/restaurant-system \
  --install \
  --namespace restaurant-system \
  --values helm/restaurant-system/values.yaml \
  --wait
```

**Production** (on prod laptop):
```bash
# Deploy with production values
helm upgrade restaurant-system helm/restaurant-system \
  --install \
  --namespace restaurant-prod \
  --create-namespace \
  --values helm/restaurant-system/values-prod.yaml \
  --wait

# Or use the deployment script (recommended)
./scripts/deploy-production.sh v1.0.0
```

### Managing Helm Releases

```bash
# List releases
helm list -n restaurant-system      # Dev
helm list -n restaurant-prod         # Prod

# Check release status
helm status restaurant-system -n restaurant-system

# View release history
helm history restaurant-system -n restaurant-prod

# Rollback to previous release
helm rollback restaurant-system -n restaurant-prod

# Rollback to specific revision
helm rollback restaurant-system 3 -n restaurant-prod

# Uninstall release (careful!)
helm uninstall restaurant-system -n restaurant-prod
```

---

## Required Setup on Production Laptop

### Initial Setup Script

The production setup script is already created at `scripts/setup-production-laptop.sh`.

**What it does**:
1. Checks and installs prerequisites (kubectl, kind, Helm, istioctl)
2. Creates kind cluster named `restaurant-prod-cluster`
3. Installs Istio service mesh with production profile
4. Creates production namespace (`restaurant-prod`)
5. Installs Nginx Ingress Controller
6. Sets up Prometheus + Grafana monitoring
7. Guides you through creating production secrets
8. Provides DNS configuration instructions

**How to run**:
```bash
cd ~/Restaurant_management
./scripts/setup-production-laptop.sh
```

**What you need to configure BEFORE running**:
Edit these files and replace placeholders:
1. `helm/restaurant-system/values-prod.yaml`:
   - Production domain (lines 246, 253)
   - Docker registry/username (all `repository:` lines)
   - Production secrets (lines 287-289, 204, 224)

2. `scripts/setup-production-laptop.sh`:
   - Production domain (line 16)

3. `scripts/deploy-production.sh`:
   - Production domain (line 16)
   - Docker registry (line 19)

See [PRODUCTION_LAPTOP_SETUP.md](PRODUCTION_LAPTOP_SETUP.md) for detailed configuration instructions.

### Production-Specific kind Config

Create `infrastructure/k8s/kind-config-prod.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: restaurant-prod
nodes:
- role: control-plane
  image: kindest/node:v1.28.0
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "environment=production"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
  image: kindest/node:v1.28.0
- role: worker
  image: kindest/node:v1.28.0
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
```

---

## What I Need From You

### Information Needed

1. **Production Domain**
   - What subdomain for production? (e.g., `prod.corpv3.com`, `restaurant-prod.corpv3.com`)
   - Do you want staging environment too? (e.g., `staging.corpv3.com`)

2. **Docker Registry**
   - Continue using Docker Hub? (`shadrach001/*`)
   - Or set up private registry?

3. **Production Secrets**
   - Generate new JWT secret key for production
   - New database passwords
   - Any API keys that differ from dev

4. **Deployment Schedule**
   - Preferred deployment window (day/time)?
   - Maintenance window for updates?

5. **Monitoring & Alerts**
   - Email for alerts?
   - Slack/Discord webhook for notifications?

6. **Backup Strategy**
   - Database backup frequency?
   - Backup retention period?

### Actions You Need to Take

1. **On Production Laptop:**
   ```bash
   # Clone repository
   git clone git@github.com:yourusername/Restaurant_management.git
   cd Restaurant_management

   # Run setup script (I'll create this)
   ./scripts/setup-production-laptop.sh
   ```

2. **Cloudflare Setup:**
   - Create new tunnel for production
   - Point new subdomain to production laptop

3. **GitHub Secrets** (for CI/CD):
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - `PRODUCTION_SSH_KEY` (if using SSH deploy)

---

## Summary

### Development Workflow
1. Work on feature branches
2. Test on dev laptop
3. Merge to `develop` branch
4. Auto-deploys to dev environment

### Release Workflow
1. Create release branch from `develop`
2. Bump version, update changelog
3. Merge to `main`
4. Tag with version number
5. CI/CD builds and pushes images
6. Manual deployment on production laptop

### Deployment Command
```bash
# On production laptop
git fetch --tags
git checkout v1.2.0
./scripts/deploy-production.sh v1.2.0
```

---

## Next Steps

Let me know:
1. ✅ Your chosen production subdomain
2. ✅ If you want automated CI/CD or manual deploys
3. ✅ Any specific requirements or concerns

I'll then create all the necessary scripts and configurations!

---

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Author:** Claude Sonnet 4.5
