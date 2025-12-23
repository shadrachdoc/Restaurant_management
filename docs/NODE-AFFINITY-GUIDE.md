# Node Affinity Quick Reference Guide

A practical guide to understanding and using Kubernetes Node Affinity in the Restaurant Management System.

---

## What is Node Affinity?

Node Affinity is like saying: **"I want my pod to run ONLY on specific nodes"** or **"I PREFER my pod to run on specific nodes"**.

Think of it as:
- 🏠 **Hotel Booking**: You can REQUEST a room on a specific floor (soft constraint)
- 🔒 **Reserved Seating**: You can REQUIRE a specific seat (hard constraint)

---

## Our Use Case

### The Problem
```
worker node  → DNS broken ❌ → Services can't find database
worker2 node → DNS works ✅  → Services run perfectly
```

### The Solution
Use Node Affinity to tell Kubernetes:
> "Hey Kubernetes, please ONLY schedule auth-service, order-service, and restaurant-service on worker2 node!"

---

## Two Types of Node Affinity

### 1. Required (HARD Constraint) 🔴
**"Pod MUST run here, or don't run at all"**

```yaml
requiredDuringSchedulingIgnoredDuringExecution
```

**Behavior**:
- Pod will ONLY schedule on matching nodes
- If no match found → Pod stays in Pending state forever
- Use when: Node requirement is critical (like our DNS issue)

**Example**:
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

**Result**: Pod will ONLY run on worker2, never anywhere else.

---

### 2. Preferred (SOFT Constraint) 🟡
**"I'd like pod to run here, but it's okay if it runs elsewhere"**

```yaml
preferredDuringSchedulingIgnoredDuringExecution
```

**Behavior**:
- Kubernetes tries to schedule on matching nodes
- If not available → Falls back to other nodes
- Use when: Preference is nice-to-have, not critical

**Example**:
```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 80  # Priority 0-100
      preference:
        matchExpressions:
        - key: disktype
          operator: In
          values:
          - ssd
```

**Result**: Pod prefers SSD nodes, but will run on HDD if SSD unavailable.

---

## Common Match Operators

| Operator | Meaning | Example Use Case |
|----------|---------|------------------|
| `In` | Value is in list | `values: [worker2, worker3]` - Run on these nodes |
| `NotIn` | Value NOT in list | `values: [worker1]` - Avoid this node |
| `Exists` | Label exists (any value) | `key: gpu` - Any node with GPU |
| `DoesNotExist` | Label doesn't exist | Ensure node doesn't have certain capability |
| `Gt` | Greater than (numbers) | `key: cpu-count, value: "16"` - Powerful nodes |
| `Lt` | Less than (numbers) | `key: memory, value: "8"` - Small nodes |

---

## Real-World Examples

### Example 1: GPU Workloads (ML/AI)
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: gpu-type
          operator: In
          values:
          - nvidia-a100
          - nvidia-v100
```
**Use Case**: TensorFlow training job needs powerful GPUs.

---

### Example 2: Avoid Unhealthy Nodes
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
**Use Case**: Temporarily avoid nodes with known issues.

---

### Example 3: Multi-Zone High Availability
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
    - weight: 50
      preference:
        matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values:
          - us-east-1b
```
**Use Case**: Prefer us-east-1a zone, fallback to us-east-1b.

---

### Example 4: High Memory Applications
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - m5.8xlarge
          - m5.16xlarge
```
**Use Case**: Database that needs lots of RAM.

---

### Example 5: Development vs Production
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: environment
          operator: In
          values:
          - production
```
**Use Case**: Keep prod workloads separate from dev/staging.

---

## How to Apply Node Affinity

### Method 1: In Deployment YAML

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
      containers:
      - name: auth-service
        image: auth-service:latest
```

Then apply:
```bash
kubectl apply -f auth-service-deployment.yaml
```

---

### Method 2: Using kubectl patch (Our Method)

```bash
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
```

**Pros**: Quick fix without editing YAML files.

---

## Checking Node Affinity

### View Node Labels
```bash
# All nodes with labels
kubectl get nodes --show-labels

# Specific node
kubectl describe node restaurant-cluster-worker2

# Just hostnames
kubectl get nodes -o jsonpath='{.items[*].metadata.name}'
```

### View Pod's Node Affinity
```bash
# From deployment
kubectl get deployment auth-service -n restaurant-system -o yaml | grep -A 20 "affinity:"

# From pod
kubectl get pod auth-service-xxx -n restaurant-system -o yaml | grep -A 20 "affinity:"
```

### See Pod Placement
```bash
# Which node is each pod on?
kubectl get pods -n restaurant-system -o wide

# Filter by node
kubectl get pods -n restaurant-system -o wide | grep worker2
```

---

## Removing Node Affinity

### Remove from Deployment
```bash
kubectl patch deployment auth-service -n restaurant-system --type json \
  -p='[{"op": "remove", "path": "/spec/template/spec/affinity"}]'
```

### Edit Directly
```bash
kubectl edit deployment auth-service -n restaurant-system
# Then delete the affinity section and save
```

---

## Combining with Other Scheduling Features

### Node Affinity + Pod Anti-Affinity
**Use Case**: Spread replicas across different zones

```yaml
affinity:
  # Run on specific instance types
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - m5.large

  # Don't put replicas on same node
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - auth-service
      topologyKey: kubernetes.io/hostname
```

---

## Troubleshooting

### Pod Stuck in Pending
**Symptom**: Pod never starts

**Check**:
```bash
kubectl describe pod <pod-name> -n restaurant-system
```

**Look for**:
```
Events:
  Warning  FailedScheduling  ... no nodes available to schedule pods
```

**Cause**: Node affinity constraint can't be satisfied

**Solutions**:
1. Check if target node exists: `kubectl get nodes`
2. Check node labels match: `kubectl describe node <node-name>`
3. Relax constraint: Change `required` to `preferred`
4. Remove affinity: See "Removing Node Affinity" section

---

### Pod Scheduled on Wrong Node
**Check current affinity**:
```bash
kubectl get deployment <name> -n restaurant-system -o yaml | grep -A 20 "affinity:"
```

**If no affinity shown**: It hasn't been applied yet

**If affinity exists but wrong node**: Pods created before affinity was added

**Solution**: Delete old pods
```bash
kubectl delete pod <pod-name> -n restaurant-system
# Kubernetes will create new pod with correct affinity
```

---

## Best Practices

### ✅ DO:
- Use `required` for critical constraints (like our DNS issue)
- Use `preferred` for performance optimizations
- Label nodes meaningfully: `disktype=ssd`, `gpu=true`, `region=us-west`
- Document why affinity is needed
- Test affinity rules in dev before production

### ❌ DON'T:
- Overuse `required` - reduces scheduling flexibility
- Hardcode node names in production (use labels instead)
- Forget to remove temporary affinity rules
- Use affinity for what taints/tolerations do better
- Ignore warning events when pods stay Pending

---

## Node Affinity vs Alternatives

| Feature | Best For | Complexity |
|---------|----------|-----------|
| **NodeSelector** | Simple label matching | Low |
| **Node Affinity** | Complex rules with AND/OR logic | Medium |
| **Taints/Tolerations** | Preventing pods from scheduling | Medium |
| **Pod Affinity** | Co-locate pods together | High |
| **Topology Spread** | Even distribution across zones | High |

---

## Quick Reference Commands

```bash
# List all node labels
kubectl get nodes --show-labels

# Add label to node
kubectl label nodes worker2 disktype=ssd

# Remove label from node
kubectl label nodes worker2 disktype-

# Check which node pod is on
kubectl get pods -n restaurant-system -o wide

# View deployment's affinity config
kubectl get deployment auth-service -n restaurant-system -o yaml | grep -A 20 affinity

# Patch deployment with node affinity
kubectl patch deployment <name> -n restaurant-system --type='json' -p='[...]'

# Remove node affinity
kubectl patch deployment <name> -n restaurant-system --type json -p='[{"op":"remove","path":"/spec/template/spec/affinity"}]'

# Force pod to reschedule (delete old pod)
kubectl delete pod <pod-name> -n restaurant-system
```

---

## Further Reading

- [Kubernetes Official Docs - Affinity and Anti-Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)
- [Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)
- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)

---

**Last Updated**: 2025-12-23
**Related Documents**:
- [ISSUES.md](../ISSUES.md) - Known issues and solutions
- [DNS-ISSUE.md](DNS-ISSUE.md) - DNS resolution problem details
