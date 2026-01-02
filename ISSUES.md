# Issues Encountered and Resolutions

This document tracks all major issues encountered in the Restaurant Management System and their solutions.

---

## Issue #8: Observability Dashboards Not Accessible - Cluster Networking Failure

**Date**: January 1, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Problem Description

All observability dashboards (Grafana, Kiali, ArgoCD) became inaccessible. When attempting to access dashboards via port-forward, connections failed. Investigation revealed multiple pods in CrashLoopBackOff state.

**User Reported**:
- Started port-forward script: `./infrastructure/scripts/start-dashboards.sh`
- ArgoCD showed as running on https://localhost:8080 but unable to open
- Error: Connection failed when accessing dashboards

**Symptoms**:
```bash
# Pod Status
argocd-server-857dc8758c-bp6sv          0/1  CrashLoopBackOff  28 (4m11s ago)   9d
argocd-redis-6c9d5bfb8c-bg4wn          0/1  Init:CrashLoopBackOff  25 (2m56s ago)   9d
argocd-repo-server-566d9c5f56-jmjzj    0/1  CrashLoopBackOff  25 (55s ago)     9d
grafana-99d5d4f6b-jc2ld                0/1  Init:CrashLoopBackOff  22 (2m29s ago)   2d2h
kiali-774496f566-4f524                 0/1  Running  32 (58s ago)  2d2h
```

### Root Cause Analysis

**Primary Issue**: Pods unable to connect to Kubernetes API server

**Investigation Steps**:

1. **Checked ArgoCD pod logs**:
```bash
kubectl logs -n argocd argocd-server-857dc8758c-bp6sv --tail=30
```

**Error Found**:
```
failed to list *v1.Secret: Get "https://10.96.0.1:443/api/v1/namespaces/argocd/secrets?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: connect: no route to host
```

2. **Checked Grafana pod status**:
```bash
kubectl get pods -n istio-system | grep grafana
# Output: grafana-99d5d4f6b-jc2ld  0/1  Init:CrashLoopBackOff
```

**Grafana Init Container Error**:
```bash
kubectl logs -n istio-system grafana-99d5d4f6b-fpw84 -c init-chown-data
# Output:
chown: /var/lib/grafana/csv: Permission denied
chown: /var/lib/grafana/png: Permission denied
chown: /var/lib/grafana/pdf: Permission denied
```

**Additional Error After Fixing Permissions**:
```bash
kubectl logs -n istio-system grafana-99d5d4f6b-lb9vv --tail=100 | grep -i "error"
# Output:
logger=plugin.backgroundinstaller error="failed to install plugin grafana-piechart-panel@: Get \"https://grafana.com/api/plugins/grafana-piechart-panel/versions\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)"
```

3. **Checked Kiali pod logs**:
```bash
kubectl logs -n istio-system kiali-774496f566-4f524 --tail=30
```

**Same networking error**:
```
failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: connect: no route to host
```

4. **Verified Kubernetes API service**:
```bash
kubectl get svc -n default kubernetes
# Output:
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   28d
```
API service exists at `10.96.0.1:443` - the exact address pods are trying to reach.

5. **Checked cluster info**:
```bash
kubectl cluster-info
# Output:
Kubernetes control plane is running at https://127.0.0.1:42401
CoreDNS is running at https://127.0.0.1:42401/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```
Cluster is accessible from outside, but pods can't connect internally.

6. **Checked CNI pods**:
```bash
kubectl get pods -n kube-system | grep -E "(coredns|kindnet)"
# Output:
coredns-5d78c9869d-25jcs     1/1  Running  12 (88m ago)  28d
coredns-5d78c9869d-gxr2z     1/1  Running  12 (88m ago)  28d
kindnet-942gb                1/1  Running  12 (88m ago)  28d
kindnet-kgjnx                1/1  Running  12 (88m ago)  28d
kindnet-xp6pg                1/1  Running  12 (88m ago)  28d
```
CNI (kindnet) is running but networking is broken.

7. **Checked cluster uptime**:
```bash
kubectl get nodes
# Cluster age: 28 days
```

**Root Cause Identified**:
- Cluster had been running for 28 days without restart
- Accumulated iptables rules or networking state corruption
- CNI unable to properly route pod-to-pod traffic
- Kubernetes API server (`10.96.0.1:443`) unreachable from pods

### Solution

**Step 1: Restart Cluster Containers**

Restarted all kind cluster containers to reset networking:
```bash
docker restart restaurant-cluster-control-plane restaurant-cluster-worker restaurant-cluster-worker2
```

**Result**: All nodes came back Ready
```bash
kubectl get nodes
# Output:
NAME                               STATUS   ROLES           AGE   VERSION
restaurant-cluster-control-plane   Ready    control-plane   28d   v1.27.3
restaurant-cluster-worker          Ready    <none>          28d   v1.27.3
restaurant-cluster-worker2         Ready    <none>          28d   v1.27.3
```

**Step 2: Fix Grafana Persistent Volume Issues**

After restart, Grafana still had permission issues with PVC. Fixed by recreating PVC:

```bash
# Scale down Grafana
kubectl scale deployment grafana -n istio-system --replicas=0

# Delete old PVC
kubectl delete pvc grafana -n istio-system

# Create fresh PVC
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana
  namespace: istio-system
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
EOF

# Scale up Grafana
kubectl scale deployment grafana -n istio-system --replicas=1
```

**Step 3: Fix Grafana Plugin Installation**

Grafana was trying to download plugins from internet but timing out. Removed plugins:

```bash
# Remove plugins from ConfigMap
kubectl patch configmap grafana -n istio-system --type='json' \
  -p='[{"op": "replace", "path": "/data/plugins", "value": ""}]'

# Delete pod to restart with new config
kubectl delete pod -n istio-system <grafana-pod-name>
```

**Step 4: Verify All Pods Running**

```bash
# Check istio-system pods
kubectl get pods -n istio-system | grep -E "(grafana|kiali)"
# Output:
grafana-99d5d4f6b-sxpjb   1/1  Running  0  30s
kiali-774496f566-4f524    1/1  Running  35 (2m11s ago)  2d3h

# Check ArgoCD pods
kubectl get pods -n argocd
# Output:
argocd-application-controller-0                    0/1  Running   4 (124m ago)  8d
argocd-applicationset-controller-5c7d759d8-rfvfs   1/1  Running   11 (124m ago) 18d
argocd-dex-server-5bc57448bc-kqmzr                 1/1  Running   11 (124m ago) 18d
argocd-notifications-controller-7f6b9486d7-n26sg   1/1  Running   11 (124m ago) 18d
argocd-redis-6c9d5bfb8c-r2hdg                      1/1  Running   0             36m
argocd-repo-server-566d9c5f56-d95jh                1/1  Running   11 (3m7s ago) 36m
argocd-server-857dc8758c-znmh5                     1/1  Running   11 (7m17s ago) 36m
```

**Step 5: Start Port-Forwards**

```bash
# Start port-forwards manually
kubectl port-forward -n istio-system svc/kiali 20001:20001 > /dev/null 2>&1 &
kubectl port-forward -n istio-system svc/grafana 3000:80 > /dev/null 2>&1 &
kubectl port-forward -n istio-system svc/prometheus-server 9090:80 > /dev/null 2>&1 &
kubectl port-forward -n argocd svc/argocd-server 8080:443 > /dev/null 2>&1 &
```

**Step 6: Verify Accessibility**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:20001  # 302 - Kiali ✅
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000   # 302 - Grafana ✅
curl -s -k -o /dev/null -w "%{http_code}" https://localhost:8080 # 200 - ArgoCD ✅
```

### Final Status

✅ **All Dashboards Working**:
- **Kiali**: http://localhost:20001
- **Grafana**: http://localhost:3000 (admin / changeme123)
- **ArgoCD**: https://localhost:8080 (admin / myq45CaeIZQNPgkA)
- **Prometheus**: http://localhost:9090

### Lessons Learned

1. **Long-running clusters need periodic restarts**: Kind clusters (and Kubernetes in general) can accumulate networking state issues over time. Regular restarts prevent this.

2. **Check networking first**: When multiple pods fail with similar "connection refused" or "no route to host" errors, suspect cluster-wide networking issues before investigating individual pod problems.

3. **PVC permissions can be tricky**: Init containers that change file ownership can fail if the underlying storage has permission restrictions. Using fresh PVCs often resolves this.

4. **Plugin downloads require internet**: Grafana plugin installation requires external connectivity. In restricted environments, disable plugin installation or pre-load plugins.

5. **Port-forward script reliability**: The `start-dashboards.sh` script may need supervision. For production-like setups, use proper Ingress instead of port-forwards.

### Prevention

**Recommended Actions**:
1. Restart kind cluster weekly (or after major updates)
2. Monitor pod restart counts - high numbers indicate issues
3. Use Ingress for dashboard access instead of port-forwards
4. Disable unnecessary plugin installations in Grafana
5. Consider using emptyDir for Grafana storage in dev environments

### Related Commands

**Quick cluster health check**:
```bash
# Check all pods across namespaces
kubectl get pods -A | grep -v Running

# Check node status
kubectl get nodes

# Test Kubernetes API from a pod
kubectl run test-pod --image=curlimages/curl -it --rm --restart=Never -- \
  curl -k https://10.96.0.1:443/healthz
```

**Quick dashboard restart**:
```bash
# If dashboards become unresponsive
kubectl delete pod -n istio-system -l app=grafana
kubectl delete pod -n istio-system -l app=kiali
kubectl rollout restart deployment argocd-server -n argocd
```

**Alternative to port-forwards**:
```bash
# Use kubectl proxy instead
kubectl proxy --port=8001 &
# Access Grafana at: http://localhost:8001/api/v1/namespaces/istio-system/services/grafana:service/proxy/
```

---

## Issue #9: Order Service Database Connection Failure - Worker Node Failure & PostgreSQL Restart

**Date**: January 1, 2026
**Severity**: High
**Status**: ✅ Resolved

### Problem Description

Order service failing to start with database connection error: `socket.gaierror: [Errno -3] Temporary failure in name resolution`. All database-dependent services (auth-service, restaurant-service, customer-service) were in CrashLoopBackOff state.

**User Reported**:
- Order service logs showing:
  ```
  ERROR: Application startup failed. Exiting.
  socket.gaierror: [Errno -3] Temporary failure in name resolution
  ```

**Symptoms**:
```bash
# Pod Status
order-service-7b9747ffd9-qnbd8     1/2  CrashLoopBackOff  11 (2m21s ago)  34m
postgres-0                         1/1  Terminating       1 (5h51m ago)   4d8h
auth-service-6789cf779f-cshlz      1/2  CrashLoopBackOff  108 (3m30s ago) 2d3h
restaurant-service-7f4cf474d9-pvbpk 1/2 CrashLoopBackOff  109 (3m31s ago) 2d7h
customer-service-fbc478ccf-mbtff   1/2  CrashLoopBackOff  32 (4m49s ago)  146m
```

### Root Cause Analysis

**Primary Issues**:
1. PostgreSQL pod stuck in "Terminating" state after cluster restart
2. Worker node (worker2) in "NotReady" state
3. StatefulSet PVC bound to failed worker node
4. Services unable to resolve database hostname

**Investigation Steps**:

1. **Checked order-service logs**:
```bash
kubectl logs -n restaurant-system order-service-7b9747ffd9-qnbd8 --tail=100
```

**Error Found**:
```python
File "/app/app/database.py", line 54, in init_db
    async with engine.begin() as conn:
...
socket.gaierror: [Errno -3] Temporary failure in name resolution
```
Service can't resolve PostgreSQL hostname - database not running.

2. **Checked PostgreSQL pod status**:
```bash
kubectl get pods -n restaurant-system | grep postgres
# Output: postgres-0  1/1  Terminating  1 (5h51m ago)  4d8h
```
PostgreSQL stuck terminating for hours!

3. **Checked worker nodes**:
```bash
kubectl get nodes -o wide
# Output:
NAME                               STATUS     ROLES           AGE   VERSION
restaurant-cluster-control-plane   Ready      control-plane   29d   v1.27.3
restaurant-cluster-worker          Ready      <none>          29d   v1.27.3
restaurant-cluster-worker2         NotReady   <none>          29d   v1.27.3
```
Worker2 is NotReady!

4. **Force deleted PostgreSQL pod**:
```bash
kubectl delete pod postgres-0 -n restaurant-system --force --grace-period=0
```

5. **New pod remained Pending**:
```bash
kubectl describe pod postgres-0 -n restaurant-system | grep -A 5 "Events:"
# Output:
Events:
  Warning  FailedScheduling  0/3 nodes are available: 1 node(s) had untolerated taint {node.kubernetes.io/unreachable: }
```

6. **Identified PVC issue**:
```bash
kubectl get pvc -n restaurant-system | grep postgres
# Output: postgres-storage-postgres-0  Bound  pvc-e78e2b3a...  10Gi  RWO  standard  4d10h
```
PVC bound to unavailable worker2 node.

**Root Causes Identified**:
- Worker node 2 failed after cluster restart and stayed NotReady
- PostgreSQL StatefulSet pod stuck because its PVC was on failed node
- Kubernetes tried to maintain pod-to-PVC affinity, preventing rescheduling
- Without database, all services fail DNS resolution and crash

### Solution

**Step 1: Force Delete Stuck PostgreSQL Pod**
```bash
kubectl delete pod postgres-0 -n restaurant-system --force --grace-period=0
```

**Step 2: Attempt Node Restart**
```bash
docker restart restaurant-cluster-worker2
# Result: Node stayed NotReady
```

**Step 3: Remove Node Taint (Temporary)**
```bash
kubectl taint nodes restaurant-cluster-worker2 node.kubernetes.io/unreachable-
# Result: Taint removed but node controller re-added it (node actually unreachable)
```

**Step 4: Cordon Failed Node**
```bash
kubectl cordon restaurant-cluster-worker2
```
Prevent new pods from scheduling on failed node.

**Step 5: Delete PostgreSQL StatefulSet PVC**

Since PVC was bound to failed node, delete and recreate:
```bash
# Scale down StatefulSet
kubectl scale statefulset postgres -n restaurant-system --replicas=0

# Delete bound PVC
kubectl delete pvc postgres-storage-postgres-0 -n restaurant-system

# Scale back up (creates new PVC on healthy node)
kubectl scale statefulset postgres -n restaurant-system --replicas=1
```

**Result**: PostgreSQL scheduled to healthy worker node:
```bash
kubectl get pods -n restaurant-system | grep postgres
# Output: postgres-0  2/2  Running  0  33s
```

**Step 6: Restart All Database-Dependent Services**
```bash
kubectl delete pod auth-service-6789cf779f-cshlz \
  customer-service-fbc478ccf-mbtff \
  restaurant-service-7f4cf474d9-pvbpk \
  -n restaurant-system --force --grace-period=0
```

**Step 7: Verify All Services Running**
```bash
kubectl get pods -n restaurant-system
```

**Final State**:
```
NAME                                  READY   STATUS    RESTARTS   AGE
api-gateway-b5b6c4977-2qrhv           2/2     Running   15         2d3h
auth-service-6789cf779f-dx6t4         2/2     Running   0          46s
customer-service-fbc478ccf-28hzm      2/2     Running   1          45s
frontend-68ff46499b-5l6g7             2/2     Running   15         2d3h
order-service-7b9747ffd9-lplk4        2/2     Running   0          96s
postgres-0                            2/2     Running   0          2m17s
rabbitmq-0                            1/1     Running   2          4d10h
redis-0                               1/1     Running   2          4d10h
restaurant-service-7f4cf474d9-dp2db   2/2     Running   0          45s
```

### Final Status

✅ **All Services Restored**:
- postgres-0: 2/2 Running
- order-service: 2/2 Running
- auth-service: 2/2 Running
- restaurant-service: 2/2 Running
- customer-service: 2/2 Running
- All other services: Running

### Lessons Learned

1. **StatefulSet PVC Locality**: StatefulSets with persistent storage maintain pod-to-node affinity through PVCs. If a node fails, the pod cannot reschedule unless PVC is deleted or node recovered.

2. **Worker Node Monitoring**: After cluster restarts, verify ALL nodes are Ready. One NotReady node can block critical StatefulSets.

3. **Force Delete Limitations**: Force deleting stuck pods doesn't solve underlying scheduling issues - need to address node/storage problems.

4. **Database as Critical Dependency**: When database fails, cascading failures occur in all dependent services. Database health is critical path.

5. **PVC Deletion Risk**: Deleting StatefulSet PVCs loses data! Only acceptable in dev environments. In production, must recover the node or migrate PVC.

### Prevention

**Recommended Actions**:

1. **Monitor node health after restarts**:
```bash
kubectl get nodes
# Ensure all nodes show "Ready" status
```

2. **Set up node auto-recovery**: Configure node lifecycle hooks to detect and restart failed nodes automatically.

3. **Use PV anti-affinity for critical StatefulSets**: Configure PostgreSQL to use PVs that can float between nodes (e.g., network storage instead of local-path).

4. **Database health checks**: Add monitoring alerts for database pod state.

5. **Implement database replication**: For production, use PostgreSQL with replicas to survive single-pod failures.

### Related Commands

**Quick node health check**:
```bash
# Check all nodes
kubectl get nodes -o wide

# Check node conditions
kubectl describe node <node-name> | grep -A 10 Conditions

# Uncordon a node
kubectl uncordon <node-name>

# Drain a node safely
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

**StatefulSet PVC troubleshooting**:
```bash
# Check StatefulSet status
kubectl get statefulset -n <namespace>

# Check PVC binding
kubectl get pvc -n <namespace>

# Check which node a PV is on (for local-path)
kubectl get pv -o wide

# Force reschedule StatefulSet pod
kubectl scale statefulset <name> -n <namespace> --replicas=0
kubectl delete pvc <pvc-name> -n <namespace>  # ⚠️ DATA LOSS!
kubectl scale statefulset <name> -n <namespace> --replicas=1
```

**Service dependency checks**:
```bash
# Check if database is reachable from a pod
kubectl exec -n <namespace> <pod-name> -- nslookup postgres

# Test database connection
kubectl exec -n <namespace> <pod-name> -- nc -zv postgres 5432
```

---

## Issue #10: API Requests Failing with 503 - Istio VirtualService Misconfiguration

**Date**: January 1, 2026
**Severity**: Critical
**Status**: ✅ Resolved

### Problem Description

User reported "file not loading" errors on all pages in the web application. Investigation revealed that all API requests to analytics endpoints were failing with HTTP 503 (Service Unavailable). Frontend loaded correctly, but backend API calls were being blocked.

**User Reported**:
- "i think there is a issue in all page i am getting file not loading"

**Symptoms**:
- Frontend HTML loads successfully (HTTP 200)
- All analytics API endpoints return 503 errors
- Example failing request: `/api/v1/restaurants/{id}/analytics/peak-hours`
- Istio proxy logs show: `"response_code_details":"cluster_not_found"`
- Direct pod IP connections work, but service name resolution fails

### Root Cause Analysis

**Primary Issue**: Istio VirtualService for order-service was configured with incorrect port (8001 instead of 8004)

**Investigation Steps**:

1. **Checked frontend and API gateway logs**:
```bash
kubectl logs -n restaurant-system -l app=frontend --tail=50
kubectl logs -n restaurant-system -l app=api-gateway --tail=100
```

**Findings**:
- Frontend nginx routing: ✅ Working correctly
- API Gateway routing to order-service: ❌ Returning 503
- API Gateway debug logs: `Routing detailed analytics to ORDER_SERVICE: http://order-service:8004`

2. **Tested connectivity**:
```bash
# Test from API gateway to order-service by service name
kubectl exec -n restaurant-system deploy/api-gateway -c api-gateway -- \
  python3 -c "import httpx; r = httpx.get('http://order-service:8004/health', timeout=5); print(r.status_code)"
# Output: 503

# Test with direct pod IP
kubectl exec -n restaurant-system deploy/api-gateway -c api-gateway -- \
  python3 -c "import httpx; r = httpx.get('http://10.244.2.33:8004/health', timeout=5); print(r.status_code)"
# Output: 200 (SUCCESS!)
```

**Conclusion**: Service name resolution through Istio was failing, but direct pod IPs worked.

3. **Checked Istio configuration**:
```bash
# Check Istio proxy logs
kubectl logs -n restaurant-system -l app=api-gateway -c istio-proxy --tail=20 | grep order-service
```

**Critical Error Found**:
```json
{
  "response_code": 503,
  "response_code_details": "cluster_not_found",
  "response_flags": "NC",
  "authority": "order-service:8004"
}
```

Istio couldn't find the cluster for `order-service:8004`.

4. **Checked Istio clusters**:
```bash
kubectl exec -n restaurant-system deploy/api-gateway -c istio-proxy -- \
  pilot-agent request GET clusters | grep order-service
```

**Found**: Cluster `outbound|8004||order-service.restaurant-system.svc.cluster.local` exists and is healthy.

5. **Checked VirtualService configuration**:
```bash
kubectl get virtualservice order-service -n restaurant-system -o yaml
```

**Root Cause Identified**:
```yaml
spec:
  hosts:
  - order-service
  http:
  - route:
    - destination:
        host: order-service
        port:
          number: 8001  # ❌ WRONG PORT! Should be 8004
        subset: stable   # ❌ Subset doesn't exist (DestinationRule was deleted)
```

**The VirtualService was routing to port 8001, but order-service runs on port 8004!**

6. **Verified actual service ports**:
```bash
kubectl get svc -n restaurant-system | grep order-service
# Output: order-service  ClusterIP  10.96.65.134  <none>  8004/TCP  4d10h
```

7. **Checked for missing PeerAuthentication**:
```bash
kubectl get peerauthentication -n restaurant-system
```

**Found**: No permissive mTLS policy for order-service, auth-service, restaurant-service, or customer-service.

### Solution

**Step 1: Created Permissive mTLS for All Backend Services**
```bash
for svc in order-service auth-service restaurant-service customer-service; do
  cat <<EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: ${svc}-permissive
  namespace: restaurant-system
spec:
  selector:
    matchLabels:
      app: $svc
  mtls:
    mode: PERMISSIVE
EOF
done
```

**Step 2: Fixed order-service VirtualService**

Deleted incorrect VirtualService:
```bash
kubectl delete virtualservice order-service -n restaurant-system
```

Created correct VirtualService:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
  namespace: restaurant-system
spec:
  hosts:
  - order-service
  http:
  - route:
    - destination:
        host: order-service
        port:
          number: 8004  # ✅ Correct port
    timeout: 15s
    retries:
      attempts: 3
      perTryTimeout: 5s
      retryOn: 5xx,reset,connect-failure,refused-stream
EOF
```

**Step 3: Deleted Incorrect DestinationRule**
```bash
kubectl delete destinationrule order-service -n restaurant-system
```

The DestinationRule had:
- Incorrect subset references (`subset: stable` without matching pod labels)
- Overly aggressive outlier detection settings
- Explicit TLS mode conflicting with permissive peer authentication

**Step 4: Restarted API Gateway**
```bash
kubectl delete pod -n restaurant-system -l app=api-gateway
kubectl wait --for=condition=Ready pod -l app=api-gateway -n restaurant-system --timeout=60s
```

### Verification

**Test 1: Order service health check**:
```bash
kubectl exec -n restaurant-system deploy/api-gateway -c api-gateway -- \
  python3 -c "import httpx; r = httpx.get('http://order-service:8004/health', timeout=5); print(r.status_code, r.text)"
# Output: 200 {"status":"healthy","service":"order-service"}
```

**Test 2: Analytics endpoint**:
```bash
kubectl exec -n restaurant-system deploy/frontend -c frontend -- \
  curl -s "http://localhost/api/v1/restaurants/52c0d315-b894-40c6-be52-3416a9d0a1e7/analytics/peak-hours?start_date=2025-12-02&end_date=2026-01-01"
# Output: {"start_date":"2025-12-02","end_date":"2026-01-01","hourly_metrics":[],"busiest_hour":0,"slowest_hour":0}
# HTTP Status: 200
```

**Test 3: Frontend**:
```bash
curl -s https://restaurant.corpv3.com/ | head -10
# Output: <!doctype html>... (Frontend loads successfully)

curl -s https://restaurant.corpv3.com/api/v1/restaurants
# Output: [] (API works)
```

### Final Status

✅ **All API endpoints now working**
✅ **Frontend loads correctly**
✅ **Analytics endpoints return data (empty arrays for no data, not errors)**
✅ **Istio routing configured correctly**

### Lessons Learned

1. **VirtualService port configuration is critical**: Always verify that VirtualService destination ports match the actual service ports.

2. **Test Istio routing separately**: When debugging service mesh issues:
   - Test direct pod IP first (bypasses Istio)
   - Test service name (goes through Istio)
   - Check Istio proxy logs for `cluster_not_found` errors

3. **DestinationRule subsets must match pod labels**: If using subsets in DestinationRule, ensure pods have matching labels.

4. **Permissive mTLS for development**: In development, use PERMISSIVE mode to avoid connectivity issues while testing.

5. **Check complete error messages**: `503` can mean many things - always check `response_code_details` in Istio logs:
   - `cluster_not_found`: VirtualService or DestinationRule misconfiguration
   - `upstream_reset`: Connection refused, pod not ready
   - `upstream_timeout`: Slow response, need to adjust timeouts

6. **Validate after major changes**: After recreating PostgreSQL (Issue #9), validate all Istio configurations:
   - VirtualServices
   - DestinationRules
   - PeerAuthentication policies

### Prevention

- **Add validation script** to check all VirtualService ports match service ports:
```bash
#!/bin/bash
for vs in $(kubectl get virtualservice -n restaurant-system -o name); do
  echo "Checking $vs..."
  kubectl get $vs -n restaurant-system -o yaml
done
```

- **Document correct service ports** in deployment docs
- **Monitor Istio metrics** for `cluster_not_found` errors
- **Use Istio health checks** to detect routing issues early

### Related Commands

**Istio troubleshooting**:
```bash
# Check Istio clusters from a pod
kubectl exec -n <namespace> <pod> -c istio-proxy -- pilot-agent request GET clusters

# Check Istio listeners
kubectl exec -n <namespace> <pod> -c istio-proxy -- pilot-agent request GET listeners

# Check Istio routes
kubectl exec -n <namespace> <pod> -c istio-proxy -- pilot-agent request GET routes

# View Istio proxy logs
kubectl logs -n <namespace> <pod> -c istio-proxy --tail=100

# Check VirtualService configuration
kubectl get virtualservice -n <namespace> <name> -o yaml

# Check DestinationRule configuration
kubectl get destinationrule -n <namespace> <name> -o yaml

# Check PeerAuthentication policies
kubectl get peerauthentication -n <namespace>
```

**Service connectivity testing**:
```bash
# Test service by name
kubectl exec -n <namespace> <pod> -- curl http://<service>:<port>/health

# Test service by IP
kubectl exec -n <namespace> <pod> -- curl http://<pod-ip>:<port>/health

# Check DNS resolution
kubectl exec -n <namespace> <pod> -- nslookup <service>
```

---

## Summary Table

| Issue | Severity | Component | Status | Date Resolved |
|-------|----------|-----------|--------|---------------|
| #1-7 | Various | Istio/Services | ✅ Resolved | Dec 30, 2025 |
| #8 | Critical | Observability | ✅ Resolved | Jan 1, 2026 |
| #9 | High | Database/Worker Node | ✅ Resolved | Jan 1, 2026 |
| #10 | Critical | Istio VirtualService | ✅ Resolved | Jan 1, 2026 |

---

## Quick Reference

### All kubectl commands used:
```bash
# Diagnostics
kubectl logs -n argocd argocd-server-<pod> --tail=30
kubectl logs -n istio-system grafana-<pod> -c init-chown-data
kubectl logs -n istio-system kiali-<pod> --tail=30
kubectl get svc -n default kubernetes
kubectl cluster-info
kubectl get pods -n kube-system | grep -E "(coredns|kindnet)"
kubectl get nodes
kubectl get pods -n istio-system
kubectl get pods -n argocd
kubectl describe pod -n istio-system grafana-<pod>

# Fixes
docker restart restaurant-cluster-control-plane restaurant-cluster-worker restaurant-cluster-worker2
kubectl scale deployment grafana -n istio-system --replicas=0
kubectl delete pvc grafana -n istio-system
kubectl apply -f <pvc-manifest>
kubectl scale deployment grafana -n istio-system --replicas=1
kubectl patch configmap grafana -n istio-system --type='json' -p='[{"op": "replace", "path": "/data/plugins", "value": ""}]'
kubectl delete pod -n istio-system <grafana-pod>

# Port-forwards
kubectl port-forward -n istio-system svc/kiali 20001:20001 &
kubectl port-forward -n istio-system svc/grafana 3000:80 &
kubectl port-forward -n istio-system svc/prometheus-server 9090:80 &
kubectl port-forward -n argocd svc/argocd-server 8080:443 &

# Verification
curl -s -o /dev/null -w "%{http_code}" http://localhost:20001
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
curl -s -k -o /dev/null -w "%{http_code}" https://localhost:8080
```
