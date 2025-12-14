# Quick Start: CI/CD Pipeline Setup (5 Minutes)

This is a condensed version for quick setup. For detailed instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

---

## Step 1: DockerHub Setup (2 minutes)

1. **Create DockerHub account**: https://hub.docker.com/signup
2. **Generate access token**:
   - Login → Click username → Account Settings → Security
   - Click "New Access Token"
   - Name: `github-actions`
   - Permissions: **Read, Write, Delete**
   - Copy the token (starts with `dckr_pat_...`)

---

## Step 2: GitHub Secrets (1 minute)

Go to: `https://github.com/YOUR_USERNAME/Restaurant_management/settings/secrets/actions`

Add two secrets:

| Name | Value |
|------|-------|
| `DOCKERHUB_USERNAME` | Your DockerHub username |
| `DOCKERHUB_TOKEN` | Token from Step 1 |

---

## Step 3: Update Configuration Files (2 minutes)

### File 1: `argocd/application.yaml`
**Line 10** - Update repository URL:
```yaml
repoURL: https://github.com/YOUR_GITHUB_USERNAME/Restaurant_management.git
```

### File 2: `helm/restaurant-system/values.yaml`
**Update all image repositories** - Replace `yourdockerhub` with your DockerHub username:
```yaml
apiGateway:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/restaurant-api-gateway

authService:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/restaurant-auth-service

restaurantService:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/restaurant-restaurant-service

frontend:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/restaurant-frontend
```

---

## Step 4: Test Pipeline

```bash
# Commit changes
git add argocd/application.yaml helm/restaurant-system/values.yaml
git commit -m "Configure CI/CD pipeline"

# Push to trigger pipeline
git push origin main
```

**Check pipeline**: Go to GitHub → Actions tab → Watch the "CI/CD Pipeline" run

**Verify DockerHub**: After ~10-15 minutes, check https://hub.docker.com/ for your images

---

## Step 5: Local Kubernetes Deployment (Optional)

### Prerequisites:
```bash
# Install KIND
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# Install kubectl (if not installed)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Deploy:
```bash
# Create KIND cluster
kind create cluster --name restaurant-cluster --config infrastructure/kubernetes/kind-config.yaml

# Add Bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy application (replace YOUR_DOCKERHUB_USERNAME)
helm install restaurant-system ./helm/restaurant-system \
  --namespace restaurant-system \
  --create-namespace \
  --set global.imageRegistry=docker.io \
  --set apiGateway.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-api-gateway \
  --set authService.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-auth-service \
  --set restaurantService.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-restaurant-service \
  --set frontend.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-frontend

# Watch deployment
kubectl get pods -n restaurant-system -w
```

### Access Application:
```bash
# Frontend
kubectl port-forward svc/frontend 3000:3000 -n restaurant-system
# Open: http://localhost:3000

# API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system
# Test: curl http://localhost:8000/health
```

---

## Quick Commands Reference

```bash
# Check pipeline status (GitHub CLI)
gh run list

# View Helm deployment
helm list -n restaurant-system

# Check all pods
kubectl get pods -n restaurant-system

# View logs
kubectl logs -f deployment/api-gateway -n restaurant-system

# Uninstall
helm uninstall restaurant-system -n restaurant-system
kind delete cluster --name restaurant-cluster
```

---

## Troubleshooting

**Pipeline fails with "unauthorized"**
→ Verify GitHub secrets are correct (DOCKERHUB_USERNAME and DOCKERHUB_TOKEN)

**ImagePullBackOff error**
→ Check image names match your DockerHub username
→ Make repositories public in DockerHub

**Pods stuck in Pending**
→ Check: `kubectl describe pod <pod-name> -n restaurant-system`

---

## What the Pipeline Does

When you push to `main` or `develop`:

1. ✅ Runs Python tests for all backend services
2. ✅ Runs frontend linting and build
3. ✅ Builds Docker images for 4 services
4. ✅ Pushes images to DockerHub with tags `main-<commit-sha>` or `develop-<commit-sha>`
5. ✅ Deploys to KIND cluster for testing (if on main/develop)
6. ✅ Updates Helm values for ArgoCD (if on main)

**Total Pipeline Time**: ~10-15 minutes

---

## Next Steps

- [ ] Set up ArgoCD for production deployments (see SETUP_GUIDE.md Part 6)
- [ ] Configure monitoring and alerting
- [ ] Set up ingress for external access
- [ ] Add database backups
- [ ] Enable POS service when ready

For detailed instructions, troubleshooting, and ArgoCD setup, see [SETUP_GUIDE.md](SETUP_GUIDE.md).
