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
