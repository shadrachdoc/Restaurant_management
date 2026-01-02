# Production Configuration Checklist

**Before deploying to production laptop, you MUST configure these items:**

---

## 1. Production Domain Name

**Decision needed**: What subdomain will you use for production?

**Options**:
- `prod.corpv3.com` (recommended)
- `restaurant-prod.corpv3.com`
- `production.corpv3.com`
- Your choice: `_________________.corpv3.com`

**Files to update once decided**:
- [ ] `helm/restaurant-system/values-prod.yaml` - Lines 246, 253
- [ ] `scripts/deploy-production.sh` - Line 16
- [ ] `scripts/setup-production-laptop.sh` - Line 16

**DNS Setup**:
- [ ] Add A record in DNS provider: `<your-domain>` → `<production-laptop-ip>`
- OR add to `/etc/hosts` for testing: `<prod-laptop-ip> <your-domain>`

---

## 2. Docker Registry Configuration 

**Current**: Using Docker Hub with username `shadrach001`

**Decision needed**: Keep this or change?

**Option A - Keep current (shadrach001)**:
✅ No changes needed - scripts already configured

**Option B - Change Docker Hub username**:
Update these in `helm/restaurant-system/values-prod.yaml`:
- [ ] Line 21: `repository: YOUR_USERNAME/restaurant_management_api-gateway`
- [ ] Line 51: `repository: YOUR_USERNAME/restaurant_management_auth-service`
- [ ] Line 79: `repository: YOUR_USERNAME/restaurant_management_restaurant-service`
- [ ] Line 106: `repository: YOUR_USERNAME/restaurant_management_order-service`
- [ ] Line 135: `repository: YOUR_USERNAME/restaurant_management_customer-service`
- [ ] Line 161: `repository: YOUR_USERNAME/restaurant-frontend`
- [ ] `scripts/deploy-production.sh` - Line 19: `DOCKER_REGISTRY="YOUR_USERNAME"`

---

## 3. Production Secrets (CRITICAL!)

**NEVER use dev secrets in production!**

### Generate Secrets:

```bash
# Generate JWT secret (32 bytes hex)
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT Secret: $JWT_SECRET"

# Generate session secret
SESSION_SECRET=$(openssl rand -hex 32)
echo "Session Secret: $SESSION_SECRET"

# Generate PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 24)
echo "PostgreSQL Password: $POSTGRES_PASSWORD"

# Generate RabbitMQ password
RABBITMQ_PASSWORD=$(openssl rand -base64 24)
echo "RabbitMQ Password: $RABBITMQ_PASSWORD"

# SAVE THESE SOMEWHERE SECURE!
# Create a secure file
cat > ~/prod-secrets-$(date +%Y%m%d).txt <<EOF
Production Secrets - Generated $(date)
====================================
JWT Secret: $JWT_SECRET
Session Secret: $SESSION_SECRET
PostgreSQL Password: $POSTGRES_PASSWORD
RabbitMQ Password: $RABBITMQ_PASSWORD
====================================
KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT
EOF
chmod 600 ~/prod-secrets-$(date +%Y%m%d).txt
```

### Update Configuration Files:

Edit `helm/restaurant-system/values-prod.yaml`:

- [ ] Line 204: Replace `REPLACE_WITH_SECURE_PASSWORD` with PostgreSQL password
- [ ] Line 224: Replace `REPLACE_WITH_SECURE_PASSWORD` with RabbitMQ password
- [ ] Line 287: Replace `REPLACE_WITH_PRODUCTION_SECRET` with JWT secret
- [ ] Line 288: Replace `REPLACE_WITH_PRODUCTION_SECRET` with session secret
- [ ] Line 289: Replace `REPLACE_WITH_PRODUCTION_SECRET` with PostgreSQL password

### Create Kubernetes Secrets:

**On production laptop**, after running setup script:

```bash
# JWT Secret
kubectl create secret generic jwt-secret \
  --from-literal=secret-key="<YOUR_JWT_SECRET>" \
  -n restaurant-prod

# Database passwords
kubectl create secret generic db-passwords \
  --from-literal=auth-db-password="<YOUR_POSTGRES_PASSWORD>" \
  --from-literal=restaurant-db-password="<YOUR_POSTGRES_PASSWORD>" \
  -n restaurant-prod
```

---

## 4. Resource Limits (Optional - Adjust Based on Laptop)

**Current production settings** in `values-prod.yaml`:
```yaml
resources:
  limits:
    cpu: 1000m      # 1 CPU core
    memory: 1Gi     # 1GB RAM
  requests:
    cpu: 500m
    memory: 512Mi
```

**When to adjust**:
- Laptop has 16GB+ RAM and 8+ cores → Increase limits to 2000m CPU / 2Gi RAM
- Laptop has 8GB RAM or 4 cores → Decrease to 500m CPU / 512Mi RAM
- Start with default, monitor with Grafana, adjust as needed

**Files to update** (if needed):
- [ ] `helm/restaurant-system/values-prod.yaml` - Lines 32-37, 62-67, 90-95, etc.

---

## 5. Replica Counts (Optional)

**Current**: 2 replicas per service for high availability

**When to adjust**:
- Limited laptop resources → Set to 1 replica
- More powerful laptop → Keep at 2-3 replicas
- Autoscaling is enabled, will scale automatically

**Files to update** (if needed):
- [ ] `helm/restaurant-system/values-prod.yaml` - Lines 19, 49, 77, etc. (all `replicaCount:`)

---

## 6. Storage Sizes (Optional)

**Current production settings**:
- PostgreSQL: 50GB
- RabbitMQ: 20GB
- Redis: 20GB

**When to adjust**:
- Check available disk space: `df -h`
- Ensure enough space for all storage + OS
- Can start smaller and expand later

**Files to update** (if needed):
- [ ] `helm/restaurant-system/values-prod.yaml` - Lines 195, 221, 245

---

## Configuration Summary

### Minimal Configuration (Required):

1. ✅ **Production domain** - Choose and update in 3 files
2. ✅ **Production secrets** - Generate and update in values-prod.yaml
3. ✅ **Kubernetes secrets** - Create on production laptop after setup

### Optional Configuration:

4. **Docker registry** - Change only if not using shadrach001
5. **Resource limits** - Adjust based on laptop hardware
6. **Replica counts** - Adjust for resource constraints
7. **Storage sizes** - Adjust based on available disk space

---

## Quick Start Commands

After configuring above:

### On Production Laptop:

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Restaurant_management

# 2. Run setup script
./scripts/setup-production-laptop.sh

# 3. Create secrets (prompted during setup)
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  -n restaurant-prod

kubectl create secret generic db-passwords \
  --from-literal=auth-db-password=$(openssl rand -base64 24) \
  --from-literal=restaurant-db-password=$(openssl rand -base64 24) \
  -n restaurant-prod

# 4. Configure DNS (shown by setup script)

# 5. Deploy first release (from dev laptop after building images)
./scripts/deploy-production.sh v1.0.0
```

### On Dev Laptop (Prepare Release):

```bash
# 1. Tag release
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0

# 2. Build and push images
VERSION=v1.0.0

# Frontend
docker build -t shadrach001/restaurant-frontend:$VERSION -f frontend/Dockerfile .
docker push shadrach001/restaurant-frontend:$VERSION

# API Gateway
docker build -t shadrach001/restaurant_management_api-gateway:$VERSION \
  -f services/api-gateway/Dockerfile .
docker push shadrach001/restaurant_management_api-gateway:$VERSION

# Auth Service
docker build -t shadrach001/restaurant_management_auth-service:$VERSION \
  -f services/auth-service/Dockerfile .
docker push shadrach001/restaurant_management_auth-service:$VERSION

# Restaurant Service
docker build -t shadrach001/restaurant_management_restaurant-service:$VERSION \
  -f services/restaurant-service/Dockerfile .
docker push shadrach001/restaurant_management_restaurant-service:$VERSION

# (Repeat for other services if enabled)
```

---

## Verification

After setup and first deployment:

```bash
# Check cluster
kubectl get nodes

# Check pods
kubectl get pods -n restaurant-prod

# Check services
kubectl get svc -n restaurant-prod

# Check ingress
kubectl get ingress -n restaurant-prod

# Access application
curl https://<your-domain>
# Or open in browser
```

---

## Need Help?

See detailed guides:
- **[PRODUCTION_LAPTOP_SETUP.md](PRODUCTION_LAPTOP_SETUP.md)** - Step-by-step setup guide
- **[RELEASE_MANAGEMENT_PLAN.md](RELEASE_MANAGEMENT_PLAN.md)** - Complete release strategy
- **[scripts/README.md](scripts/README.md)** - Script usage and troubleshooting
