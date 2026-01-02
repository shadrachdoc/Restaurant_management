# Deployment Scripts

This directory contains scripts for managing deployments across development and production environments.

## Overview

These scripts help you:
- Set up the production environment on a new laptop
- Deploy specific versions to production
- Rollback deployments when issues occur
- Manage the release lifecycle

## Scripts

### 1. setup-production-laptop.sh

**Purpose**: Initial setup of production environment on a new laptop

**When to use**:
- First time setting up production laptop
- Rebuilding production environment from scratch

**What it does**:
- Checks and installs prerequisites (kubectl, kind, Helm, istioctl)
- Creates kind cluster for production
- Installs Istio service mesh
- Creates production namespace
- Installs Nginx Ingress Controller
- Sets up Prometheus + Grafana monitoring
- Guides you through secrets creation
- Provides DNS configuration instructions

**Usage**:
```bash
# On your new production laptop
./scripts/setup-production-laptop.sh
```

**Prerequisites**:
- Ubuntu Linux (recommended)
- Docker installed
- Sudo access

**Configuration**:
Edit these variables at the top of the script before running:
```bash
PROD_DOMAIN="prod.corpv3.com"  # Your production domain
PROD_NAMESPACE="restaurant-prod"
KIND_CLUSTER_NAME="restaurant-prod-cluster"
```

**Time required**: 10-15 minutes

---

### 2. deploy-production.sh

**Purpose**: Deploy a specific version to production

**When to use**:
- Deploying a new release version
- Promoting code from dev to prod

**What it does**:
- Validates version format
- Pulls Docker images for the specified version
- Loads images into kind cluster
- Updates all deployments to new version
- Waits for rollout to complete
- Verifies deployment health
- Creates git tag for deployment
- Records deployment in PRODUCTION_DEPLOYMENTS.md

**Usage**:
```bash
# Deploy version v1.0.0 to production
./scripts/deploy-production.sh v1.0.0

# Dry run (see what would happen without making changes)
./scripts/deploy-production.sh v1.0.0 dry-run
```

**Prerequisites**:
- Production environment already set up (via setup-production-laptop.sh)
- Version tagged in git (e.g., `git tag v1.0.0`)
- Docker images built and pushed with version tag

**Configuration**:
Edit these variables at the top of the script:
```bash
PROD_DOMAIN="prod.corpv3.com"
PROD_NAMESPACE="restaurant-prod"
DOCKER_REGISTRY="shadrach001"  # Your Docker Hub username
KIND_CLUSTER_NAME="restaurant-prod-cluster"
```

**Version format**: Must follow semantic versioning: `vMAJOR.MINOR.PATCH`
- Examples: `v1.0.0`, `v1.2.3`, `v2.0.0`
- Invalid: `v1.0`, `1.0.0`, `version-1.0`

**Time required**: 5-10 minutes

---

### 3. rollback-production.sh

**Purpose**: Rollback production to a previous version

**When to use**:
- Production deployment has critical bugs
- Need to revert to stable version quickly
- Emergency situations

**What it does**:
- Shows deployment history for all services
- Allows interactive selection of what to rollback
- Confirms before executing rollback
- Performs rollback to specified revision
- Verifies rollback success
- Records rollback in PRODUCTION_DEPLOYMENTS.md

**Usage**:

**Interactive mode** (recommended):
```bash
./scripts/rollback-production.sh
```
This will show you deployment history and let you choose what to rollback.

**Emergency mode** (immediate rollback of all services):
```bash
./scripts/rollback-production.sh --emergency
```
⚠️ **Warning**: Emergency mode immediately rolls back ALL services to their previous versions without confirmation!

**Prerequisites**:
- Production environment running
- At least one previous deployment to rollback to

**Time required**: 3-5 minutes

---

## Complete Workflow

### Initial Production Setup (One-time)

**On Production Laptop:**
```bash
# 1. Clone repository
git clone <repository-url>
cd Restaurant_management

# 2. Configure production domain
nano scripts/setup-production-laptop.sh
# Update PROD_DOMAIN to your domain

# 3. Run setup script
./scripts/setup-production-laptop.sh

# 4. Create production secrets
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  -n restaurant-prod

kubectl create secret generic db-passwords \
  --from-literal=auth-db-password=$(openssl rand -base64 24) \
  --from-literal=restaurant-db-password=$(openssl rand -base64 24) \
  -n restaurant-prod

# 5. Configure DNS
# Add A record: prod.corpv3.com -> <production-laptop-ip>
```

---

### Regular Release Process

**On Development Laptop:**

```bash
# 1. Develop and test features
# ... work on feature branches ...

# 2. Merge to main when ready
git checkout main
git merge feature/my-feature

# 3. Create version tag
git tag -a v1.0.0 -m "Release v1.0.0: Initial production release"
git push origin v1.0.0

# 4. Build and push Docker images with version tag
VERSION=v1.0.0

# Build frontend
docker build -t shadrach001/restaurant-frontend:$VERSION \
  -f frontend/Dockerfile .
docker push shadrach001/restaurant-frontend:$VERSION

# Build API Gateway
docker build -t shadrach001/restaurant_management_api-gateway:$VERSION \
  -f services/api-gateway/Dockerfile .
docker push shadrach001/restaurant_management_api-gateway:$VERSION

# Build Auth Service
docker build -t shadrach001/restaurant_management_auth-service:$VERSION \
  -f services/auth-service/Dockerfile .
docker push shadrach001/restaurant_management_auth-service:$VERSION

# Build Restaurant Service
docker build -t shadrach001/restaurant_management_restaurant-service:$VERSION \
  -f services/restaurant-service/Dockerfile .
docker push shadrach001/restaurant_management_restaurant-service:$VERSION

# 5. Update CHANGELOG.md
nano CHANGELOG.md
# Add release notes for v1.0.0
git add CHANGELOG.md
git commit -m "Update CHANGELOG for v1.0.0"
git push
```

**On Production Laptop:**

```bash
# 1. Pull latest code
git pull origin main
git fetch --tags

# 2. Deploy new version
./scripts/deploy-production.sh v1.0.0

# 3. Verify deployment
kubectl get pods -n restaurant-prod
curl https://prod.corpv3.com/health

# 4. Monitor logs
kubectl logs -n restaurant-prod -l app=frontend -f

# 5. If issues occur, rollback
./scripts/rollback-production.sh
```

---

## Troubleshooting

### Deployment fails with "image not found"

**Problem**: Docker images not available in registry

**Solution**:
```bash
# Verify images exist in Docker Hub
docker pull shadrach001/restaurant-frontend:v1.0.0

# If missing, rebuild and push from dev laptop
docker build -t shadrach001/restaurant-frontend:v1.0.0 -f frontend/Dockerfile .
docker push shadrach001/restaurant-frontend:v1.0.0
```

### Rollout stuck or timing out

**Problem**: Pods not starting, deployment hanging

**Solution**:
```bash
# Check pod status
kubectl get pods -n restaurant-prod

# Check pod logs
kubectl logs -n restaurant-prod <pod-name>

# Describe pod for events
kubectl describe pod -n restaurant-prod <pod-name>

# Common issues:
# - Image pull errors: Check image name and tag
# - CrashLoopBackOff: Check application logs
# - Pending: Check resource availability
```

### Production cluster not accessible

**Problem**: Cannot connect to production cluster

**Solution**:
```bash
# List available clusters
kind get clusters

# Switch to production cluster
kubectl config use-context kind-restaurant-prod-cluster

# Verify connection
kubectl get nodes
```

### DNS not resolving

**Problem**: Domain doesn't point to production

**Solution**:
```bash
# Get production cluster IP
kubectl get nodes -o wide

# Verify DNS (from another machine)
nslookup prod.corpv3.com

# Temporary workaround: Add to /etc/hosts
echo "<cluster-ip> prod.corpv3.com" | sudo tee -a /etc/hosts
```

### Emergency: Everything is broken

**Problem**: Production is completely down

**Solution**:
```bash
# Immediate rollback to previous version
./scripts/rollback-production.sh --emergency

# Verify rollback
kubectl get pods -n restaurant-prod

# Check application
curl https://prod.corpv3.com/health

# Investigate issue
kubectl logs -n restaurant-prod -l app=api-gateway --tail=100
```

---

## Environment Variables

You can override default values using environment variables:

```bash
# Custom production domain
export PROD_DOMAIN="restaurant-prod.example.com"
./scripts/deploy-production.sh v1.0.0

# Custom Docker registry
export DOCKER_REGISTRY="mycompany"
./scripts/deploy-production.sh v1.0.0

# Both
PROD_DOMAIN="prod.example.com" DOCKER_REGISTRY="mycompany" \
  ./scripts/deploy-production.sh v1.0.0
```

---

## Best Practices

### 1. Always Test in Dev First
- Deploy and test in dev environment before production
- Run full test suite
- Verify all features work as expected

### 2. Use Semantic Versioning
- **MAJOR** (v2.0.0): Breaking changes
- **MINOR** (v1.1.0): New features, backward compatible
- **PATCH** (v1.0.1): Bug fixes, backward compatible

### 3. Tag Everything
- Every production deployment should have a git tag
- Use annotated tags: `git tag -a v1.0.0 -m "Description"`
- Push tags: `git push origin v1.0.0`

### 4. Keep CHANGELOG.md Updated
- Document all changes for each version
- Include breaking changes, new features, bug fixes
- Reference issue/PR numbers

### 5. Monitor After Deployment
```bash
# Watch pods
watch kubectl get pods -n restaurant-prod

# Monitor logs
kubectl logs -n restaurant-prod -l app=api-gateway -f

# Check Grafana dashboards
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open http://localhost:3000
```

### 6. Have a Rollback Plan
- Know how to rollback before deploying
- Test rollback in dev environment
- Keep previous version images available

### 7. Deploy During Low Traffic
- Schedule deployments during off-peak hours
- Notify users of maintenance window if downtime expected
- Have team available to monitor

### 8. Database Migrations
If your release includes database changes:
```bash
# Test migrations in dev first
# Create backup before production deployment
kubectl exec -n restaurant-prod <postgres-pod> -- \
  pg_dump -U postgres restaurant_db > backup_$(date +%Y%m%d).sql

# Deploy new version
./scripts/deploy-production.sh v1.0.0

# Verify migrations
kubectl exec -n restaurant-prod <postgres-pod> -- \
  psql -U postgres -d restaurant_db -c "\dt"
```

---

## Security Notes

### Secrets Management
- ✅ Never commit secrets to git
- ✅ Use different secrets for dev and prod
- ✅ Rotate secrets regularly
- ✅ Use strong, random passwords

### Access Control
- Limit who can access production cluster
- Use separate kubeconfig for production
- Require confirmation for destructive operations

### Image Security
- Scan images for vulnerabilities before pushing
- Use specific version tags, not `latest`
- Keep base images updated

---

## Quick Reference

### Check Deployment Status
```bash
kubectl get deployments -n restaurant-prod
kubectl get pods -n restaurant-prod
kubectl get svc -n restaurant-prod
```

### View Logs
```bash
# All pods for a service
kubectl logs -n restaurant-prod -l app=frontend -f

# Specific pod
kubectl logs -n restaurant-prod <pod-name> -f

# Previous container (if crashed)
kubectl logs -n restaurant-prod <pod-name> --previous
```

### Access Grafana
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open http://localhost:3000
# Login: admin / admin
```

### Restart a Service
```bash
kubectl rollout restart deployment/frontend -n restaurant-prod
```

### Scale a Service
```bash
kubectl scale deployment/frontend --replicas=3 -n restaurant-prod
```

### Delete a Stuck Pod
```bash
kubectl delete pod <pod-name> -n restaurant-prod --force
```

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `kubectl logs -n restaurant-prod -l app=<service>`
3. Check pod status: `kubectl describe pod -n restaurant-prod <pod-name>`
4. Consult ISTIO_SERVICE_MESH_ISSUES_RESOLVED.md for known issues
5. If critical, execute emergency rollback

---

## File Locations

- **Deployment History**: `PRODUCTION_DEPLOYMENTS.md`
- **Release Notes**: `CHANGELOG.md`
- **Release Plan**: `RELEASE_MANAGEMENT_PLAN.md`
- **Istio Issues**: `ISTIO_SERVICE_MESH_ISSUES_RESOLVED.md`
- **Scripts**: `scripts/`
  - `setup-production-laptop.sh`
  - `deploy-production.sh`
  - `rollback-production.sh`
