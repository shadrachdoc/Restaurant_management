# ArgoCD Access Information

## ArgoCD Installation Status
✅ **ArgoCD is now installed in your KIND cluster!**

---

## Access Credentials

### ArgoCD UI Login
- **URL**: https://localhost:8080 (after port-forward)
- **Username**: `admin`
- **Password**: `myq45CaeIZQNPgkA`

⚠️ **IMPORTANT**: Save this password securely. Change it after first login!

---

## How to Access ArgoCD UI

### Step 1: Start Port Forward
Open a terminal and run:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Keep this terminal open while using ArgoCD.

### Step 2: Access UI
1. Open your browser
2. Go to: **https://localhost:8080**
3. Accept the self-signed certificate warning (click "Advanced" → "Proceed")
4. Login with credentials above

---

## Check ArgoCD Pod Status

```bash
# Check if all pods are running
kubectl get pods -n argocd

# Wait for all pods to be ready (may take 2-5 minutes)
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
```

---

## Next Steps

### 1. Update GitHub Repository URL
Before deploying your application, update the ArgoCD application manifest:

**Edit file**: `argocd/application.yaml`

**Line 10** - Replace with your actual GitHub repository URL:
```yaml
repoURL: https://github.com/YOUR_GITHUB_USERNAME/Restaurant_management.git
```

For example:
```yaml
repoURL: https://github.com/shadrach/Restaurant_management.git
```

### 2. Commit and Push
```bash
git add argocd/application.yaml
git commit -m "Update ArgoCD repository URL"
git push origin main
```

### 3. Deploy Application
After updating the repository URL, apply the ArgoCD application:
```bash
kubectl apply -f argocd/application.yaml -n argocd
```

### 4. Monitor Deployment
Via UI:
- Go to https://localhost:8080
- You'll see "restaurant-system" application
- Click on it to see deployment progress

Via CLI:
```bash
# Watch application status
kubectl get applications -n argocd -w

# Check application details
kubectl describe application restaurant-system -n argocd
```

---

## Change Admin Password (Recommended)

### Option 1: Via ArgoCD CLI
```bash
# Install ArgoCD CLI first (Linux)
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

# Login
argocd login localhost:8080 --username admin --password myq45CaeIZQNPgkA --insecure

# Change password
argocd account update-password
```

### Option 2: Via UI
1. Login to ArgoCD UI
2. Click on "User Info" (top right)
3. Click "Update Password"
4. Enter current and new password

---

## Useful Commands

```bash
# Check ArgoCD server status
kubectl get svc argocd-server -n argocd

# Get all ArgoCD applications
kubectl get applications -n argocd

# View ArgoCD logs
kubectl logs -n argocd deployment/argocd-server

# Restart ArgoCD server
kubectl rollout restart deployment/argocd-server -n argocd

# Delete an application
kubectl delete application restaurant-system -n argocd

# Uninstall ArgoCD completely
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd
```

---

## Troubleshooting

### Can't access ArgoCD UI
1. Ensure port-forward is running
2. Try different port: `kubectl port-forward svc/argocd-server -n argocd 8081:443`
3. Access: https://localhost:8081

### Pods not starting
```bash
# Check pod status
kubectl get pods -n argocd

# Describe problematic pod
kubectl describe pod <pod-name> -n argocd

# Check logs
kubectl logs <pod-name> -n argocd
```

### Application not syncing
1. Check repository URL is correct
2. Ensure GitHub repository is accessible (public or correct credentials)
3. Check application details: `kubectl describe application restaurant-system -n argocd`

---

## For More Details

See the complete guides:
- [ARGOCD_INSTALLATION.md](ARGOCD_INSTALLATION.md) - Full installation guide
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete CI/CD setup
- [QUICK_START_CICD.md](QUICK_START_CICD.md) - Quick start guide

---

**Installation Date**: 2025-12-14
**Cluster**: kind-restaurant-cluster
**Namespace**: argocd
