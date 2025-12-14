# CI/CD Pipeline Setup Guide

This guide will help you configure the CI/CD pipeline for automated DockerHub image builds and Kubernetes deployments.

---

## Part 1: DockerHub Configuration

### Step 1.1: Create DockerHub Account
1. Go to https://hub.docker.com/
2. Sign up for a free account (if you don't have one)
3. Verify your email address

### Step 1.2: Create DockerHub Access Token
1. Log in to DockerHub
2. Click on your **username** (top right corner)
3. Select **Account Settings**
4. Go to **Security** tab
5. Click **New Access Token**
6. Configure the token:
   - **Description**: `github-actions-restaurant-management`
   - **Access permissions**: Select **Read, Write, Delete**
7. Click **Generate**
8. **CRITICAL**: Copy the token immediately and save it securely
   - You will NOT be able to see this token again
   - Example token format: `dckr_pat_xxxxxxxxxxxxxxxxxxxxx`

---

## Part 2: GitHub Repository Secrets

### Step 2.1: Navigate to GitHub Secrets
1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/Restaurant_management`
2. Click the **Settings** tab (top navigation)
3. In the left sidebar, expand **Secrets and variables**
4. Click **Actions**

### Step 2.2: Add DockerHub Secrets

Click **New repository secret** button and add these two secrets:

**Secret 1: DOCKERHUB_USERNAME**
- Name: `DOCKERHUB_USERNAME`
- Value: Your DockerHub username (e.g., `johndoe`)
- Click **Add secret**

**Secret 2: DOCKERHUB_TOKEN**
- Name: `DOCKERHUB_TOKEN`
- Value: The access token you copied in Step 1.2
- Click **Add secret**

### Step 2.3: Verify Secrets
After adding, you should see:
- ✅ `DOCKERHUB_USERNAME`
- ✅ `DOCKERHUB_TOKEN`

---

## Part 3: Update Repository Configuration Files

### Step 3.1: Update ArgoCD Repository URL

Edit the file: `argocd/application.yaml`

Find line 10:
```yaml
repoURL: https://github.com/your-org/Restaurant_management.git  # Update with your repo
```

Replace with your actual GitHub repository:
```yaml
repoURL: https://github.com/YOUR_GITHUB_USERNAME/Restaurant_management.git
```

### Step 3.2: Update Helm Values (Optional)

Edit the file: `helm/restaurant-system/values.yaml`

Update the image repositories with your DockerHub username:

Find these lines and replace `yourdockerhub` with your actual DockerHub username:
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

**Note**: The GitHub Actions workflow already handles this dynamically, but it's good to update the defaults.

---

## Part 4: Testing the Pipeline

### Step 4.1: Trigger the Pipeline

The pipeline automatically runs when you:
1. Push to `main` or `develop` branch
2. Create a Pull Request to `main` or `develop`

**Test it now:**
```bash
# Make sure you're on the develop or main branch
git checkout main

# Add a small change (e.g., update README)
echo "# CI/CD Pipeline Active" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

### Step 4.2: Monitor Pipeline Execution

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You should see your workflow running: "CI/CD Pipeline"
4. Click on the workflow to see details

**Pipeline Stages:**
1. ✅ **test-backend**: Tests auth-service, restaurant-service, api-gateway
2. ✅ **test-frontend**: Lints and builds frontend
3. ✅ **build-images**: Builds Docker images and pushes to DockerHub
4. ✅ **deploy-kind**: Deploys to local KIND cluster (on main/develop)
5. ✅ **update-argocd**: Updates Helm values for ArgoCD (on main only)

### Step 4.3: Verify DockerHub Images

1. Go to https://hub.docker.com/
2. Log in and go to **Repositories**
3. You should see 4 new repositories:
   - `restaurant-auth-service`
   - `restaurant-restaurant-service`
   - `restaurant-api-gateway`
   - `restaurant-frontend`
4. Click on each to see the pushed image tags (e.g., `main-abc1234`)

---

## Part 5: Local Kubernetes Deployment

### Step 5.1: Install Required Tools

**Install KIND (Kubernetes in Docker):**
```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS
brew install kind

# Verify installation
kind version
```

**Install kubectl:**
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# macOS
brew install kubectl

# Verify installation
kubectl version --client
```

**Install Helm:**
```bash
# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# macOS
brew install helm

# Verify installation
helm version
```

### Step 5.2: Create KIND Cluster

```bash
# Create cluster with custom config
kind create cluster --name restaurant-cluster --config infrastructure/kubernetes/kind-config.yaml

# Verify cluster is running
kubectl cluster-info --context kind-restaurant-cluster
kubectl get nodes
```

### Step 5.3: Deploy Using Helm

**Add Bitnami repository (for PostgreSQL and Redis):**
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

**Deploy the application:**
```bash
# Deploy with your DockerHub images
helm install restaurant-system ./helm/restaurant-system \
  --namespace restaurant-system \
  --create-namespace \
  --set global.imageRegistry=docker.io \
  --set apiGateway.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-api-gateway \
  --set apiGateway.image.tag=latest \
  --set authService.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-auth-service \
  --set authService.image.tag=latest \
  --set restaurantService.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-restaurant-service \
  --set restaurantService.image.tag=latest \
  --set frontend.image.repository=YOUR_DOCKERHUB_USERNAME/restaurant-frontend \
  --set frontend.image.tag=latest \
  --set posService.enabled=false
```

**Replace `YOUR_DOCKERHUB_USERNAME` with your actual DockerHub username!**

### Step 5.4: Monitor Deployment

```bash
# Watch pods being created
kubectl get pods -n restaurant-system -w

# Check all resources
kubectl get all -n restaurant-system

# Check if services are ready (wait until all show "Running")
kubectl wait --for=condition=ready pod --all -n restaurant-system --timeout=300s
```

### Step 5.5: Access the Application

**Frontend (LoadBalancer - with KIND use port-forward):**
```bash
# Port forward frontend
kubectl port-forward svc/frontend 3000:3000 -n restaurant-system

# Open browser: http://localhost:3000
```

**API Gateway:**
```bash
# Port forward API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system

# Test health endpoint
curl http://localhost:8000/health
```

**PostgreSQL (for debugging):**
```bash
# Get PostgreSQL password
kubectl get secret restaurant-secrets -n restaurant-system -o jsonpath="{.data.POSTGRES_PASSWORD}" | base64 -d

# Port forward PostgreSQL
kubectl port-forward svc/restaurant-system-postgresql 5432:5432 -n restaurant-system

# Connect with psql
psql -h localhost -U restaurant_admin -d restaurant_db
```

---

## Part 6: ArgoCD Setup (Optional - For Production)

If you want to set up ArgoCD for GitOps deployment:

### Step 6.1: Install ArgoCD

```bash
# Create ArgoCD namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
```

### Step 6.2: Access ArgoCD UI

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser: https://localhost:8080
# Username: admin
# Password: (from command above)
```

### Step 6.3: Deploy Application via ArgoCD

```bash
# Install ArgoCD CLI (optional)
# Linux
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# Login to ArgoCD
argocd login localhost:8080 --username admin --password <password>

# Apply the application
kubectl apply -f argocd/application.yaml -n argocd

# Check application status
argocd app get restaurant-system
argocd app sync restaurant-system
```

### Step 6.4: Add ArgoCD Secrets to GitHub (Optional)

For automated ArgoCD sync in CI/CD:

**Get ArgoCD Auth Token:**
```bash
# Login and generate token
argocd account generate-token --account admin
```

**Add to GitHub Secrets:**
- Name: `ARGOCD_SERVER`
  - Value: `https://your-argocd-server.com` or `https://localhost:8080`
- Name: `ARGOCD_AUTH_TOKEN`
  - Value: (token from command above)

---

## Part 7: Cleanup

### Remove KIND Cluster
```bash
kind delete cluster --name restaurant-cluster
```

### Uninstall Helm Release
```bash
helm uninstall restaurant-system --namespace restaurant-system
kubectl delete namespace restaurant-system
```

---

## Troubleshooting

### Pipeline Fails: "unauthorized: incorrect username or password"
- ✅ Verify `DOCKERHUB_USERNAME` secret is correct
- ✅ Verify `DOCKERHUB_TOKEN` is valid and not expired
- ✅ Regenerate token if needed

### Pipeline Fails: Tests failing
```bash
# Run tests locally first
cd services/auth-service
python -m pytest tests/ -v

cd ../restaurant-service
python -m pytest tests/ -v

cd ../api-gateway
python -m pytest tests/ -v
```

### Pods stuck in "ImagePullBackOff"
- ✅ Check if images exist in DockerHub
- ✅ Verify image names match your DockerHub username
- ✅ Make images public in DockerHub or add image pull secrets

### Pods stuck in "Pending"
```bash
# Check events
kubectl describe pod <pod-name> -n restaurant-system

# Check if resources are available
kubectl top nodes
```

### Database connection errors
```bash
# Check if PostgreSQL is running
kubectl get pods -l app.kubernetes.io/name=postgresql -n restaurant-system

# Check logs
kubectl logs -l app.kubernetes.io/name=postgresql -n restaurant-system
```

---

## Quick Reference Commands

```bash
# Check pipeline status
gh workflow view  # requires GitHub CLI

# Check DockerHub images
docker search YOUR_DOCKERHUB_USERNAME/restaurant

# View Helm release
helm list -n restaurant-system

# Check pod logs
kubectl logs -f <pod-name> -n restaurant-system

# Get all services
kubectl get svc -n restaurant-system

# Restart a deployment
kubectl rollout restart deployment/api-gateway -n restaurant-system

# Scale a deployment
kubectl scale deployment/api-gateway --replicas=3 -n restaurant-system
```

---

## Summary Checklist

Before pushing to trigger the pipeline:

- [ ] DockerHub account created
- [ ] DockerHub access token generated
- [ ] `DOCKERHUB_USERNAME` secret added to GitHub
- [ ] `DOCKERHUB_TOKEN` secret added to GitHub
- [ ] `argocd/application.yaml` updated with your GitHub repo URL
- [ ] `helm/restaurant-system/values.yaml` updated with your DockerHub username
- [ ] Committed and pushed changes to `main` or `develop` branch
- [ ] Pipeline running successfully in GitHub Actions
- [ ] Docker images visible in DockerHub
- [ ] (Optional) KIND cluster created and application deployed locally
- [ ] (Optional) ArgoCD installed and application synced

---

**Need Help?**
- Check GitHub Actions logs for detailed error messages
- Review this guide for missed steps
- Check DockerHub to verify images are being pushed correctly
