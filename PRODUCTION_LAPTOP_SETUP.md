# Production Laptop Setup Guide

This guide explains exactly what you need to configure on your production laptop to run the Restaurant Management System in production.

## Overview

Your production laptop will run:
- **Kind cluster** (Kubernetes in Docker)
- **Istio service mesh**
- **Restaurant application** (all microservices)
- **PostgreSQL, Redis, RabbitMQ** (databases and message queue)
- **Prometheus + Grafana** (monitoring)
- **Nginx Ingress** (routing)

---

## What You Need to Configure

### 1. Production Domain (Using Cloudflare Tunnel)

**What**: A subdomain that points to your production laptop via Cloudflare Tunnel

**Options**:
```
prod.corpv3.com           (Recommended)
restaurant-prod.corpv3.com
production.corpv3.com
```

**Where to configure**:
- In `scripts/deploy-production.sh` - Line 16
- In `scripts/setup-production-laptop.sh` - Line 16
- In `helm/restaurant-system/values-prod.yaml` - Lines 246, 253

**Important - Cloudflare Tunnel (NO IP Address Needed!)**:

Since you're using Cloudflare Tunnel, you **DON'T need**:
- ❌ Production laptop's IP address
- ❌ Port forwarding
- ❌ Open firewall ports
- ❌ Static IP or DDNS

**You will have TWO separate tunnels**:

| Environment | Laptop | Tunnel Name | Domain | Purpose |
|-------------|--------|-------------|--------|---------|
| **Development** | Current laptop | `restaurant-dev` | `restaurant.corpv3.com` | Testing & development |
| **Production** | New Ubuntu laptop | `restaurant-prod` | `prod.corpv3.com` | Live production system |

Each laptop runs its own Cloudflare tunnel. See **Cloudflare Tunnel Setup** section below for complete instructions.

---

### 2. Docker Registry Configuration

**What**: Where your Docker images are stored

**Current setup**: Docker Hub (`shadrach001`)

**Where to configure**:
- In `scripts/deploy-production.sh` - Line 19
- In `helm/restaurant-system/values-prod.yaml` - Lines 21, 51, 79, etc. (all image repositories)

**Options**:
1. **Use Docker Hub** (easiest):
   ```yaml
   repository: shadrach001/restaurant-frontend
   ```

2. **Change Docker Hub username**:
   ```yaml
   repository: YOUR_DOCKERHUB_USERNAME/restaurant-frontend
   ```

3. **Use private registry** (advanced):
   ```yaml
   repository: registry.yourcompany.com/restaurant-frontend
   ```

---

### 3. Production Secrets

**What**: Secure passwords and keys for production (MUST be different from dev!)

**Critical**: NEVER use the same secrets in dev and prod!

**Secrets to create**:

#### a) JWT Secret Key
```bash
# Generate a random JWT secret
openssl rand -hex 32

# Create the secret in Kubernetes
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  -n restaurant-prod
```

#### b) Database Passwords
```bash
# Generate secure passwords
AUTH_DB_PASS=$(openssl rand -base64 24)
RESTAURANT_DB_PASS=$(openssl rand -base64 24)

# Create the secrets
kubectl create secret generic db-passwords \
  --from-literal=auth-db-password="$AUTH_DB_PASS" \
  --from-literal=restaurant-db-password="$RESTAURANT_DB_PASS" \
  -n restaurant-prod

# Save these passwords somewhere secure!
echo "Auth DB Password: $AUTH_DB_PASS" >> ~/prod-secrets.txt
echo "Restaurant DB Password: $RESTAURANT_DB_PASS" >> ~/prod-secrets.txt
chmod 600 ~/prod-secrets.txt
```

#### c) Update values-prod.yaml
Before first deployment, edit `helm/restaurant-system/values-prod.yaml`:
```yaml
# Line 204: PostgreSQL password
postgresql:
  auth:
    password: "YOUR_SECURE_PASSWORD_HERE"

# Line 224: RabbitMQ password
rabbitmq:
  auth:
    password: "YOUR_SECURE_PASSWORD_HERE"

# Lines 287-289: Application secrets
secrets:
  jwtSecretKey: "YOUR_JWT_SECRET_HERE"
  sessionSecret: "YOUR_SESSION_SECRET_HERE"
  postgresPassword: "YOUR_POSTGRES_PASSWORD_HERE"
```

---

### 4. Resource Limits

**What**: CPU and memory limits for each service

**Current production settings** in `values-prod.yaml`:
```yaml
# Each service (api-gateway, auth-service, etc.):
resources:
  limits:
    cpu: 1000m      # 1 CPU core
    memory: 1Gi     # 1GB RAM
  requests:
    cpu: 500m       # 0.5 CPU core baseline
    memory: 512Mi   # 512MB RAM baseline
```

**When to adjust**:
- If production laptop is more powerful, increase limits
- If laptop struggles, decrease limits
- Monitor with Grafana and adjust based on actual usage

**Where to configure**: `helm/restaurant-system/values-prod.yaml`

**Example adjustments**:
```yaml
# For a powerful laptop (16GB RAM, 8 CPU):
resources:
  limits:
    cpu: 2000m      # 2 CPU cores
    memory: 2Gi     # 2GB RAM

# For a modest laptop (8GB RAM, 4 CPU):
resources:
  limits:
    cpu: 500m       # 0.5 CPU cores
    memory: 512Mi   # 512MB RAM
```

---

### 5. Replica Counts

**What**: Number of pods running for each service

**Current production settings**:
```yaml
replicaCount: 2  # 2 pods per service
```

**When to adjust**:
- Start with 1 replica if laptop has limited resources
- Increase to 2-3 for high availability
- Autoscaling is enabled (will scale automatically based on load)

**Where to configure**: `helm/restaurant-system/values-prod.yaml`

---

### 6. Storage Sizes

**What**: Disk space for databases

**Current production settings**:
```yaml
postgresql:
  persistence:
    size: 50Gi      # 50GB for PostgreSQL

rabbitmq:
  persistence:
    size: 20Gi      # 20GB for RabbitMQ

redis:
  persistence:
    size: 20Gi      # 20GB for Redis
```

**When to adjust**:
- Based on available disk space on production laptop
- Monitor actual usage and adjust over time

---

## Step-by-Step Setup Process

### Step 1: Prepare Production Laptop

1. **Install Ubuntu** (if not already installed)
   - Recommended: Ubuntu 22.04 LTS or later

2. **Install Docker**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo usermod -aG docker $USER
   # Log out and log back in for group changes to take effect
   ```

3. **Verify Docker works**:
   ```bash
   docker run hello-world
   ```

---

### Step 2: Transfer Files to Production Laptop

**Option A: Using Git (Recommended)**:
```bash
# On production laptop
git clone https://github.com/YOUR_USERNAME/Restaurant_management.git
cd Restaurant_management
git checkout main  # Or your production branch
```

**Option B: Using SCP**:
```bash
# From dev laptop
scp -r ~/Restaurant_management production-user@production-laptop-ip:~/
```

**Option C: Using USB Drive**:
1. Copy entire `Restaurant_management` folder to USB
2. Copy from USB to production laptop

---

### Step 3: Configure Production Settings

1. **Update production domain** in these files:
   - `scripts/deploy-production.sh` (Line 16)
   - `scripts/setup-production-laptop.sh` (Line 16)
   - `helm/restaurant-system/values-prod.yaml` (Lines 246, 253)

2. **Update Docker registry** (if needed):
   - `helm/restaurant-system/values-prod.yaml` (all `repository:` lines)

3. **Generate and configure secrets**:
   ```bash
   # Edit values-prod.yaml and replace all REPLACE_WITH_* placeholders
   nano helm/restaurant-system/values-prod.yaml
   ```

4. **Adjust resource limits** (if needed):
   - Edit `helm/restaurant-system/values-prod.yaml`
   - Adjust CPU/memory based on your laptop specs

---

### Step 4: Run Setup Script

```bash
cd ~/Restaurant_management

# Make scripts executable
chmod +x scripts/*.sh

# Run setup script
./scripts/setup-production-laptop.sh
```

**What this script does**:
1. Checks/installs prerequisites (kubectl, kind, Helm, istioctl)
2. Creates kind cluster named `restaurant-prod-cluster`
3. Installs Istio service mesh
4. Creates namespace `restaurant-prod`
5. Installs Nginx Ingress Controller
6. Sets up Prometheus + Grafana monitoring
7. Guides you through creating secrets
8. Shows DNS configuration instructions

**Time required**: 10-15 minutes

---

### Step 5: Create Production Secrets

During setup script, you'll be prompted to create secrets:

```bash
# JWT Secret
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  -n restaurant-prod

# Database passwords
kubectl create secret generic db-passwords \
  --from-literal=auth-db-password=$(openssl rand -base64 24) \
  --from-literal=restaurant-db-password=$(openssl rand -base64 24) \
  -n restaurant-prod
```

**Important**: Save these secrets somewhere safe! You'll need them if you ever need to recreate the cluster.

---

### Step 6: Configure DNS

**Get production laptop IP**:
```bash
hostname -I | awk '{print $1}'
```

**Option A: Update DNS records (if you control the domain)**:
- Log into your DNS provider
- Add A record: `prod.corpv3.com` → `<production-laptop-ip>`
- Wait for DNS propagation (5-60 minutes)

**Option B: Use /etc/hosts for testing**:
```bash
# On any machine you want to access from
echo "<production-laptop-ip>  prod.corpv3.com" | sudo tee -a /etc/hosts
```

**Verify DNS**:
```bash
# From another machine
ping prod.corpv3.com
```

---

### Step 7: First Production Deployment

**On dev laptop**, prepare release:
```bash
# Tag release
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0

# Build and push images (see scripts/README.md for complete commands)
VERSION=v1.0.0

docker build -t shadrach001/restaurant-frontend:$VERSION -f frontend/Dockerfile .
docker push shadrach001/restaurant-frontend:$VERSION

# ... repeat for all services ...
```

**On production laptop**, deploy:
```bash
cd ~/Restaurant_management

# Pull latest code (if using git)
git pull origin main
git fetch --tags

# Deploy
./scripts/deploy-production.sh v1.0.0
```

**Verify deployment**:
```bash
# Check pods
kubectl get pods -n restaurant-prod

# Access application
curl https://prod.corpv3.com
# Or open in browser: https://prod.corpv3.com
```

---

## Configuration Summary Checklist

Before first deployment, ensure you've configured:

- [ ] Production domain name
- [ ] Docker registry (Docker Hub username or private registry)
- [ ] JWT secret key (generated with `openssl rand -hex 32`)
- [ ] Database passwords (generated with `openssl rand -base64 24`)
- [ ] Resource limits (CPU/memory for each service)
- [ ] Storage sizes (disk space for databases)
- [ ] Replica counts (number of pods per service)
- [ ] DNS configuration (A record or /etc/hosts)
- [ ] All secrets created in Kubernetes
- [ ] All `REPLACE_WITH_*` placeholders updated in values-prod.yaml

---

## Post-Setup Configuration

### Accessing Monitoring

**Grafana** (metrics dashboards):
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open: http://localhost:3000
# Login: admin / admin (change password on first login)
```

**Prometheus** (metrics database):
```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090
```

### Viewing Logs

```bash
# All logs for a service
kubectl logs -n restaurant-prod -l app=frontend -f

# Specific pod
kubectl logs -n restaurant-prod <pod-name> -f

# Last 100 lines
kubectl logs -n restaurant-prod <pod-name> --tail=100
```

### Scaling Services

```bash
# Manual scaling
kubectl scale deployment/frontend --replicas=3 -n restaurant-prod

# Check autoscaling status
kubectl get hpa -n restaurant-prod
```

---

## Security Best Practices

1. **Never commit secrets to git**
   - Keep `values-prod.yaml` with real secrets outside git
   - Or use git-crypt/sops to encrypt secrets

2. **Use strong passwords**
   - At least 24 characters for database passwords
   - Use cryptographically random generation

3. **Regular updates**
   - Keep base images updated
   - Update Kubernetes/Istio regularly
   - Apply security patches

4. **Backup databases**
   - Schedule regular backups
   - Test restore procedure
   - Store backups securely

5. **Monitor access**
   - Review who can access production cluster
   - Use separate kubeconfig for production
   - Audit deployment history

---

## Troubleshooting

### Issue: Setup script fails at "kind not found"

**Solution**:
```bash
# Install kind manually
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Issue: Deployment fails with "insufficient resources"

**Solution**: Reduce resource limits in `values-prod.yaml`:
```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
```

### Issue: Pods stuck in "Pending" state

**Check**:
```bash
kubectl describe pod <pod-name> -n restaurant-prod
# Look for "Insufficient memory" or "Insufficient cpu"
```

**Solution**: Reduce replica counts or resource requests

### Issue: Can't access application from browser

**Check**:
1. DNS is configured correctly
2. Ingress is running: `kubectl get pods -n ingress-nginx`
3. Services are running: `kubectl get svc -n restaurant-prod`
4. Firewall allows ports 80/443

---

## Next Steps

After setup:
1. Test all application features
2. Set up backup procedures
3. Configure monitoring alerts
4. Document any custom configurations
5. Create disaster recovery plan

For regular deployments, see: [scripts/README.md](scripts/README.md)
