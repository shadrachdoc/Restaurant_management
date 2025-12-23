# Known Issues & Solutions

This document tracks all known issues in the Restaurant Management System and their solutions.

---

## Table of Contents
- [Active Issues](#active-issues)
- [Resolved Issues](#resolved-issues)
- [Kubernetes Concepts](#kubernetes-concepts)
  - [Node Affinity Explained](#node-affinity-explained)
- [Common Problems](#common-problems)

---

## Active Issues

### None Currently

All known issues have been resolved. System is running smoothly.

---

## Resolved Issues

### Quick Reference

| # | Issue | Root Cause | Solution | Date |
|---|-------|------------|----------|------|
| 1 | [DNS Resolution Failures](#1-dns-resolution-failures-in-kind-cluster--resolved) | Worker node has intermittent DNS issues | Node affinity to worker2 | 2025-12-23 |
| 2 | [Master Admin CRUD Missing](#2-master-admin-dashboard-missing-crud-controls--resolved) | Frontend component lacked controls | Added CRUD buttons & modals | 2025-12-23 |
| 3 | [ArgoCD Pods Failing](#3-argocd-pods-failing-to-start--resolved) | Worker node can't reach K8s API | Removed node affinity | 2025-12-23 |
| 4 | [Ingress Not Accessible](#4-ingress-not-accessible-in-browser--resolved) | Missing /etc/hosts entries | Added host entries | 2025-12-23 |
| 5 | [CI/CD Pipeline Complex](#5-cicd-pipeline-too-complex--resolved) | Too many cluster management steps | Simplified to build + ArgoCD | 2025-12-23 |
| 6 | [RabbitMQ Restarting](#6-rabbitmq-pod-constantly-restarting--resolved) | Probes timeout before startup | Increased probe delays | 2025-12-23 |
| 7 | [Localhost Not Working](#7-frontend-not-accessible-via-localhost-kind-cluster--resolved) | Ingress on wrong node | hostNetwork + control-plane affinity + toleration | 2025-12-23 |

---

### 1. DNS Resolution Failures in KIND Cluster ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed via Node Affinity
**Severity**: High

#### Problem
Application services (auth-service, order-service, restaurant-service) were crashing with DNS resolution errors when scheduled on the `worker` node.

**Error Message**:
```
socket.gaierror: [Errno -3] Temporary failure in name resolution
ERROR: Application startup failed. Exiting.
```

**Full Error Stack**:
```python
File "/usr/local/lib/python3.11/site-packages/asyncpg/connect_utils.py", line 873, in __connect_addr
    tr, pr = await connector
socket.gaierror: [Errno -3] Temporary failure in name resolution

ERROR: Application startup failed. Exiting.
```

#### Root Cause Analysis

**Investigation Results**:

1. **DNS Configuration Check**
   - Both worker nodes had identical `/etc/resolv.conf` configuration
   - CoreDNS pods running on control-plane node
   - DNS service IP: `10.96.0.10`

2. **Node-Specific Testing**
   ```bash
   # Test from worker node - FAILED (intermittent)
   kubectl exec -n restaurant-system <pod-on-worker> -- getent hosts postgres-service

   # Test from worker2 node - SUCCESS
   kubectl exec -n restaurant-system <pod-on-worker2> -- getent hosts postgres-service
   ```

3. **Pod Distribution**
   - Failing pods: All on `restaurant-cluster-worker`
   - Working pods: All on `restaurant-cluster-worker2`

**Root Cause**: The `restaurant-cluster-worker` node has **intermittent DNS resolution issues** in the KIND cluster environment. This is likely due to:
- Timing issues during pod startup
- Network race conditions in KIND's Docker bridge networking
- Occasional connectivity issues between worker node and CoreDNS on control-plane

#### Solution: Node Affinity

Applied **Node Affinity** to force database-dependent services onto `worker2` node where DNS is reliable.

**YAML Configuration**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - restaurant-cluster-worker2
```

**Commands Used**:
```bash
# Auth Service
kubectl patch deployment auth-service -n restaurant-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/affinity",
    "value": {
      "nodeAffinity": {
        "requiredDuringSchedulingIgnoredDuringExecution": {
          "nodeSelectorTerms": [{
            "matchExpressions": [{
              "key": "kubernetes.io/hostname",
              "operator": "In",
              "values": ["restaurant-cluster-worker2"]
            }]
          }]
        }
      }
    }
  }
]'

# Order Service
kubectl patch deployment order-service -n restaurant-system --type='json' -p='[...]'

# Restaurant Service
kubectl patch deployment restaurant-service -n restaurant-system --type='json' -p='[...]'
```

#### Results

**Before Fix**:
```
NAME                                  READY   STATUS             AGE
auth-service-6c978565db-nn2pr         0/1     CrashLoopBackOff   2d13h
order-service-56ddd5bbf8-r9497        0/1     CrashLoopBackOff   37h
restaurant-service-746794b477-2s6fr   0/1     CrashLoopBackOff   16h
```

**After Fix**:
```
NAME                                  READY   STATUS    AGE     NODE
auth-service-5bfbd779d6-q9fsz         1/1     Running   48s     restaurant-cluster-worker2
auth-service-5bfbd779d6-xl5tr         1/1     Running   33s     restaurant-cluster-worker2
order-service-5d6c77459d-zhgpc        1/1     Running   48s     restaurant-cluster-worker2
restaurant-service-7cb9548785-lwkck   1/1     Running   31s     restaurant-cluster-worker2
restaurant-service-7cb9548785-rjzd4   1/1     Running   47s     restaurant-cluster-worker2
```

**Deployment Status**:
```
NAME                 READY   UP-TO-DATE   AVAILABLE
auth-service         2/2     2            2           ✅
order-service        1/1     1            1           ✅
restaurant-service   2/2     2            2           ✅
```

**Affected Services**:
- ✅ auth-service (2/2 replicas running)
- ✅ order-service (1/1 replica running)
- ✅ restaurant-service (2/2 replicas running)

**Result**: All services running with 100% availability.

#### Node Placement Strategy

| Node | K8s API Access | DNS Reliability | Services Assigned |
|------|---------------|-----------------|-------------------|
| **control-plane** | ✅ | ✅ | CoreDNS, kube-system |
| **worker2** | ✅ | ✅ | auth, order, restaurant, frontend, redis |
| **worker** | ❌ | ⚠️ Intermittent | postgres, rabbitmq, api-gateway |

**Why This Distribution Works**:
- **Database services (postgres, rabbitmq)** run on `worker` node
  - They don't need to resolve hostnames (they ARE the endpoints)
  - Other services connect TO them, not FROM them
- **Application services** run on `worker2` node
  - Need to resolve database hostnames (postgres-service, redis-service, etc.)
  - Require reliable DNS for database connections

#### Alternative Solutions Considered

1. **✅ Node Affinity (IMPLEMENTED)**
   - **Pros**: Immediate fix, no code changes, works with KIND limitations
   - **Cons**: Reduces scheduling flexibility
   - **Verdict**: Best solution for KIND environment

2. **Increase Probe Delays**
   ```yaml
   livenessProbe:
     initialDelaySeconds: 60  # Increase from 30
   readinessProbe:
     initialDelaySeconds: 30  # Increase from 10
   ```
   - **Pros**: Simple YAML change, handles timing issues
   - **Cons**: Slower pod startup
   - **Verdict**: Good complementary solution

3. **Application-Level Retry Logic**
   ```python
   def create_db_engine_with_retry(database_url, max_retries=5):
       for attempt in range(max_retries):
           try:
               engine = create_engine(database_url)
               with engine.connect() as conn:
                   conn.execute("SELECT 1")
               return engine
           except OperationalError as e:
               if "name resolution" in str(e) and attempt < max_retries - 1:
                   wait_time = 2 ** attempt
                   time.sleep(wait_time)
               else:
                   raise
   ```
   - **Pros**: Robust, handles transient failures anywhere
   - **Cons**: Requires code changes in all services
   - **Verdict**: Recommended for production environments

4. **Restart CoreDNS**
   ```bash
   kubectl rollout restart deployment coredns -n kube-system
   ```
   - **Pros**: Quick temporary fix
   - **Cons**: Issue may recur
   - **Verdict**: Not a permanent solution

5. **Rebuild KIND Cluster with DNS Config**
   - **Pros**: Proper cluster-wide fix
   - **Cons**: Requires full cluster rebuild
   - **Verdict**: Too disruptive for running system

6. **NodeLocal DNSCache**
   ```bash
   kubectl apply -f https://k8s.io/examples/admin/dns/nodelocaldns.yaml
   ```
   - **Pros**: Better DNS performance and reliability
   - **Cons**: Complex setup, more components
   - **Verdict**: Overkill for 3-node KIND cluster

#### DNS Verification Commands

**Check DNS Resolution in Pod**:
```bash
# Method 1: Using getent
kubectl exec -n restaurant-system <pod-name> -- getent hosts postgres-service

# Method 2: Using nslookup (if available)
kubectl exec -n restaurant-system <pod-name> -- nslookup postgres-service.restaurant-system.svc.cluster.local

# Method 3: Check /etc/resolv.conf
kubectl exec -n restaurant-system <pod-name> -- cat /etc/resolv.conf
```

Expected `/etc/resolv.conf`:
```
search restaurant-system.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

**Test DNS from Specific Node**:
```bash
kubectl run -it --rm debug-worker \
  --image=nicolaka/netshoot \
  --overrides='{"spec": {"nodeSelector": {"kubernetes.io/hostname": "restaurant-cluster-worker"}}}' \
  --restart=Never \
  -- nslookup postgres-service.restaurant-system.svc.cluster.local
```

**Check CoreDNS Status**:
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

#### Production Recommendations

When moving to production (EKS, GKE, AKS, etc.), consider:
1. **Remove node affinity** - Not needed in production clusters with reliable DNS
2. **Add retry logic** - Implement application-level retry for resilience
3. **Monitor DNS metrics** - Track DNS resolution latency and failures
4. **Use NodeLocal DNSCache** - For high-traffic clusters
5. **Increase probe delays** - Give services more time to start up

---

### 2. Master Admin Dashboard Missing CRUD Controls ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed
**Severity**: Medium

#### Problem
The Master Admin dashboard at `/master-admin` displayed restaurant data but had no buttons to Create, Edit, or Delete restaurants.

#### Solution
Added complete CRUD functionality to [MasterAdminDashboard.jsx](frontend/src/pages/MasterAdmin/MasterAdminDashboard.jsx):
- Create Restaurant button
- Edit button for each restaurant row
- Delete button with confirmation dialog
- Modal form for create/edit operations
- Toast notifications for success/error feedback

**Actions Taken**:
1. Updated React component with CRUD handlers
2. Built new frontend Docker image
3. Loaded image into KIND cluster
4. Restarted frontend pods
5. Instructed user to hard-refresh browser (Ctrl+Shift+R)

---

### 3. ArgoCD Pods Failing to Start ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed
**Severity**: Critical

#### Problem
ArgoCD server, redis, and repo-server pods were in CrashLoopBackOff state.

**Error**: `dial tcp 10.96.0.1:443: connect: no route to host`

#### Root Cause
ArgoCD pods were previously patched to run on `worker` node for DNS fix, but that node cannot reach the Kubernetes API server (10.96.0.1:443).

#### Solution
Removed node affinity patches to allow ArgoCD to return to `worker2` node:
```bash
kubectl patch deployment argocd-server -n argocd --type json \
  -p='[{"op": "remove", "path": "/spec/template/spec/affinity"}]'
```

**Result**: All ArgoCD services running on worker2 where they can access K8s API.

---

### 4. Ingress Not Accessible in Browser ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed
**Severity**: Low

#### Problem
User couldn't access `http://restaurant.local:8080/` in browser despite Ingress working correctly.

#### Root Cause
Missing `/etc/hosts` entries for local domain resolution.

#### Solution
Added hosts entries:
```bash
echo "127.0.0.1 restaurant.local api.restaurant.local orders.restaurant.local restaurants.restaurant.local auth.restaurant.local" | sudo tee -a /etc/hosts
```

**Verification**: All Ingress routes returning HTTP 200 via curl.

---

### 5. CI/CD Pipeline Too Complex ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Simplified
**Severity**: Low

#### Problem
Pipeline was trying to create KIND cluster, check cluster status, create namespaces, and deploy with kubectl on every run.

#### Solution
Simplified [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) to just:
1. Build Docker images
2. Load images into KIND cluster
3. Let ArgoCD handle deployment

**Result**: Clean 3-step pipeline, no cluster management, ArgoCD-driven deployments.

---

## Kubernetes Concepts

### Node Affinity Explained

**Node Affinity** is a Kubernetes scheduling feature that lets you control which nodes your pods run on.

#### Why Use Node Affinity?

In our case, we use it to avoid nodes with DNS issues:
- `worker` node: DNS problems → Don't schedule database-dependent services here
- `worker2` node: DNS works → Schedule all application services here

#### Types of Node Affinity

| Type | Description | Behavior |
|------|-------------|----------|
| **requiredDuringScheduling** | HARD constraint | Pod MUST match, or stays Pending |
| **preferredDuringScheduling** | SOFT constraint | Kubernetes tries to match, falls back if not possible |
| **IgnoredDuringExecution** | After scheduling | Existing pods NOT evicted if node labels change |

#### Syntax

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          # HARD constraint - pod MUST run on this node
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              # Match based on node label
              - key: kubernetes.io/hostname
                operator: In
                values:
                - restaurant-cluster-worker2

          # SOFT constraint - Kubernetes PREFERS this node
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: disk-type
                operator: In
                values:
                - ssd
```

#### Common Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `In` | Label value in list | `values: [worker2, worker3]` |
| `NotIn` | Label value NOT in list | Avoid certain nodes |
| `Exists` | Label key exists (any value) | Check for label presence |
| `DoesNotExist` | Label key doesn't exist | Ensure label absent |
| `Gt` | Greater than (numbers) | `key: cpu-count, value: "8"` |
| `Lt` | Less than (numbers) | `key: memory, value: "16"` |

#### Real-World Examples

**Example 1: GPU Workloads**
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: gpu
          operator: Exists
```

**Example 2: Avoid Specific Nodes**
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: NotIn
          values:
          - broken-node-1
          - broken-node-2
```

**Example 3: Multi-Zone Deployment**
```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values:
          - us-east-1a
```

#### Our Implementation

We use `requiredDuringSchedulingIgnoredDuringExecution` with hostname matching:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - restaurant-cluster-worker2
```

This means:
- ✅ Pods MUST schedule on `worker2`
- ❌ Pods will NOT schedule on `worker` or other nodes
- ⏳ If `worker2` is unavailable, pods stay Pending
- 🔒 After scheduling, pods stay even if node labels change

#### Check Node Labels

```bash
# List all node labels
kubectl get nodes --show-labels

# Get specific node labels
kubectl describe node restaurant-cluster-worker2

# Add custom label to node
kubectl label nodes restaurant-cluster-worker2 disktype=ssd

# Remove label from node
kubectl label nodes restaurant-cluster-worker2 disktype-
```

#### View Pod Node Assignment

```bash
# See which node each pod is on
kubectl get pods -n restaurant-system -o wide

# Check pod's node affinity config
kubectl get pod <pod-name> -n restaurant-system -o yaml | grep -A 20 "affinity:"
```

#### Remove Node Affinity

```bash
kubectl patch deployment <service-name> -n restaurant-system --type json \
  -p='[{"op": "remove", "path": "/spec/template/spec/affinity"}]'
```

#### Node Affinity vs NodeSelector vs Taints/Tolerations

| Feature | Complexity | Use Case |
|---------|-----------|----------|
| **NodeSelector** | Simple | Basic node selection by labels |
| **Node Affinity** | Medium | Complex selection with AND/OR logic |
| **Taints/Tolerations** | Medium | Prevent pods from scheduling (opposite approach) |

**NodeSelector** (Simple):
```yaml
spec:
  nodeSelector:
    disktype: ssd
```

**Node Affinity** (Our approach):
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values: [ssd, nvme]
```

**Taints/Tolerations** (Opposite approach):
```yaml
# On Node: Prevent pods from scheduling
kubectl taint nodes worker dns-broken=true:NoSchedule

# On Pod: Allow this pod on tainted node
spec:
  tolerations:
  - key: dns-broken
    operator: Exists
    effect: NoSchedule
```

---

### 6. RabbitMQ Pod Constantly Restarting ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed
**Severity**: High

#### Problem
RabbitMQ pod was stuck in CrashLoopBackOff with 15+ restarts. Pod status showed 0/1 ready.

**Symptoms**:
```
NAME         READY   STATUS             RESTARTS   AGE
rabbitmq-0   0/1     CrashLoopBackOff   16         7h
```

**Error Messages**:
- Liveness probe failed: timeout after 10s
- Readiness probe failed: timeout after 10s

#### Root Cause Analysis

**Investigation**:
1. Checked RabbitMQ logs and found it takes ~80 seconds to fully initialize
2. Probe configuration had `initialDelaySeconds: 30s` and `timeoutSeconds: 10s`
3. Probes were timing out before RabbitMQ finished starting up
4. Pod was being killed and restarted before it could become ready

**Timeline**:
- 0-30s: RabbitMQ starting up
- 30s: Readiness probe starts checking
- 40s: Probe times out (30s + 10s timeout)
- Pod marked as failed and restarted
- Never reaches 80s when RabbitMQ would be ready

#### Solution

Updated [infrastructure/kubernetes/rabbitmq-statefulset.yaml](infrastructure/kubernetes/rabbitmq-statefulset.yaml) with increased probe timings:

```yaml
livenessProbe:
  exec:
    command:
    - rabbitmq-diagnostics
    - ping
  initialDelaySeconds: 90  # Increased from 60s
  periodSeconds: 30
  timeoutSeconds: 20       # Increased from 10s
  failureThreshold: 6      # Added

readinessProbe:
  exec:
    command:
    - rabbitmq-diagnostics
    - ping
  initialDelaySeconds: 90  # Increased from 30s
  periodSeconds: 15
  timeoutSeconds: 20       # Increased from 10s
  failureThreshold: 3      # Added
```

**Key Changes**:
- `initialDelaySeconds`: 30s → 90s (gives RabbitMQ time to start)
- `timeoutSeconds`: 10s → 20s (allows probe command more time)
- Added `failureThreshold`: Allows multiple failures before restart

#### Results

**Before Fix**:
```
NAME         READY   STATUS             RESTARTS
rabbitmq-0   0/1     CrashLoopBackOff   16
```

**After Fix**:
```
NAME         READY   STATUS    RESTARTS
rabbitmq-0   1/1     Running   0
```

RabbitMQ now starts cleanly and stays healthy without any restarts.

---

### 7. Frontend Not Accessible via Localhost (KIND Cluster) ✅ RESOLVED

**Date**: 2025-12-23
**Status**: Fixed
**Severity**: High

#### Problem
Frontend application was not accessible via `http://localhost/` despite all pods running. User received connection errors in browser.

**Symptoms**:
- Browser: `ERR_CONNECTION_REFUSED` or `404 Not Found nginx`
- Port-forward worked: `kubectl port-forward svc/frontend 9090:80`
- All pods healthy and running (1/1)
- ArgoCD showing Synced status

#### Root Cause Analysis

**Investigation Timeline**:

1. **Initial Check**: Verified all pods were running
   ```bash
   kubectl get pods -n restaurant-system
   # All pods showing 1/1 Running
   ```

2. **Ingress Controller Investigation**:
   - Found ingress-nginx-controller running on `restaurant-cluster-worker` node
   - KIND cluster port mapping (0.0.0.0:80→80/tcp) configured on `control-plane` node
   - **Mismatch**: Traffic to localhost:80 goes to control-plane, but ingress was on worker

3. **Attempted Solutions**:

   **Attempt 1: Changed Service Type to NodePort**
   ```bash
   kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"NodePort"}}'
   ```
   - Result: NodePort assigned (30986) but still not accessible via localhost:80
   - Issue: NodePort doesn't match KIND port mapping expectations

   **Attempt 2: Tried Direct NodePort Access**
   ```bash
   curl http://localhost:30986/
   ```
   - Result: Connection refused
   - Issue: NodePort on worker node not mapped in KIND

   **Attempt 3: Enabled hostNetwork on Worker Node**
   ```bash
   kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
     --type=json -p='[{"op": "add", "path": "/spec/template/spec/hostNetwork", "value": true}]'
   ```
   - Result: Ingress bound to worker node IP (172.18.0.2)
   - Direct connection worked: `curl -H "Host: restaurant.local" http://172.18.0.2/` → 200
   - Issue: localhost:80 still not working (port mapping on different node)

   **Attempt 4: Move to Control-Plane with Node Affinity**
   ```bash
   kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
     --type=json -p='[{"op": "replace", "path": "/spec/template/spec/affinity/..."}]'
   ```
   - Result: Pod stayed Pending
   - Error: `0/3 nodes available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane}`
   - Issue: Control-plane has taint preventing pod scheduling

#### Final Solution

Added both node affinity to target control-plane AND toleration for the control-plane taint:

```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type=json -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/affinity/nodeAffinity/requiredDuringSchedulingIgnoredDuringExecution/nodeSelectorTerms/0/matchExpressions/0/values/0",
    "value": "restaurant-cluster-control-plane"
  },
  {
    "op": "add",
    "path": "/spec/template/spec/tolerations",
    "value": [
      {
        "key": "node-role.kubernetes.io/control-plane",
        "operator": "Exists",
        "effect": "NoSchedule"
      }
    ]
  }
]'
```

**Configuration Applied**:
```yaml
spec:
  template:
    spec:
      hostNetwork: true  # Bind directly to node's port 80
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - restaurant-cluster-control-plane  # Schedule on control-plane
      tolerations:  # Allow scheduling on control-plane despite taint
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
```

#### Why This Works

**KIND Cluster Architecture**:
```
Host Machine (localhost)
  ↓ Docker port mapping (0.0.0.0:80 → 80/tcp)
Control-Plane Container (172.18.0.3)
  ↓ hostNetwork: true
Ingress Controller Pod (binds to node's port 80)
  ↓ Ingress routing
Application Pods (frontend, services)
```

**Key Components**:
1. **hostNetwork: true**: Ingress controller binds directly to node's port 80 (not ClusterIP)
2. **Node Affinity**: Ensures pod runs on control-plane node
3. **Toleration**: Allows scheduling on control-plane despite NoSchedule taint
4. **KIND Port Mapping**: localhost:80 → control-plane:80
5. **Result**: localhost:80 → control-plane:80 → ingress-nginx → frontend

#### Verification Steps

1. **Check Ingress Pod Location**:
   ```bash
   kubectl get pods -n ingress-nginx -o wide
   ```
   Output:
   ```
   NAME                                        READY   STATUS    NODE
   ingress-nginx-controller-875b9684b-sxb84    1/1     Running   restaurant-cluster-control-plane
   ```

2. **Verify hostNetwork IP**:
   Pod IP matches control-plane node IP (172.18.0.3)

3. **Test Localhost Access**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" -H "Host: restaurant.local" http://localhost/
   # Output: 200
   ```

4. **Test in Browser**:
   - Navigate to `http://localhost/`
   - Frontend loads successfully

#### Results

**Before Fix**:
- ❌ localhost:80 → Connection refused
- ✅ Port-forward worked (workaround only)
- ✅ Direct IP access worked (172.18.0.2)

**After Fix**:
- ✅ localhost:80 → Frontend accessible
- ✅ No port-forward needed
- ✅ Stable environment for development

#### All Attempted Solutions Summary

| Attempt | Action | Result | Why It Failed |
|---------|--------|--------|---------------|
| 1 | Change service to NodePort | Failed | NodePort (30986) doesn't match KIND mapping (80) |
| 2 | Access via NodePort directly | Failed | Worker node NodePort not exposed by KIND |
| 3 | Enable hostNetwork on worker | Partial | Works via IP but not localhost (wrong node) |
| 4 | Move to control-plane (affinity only) | Failed | Control-plane taint blocks scheduling |
| 5 | Add toleration + affinity + hostNetwork | ✅ Success | All pieces aligned correctly |

#### KIND-Specific Notes

This issue is specific to KIND (Kubernetes in Docker) clusters:

**Why KIND is Different**:
- Nodes are Docker containers, not VMs
- Port mappings configured at container creation time
- Only control-plane container has host port mappings
- Worker nodes don't expose ports to host

**KIND Port Mapping** (configured at cluster creation):
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
```

**Production vs KIND**:
- **Production (EKS/GKE/AKS)**: LoadBalancer service gets real external IP
- **KIND**: Must use hostNetwork + port mapping to expose services

#### Lessons Learned

1. **KIND requires ingress on control-plane** for localhost access
2. **hostNetwork mode** is essential for KIND ingress controllers
3. **Control-plane taints** must be tolerated to schedule ingress there
4. **Port mappings** are defined at cluster creation, can't be changed later
5. **NodePort alone doesn't work** in KIND without explicit port mapping

#### Alternative Solutions for KIND

**Option 1: Use Port-Forward** (temporary):
```bash
kubectl port-forward -n restaurant-system svc/frontend 8080:80
# Access at http://localhost:8080
```

**Option 2: Recreate Cluster with Ingress** (destructive):
```bash
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
EOF
```

**Option 3: Our Solution** (non-destructive):
- Patch existing ingress deployment
- Enable hostNetwork
- Move to control-plane with toleration

#### Commands for Future Reference

**Check KIND Port Mappings**:
```bash
docker ps --filter "name=control-plane"
docker port <cluster-name>-control-plane
```

**Check Node Taints**:
```bash
kubectl get nodes -o json | jq '.items[].spec.taints'
```

**Remove Toleration** (if needed):
```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type json \
  -p='[{"op": "remove", "path": "/spec/template/spec/tolerations"}]'
```

**Disable hostNetwork** (if needed):
```bash
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type json \
  -p='[{"op": "remove", "path": "/spec/template/spec/hostNetwork"}]'
```

---

## Common Problems

### Pod Stuck in Pending State

**Possible Causes**:
1. Node affinity constraints not satisfied
2. Insufficient resources on target node
3. Node not ready

**Debug**:
```bash
kubectl describe pod <pod-name> -n restaurant-system
kubectl get nodes
kubectl top nodes
```

### Service Cannot Resolve Other Services

**Symptoms**: DNS errors, connection timeouts

**Check**:
1. CoreDNS running: `kubectl get pods -n kube-system -l k8s-app=kube-dns`
2. Pod DNS config: `kubectl exec <pod> -- cat /etc/resolv.conf`
3. Test DNS: `kubectl exec <pod> -- nslookup postgres-service`

### Images Not Updating After Build

**Cause**: `imagePullPolicy: IfNotPresent` with same tag

**Solutions**:
1. Delete old pods: `kubectl delete pod <pod-name>`
2. Rollout restart: `kubectl rollout restart deployment <name>`
3. Use unique tags: `image: myservice:v1.2.3` instead of `:latest`

### ArgoCD Not Auto-Syncing

**Check**:
1. ArgoCD app status: `kubectl get applications -n argocd`
2. Git repo accessible: Check ArgoCD logs
3. Sync policy: `kubectl get application restaurant-management -n argocd -o yaml | grep syncPolicy`

---

## Getting Help

### Logs and Debugging

```bash
# Service logs
kubectl logs -n restaurant-system <pod-name>

# Previous crash logs
kubectl logs -n restaurant-system <pod-name> --previous

# Follow logs in real-time
kubectl logs -n restaurant-system <pod-name> -f

# Describe pod (shows events)
kubectl describe pod <pod-name> -n restaurant-system

# Shell into pod
kubectl exec -it <pod-name> -n restaurant-system -- /bin/sh
```

### Health Checks

```bash
# All pods status
kubectl get pods -n restaurant-system

# Deployment status
kubectl get deployments -n restaurant-system

# Service endpoints
kubectl get endpoints -n restaurant-system

# Ingress status
kubectl get ingress -n restaurant-system
```

### System Status

```bash
# Node status
kubectl get nodes -o wide

# Cluster info
kubectl cluster-info

# Resource usage
kubectl top nodes
kubectl top pods -n restaurant-system
```

---

## Reporting New Issues

When reporting issues, include:

1. **Error message** (full stack trace if available)
2. **Pod logs**: `kubectl logs <pod-name> -n restaurant-system`
3. **Pod status**: `kubectl describe pod <pod-name> -n restaurant-system`
4. **Deployment config**: `kubectl get deployment <name> -o yaml`
5. **Node info**: `kubectl get pods -o wide`
6. **Steps to reproduce**

---

**Last Updated**: 2025-12-23
**Document Owner**: DevOps Team
**Next Review**: Monthly or when new issues discovered
