# Grafana Dashboards - Restaurant Management System

Comprehensive Grafana dashboards for monitoring metrics, logs, and traces across your restaurant management microservices.

## Dashboards Overview

### 1. Restaurant Management - Metrics Dashboard ⭐
**File**: `dashboards/restaurant-metrics-dashboard.json`

**Purpose**: Real-time metrics monitoring for all restaurant services

**Panels** (10 total):
1. **Total Request Rate (RPS)** - Gauge showing overall requests per second
2. **Error Rate (%)** - Gauge showing percentage of 5xx errors
3. **P95 Latency (ms)** - Gauge showing 95th percentile response time
4. **Active Pods by Service** - Time series of running pods
5. **Request Rate by Service** - Line chart comparing RPS across services
6. **Response Time by Service (P50, P95)** - Latency comparison
7. **Error Rate by Service (4xx, 5xx)** - Bar chart of client and server errors
8. **CPU Usage by Pod** - Resource utilization tracking
9. **Memory Usage by Pod** - Memory consumption per pod
10. **Service Summary Table** - Combined view of RPS, Error Rate, P95 Latency

**Datasource**: Prometheus

**Refresh**: Every 10 seconds

**Use Cases**:
- Monitor overall system health
- Identify performance bottlenecks
- Track resource consumption
- Detect anomalies in traffic patterns

---

### 2. Restaurant Management - Logs Dashboard ⭐
**File**: `dashboards/restaurant-logs-dashboard.json`

**Purpose**: Centralized log viewing and analysis across all services

**Panels** (10 total):
1. **Log Rate by Pod** - Time series showing log volume per pod
2. **Error Logs (All Services)** - Real-time error log stream
3. **Order Service Logs** - Dedicated log viewer for order-service
4. **API Gateway Logs** - Dedicated log viewer for api-gateway
5. **Restaurant Service Logs** - Dedicated log viewer for restaurant-service
6. **Auth Service Logs** - Dedicated log viewer for auth-service
7. **Error Count by Service (Last 5 min)** - Bar chart of error frequency
8. **Warning Count by Service (Last 5 min)** - Bar chart of warnings
9. **Istio Proxy Logs (Access Logs)** - Envoy sidecar access logs
10. **Failed Order Logs** - Filtered view of failed order attempts

**Datasource**: Loki

**Refresh**: Every 10 seconds

**Use Cases**:
- Debug application errors
- Investigate failed orders
- Audit access logs
- Monitor log volume spikes

**LogQL Queries Used**:
```logql
# All errors
{namespace="restaurant-system"} |= "ERROR"

# Service-specific logs
{namespace="restaurant-system",pod=~"order-service.*"}

# Failed orders
{namespace="restaurant-system"} |= "order" |= "failed"
```

---

### 3. Restaurant Management - Traces Dashboard ⭐
**File**: `dashboards/restaurant-traces-dashboard.json`

**Purpose**: Distributed tracing and request flow visualization

**Panels** (9 total):
1. **Trace Rate by Service** - Requests per second (represents trace volume)
2. **Trace Duration (P50, P95, P99)** - End-to-end latency percentiles
3. **Trace Search - Order Service** - Interactive Jaeger search for order traces
4. **Request Distribution by Service** - Pie chart showing traffic distribution
5. **Response Code Distribution** - Donut chart of 2xx/4xx/5xx codes
6. **Trace Search - API Gateway** - Interactive Jaeger search for API traces
7. **Trace Search - Restaurant Service** - Interactive Jaeger search
8. **Service Call Graph** - Table showing source → destination request flows
9. **Top 10 Slowest Endpoints (P99)** - Table of highest latency endpoints

**Datasources**:
- Prometheus (for metrics)
- Jaeger (for trace search)

**Refresh**: Every 10 seconds

**Use Cases**:
- Trace specific requests end-to-end
- Identify bottlenecks in request chains
- Analyze service dependencies
- Debug timeout issues

**Link**: Direct link to Jaeger UI (`http://localhost:16686`)

---

## Quick Start

### 1. Import Dashboards (Automated)

```bash
# Run the import script
./infrastructure/scripts/import-dashboards.sh
```

This will:
- Start port-forward to Grafana
- Import all 3 custom dashboards via API
- Display access credentials
- Show dashboard URLs

### 2. Manual Import (Alternative)

```bash
# Start Grafana port-forward
kubectl port-forward -n istio-system svc/grafana 3000:80

# Open Grafana
# URL: http://localhost:3000
# Username: admin
# Password: (run below command)
kubectl get secret --namespace istio-system grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

Then in Grafana UI:
1. Click **+** (Create) → **Import**
2. Click **Upload JSON file**
3. Select dashboard JSON file from `infrastructure/grafana/dashboards/`
4. Click **Load**
5. Select **Prometheus** or **Loki** or **Jaeger** as datasource
6. Click **Import**

Repeat for all 3 dashboards.

---

## Dashboard Details

### Metrics Dashboard - Panel Breakdown

#### Top Row (Overview)
- **Total RPS**: `sum(rate(istio_requests_total{destination_service_namespace="restaurant-system"}[5m]))`
- **Error Rate**: `sum(rate(...response_code=~"5.*"...)) / sum(rate(...)) * 100`
- **P95 Latency**: `histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket...)))`

#### Service Performance
- **Request Rate by Service**: Compares RPS across api-gateway, order-service, restaurant-service, auth-service
- **Response Time**: Shows P50 and P95 latency side-by-side

#### Error Analysis
- **4xx Errors**: Client-side errors (bad requests, unauthorized, not found)
- **5xx Errors**: Server-side errors (internal errors, service unavailable)

#### Resource Monitoring
- **CPU Usage**: Shows per-pod CPU consumption (excludes istio-proxy sidecar)
- **Memory Usage**: Shows per-pod memory consumption

#### Summary Table
Combines RPS, Error Rate %, and P95 Latency in a sortable table for quick comparison.

---

### Logs Dashboard - Panel Breakdown

#### Error Monitoring
- **Error Logs**: Real-time stream filtered by `|= "ERROR"`
- **Warning Logs**: Filtered by `|= "WARN"`
- **Failed Orders**: Filtered by `|= "order" |= "failed"`

#### Service-Specific Logs
Each service has dedicated log viewer:
- Filter by pod name pattern: `pod=~"order-service.*"`
- Shows timestamps, log levels, and messages
- Clickable to expand full log entry

#### Istio Proxy Logs
- Shows Envoy access logs
- Includes HTTP method, path, response code, duration
- Useful for debugging request routing

---

### Traces Dashboard - Panel Breakdown

#### Trace Search Panels
Interactive Jaeger integration:
- Click on a trace to view full span tree
- Filter by service name
- Sort by duration, timestamp
- Opens detailed view in Jaeger UI

#### Service Call Graph
Shows which services call which:
```
api-gateway → order-service (125 req/s)
api-gateway → restaurant-service (80 req/s)
order-service → menu-service (45 req/s)
```

#### Slowest Endpoints
Identifies performance bottlenecks:
- Sorted by P99 latency (highest first)
- Shows service name and protocol
- Helps prioritize optimization efforts

---

## Datasource Configuration

All dashboards expect these datasources:

### Prometheus
- **Name**: `Prometheus`
- **Type**: `prometheus`
- **URL**: `http://prometheus-server.istio-system:80`
- **Access**: `proxy`

### Loki
- **Name**: `Loki`
- **Type**: `loki`
- **URL**: `http://loki.istio-system:3100`
- **Access**: `proxy`

### Jaeger
- **Name**: `Jaeger`
- **Type**: `jaeger`
- **URL**: `http://jaeger-query.istio-system:16686`
- **Access**: `proxy`

These are auto-configured if you used the Helm installation from `infrastructure/helm/grafana-values.yaml`.

---

## Customization

### Change Namespace Filter

All dashboards filter by `namespace="restaurant-system"`. To change:

1. Open dashboard JSON file
2. Find and replace `restaurant-system` with your namespace
3. Re-import dashboard

### Add New Panels

1. Open dashboard in Grafana
2. Click **Add panel**
3. Select visualization type
4. Write PromQL/LogQL query
5. Click **Apply**
6. Click **Save dashboard** (disk icon)

### Export Modified Dashboard

1. Open dashboard
2. Click **Dashboard settings** (gear icon)
3. Click **JSON Model**
4. Copy JSON
5. Save to file in `infrastructure/grafana/dashboards/`

---

## Queries Reference

### Useful PromQL Queries

```promql
# Request rate for specific service
sum(rate(istio_requests_total{destination_service_name="order-service"}[5m]))

# Error rate percentage
sum(rate(istio_requests_total{response_code=~"5.*"}[5m]))
/ sum(rate(istio_requests_total[5m])) * 100

# P50, P95, P99 latency
histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le))

# CPU usage by pod
sum(rate(container_cpu_usage_seconds_total{namespace="restaurant-system"}[5m])) by (pod)

# Memory usage by pod
sum(container_memory_working_set_bytes{namespace="restaurant-system"}) by (pod)

# Request by HTTP method
sum(rate(istio_requests_total[5m])) by (request_method)

# Request by response code
sum(rate(istio_requests_total[5m])) by (response_code)
```

### Useful LogQL Queries

```logql
# All logs from restaurant-system
{namespace="restaurant-system"}

# Error logs only
{namespace="restaurant-system"} |= "ERROR"

# Service-specific logs
{namespace="restaurant-system",pod=~"order-service.*"}

# Failed order attempts
{namespace="restaurant-system"} |= "order" |= "failed"

# Logs with specific error code
{namespace="restaurant-system"} |= "500"

# Logs containing JSON and parse them
{namespace="restaurant-system"} | json

# Count errors in last 5 minutes
sum(count_over_time({namespace="restaurant-system"} |= "ERROR" [5m]))
```

---

## Alerts Configuration

To add alerts to dashboards:

1. Open panel in edit mode
2. Click **Alert** tab
3. Configure alert condition (e.g., `Error Rate > 5%`)
4. Set notification channel
5. Save

Example Alert Rules (add to Prometheus):

```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(istio_requests_total{response_code=~"5.*"}[5m]))
    / sum(rate(istio_requests_total[5m])) * 100 > 5
  for: 5m
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}%"

- alert: HighLatency
  expr: |
    histogram_quantile(0.95,
      sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le)
    ) > 1000
  for: 5m
  annotations:
    summary: "High latency detected"
    description: "P95 latency is {{ $value }}ms"
```

---

## Troubleshooting

### Dashboard Not Loading

1. Check datasource connection:
   - Go to **Configuration** → **Data sources**
   - Click **Test** button
   - Should show "Data source is working"

2. Check if metrics are being collected:
   ```bash
   # Test Prometheus query
   kubectl port-forward -n istio-system svc/prometheus-server 9090:80
   # Open http://localhost:9090
   # Run query: up{namespace="restaurant-system"}
   ```

3. Check pod labels:
   ```bash
   kubectl get pods -n restaurant-system --show-labels
   ```

### No Data in Panels

1. Verify namespace: Dashboards filter by `namespace="restaurant-system"`
2. Check time range: Try "Last 5 minutes" instead of "Last 1 hour"
3. Verify Istio sidecar injection:
   ```bash
   kubectl get pods -n restaurant-system -o jsonpath='{.items[*].spec.containers[*].name}'
   # Should see: app-container istio-proxy
   ```

### Logs Not Showing

1. Check if Promtail is running:
   ```bash
   kubectl get pods -n istio-system | grep promtail
   ```

2. Check Loki datasource URL
3. Verify logs exist:
   ```bash
   kubectl logs -n restaurant-system <pod-name>
   ```

### Traces Not Showing

1. Verify Jaeger is installed:
   ```bash
   kubectl get pods -n istio-system | grep jaeger
   ```

2. Check tracing sampling rate (should be > 0%):
   - Default is 100% in dev
   - Reduce to 1% for production

3. Test Jaeger UI directly:
   ```bash
   kubectl port-forward -n istio-system svc/jaeger-query 16686:16686
   # Open http://localhost:16686
   ```

---

## Files Created

```
infrastructure/grafana/
├── README.md                                  # This file
├── dashboard-configmap.yaml                   # Kubernetes ConfigMap (optional)
├── dashboards/
│   ├── restaurant-metrics-dashboard.json      # Metrics dashboard
│   ├── restaurant-logs-dashboard.json         # Logs dashboard
│   └── restaurant-traces-dashboard.json       # Traces dashboard
└── scripts/
    └── import-dashboards.sh                   # Automated import script
```

---

## Next Steps

1. **Import dashboards**: Run `./infrastructure/scripts/import-dashboards.sh`
2. **Start port-forward**: Run `./infrastructure/scripts/start-dashboards.sh`
3. **Access Grafana**: Open `http://localhost:3000`
4. **Explore dashboards**: Navigate to **Dashboards** → **Browse**
5. **Set as favorites**: Star the dashboards you use most
6. **Create custom views**: Combine panels from different dashboards
7. **Set up alerts**: Add alert rules for critical metrics

---

## Best Practices

1. **Use time range selectors**: Adjust based on investigation needs
2. **Refresh rate**: 10s for live monitoring, 1m for historical analysis
3. **Combine dashboards**: Use variables to filter across all dashboards
4. **Export regularly**: Save modified dashboards to JSON files
5. **Document changes**: Add descriptions to custom panels
6. **Test alerts**: Ensure notifications reach the right channels

---

**Dashboard Version**: 1.0
**Last Updated**: 2025-12-30
**Grafana Version**: 8.0.0+
**Status**: Ready to Import
