# ArgoCD Installation Guide for Restaurant Management System

This guide will walk you through installing and configuring ArgoCD for GitOps deployment.

---

## Prerequisites Check

Before starting, ensure you have:
- ✅ KIND cluster running (`restaurant-cluster`)
- ✅ kubectl installed and configured
- ✅ Helm installed

### Verify Prerequisites:
```bash
# Check KIND cluster
kind get clusters
# Should show: restaurant-cluster

# Check kubectl
kubectl cluster-info --context kind-restaurant-cluster

# Check Helm
helm version
```

---

## Step 1: Install ArgoCD

### 1.1 Create ArgoCD Namespace
```bash
kubectl create namespace argocd --context kind-restaurant-cluster
```

### 1.2 Install ArgoCD
```bash
# Install ArgoCD using official manifest
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --context kind-restaurant-cluster
```

### 1.3 Wait for ArgoCD to be Ready
```bash
# This may take 2-5 minutes
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s --context kind-restaurant-cluster
```

### 1.4 Verify Installation
```bash
# Check all ArgoCD pods are running
kubectl get pods -n argocd --context kind-restaurant-cluster

# Expected output (all should be Running):
# NAME                                  READY   STATUS
# argocd-application-controller-x       1/1     Running
# argocd-dex-server-x                   1/1     Running
# argocd-redis-x                        1/1     Running
# argocd-repo-server-x                  1/1     Running
# argocd-server-x                       1/1     Running
```

---

## Step 2: Access ArgoCD UI

### 2.1 Get Initial Admin Password
```bash
# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" --context kind-restaurant-cluster | base64 -d && echo
```

**Save this password!** You'll need it to login.

### 2.2 Port Forward ArgoCD Server
```bash
# Forward ArgoCD server to localhost:8080
kubectl port-forward svc/argocd-server -n argocd 8080:443 --context kind-restaurant-cluster
```

### 2.3 Access ArgoCD UI
1. Open browser: **https://localhost:8080**
2. Accept the self-signed certificate warning
3. Login credentials:
   - **Username**: `admin`
   - **Password**: (from Step 2.1)

---

## Step 3: Install ArgoCD CLI (Optional but Recommended)

### 3.1 Download ArgoCD CLI

**Linux:**
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

**macOS:**
```bash
brew install argocd
```

### 3.2 Login via CLI
```bash
# Port forward must be running in another terminal
argocd login localhost:8080 --username admin --password <password-from-step-2.1> --insecure
```

### 3.3 Change Admin Password (Recommended)
```bash
argocd account update-password --current-password <old-password> --new-password <new-password>
```

---

## Step 4: Configure Git Repository

### 4.1 Update ArgoCD Application Manifest

**IMPORTANT**: Before applying the ArgoCD application, update your GitHub repository URL.

Edit: `argocd/application.yaml`

**Line 10** - Replace with your actual repository:
```yaml
repoURL: https://github.com/YOUR_GITHUB_USERNAME/Restaurant_management.git
```

For example, if your GitHub username is `johndoe`:
```yaml
repoURL: https://github.com/johndoe/Restaurant_management.git
```

### 4.2 Commit the Change
```bash
git add argocd/application.yaml
git commit -m "Update ArgoCD repository URL"
git push origin main
```

---

## Step 5: Deploy Application via ArgoCD

### 5.1 Apply ArgoCD Application
```bash
kubectl apply -f argocd/application.yaml -n argocd --context kind-restaurant-cluster
```

### 5.2 Check Application Status

**Via CLI:**
```bash
argocd app get restaurant-system
```

**Via UI:**
1. Go to https://localhost:8080
2. You should see "restaurant-system" application
3. Click on it to see the deployment details

### 5.3 Sync Application (if not auto-synced)
```bash
# Manual sync
argocd app sync restaurant-system

# Or via kubectl
kubectl patch application restaurant-system -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"syncStrategy":{"hook":{}}}}}' --context kind-restaurant-cluster
```

### 5.4 Monitor Deployment
```bash
# Watch application sync status
argocd app get restaurant-system --watch

# Or watch pods being created
kubectl get pods -n restaurant-system -w --context kind-restaurant-cluster
```

---

## Step 6: Verify Deployment

### 6.1 Check All Resources
```bash
# Check application in ArgoCD
argocd app list

# Check all pods in restaurant-system namespace
kubectl get all -n restaurant-system --context kind-restaurant-cluster

# Check Helm releases
helm list -n restaurant-system
```

### 6.2 Access the Application

**Frontend:**
```bash
kubectl port-forward svc/frontend 3000:3000 -n restaurant-system --context kind-restaurant-cluster
# Open: http://localhost:3000
```

**API Gateway:**
```bash
kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system --context kind-restaurant-cluster
# Test: curl http://localhost:8000/health
```

---

## Step 7: ArgoCD Configuration for CI/CD

For the GitHub Actions pipeline to trigger ArgoCD syncs, you need to add secrets.

### 7.1 Generate ArgoCD Auth Token
```bash
argocd account generate-token --account admin
```

### 7.2 Add GitHub Secrets

Go to: `GitHub Repository → Settings → Secrets and variables → Actions`

Add these secrets:

| Name | Value |
|------|-------|
| `ARGOCD_SERVER` | `https://your-argocd-server.com` or for local: `https://localhost:8080` |
| `ARGOCD_AUTH_TOKEN` | Token from Step 7.1 |

**Note:** For production, use your actual ArgoCD server URL. For local KIND cluster, the CI/CD pipeline won't be able to reach `localhost:8080`, so this is mainly for production setups.

---

## Common ArgoCD Commands

### Application Management
```bash
# List all applications
argocd app list

# Get application details
argocd app get restaurant-system

# Sync application
argocd app sync restaurant-system

# Delete application
argocd app delete restaurant-system

# Refresh application (check for changes)
argocd app refresh restaurant-system
```

### Application Logs
```bash
# View application logs
argocd app logs restaurant-system

# View logs for specific resource
argocd app logs restaurant-system --kind Deployment --name api-gateway
```

### Repository Management
```bash
# List repositories
argocd repo list

# Add private repository (if needed)
argocd repo add https://github.com/YOUR_USERNAME/Restaurant_management.git --username YOUR_USERNAME --password YOUR_TOKEN
```

---

## Troubleshooting

### Issue 1: ArgoCD Pods Not Starting

**Check pod status:**
```bash
kubectl get pods -n argocd --context kind-restaurant-cluster
kubectl describe pod <pod-name> -n argocd --context kind-restaurant-cluster
```

**Common fix:** Wait longer (ArgoCD images are large)

### Issue 2: Application Stuck in "Unknown" State

**Cause:** Repository not accessible or invalid manifest

**Fix:**
```bash
# Check application details
argocd app get restaurant-system

# Refresh repository
argocd app refresh restaurant-system

# Check if repository is accessible
argocd repo list
```

### Issue 3: Application Sync Failed

**Check sync status:**
```bash
argocd app get restaurant-system

# View detailed sync logs
argocd app logs restaurant-system --follow
```

**Common issues:**
- Helm values syntax error
- Repository URL incorrect
- Image pull errors (check DockerHub credentials)

### Issue 4: Cannot Access ArgoCD UI

**Verify port-forward is running:**
```bash
# Kill existing port-forward
pkill -f "port-forward.*argocd-server"

# Start new port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443 --context kind-restaurant-cluster
```

### Issue 5: "Unhealthy" Resources

**Check resource health:**
```bash
kubectl get pods -n restaurant-system --context kind-restaurant-cluster
kubectl describe pod <unhealthy-pod> -n restaurant-system --context kind-restaurant-cluster
```

**Common fixes:**
- Update image tags to valid versions
- Check database connectivity
- Verify secrets and configmaps

---

## Uninstall ArgoCD

If you need to remove ArgoCD:

```bash
# Delete the application first
kubectl delete -f argocd/application.yaml -n argocd --context kind-restaurant-cluster

# Delete ArgoCD installation
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --context kind-restaurant-cluster

# Delete namespace
kubectl delete namespace argocd --context kind-restaurant-cluster
```

---

## Production Considerations

For production ArgoCD deployment:

1. **Use persistent volumes** for ArgoCD data
2. **Set up ingress** instead of port-forward
3. **Configure RBAC** for team access
4. **Enable SSO** (Google, GitHub, LDAP)
5. **Set up monitoring** (Prometheus, Grafana)
6. **Configure notifications** (Slack, email)
7. **Use app of apps pattern** for multiple applications
8. **Implement GitOps best practices** (separate repos for config)

---

## Next Steps

After ArgoCD is installed and configured:

1. ✅ Application auto-syncs on Git push to main
2. ✅ Monitor deployments in ArgoCD UI
3. ✅ Use GitOps workflow for all changes
4. ✅ Configure GitHub Actions to trigger ArgoCD sync
5. ✅ Set up notifications for deployment status

---

## Quick Reference

```bash
# ArgoCD UI
https://localhost:8080

# Login
Username: admin
Password: (from argocd-initial-admin-secret)

# Port forward ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443 --context kind-restaurant-cluster

# Port forward Application
kubectl port-forward svc/frontend 3000:3000 -n restaurant-system --context kind-restaurant-cluster
kubectl port-forward svc/api-gateway 8000:8000 -n restaurant-system --context kind-restaurant-cluster

# Sync application
argocd app sync restaurant-system

# Check status
argocd app get restaurant-system
```

---

**Ready to install? Follow the steps above in order!**
