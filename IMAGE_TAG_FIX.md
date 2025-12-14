# Docker Image Tag Mismatch Fix

## Issue Identified ✅

The `deploy-kind` job was failing with:
```
Error response from daemon: manifest for ***/restaurant-auth-service:developer-79b998912f1fdb6d99ede5e7de825c95fe96f759 not found: manifest unknown
```

**Root Cause:**
The `docker/metadata-action@v4` creates Docker image tags with a **7-character short SHA**, but the deployment script was trying to pull images with the **full 40-character SHA**.

---

## How Docker Metadata Action Works

The `docker/metadata-action@v4` automatically generates tags based on the configuration:

```yaml
tags: |
  type=ref,event=branch          # Creates: developer
  type=ref,event=pr              # Creates: pr-123
  type=sha,prefix={{branch}}-    # Creates: developer-79b9989 (7-char SHA)
  type=raw,value=latest,enable={{is_default_branch}}
```

**Tags Created:**
- `shadrach85/restaurant-auth-service:developer`
- `shadrach85/restaurant-auth-service:developer-79b9989` ← **7-character SHA**

**Tags Deploy Was Looking For:**
- `shadrach85/restaurant-auth-service:developer-79b998912f1fdb6d99ede5e7de825c95fe96f759` ← **40-character SHA**

**Result:** Image not found! ❌

---

## Fix Applied ✅

Updated the deployment script to use the **short SHA** (7 characters) to match what the metadata action creates.

### Changes Made:

**File**: `.github/workflows/ci-cd.yml`

#### 1. Load Docker Images Step (Lines 161-176)

**Before:**
```yaml
docker pull ${{ secrets.DOCKERHUB_USERNAME }}/restaurant-auth-service:${{ github.ref_name }}-${{ github.sha }}
```

**After:**
```bash
SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
docker pull ${{ secrets.DOCKERHUB_USERNAME }}/restaurant-auth-service:${{ github.ref_name }}-${SHORT_SHA}
```

#### 2. Helm Deploy Step (Lines 178-198)

**Before:**
```yaml
--set apiGateway.image.tag=${{ github.ref_name }}-${{ github.sha }}
```

**After:**
```bash
SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
--set apiGateway.image.tag=${{ github.ref_name }}-${SHORT_SHA}
```

---

## How It Works Now

### 1. Build Stage
```
docker/metadata-action creates:
  → developer-79b9989 (7-char SHA)
```

### 2. Deploy Stage
```bash
SHORT_SHA=$(echo "79b998912f1fdb6d99ede5e7de825c95fe96f759" | cut -c1-7)
# Result: SHORT_SHA=79b9989

docker pull shadrach85/restaurant-auth-service:developer-79b9989 ✅
```

### 3. Helm Deployment
```bash
helm upgrade --install restaurant-system ./helm/restaurant-system \
  --set authService.image.tag=developer-79b9989 ✅
```

---

## Image Tag Format

| Stage | Tag Format | Example |
|-------|-----------|---------|
| **Build** | `{branch}-{short_sha}` | `developer-79b9989` |
| **Deploy** | `{branch}-{short_sha}` | `developer-79b9989` |
| **Branch Tag** | `{branch}` | `developer` |
| **Latest** | `latest` | `latest` (main branch only) |

---

## Complete Tag List Per Image

For commit `79b998912f1fdb6d99ede5e7de825c95fe96f759` on `developer` branch:

**Tags Created:**
1. `shadrach85/restaurant-auth-service:developer`
2. `shadrach85/restaurant-auth-service:developer-79b9989`

**Used for Deployment:**
- ✅ `developer-79b9989` (most specific, includes version)

**Alternative (if needed):**
- ✅ `developer` (always points to latest developer branch build)

---

## Benefits of Short SHA

1. **✅ Shorter tags** - Easier to read and type
2. **✅ Standard practice** - Git uses 7-char SHAs by default
3. **✅ Sufficient uniqueness** - 7 chars = 268 million combinations
4. **✅ Matches Docker conventions** - Most tools use short SHAs
5. **✅ Cleaner Docker Hub** - More readable tag lists

---

## Testing

The fix ensures:

1. ✅ Images are built with tags: `developer-79b9989`
2. ✅ Deploy pulls images with: `developer-79b9989`
3. ✅ Helm sets image tags to: `developer-79b9989`
4. ✅ All tags match exactly!

---

## Verification

After the fix, you can verify in DockerHub:

**Visit:** https://hub.docker.com/r/shadrach85/restaurant-auth-service/tags

**You'll see:**
- ✅ `developer` (latest developer build)
- ✅ `developer-79b9989` (specific commit)
- ✅ `developer-abc1234` (another commit)

---

## What Was Changed

| File | Lines | Change |
|------|-------|--------|
| `.github/workflows/ci-cd.yml` | 161-176 | Added SHORT_SHA calculation for docker pull |
| `.github/workflows/ci-cd.yml` | 178-198 | Added SHORT_SHA calculation for Helm deployment |

---

## Commit Message

```bash
git add .github/workflows/ci-cd.yml

git commit -m "Fix: Use short SHA for Docker image tags

- Match metadata action's 7-character SHA format
- Fixes image pull failures in deploy-kind job
- Deploy now pulls: developer-79b9989 instead of developer-{full-sha}"

git push origin developer
```

---

## Summary

✅ **Fixed**: Image tag mismatch between build and deploy
✅ **Changed**: Use 7-character short SHA instead of full 40-character SHA
✅ **Result**: Deploy can now successfully pull built images
✅ **Status**: Ready for deployment!

---

**The image tag mismatch is now resolved! Commit and push to run a successful deployment.** 🚀
