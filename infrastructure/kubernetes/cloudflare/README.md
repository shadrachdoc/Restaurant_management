# Cloudflare Tunnel Setup for Kubernetes

This guide explains how to expose your Restaurant Management System publicly using Cloudflare Tunnel.

## What is Cloudflare Tunnel?

Cloudflare Tunnel creates a secure outbound connection from your Kubernetes cluster to Cloudflare's edge network, allowing you to expose services publicly without:
- Opening firewall ports
- Exposing your server's IP address
- Dealing with port forwarding or NAT traversal

## Prerequisites

1. **Cloudflare Account** (free tier works)
2. **Domain registered with Cloudflare** (or transferred to Cloudflare)
3. **Cloudflare Tunnel created** in your Cloudflare dashboard

## Setup Steps

### Step 1: Create Tunnel in Cloudflare Dashboard

1. Login to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Go to **Access → Tunnels**
3. Click **Create a tunnel**
4. Choose **Cloudflared** connector type
5. Name your tunnel (e.g., `restaurant-k8s`)
6. Copy the tunnel token (you already have one!)

### Step 2: Configure Public Hostname Routes

In Cloudflare Dashboard, configure routes for your tunnel:

#### Route 1: Frontend Application
- **Public hostname**: `restaurant.yourdomain.com`
- **Service**: `http://frontend.restaurant-system.svc.cluster.local:80`
- **Additional settings**: 
  - Enable **TLS verification** (optional)
  - Enable **No TLS Verify** for internal services

#### Route 2: API Gateway
- **Public hostname**: `api.yourdomain.com`
- **Service**: `http://api-gateway.restaurant-system.svc.cluster.local:8000`

#### Route 3: ArgoCD (Optional)
- **Public hostname**: `argocd.yourdomain.com`
- **Service**: `https://argocd-server.argocd.svc.cluster.local:443`
- **Additional settings**:
  - Enable **No TLS Verify** (ArgoCD uses self-signed cert)

### Step 3: Deploy to Kubernetes

```bash
# Apply Cloudflare secret and deployment
kubectl apply -f infrastructure/kubernetes/cloudflare/secret.yaml
kubectl apply -f infrastructure/kubernetes/cloudflare/deployment.yaml

# Verify deployment
kubectl get pods -n restaurant-system -l app=cloudflared
kubectl logs -n restaurant-system -l app=cloudflared
```

### Step 4: Verify Connection

```bash
# Check tunnel status in Cloudflare Dashboard
# You should see "Healthy" status

# Test your public URLs
curl https://restaurant.yourdomain.com
curl https://api.yourdomain.com/health
```

## Configuration Files

### 1. secret.yaml
Contains your Cloudflare Tunnel token (keep this secure!)

### 2. deployment.yaml
Runs the cloudflared connector in your cluster

## Service Routing Examples

### Internal Service Format
```
http://<service-name>.<namespace>.svc.cluster.local:<port>
```

### Examples:
- Frontend: `http://frontend.restaurant-system.svc.cluster.local:80`
- API Gateway: `http://api-gateway.restaurant-system.svc.cluster.local:8000`
- Auth Service: `http://auth-service.restaurant-system.svc.cluster.local:8001`
- Restaurant Service: `http://restaurant-service.restaurant-system.svc.cluster.local:8003`

## Advanced Configuration

### Using ConfigMap for Routes (Alternative Method)

Instead of configuring routes in the Cloudflare dashboard, you can use a config.yaml:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloudflared-config
  namespace: restaurant-system
data:
  config.yaml: |
    tunnel: YOUR_TUNNEL_ID
    credentials-file: /etc/cloudflared/creds/credentials.json
    ingress:
      - hostname: restaurant.yourdomain.com
        service: http://frontend:80
      - hostname: api.yourdomain.com
        service: http://api-gateway:8000
      - service: http_status:404  # catch-all
```

## Troubleshooting

### 1. Tunnel shows "Down" in dashboard
```bash
# Check pod logs
kubectl logs -n restaurant-system -l app=cloudflared

# Verify secret exists
kubectl get secret cloudflared-token -n restaurant-system

# Restart deployment
kubectl rollout restart deployment/cloudflared -n restaurant-system
```

### 2. Cannot access public URL
```bash
# Verify DNS records in Cloudflare
# They should be automatically created as CNAME records pointing to your tunnel

# Check if routes are configured
# Login to Cloudflare dashboard → Access → Tunnels → Your Tunnel → Public Hostname
```

### 3. 502 Bad Gateway
```bash
# Check if backend service is running
kubectl get svc -n restaurant-system

# Verify service names and ports match your tunnel configuration
kubectl get svc frontend -n restaurant-system
```

## Security Best Practices

1. **Keep tunnel token secret**: Never commit the actual token to Git
2. **Use separate tunnels**: Consider separate tunnels for dev/staging/production
3. **Enable Access policies**: Use Cloudflare Access to add authentication
4. **Monitor traffic**: Check Cloudflare Analytics for unusual patterns

## Clean Up

```bash
# Remove cloudflared deployment
kubectl delete -f infrastructure/kubernetes/cloudflare/deployment.yaml
kubectl delete -f infrastructure/kubernetes/cloudflare/secret.yaml

# Delete tunnel from Cloudflare dashboard
# Go to Access → Tunnels → Delete tunnel
```

## Benefits of Cloudflare Tunnel

✅ No open ports on your firewall  
✅ DDoS protection via Cloudflare  
✅ Free SSL certificates  
✅ Global CDN  
✅ Works behind NAT/firewall  
✅ Zero-trust security model  

## Next Steps

1. Configure custom domain routes in Cloudflare Dashboard
2. Set up Cloudflare Access for authentication (optional)
3. Enable Web Application Firewall (WAF) rules
4. Configure rate limiting
5. Set up analytics and monitoring
