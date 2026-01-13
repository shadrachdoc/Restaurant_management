# Fake Data Generation Scripts

Quick reference guide for generating test data in the Restaurant Management System.

---

## 🚀 QUICKEST WAY (1 Command)

```bash
cd /home/shadrach/Restaurant_management/scripts
./run_all_fake_data.sh
```

**Interactive menu will ask you:**
1. Quick Test (10 orders)
2. Daily Orders (250 orders) ⭐ **RECOMMENDED**
3. Historical Data (30 days)
4. Full Setup (History + Today)
5. Custom amount

---

## 📋 Manual Commands

### Generate Today's Orders (250 orders)
```bash
python3 generate_daily_orders_sql.py
```

### Verify Results
```bash
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*), ROUND(CAST(SUM(total) as numeric), 2) FROM orders WHERE DATE(created_at) = CURRENT_DATE;"
```

### View Analytics
```
https://restaurant.corpv3.com/analytics
```

---

## 📚 Full Documentation

📖 **Complete Guide**: `HOW_TO_RUN_FAKE_DATA_SCRIPTS.md`

---

## 📁 Available Scripts

| File | Purpose | Speed |
|------|---------|-------|
| `generate_daily_orders_sql.py` | 250 orders for TODAY | ⚡ 30s |
| `run_all_fake_data.sh` | Interactive wrapper | ⚡ Fast |

---

## ⚡ Quick Example

```bash
# One command to generate 250 orders
./run_all_fake_data.sh

# Or directly
python3 generate_daily_orders_sql.py
```

---

**Last Updated**: 2026-01-13
