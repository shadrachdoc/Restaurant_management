# Release Management Guide

Complete guide for creating and managing releases of the Restaurant Management System.

---

## Overview

This project uses **Semantic Versioning** (SemVer) with Git tags to manage releases. When you push a version tag, GitHub Actions automatically:

1. Builds Docker images with the version tag
2. Pushes to DockerHub with multiple tags (version + latest + commit SHA)
3. Updates Kubernetes deployment manifests
4. Generates changelog from commits
5. Creates a GitHub Release
6. ArgoCD deploys the versioned release

---

## Semantic Versioning

**Version Format**: `vMAJOR.MINOR.PATCH`

### Version Components

- **MAJOR** (v2.0.0): Breaking changes, incompatible API changes
  - Example: Changing database schema, removing API endpoints

- **MINOR** (v1.1.0): New features, backward-compatible additions
  - Example: Adding new restaurant management features

- **PATCH** (v1.0.1): Bug fixes, backward-compatible fixes
  - Example: Fixing DNS issues, fixing UI bugs

### Examples

```
v1.0.0 → v1.0.1  (Bug fix)
v1.0.1 → v1.1.0  (New feature)
v1.1.0 → v2.0.0  (Breaking change)
```

---

## Release Workflow

### Environment Strategy

| Branch | Purpose | Image Tag | ArgoCD Deployment |
|--------|---------|-----------|-------------------|
| `developer` | Development/Testing | `latest` | Auto-deploy with latest |
| `main` | Production-ready | `v1.2.3` | Auto-deploy with version tag |

---

## Creating a Release

### Step 1: Prepare Your Code

1. **Merge all changes to main branch**:
   ```bash
   git checkout main
   git merge developer
   ```

2. **Test thoroughly** in developer environment first

3. **Update VERSION file** (optional, for reference):
   ```bash
   echo "1.2.0" > VERSION
   git add VERSION
   git commit -m "Bump version to 1.2.0"
   ```

### Step 2: Create and Push Git Tag

1. **Create annotated tag**:
   ```bash
   # For a new feature release
   git tag -a v1.2.0 -m "Release v1.2.0: Add restaurant menu management"

   # For a bug fix release
   git tag -a v1.0.1 -m "Release v1.0.1: Fix DNS resolution issues"

   # For a major release
   git tag -a v2.0.0 -m "Release v2.0.0: New authentication system"
   ```

2. **Push tag to GitHub**:
   ```bash
   git push origin v1.2.0
   ```

   **IMPORTANT**: Pushing the tag triggers the release workflow automatically!

### Step 3: Monitor Release Pipeline

1. **Go to GitHub Actions**:
   ```
   https://github.com/shadrachdoc/Restaurant_management/actions
   ```

2. **Watch the "Release and Deploy" workflow**:
   - ✅ Build all 5 Docker images
   - ✅ Push to DockerHub with version tags
   - ✅ Generate changelog
   - ✅ Update deployment manifests
   - ✅ Create GitHub Release

3. **Verify on DockerHub**:
   ```
   https://hub.docker.com/u/shadrachdoc
   ```

   You should see images tagged with:
   - `v1.2.0` (version tag)
   - `latest` (always latest release)
   - `commit-sha` (immutable reference)

### Step 4: Verify ArgoCD Deployment

1. **Check ArgoCD application**:
   ```bash
   kubectl get applications -n argocd
   ```

2. **Verify image versions in pods**:
   ```bash
   kubectl get pods -n restaurant-system \
     -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
   ```

   Expected output:
   ```
   frontend-xxx    shadrachdoc/restaurant-frontend:v1.2.0
   auth-service-xxx    shadrachdoc/auth-service:v1.2.0
   order-service-xxx   shadrachdoc/order-service:v1.2.0
   ...
   ```

3. **Check ArgoCD UI** (if port-forwarded):
   ```
   http://localhost:8081
   ```

   You should see version `v1.2.0` instead of commit SHA!

---

## Commit Message Conventions

For better changelog generation, use these prefixes:

### Features
```bash
git commit -m "feat: Add restaurant menu management"
git commit -m "feature: Implement order tracking system"
```

### Bug Fixes
```bash
git commit -m "fix: Resolve DNS resolution issues"
git commit -m "bug: Fix authentication timeout"
```

### Documentation
```bash
git commit -m "docs: Add release management guide"
git commit -m "documentation: Update API documentation"
```

### Other
```bash
git commit -m "refactor: Simplify authentication logic"
git commit -m "test: Add integration tests for orders"
git commit -m "chore: Update dependencies"
```

---

## Changelog Generation

The release workflow automatically generates a changelog from commits:

**Example Changelog** (auto-generated):

```markdown
## Changes since v1.1.0

### ✨ Features
- feat: Add restaurant menu management (a1b2c3d)
- feature: Implement order tracking system (d4e5f6g)

### 🐛 Bug Fixes
- fix: Resolve DNS resolution issues via Node Affinity (h7i8j9k)
- bug: Fix ArgoCD sync problems (l0m1n2o)

### 📚 Documentation
- docs: Add comprehensive DOCKERHUB-CICD.md guide (p1q2r3s)
- docs: Update NODE-AFFINITY-GUIDE.md (t4u5v6w)

### 🐳 Docker Images
All images are available on DockerHub with the following tags:
- `shadrachdoc/restaurant-frontend:v1.2.0`
- `shadrachdoc/api-gateway:v1.2.0`
- `shadrachdoc/auth-service:v1.2.0`
- `shadrachdoc/restaurant-service:v1.2.0`
- `shadrachdoc/order-service:v1.2.0`
```

---

## Rollback Procedure

### Option 1: Deploy Previous Version Tag

```bash
# Find previous version
git tag -l | sort -V

# Create new tag pointing to previous version
git checkout v1.1.0
git tag -a v1.1.1 -m "Rollback: Revert to v1.1.0 functionality"
git push origin v1.1.1
```

The release workflow will automatically deploy v1.1.1.

### Option 2: Manual Rollback with kubectl

```bash
# Rollback to specific version
kubectl set image deployment/auth-service \
  auth-service=shadrachdoc/auth-service:v1.1.0 \
  -n restaurant-system

kubectl set image deployment/order-service \
  order-service=shadrachdoc/order-service:v1.1.0 \
  -n restaurant-system

# ... repeat for all services
```

### Option 3: Update Manifests Manually

```bash
# Edit deployment files
vim infrastructure/kubernetes/auth-service-deployment.yaml

# Change image tag:
image: shadrachdoc/auth-service:v1.1.0

# Commit and push
git add infrastructure/kubernetes/*.yaml
git commit -m "Rollback to v1.1.0"
git push origin main
```

ArgoCD will detect changes and rollback automatically.

---

## Release Checklist

Before creating a release, ensure:

- [ ] All features tested in `developer` branch
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md reviewed (auto-generated, but review after)
- [ ] Version number follows SemVer
- [ ] Breaking changes documented (if MAJOR version bump)
- [ ] Database migrations tested (if applicable)
- [ ] ArgoCD application healthy
- [ ] Secrets/ConfigMaps up to date

---

## Viewing Releases

### GitHub Releases Page
```
https://github.com/shadrachdoc/Restaurant_management/releases
```

Shows:
- Release notes
- Changelog
- Docker image tags
- Download source code

### Git Tags
```bash
# List all tags
git tag -l

# Show tag details
git show v1.2.0

# List tags with dates
git tag -l --sort=-creatordate --format='%(creatordate:short) %(refname:short)'
```

### DockerHub
```
https://hub.docker.com/u/shadrachdoc
```

Click on each repository → "Tags" to see all versions.

---

## Development vs Release Workflow

### Development Workflow (developer branch)
```bash
git checkout developer
git add .
git commit -m "feat: Add new feature"
git push origin developer
```
- CI/CD builds with `latest` tag
- Fast iteration
- ArgoCD deploys automatically

### Release Workflow (main branch + tag)
```bash
git checkout main
git merge developer
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags
```
- Release workflow builds with version tag
- Creates GitHub Release
- Updates deployment manifests
- ArgoCD deploys versioned release

---

## Multi-Service Versioning

All services share the same version number:
- `restaurant-frontend:v1.2.0`
- `api-gateway:v1.2.0`
- `auth-service:v1.2.0`
- `restaurant-service:v1.2.0`
- `order-service:v1.2.0`

**Why?** Simplifies deployment tracking and ensures all services are compatible.

**Alternative**: Use independent versioning per service (requires more complex workflow).

---

## Troubleshooting

### Release Workflow Not Triggering

**Problem**: Pushed tag but no workflow run

**Solution**:
1. Check tag format: Must be `v*.*.*` (e.g., `v1.0.0`)
2. Check GitHub Actions are enabled
3. Verify workflow file exists: `.github/workflows/release.yml`

### DockerHub Push Failed

**Problem**: `Error: denied: requested access to the resource is denied`

**Solution**:
1. Verify DockerHub credentials:
   - `DOCKERHUB_USERNAME` in GitHub Secrets
   - `DOCKERHUB_TOKEN` in GitHub Secrets
2. Check token hasn't expired
3. Verify token has push permissions

### ArgoCD Not Deploying New Version

**Problem**: ArgoCD shows "Synced" but old version running

**Solution**:
1. Check deployment manifests updated:
   ```bash
   git log -1 infrastructure/kubernetes/
   ```
2. Force ArgoCD sync:
   ```bash
   kubectl get application restaurant-management -n argocd
   ```
3. Check ArgoCD application points to `main` branch:
   ```yaml
   spec:
     source:
       targetRevision: main
   ```

### Image Pull Errors After Release

**Problem**: Pods fail with `ImagePullBackOff`

**Solution**:
1. Verify image exists on DockerHub
2. Check image name matches deployment:
   ```bash
   kubectl describe pod <pod-name> -n restaurant-system
   ```
3. If images are private, add image pull secret

---

## Best Practices

1. **Always test in developer first**
   - Merge to `developer` → test → merge to `main` → tag

2. **Use meaningful commit messages**
   - Helps with changelog generation
   - Use conventional commits (feat:, fix:, docs:)

3. **Tag from main branch**
   - Ensures stable, tested code

4. **Never force-push tags**
   - Tags should be immutable
   - Create new tag instead

5. **Document breaking changes**
   - Add to tag message
   - Update migration guides

6. **Test rollback procedure**
   - Practice rolling back in dev environment
   - Verify data migrations are reversible

---

## Quick Reference

### Create Release
```bash
git checkout main
git merge developer
git tag -a v1.2.0 -m "Release v1.2.0: Description"
git push origin main --tags
```

### List Releases
```bash
git tag -l --sort=-v:refname
```

### Delete Tag (if mistake)
```bash
# Delete locally
git tag -d v1.2.0

# Delete remotely (CAREFUL!)
git push origin :refs/tags/v1.2.0
```

### Check Current Deployed Version
```bash
kubectl get pods -n restaurant-system \
  -o jsonpath='{.items[0].spec.containers[0].image}'
```

---

## Next Steps

1. **First Release**: Create `v1.0.0` tag to establish baseline
2. **Configure ArgoCD**: Ensure it tracks `main` branch
3. **Test Release Process**: Create test release `v1.0.1`
4. **Document Rollback**: Practice rollback procedure

---

**Last Updated**: 2025-12-23
**Document Owner**: DevOps Team
