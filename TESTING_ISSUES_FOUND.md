# 🔍 Testing Issues Found - January 16, 2026

## Summary
Tested the README.md deployment guide from scratch. Found critical issues in BƯỚC 1-2 (Kafka setup).

---

## ❌ Issue 1: PersistentVolume Binding Conflict

### Problem
Multiple PVs with same size (10Gi) caused incorrect binding:
- `postgres-pv`: 10Gi
- `kafka-pv`: 10Gi (originally)
- Kafka PVC bound to `postgres-pv` instead of `kafka-pv`

### Root Cause
No selectors/labels to distinguish PVs when they have identical:
- storageClassName: `standard`
- capacity: `10Gi`
- accessModes: `ReadWriteOnce`

### Attempted Fix
1. Added labels to all PVs:
   - `type: postgres` for postgres-pv
   - `type: kafka` for kafka-pv
   - `type: namenode` for namenode-pv
   - `type: datanode` for datanode-pv
   - `type: zookeeper` for zookeeper-pv

2. Changed kafka-pv size from 10Gi → 8Gi to avoid size conflict

3. Added selectors to volumeClaimTemplates:
   - postgres: ✅ Works (selector supported in StatefulSet)
   - namenode: ✅ Works
   - datanode: ✅ Works
   - kafka: ❌ **FAILED - Strimzi KafkaNodePool doesn't support `spec.storage.selector`**

### Error Message
```
Error from server (BadRequest): error when creating "k8s/kafka-strimzi.yaml": 
KafkaNodePool in version "v1beta2" cannot be handled as a KafkaNodePool: 
strict decoding error: unknown field "spec.storage.selector.matchLabels.type"
```

---

## ❌ Issue 2: Kafka Permission Denied on hostPath PV

### Problem
Kafka pod crashes with:
```
Error while writing meta.properties file /var/lib/kafka/data/kafka-log0: 
java.nio.file.AccessDeniedException: /var/lib/kafka/data/kafka-log0
```

### Root Cause
- Minikube hostPath volumes have root:root ownership
- Kafka container runs as non-root user (UID 1000)
- No write permission to `/data/kafka` mount

### Common on Minikube
This is a well-known limitation of hostPath PVs on Minikube for stateful workloads.

### Possible Solutions
1. **Use emptyDir** (recommended for testing/demo):
   - Pros: No permission issues, works immediately
   - Cons: Data lost on pod restart
   - **Best for**: Quick demos, testing, development

2. **Add initContainer to fix permissions**:
   - Pros: Keeps persistent storage
   - Cons: Requires modifying Strimzi CRD, complex
   
3. **Use dynamic provisioning with custom StorageClass**:
   - Pros: Production-like setup
   - Cons: Requires additional configuration

4. **Run Kafka as root** (NOT recommended):
   - Security risk

---

## 📝 Recommended Fix for README.md

### Option A: Simplify for Minikube (Recommended)
Use **emptyDir** for Kafka storage in test/demo scenarios:

```yaml
# In kafka-strimzi.yaml
spec:
  storage:
    type: ephemeral  # Uses emptyDir internally
```

**Pros:**
- Works immediately on Minikube
- No PV conflicts
- Faster pod startup
- Suitable for demos/testing

**Cons:**
- Data lost on pod restart
- Not production-ready

**Update README to say:**
> **Note for Minikube:** This guide uses ephemeral storage for Kafka (emptyDir). 
> Data will be lost on pod restart. For production, use persistent storage with proper PV configuration.

### Option B: Add Init Container (Complex)
Add initContainer to fix permissions - requires custom Strimzi pod template.

**Not recommended** because:
- More complex for beginners
- Requires understanding Strimzi pod templates
- Still has PV binding issues

---

## ✅ Files Modified During Testing

### Changed Files:
1. `k8s/00-namespace-config.yaml`
   - Added labels to all PVs
   - Changed kafka-pv: 10Gi → 8Gi

2. `k8s/03-hadoop.yaml`
   - Added selectors to namenode/datanode PVC templates

3. `k8s/05-database.yaml`
   - Added selector to postgres PVC template

4. `k8s/kafka-strimzi.yaml`
   - Changed storage size 10Gi → 8Gi
   - Attempted (failed) to add selector

### Testing State:
- Minikube: Fresh cluster (deleted and recreated)
- Namespace: `air-quality` created
- Strimzi Operator: ✅ Running
- Kafka: ❌ CrashLoopBackOff (permission denied)
- Other services: Not tested yet (blocked by Kafka)

---

## 🎯 Next Steps

1. **Immediate Fix:**
   - Change Kafka storage to `type: ephemeral` in kafka-strimzi.yaml
   - Update README BƯỚC 1-2 with note about Minikube limitations
   - Revert PV size changes (keep labels for documentation)

2. **Update README:**
   - Add "⚠️ Minikube Note" section in BƯỚC 1-2
   - Explain why ephemeral storage is used
   - Optional: Add appendix for production PV setup

3. **Continue Testing:**
   - After Kafka fix, test BƯỚC 3-5 (HDFS, Spark, PostgreSQL)
   - Verify all services start correctly
   - Test data flow end-to-end

---

## 📊 Test Environment

- OS: Windows 11
- Minikube: v1.35.0
- Kubernetes: v1.32.0
- Docker: Desktop (driver)
- Strimzi: 0.49.1
- Kafka: 4.0.1

---

## 💡 Key Learnings

1. **PV Binding Rules:**
   - Kubernetes binds PVCs to PVs based on size, accessMode, and storageClass
   - When multiple PVs match, binding is **random/alphabetical**
   - **Must use** unique sizes OR labels+selectors to control binding

2. **Strimzi Limitations:**
   - KafkaNodePool CRD doesn't support `spec.storage.selector`
   - Cannot force PV binding via Strimzi spec
   - Must rely on unique PV sizes or StorageClass names

3. **Minikube hostPath:**
   - Default ownership: root:root
   - Many container images run as non-root (security best practice)
   - Causes permission errors for stateful workloads
   - **Solution:** Use emptyDir for testing OR add initContainers

4. **README Best Practices:**
   - Document platform-specific limitations (Minikube vs GKE vs EKS)
   - Provide "quick start" path (ephemeral) AND "production" path (persistent)
   - Expected outputs are crucial for debugging
   - Timing estimates help users understand if something is stuck

---

**Tested by:** GitHub Copilot  
**Date:** January 16, 2026  
**Status:** Kafka deployment blocked, needs configuration fix
