# Documentation Index

This folder contains detailed technical documentation for the Restaurant Management System.

---

## 📚 Available Documents

### 🔴 Critical Issues & Troubleshooting
- **[../ISSUES.md](../ISSUES.md)** - All known issues and their solutions
  - DNS resolution failure (resolved via Node Affinity)
  - Master Admin CRUD controls (resolved)
  - ArgoCD pods failing (resolved)
  - Ingress browser access (resolved)
  - CI/CD pipeline optimization (resolved)

### 📖 Kubernetes Concepts
- **[NODE-AFFINITY-GUIDE.md](NODE-AFFINITY-GUIDE.md)** - Comprehensive guide to Node Affinity
  - What is Node Affinity and why use it
  - Required vs Preferred constraints
  - Real-world examples
  - How to apply and remove
  - Troubleshooting tips
  - Quick reference commands

---

## 🚀 Getting Started

### New to the Project?
1. Start with [../STARTUP.md](../STARTUP.md) - System setup and configuration
2. Read [../ISSUES.md](../ISSUES.md) - All issues, solutions, and troubleshooting
3. Check [NODE-AFFINITY-GUIDE.md](NODE-AFFINITY-GUIDE.md) - Understanding node placement

### Need to Use Node Affinity?
1. Read [NODE-AFFINITY-GUIDE.md](NODE-AFFINITY-GUIDE.md) - Complete guide
2. See practical examples in [../ISSUES.md](../ISSUES.md) - DNS issue section
3. Reference quick commands in [NODE-AFFINITY-GUIDE.md](NODE-AFFINITY-GUIDE.md)

### Troubleshooting Issues?
1. Check [../ISSUES.md](../ISSUES.md) - All issues with detailed solutions
2. Review DNS troubleshooting in [../ISSUES.md](../ISSUES.md#dns-verification-commands)
3. See debugging commands in [../ISSUES.md](../ISSUES.md#logs-and-debugging)

---

## 📝 Document Structure

```
docs/
├── README.md                    # This file - documentation index
├── NODE-AFFINITY-GUIDE.md       # Node Affinity tutorial
├── GETTING_STARTED.md           # Getting started guide
├── KUBERNETES.md                # Kubernetes setup
└── TESTING_RESTAURANT_SERVICE.md # Service testing

../
├── STARTUP.md                   # System startup guide (MAIN GUIDE)
├── ISSUES.md                    # All known issues and solutions (MAIN ISSUES)
├── CICD-SETUP.md               # CI/CD pipeline documentation
└── POSTMAN.md                  # API testing guide
```

---

## 🔍 Quick Links

### System Operations
- [System Startup](../STARTUP.md#-quick-start)
- [Port Forwarding](../STARTUP.md#-accessing-services)
- [Test Credentials](../STARTUP.md#-test-credentials)

### Kubernetes Operations
- [Node Affinity Commands](NODE-AFFINITY-GUIDE.md#quick-reference-commands)
- [DNS Troubleshooting](../ISSUES.md#dns-verification-commands)
- [Pod Debugging](../ISSUES.md#logs-and-debugging)

### CI/CD
- [Pipeline Overview](../CICD-SETUP.md)
- [Build and Deploy Process](../CICD-SETUP.md#workflow-details)
- [ArgoCD Setup](../CICD-SETUP.md#argocd-setup)

### API Testing
- [Postman Collection](../POSTMAN.md)
- [API Documentation URLs](../STARTUP.md#-api-documentation-swagger-ui)

---

## 🆘 Need Help?

### Common Scenarios

| Problem | See Document |
|---------|-------------|
| Pods failing with DNS errors | [ISSUES.md](../ISSUES.md#1-dns-resolution-failures-in-kind-cluster--resolved) |
| Need to schedule pods on specific nodes | [NODE-AFFINITY-GUIDE.md](NODE-AFFINITY-GUIDE.md) or [ISSUES.md](../ISSUES.md#node-affinity-explained) |
| Service not starting | [ISSUES.md](../ISSUES.md#common-problems) |
| ArgoCD not syncing | [ISSUES.md](../ISSUES.md#argocd-not-auto-syncing) |
| Images not updating | [ISSUES.md](../ISSUES.md#images-not-updating-after-build) |
| Cannot access Ingress | [ISSUES.md](../ISSUES.md#4-ingress-not-accessible-in-browser--resolved) |

### Debug Commands

```bash
# Check pod status and node placement
kubectl get pods -n restaurant-system -o wide

# View pod logs
kubectl logs -n restaurant-system <pod-name>

# Describe pod (includes events)
kubectl describe pod <pod-name> -n restaurant-system

# Check node affinity
kubectl get deployment <name> -n restaurant-system -o yaml | grep -A 20 affinity

# Test DNS resolution
kubectl exec -n restaurant-system <pod-name> -- nslookup postgres-service
```

---

## 📦 Document Maintenance

### When to Update

- **DNS-ISSUE.md**: When DNS issues recur or permanent fix is applied
- **NODE-AFFINITY-GUIDE.md**: When adding new affinity patterns
- **../ISSUES.md**: When new issues discovered or resolved

### Document Maintenance

- **ISSUES.md**: Updated when issues discovered/resolved
- **NODE-AFFINITY-GUIDE.md**: Updated when new patterns added
- **STARTUP.md**: Updated when setup process changes

---

## 🎯 Related Resources

### Official Documentation
- [Kubernetes Node Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)
- [CoreDNS Troubleshooting](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [KIND Known Issues](https://kind.sigs.k8s.io/docs/user/known-issues/)

### Internal Documentation
- [Project README](../README.md) - Project overview
- [Architecture Diagrams](../CICD-SETUP.md#architecture) - System architecture

---

**Last Updated**: 2025-12-23
**Maintained By**: DevOps Team
