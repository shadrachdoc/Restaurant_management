# Observability Dashboard Scripts

Quick access scripts for Istio and Observability dashboards.

## Available Scripts

### 1. install-istio-observability.sh
**Purpose**: One-command installation of Istio and full observability stack

**Usage**:
```bash
./infrastructure/scripts/install-istio-observability.sh
```

**What it installs**:
- Istio 1.20.1 (Control Plane + Ingress Gateway)
- Prometheus (Metrics collection)
- Grafana (Dashboards)
- Loki (Log storage)
- Kiali (Service mesh visualization)
- Jaeger (Distributed tracing - if PVC available)

**Duration**: 10-15 minutes

---

### 2. start-dashboards.sh ⭐ NEW
**Purpose**: Start all observability dashboards with a single command

**Usage**:
```bash
./infrastructure/scripts/start-dashboards.sh
```

**What it does**:
- Starts port-forwards for all dashboards in the background
- Keeps all processes running until you press CTRL+C
- Optionally auto-opens dashboards in your browser
- Monitors dashboard health every 30 seconds
- Automatically cleans up on exit

**Dashboards started**:
- Kiali: http://localhost:20001
- Grafana: http://localhost:3000 (admin / changeme123)
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686 (if available)

**Features**:
✅ Single command to access all dashboards
✅ Runs in foreground with status updates
✅ Clean shutdown with CTRL+C
✅ Auto-recovery detection
✅ Optional browser auto-launch

---

### 3. stop-dashboards.sh
**Purpose**: Stop all running dashboard port-forwards

**Usage**:
```bash
./infrastructure/scripts/stop-dashboards.sh
```

**What it does**:
- Stops all port-forward processes started by start-dashboards.sh
- Cleans up PID files
- Frees up ports 20001, 3000, 9090, 16686

---

## Quick Start Guide

### First Time Setup
```bash
# 1. Install everything
./infrastructure/scripts/install-istio-observability.sh

# 2. Start all dashboards
./infrastructure/scripts/start-dashboards.sh

# 3. Access dashboards in browser (auto-opens or manually):
#    - Kiali:      http://localhost:20001
#    - Grafana:    http://localhost:3000
#    - Prometheus: http://localhost:9090
```

### Daily Usage
```bash
# Start dashboards
./infrastructure/scripts/start-dashboards.sh

# When done, press CTRL+C in the terminal
# OR run in another terminal:
./infrastructure/scripts/stop-dashboards.sh
```

### Background Mode (Advanced)
```bash
# Start dashboards in background (detached)
nohup ./infrastructure/scripts/start-dashboards.sh > /tmp/dashboards.log 2>&1 &

# Check if running
ps aux | grep "start-dashboards"

# Stop when needed
./infrastructure/scripts/stop-dashboards.sh
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :20001  # Kiali
lsof -i :3000   # Grafana
lsof -i :9090   # Prometheus
lsof -i :16686  # Jaeger

# Kill specific port-forward
pkill -f "kubectl port-forward.*20001"

# Or stop all dashboards
./infrastructure/scripts/stop-dashboards.sh
```

### Dashboard Not Accessible
```bash
# Check if pods are running
kubectl get pods -n istio-system

# Restart specific dashboard
kubectl rollout restart deployment/kiali -n istio-system
kubectl rollout restart deployment/grafana -n istio-system

# Check logs
kubectl logs -n istio-system deployment/kiali
kubectl logs -n istio-system deployment/grafana
```

### Script Permission Denied
```bash
# Make scripts executable
chmod +x infrastructure/scripts/*.sh
```

---

## Example Session

```bash
# Terminal 1: Start dashboards
$ ./infrastructure/scripts/start-dashboards.sh

╔════════════════════════════════════════════════════════════╗
║          Starting Observability Dashboards                ║
╚════════════════════════════════════════════════════════════╝

Starting port-forwards...

1. Starting Kiali (Service Mesh Dashboard)...
   ✅ Kiali running on http://localhost:20001

2. Starting Grafana (Metrics & Dashboards)...
   ✅ Grafana running on http://localhost:3000
   📝 Username: admin
   📝 Password: changeme123

3. Starting Prometheus (Metrics Database)...
   ✅ Prometheus running on http://localhost:9090

╔════════════════════════════════════════════════════════════╗
║              All Dashboards are Running!                  ║
╚════════════════════════════════════════════════════════════╝

📊 Dashboard URLs:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Kiali (Service Mesh):      http://localhost:20001
2. Grafana (Dashboards):      http://localhost:3000  (admin / changeme123)
3. Prometheus (Metrics):      http://localhost:9090
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you want to open all dashboards in your browser? [y/N]: y

Opening dashboards in browser...
✅ Dashboards opened

✨ Dashboards are ready! Press CTRL+C to stop all port-forwards.

[14:23:45] Status: 3/3 dashboards running
[14:24:15] Status: 3/3 dashboards running
...

^C
Stopping all port-forwards...
✅ All dashboards stopped
```

---

## Script Features Comparison

| Feature | install-istio-observability.sh | start-dashboards.sh | stop-dashboards.sh |
|---------|-------------------------------|---------------------|-------------------|
| One-time setup | ✅ | ❌ | ❌ |
| Daily use | ❌ | ✅ | ✅ |
| Installs components | ✅ | ❌ | ❌ |
| Starts port-forwards | ❌ | ✅ | ❌ |
| Stops port-forwards | ❌ | ❌ | ✅ |
| Auto-browser launch | ❌ | ✅ | ❌ |
| Health monitoring | ❌ | ✅ | ❌ |
| Clean shutdown | ❌ | ✅ | ✅ |

---

## Tips & Best Practices

1. **Keep Terminal Open**: The start-dashboards.sh script runs in the foreground. Keep the terminal window open.

2. **Multiple Terminals**: If you need to run kubectl commands while dashboards are running, open a new terminal tab.

3. **Resource Usage**: All port-forwards are lightweight. They only forward network traffic.

4. **Security**: Dashboards are only accessible on localhost. They're not exposed externally.

5. **Auto-start on Login** (Optional):
   ```bash
   # Add to ~/.bashrc or create systemd service
   alias dashboards='~/Restaurant_management/infrastructure/scripts/start-dashboards.sh'
   ```

6. **Check Status Anytime**:
   ```bash
   # See what's running
   ps aux | grep "kubectl port-forward"

   # Check dashboard pods
   kubectl get pods -n istio-system
   ```

---

## Files Created

```
infrastructure/scripts/
├── install-istio-observability.sh    # One-time installation
├── start-dashboards.sh               # Start all dashboards (NEW)
├── stop-dashboards.sh                # Stop all dashboards (NEW)
└── README.md                         # This file (NEW)
```

---

## What's Next?

After starting dashboards:

1. **Deploy your app** to `restaurant-management` namespace
2. **Open Kiali** to see service topology
3. **Check Grafana** for Istio metrics dashboards
4. **Query Prometheus** for custom metrics
5. **Monitor traffic** in real-time

Happy monitoring! 🎉
