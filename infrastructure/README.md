# Infrastructure Setup - Istio & Observability

This directory contains all configuration files for deploying Istio service mesh and the observability stack (Prometheus, Grafana, Loki, Jaeger, Kiali) for the Restaurant Management System.

## Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Run the installation script
./infrastructure/scripts/install-istio-observability.sh
```

This script will:
1. Install Istio 1.20.1
2. Deploy Prometheus, Grafana, Loki, Jaeger, and Kiali
3. Configure application namespace with Istio injection
4. Apply all Istio configurations

### Option 2: Manual Installation

Follow the detailed steps in [SERVICE_MESH_OBSERVABILITY.md](../SERVICE_MESH_OBSERVABILITY.md)

## Directory Structure

```
infrastructure/
├── istio/                          # Istio service mesh configurations
│   ├── istio-config.yaml          # Istio installation profile
│   ├── gateway.yaml               # Main ingress gateway
│   ├── peerauthentication.yaml    # mTLS configuration
│   ├── virtualservices/           # Traffic routing rules
│   │   ├── api-gateway-vs.yaml
│   │   └── services-vs.yaml
│   └── destinationrules/          # Load balancing & circuit breaking
│       ├── api-gateway-dr.yaml
│       └── services-dr.yaml
│
├── helm/                          # Helm values files
│   ├── prometheus-values.yaml     # Metrics collection
│   ├── grafana-values.yaml        # Dashboards & visualization
│   ├── loki-values.yaml           # Log aggregation
│   ├── jaeger-values.yaml         # Distributed tracing
│   └── kiali-values.yaml          # Service mesh management
│
└── scripts/
    └── install-istio-observability.sh  # Automated installation
```

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x installed
- Minimum 3 worker nodes
- 16 GB RAM per node
- 50 GB disk space

## Installation Steps

### 1. Install Istio

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.1 sh -
cd istio-1.20.1

# Install with custom config
./bin/istioctl install -f ../infrastructure/istio/istio-config.yaml -y

# Verify
kubectl get pods -n istio-system
```

### 2. Install Observability Stack

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo add kiali https://kiali.org/helm-charts
helm repo update

# Install Prometheus
helm upgrade --install prometheus prometheus-community/prometheus \
  -f infrastructure/helm/prometheus-values.yaml \
  -n istio-system --create-namespace

# Install Grafana
helm upgrade --install grafana grafana/grafana \
  -f infrastructure/helm/grafana-values.yaml \
  -n istio-system

# Install Loki
helm upgrade --install loki grafana/loki-stack \
  -f infrastructure/helm/loki-values.yaml \
  -n istio-system

# Install Jaeger
helm upgrade --install jaeger jaegertracing/jaeger \
  -f infrastructure/helm/jaeger-values.yaml \
  -n istio-system

# Install Kiali
helm upgrade --install kiali-server kiali/kiali-server \
  -f infrastructure/helm/kiali-values.yaml \
  -n istio-system
```

### 3. Configure Application Namespace

```bash
# Create namespace with Istio injection enabled
kubectl create namespace restaurant-management
kubectl label namespace restaurant-management istio-injection=enabled

# Apply Istio configurations
kubectl apply -f infrastructure/istio/gateway.yaml -n restaurant-management
kubectl apply -f infrastructure/istio/virtualservices/ -n restaurant-management
kubectl apply -f infrastructure/istio/destinationrules/ -n restaurant-management
kubectl apply -f infrastructure/istio/peerauthentication.yaml -n restaurant-management
```

### 4. Deploy Application

```bash
# Deploy using Helm (your application chart)
helm upgrade --install restaurant-app infrastructure/helm/restaurant-app \
  --set image.tag=latest \
  --set istio.enabled=true \
  -n restaurant-management
```

## Accessing Dashboards

### Kiali (Service Mesh Visualization)

```bash
kubectl port-forward -n istio-system svc/kiali 20001:20001
```

Open: http://localhost:20001

Features:
- Real-time service topology graph
- Traffic flow visualization
- Error rates and latencies
- Configuration validation

### Grafana (Metrics & Dashboards)

```bash
kubectl port-forward -n istio-system svc/grafana 3000:80
```

Open: http://localhost:3000

Default credentials:
- Username: `admin`
- Password: Run `kubectl get secret -n istio-system grafana -o jsonpath='{.data.admin-password}' | base64 -d`

Pre-configured dashboards:
- Istio Mesh Dashboard
- Istio Service Dashboard
- Istio Workload Dashboard
- Kubernetes Cluster Monitoring

### Prometheus (Metrics Database)

```bash
kubectl port-forward -n istio-system svc/prometheus-server 9090:80
```

Open: http://localhost:9090

Use for:
- Raw metrics queries
- Alert rule testing
- Data exploration

### Jaeger (Distributed Tracing)

```bash
kubectl port-forward -n istio-system svc/jaeger-query 16686:16686
```

Open: http://localhost:16686

Use for:
- End-to-end request tracing
- Latency breakdown
- Dependency analysis
- Error investigation

## Key Metrics to Monitor

### Golden Signals (RED Metrics)

```promql
# Request Rate
sum(rate(istio_requests_total{destination_service="order-service"}[5m]))

# Error Rate
sum(rate(istio_requests_total{response_code=~"5.*"}[5m])) / sum(rate(istio_requests_total[5m])) * 100

# Duration (P95)
histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le, destination_service))
```

### Service Health

```promql
# Pod availability
count(up{namespace="restaurant-management"} == 1) / count(up{namespace="restaurant-management"})

# CPU usage
sum(rate(container_cpu_usage_seconds_total{namespace="restaurant-management"}[5m])) by (pod)

# Memory usage
sum(container_memory_working_set_bytes{namespace="restaurant-management"}) by (pod)
```

## Istio Traffic Management

### Canary Deployment Example

Edit `virtualservices/order-service-vs.yaml`:

```yaml
spec:
  http:
    - route:
        - destination:
            host: order-service
            subset: stable
          weight: 90
        - destination:
            host: order-service
            subset: canary
          weight: 10
```

Apply:
```bash
kubectl apply -f infrastructure/istio/virtualservices/order-service-vs.yaml
```

### Circuit Breaking Configuration

Edit `destinationrules/order-service-dr.yaml`:

```yaml
spec:
  trafficPolicy:
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

## Troubleshooting

### Check Sidecar Injection

```bash
# View pods with sidecar status
kubectl get pods -n restaurant-management -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Each pod should show 2 containers: app + istio-proxy
```

### Verify mTLS

```bash
# Check if mTLS is enforced
istioctl authn tls-check order-service.restaurant-management.svc.cluster.local
```

### View Istio Proxy Logs

```bash
# Application logs
kubectl logs -n restaurant-management <pod-name> -c <container-name>

# Envoy proxy logs
kubectl logs -n restaurant-management <pod-name> -c istio-proxy
```

### Debug Configuration

```bash
# Validate Istio configuration
istioctl analyze -n restaurant-management

# Check proxy configuration sync
istioctl proxy-status
```

## Cleanup

### Remove Observability Stack

```bash
helm uninstall prometheus -n istio-system
helm uninstall grafana -n istio-system
helm uninstall loki -n istio-system
helm uninstall jaeger -n istio-system
helm uninstall kiali-server -n istio-system
```

### Remove Istio

```bash
kubectl delete namespace istio-system
istioctl uninstall --purge
```

## Cost Optimization

### Reduce Resources for Dev/Staging

1. **Single Istio control plane replica**: Edit `istio-config.yaml` and set `minReplicas: 1`
2. **Reduce sidecar resources**: Change proxy CPU from `10m` to `5m`
3. **Shorter retention**: Reduce Prometheus retention from 15d to 7d
4. **Lower trace sampling**: Change from 100% to 1% in production

Estimated savings: ~$40-50/month

### Disable Components Not Needed

```bash
# Disable Loki if not using logs
helm uninstall loki -n istio-system

# Disable Jaeger if not using traces
helm uninstall jaeger -n istio-system
```

## Security Considerations

1. **mTLS**: Enabled by default (STRICT mode)
2. **Dashboard Access**: Use port-forward or configure authentication
3. **Grafana Credentials**: Change default password immediately
4. **Network Policies**: Apply Kubernetes network policies for defense in depth
5. **RBAC**: Configure proper role-based access control

## CI/CD Integration

The GitHub Actions workflow in `.github/workflows/ci-cd-istio.yml` automatically:
1. Builds and pushes Docker images
2. Installs/updates Istio and observability stack
3. Deploys application with sidecars
4. Runs smoke tests
5. Reports deployment status

## Support & Documentation

- Comprehensive guide: [SERVICE_MESH_OBSERVABILITY.md](../SERVICE_MESH_OBSERVABILITY.md)
- Istio docs: https://istio.io/latest/docs/
- Kiali docs: https://kiali.io/docs/
- Grafana docs: https://grafana.com/docs/

## Resource Requirements Summary

| Component | Pods | CPU | Memory | Storage |
|-----------|------|-----|--------|---------|
| Istio Control Plane | 2 | 1 core | 4 GB | - |
| Istio Sidecars | ~16 | 160m | 640 MB | - |
| Istio Ingress | 2 | 200m | 256 MB | - |
| Prometheus | 1 | 500m | 2 GB | 50 GB |
| Grafana | 1 | 100m | 256 MB | 10 GB |
| Loki | 1 | 200m | 512 MB | 100 GB |
| Promtail (DaemonSet) | 3 | 150m | 384 MB | - |
| Jaeger | 1 | 100m | 256 MB | 20 GB |
| Kiali | 1 | 100m | 256 MB | - |
| **TOTAL** | **~28** | **2.5 cores** | **8.6 GB** | **180 GB** |

**Estimated Cost**: $121-153/month (AWS EKS)

## Next Steps

1. ✅ Complete installation using the script
2. ✅ Access dashboards and verify metrics
3. ✅ Deploy your application
4. ✅ Monitor traffic in Kiali
5. ✅ Set up alerts in Prometheus/Grafana
6. ✅ Test canary deployments
7. ✅ Configure CI/CD pipeline

---

**Last Updated**: 2025-12-30
**Istio Version**: 1.20.1
**Status**: Production Ready
