# ArgoCD Setup for Restaurant Management System

## Prerequisites

1. **ArgoCD installed on your Kubernetes cluster**
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

2. **Access ArgoCD UI**
   ```bash
   # Port-forward to access UI
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   
   # Get initial admin password
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

## Deploy Application

### Method 1: Using kubectl

```bash
# Update the repoURL in application.yaml with your GitHub repository
# Then apply:
kubectl apply -f infrastructure/argocd/application.yaml
```

### Method 2: Using ArgoCD CLI

```bash
# Install ArgoCD CLI
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login
argocd login localhost:8080

# Create application
argocd app create restaurant-system \
  --repo https://github.com/YOUR_USERNAME/Restaurant_management.git \
  --path infrastructure/kubernetes \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace restaurant-system \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### Method 3: Using ArgoCD UI

1. Open ArgoCD UI at http://localhost:8080
2. Click "+ NEW APP"
3. Fill in:
   - **Application Name**: restaurant-system
   - **Project**: default
   - **Sync Policy**: Automatic
   - **Repository URL**: your GitHub repo URL
   - **Path**: infrastructure/kubernetes
   - **Cluster**: in-cluster
   - **Namespace**: restaurant-system
4. Click "CREATE"

## Verify Deployment

```bash
# Check ArgoCD application status
argocd app get restaurant-system

# Or using kubectl
kubectl get application -n argocd restaurant-system

# Check deployed resources
kubectl get all -n restaurant-system
```

## Sync Application

```bash
# Manual sync
argocd app sync restaurant-system

# View sync status
argocd app wait restaurant-system
```

## Troubleshooting

### Application not syncing
```bash
# Check application status
argocd app get restaurant-system

# View logs
kubectl logs -n argocd deployment/argocd-application-controller
```

### Authentication issues
```bash
# Reset admin password
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData": {"admin.password": "$2a$10$rRyBsGSHK6.uc8fntPwVIuLVHgsAhAX7TcdrqW/RADU0uh7CaChLa"}}' 
# Password: admin
```

## GitHub Actions Integration

The CI/CD pipeline (`
.github/workflows/ci-cd.yml`) automatically:
1. Builds Docker images
2. Pushes to Docker Hub
3. Updates image tags in Kubernetes manifests (for ArgoCD to detect)
4. Optionally triggers ArgoCD sync via API

### Required GitHub Secrets

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `ARGOCD_SERVER`: ArgoCD server URL (optional)
- `ARGOCD_AUTH_TOKEN`: ArgoCD API token (optional)

To get ArgoCD token:
```bash
argocd account generate-token --account admin
```
