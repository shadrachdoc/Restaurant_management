# How to Run All Fake Data Generation Scripts

## 📁 Location
All scripts are located in: `/home/shadrach/Restaurant_management/scripts/`

---

## 🎯 Available Scripts Overview

| Script | Purpose | Method | Speed | Best For |
|--------|---------|--------|-------|----------|
| `generate_daily_orders_sql.py` | Generate 250 orders for TODAY | Direct SQL | ⚡ Fast (30s) | **Daily analytics** (RECOMMENDED) |
| `generate_daily_orders.py` | Generate orders via API | REST API | 🐌 Slow (rate limits) | Testing API endpoints |
| `generate_fake_orders_api.py` | Bulk order generation | REST API | 🐌 Very slow | Not recommended |
| `generate_fake_orders.py` | Legacy bulk orders | SQL | ⚡ Fast | Historical data |

---

## ✅ RECOMMENDED: Daily Order Generator (SQL Version)

### 📋 Script Details
- **File**: `generate_daily_orders_sql.py`
- **Orders**: 250 orders for TODAY
- **Method**: Direct PostgreSQL insert
- **Time**: ~30 seconds
- **No API rate limits**

### 🚀 Quick Start

```bash
# Navigate to scripts directory
cd /home/shadrach/Restaurant_management/scripts

# Run the script
python3 generate_daily_orders_sql.py
```

### 📊 What It Generates

- **250 orders** spread across 24 hours
- **Realistic time distribution**:
  - Breakfast: 6AM-11AM (18% of orders)
  - Lunch: 12PM-2PM (28% of orders - PEAK)
  - Dinner: 6PM-9PM (35% of orders - PEAK)
  - Other times: 19% of orders

- **Order details**:
  - Random customer names (international)
  - Random phone numbers
  - Order types: 50% TABLE, 50% ONLINE
  - Order statuses: PENDING, CONFIRMED, PREPARING, READY, SERVED, COMPLETED
  - 1-5 items per order (realistic distribution)
  - Proper billing: subtotal + 10% tax

- **Menu items used**:
  - All 9 menu items from database
  - Realistic combinations (appetizers + mains + drinks + desserts)

### ✅ Verify Results

```bash
# Check today's orders
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*) as orders, ROUND(CAST(SUM(total) as numeric), 2) as revenue FROM orders WHERE DATE(created_at) = CURRENT_DATE;"

# Check popular items today
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT mi.name, COUNT(oi.id) as orders, SUM(oi.quantity) as total_qty FROM order_items oi JOIN menu_items mi ON oi.menu_item_id = mi.id JOIN orders o ON oi.order_id = o.id WHERE DATE(o.created_at) = CURRENT_DATE GROUP BY mi.name ORDER BY total_qty DESC LIMIT 5;"

# Check hourly distribution
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as orders FROM orders WHERE DATE(created_at) = CURRENT_DATE GROUP BY EXTRACT(HOUR FROM created_at) ORDER BY hour;"
```

### 🌐 View in Application

Open your browser:
```
https://restaurant.corpv3.com/analytics
```

Check predictions API:
```bash
curl -s "https://restaurant.corpv3.com/api/v1/restaurants/6956017d-3aea-4ae2-9709-0ca0ac0a1a09/analytics/predictions/demand" | jq '.predictions | length'
```

---

## 📅 Schedule Daily Automatic Generation

### Option 1: Cron Job (Recommended)

Run daily at midnight:
```bash
# Edit crontab
crontab -e

# Add this line (runs at midnight every day)
0 0 * * * cd /home/shadrach/Restaurant_management/scripts && /usr/bin/python3 generate_daily_orders_sql.py >> /tmp/daily_orders.log 2>&1

# Or run at 6 AM every day
0 6 * * * cd /home/shadrach/Restaurant_management/scripts && /usr/bin/python3 generate_daily_orders_sql.py >> /tmp/daily_orders.log 2>&1
```

### Option 2: Kubernetes CronJob

Create a CronJob that runs in the cluster:
```yaml
# Save as cronjob-daily-orders.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: generate-daily-orders
  namespace: restaurant-system
spec:
  schedule: "0 0 * * *"  # Midnight every day
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: order-generator
            image: python:3.11-slim
            command:
            - /bin/sh
            - -c
            - |
              apt-get update && apt-get install -y kubectl
              python3 /scripts/generate_daily_orders_sql.py
            volumeMounts:
            - name: scripts
              mountPath: /scripts
          volumes:
          - name: scripts
            hostPath:
              path: /home/shadrach/Restaurant_management/scripts
          restartPolicy: OnFailure
```

Apply the CronJob:
```bash
kubectl apply -f cronjob-daily-orders.yaml
```

---

## 📊 Other Available Scripts

### 1. API-Based Daily Orders (Not Recommended)

**File**: `generate_daily_orders.py`

⚠️ **Issue**: Hits rate limits after ~10 orders

```bash
# Only use for testing API endpoints
python3 generate_daily_orders.py 10
```

**When to use**:
- Testing API authentication
- Testing rate limiting
- Development/debugging

**Don't use for**:
- Production data generation
- Large datasets
- Daily analytics

---

### 2. Bulk Historical Orders

**File**: `generate_fake_orders.py`

Generates orders for past dates (historical data):

```bash
# Generate 1000 orders for the last 30 days
python3 generate_fake_orders.py --days 30 --orders 1000
```

**Use cases**:
- Seeding database for first time
- Creating historical trends
- Testing ML predictions with past data

---

### 3. API Bulk Generator (Legacy)

**File**: `generate_fake_orders_api.py`

⚠️ **Very slow** - Uses API calls

```bash
# Not recommended - use SQL version instead
python3 generate_fake_orders_api.py
```

---

## 🔧 Complete Setup Guide

### Step 1: First Time Setup (Historical Data)

Generate 30 days of historical data:

```bash
cd /home/shadrach/Restaurant_management/scripts

# Generate 1000 orders spread over last 30 days
python3 generate_fake_orders.py --days 30 --orders 1000
```

### Step 2: Daily Orders (Today)

Generate today's orders:

```bash
python3 generate_daily_orders_sql.py
```

### Step 3: Verify Everything

```bash
# Total orders
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*) FROM orders;"

# Orders by date (last 7 days)
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT DATE(created_at) as date, COUNT(*) as orders, ROUND(CAST(SUM(total) as numeric), 2) as revenue FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at) ORDER BY date DESC;"

# Total revenue
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT ROUND(CAST(SUM(total) as numeric), 2) as total_revenue FROM orders;"
```

### Step 4: Check Analytics Dashboard

Open browser:
```
https://restaurant.corpv3.com/analytics
```

You should see:
- ✅ Sales trends
- ✅ Popular items
- ✅ Revenue charts
- ✅ Hourly distribution
- ✅ ML predictions (if enough data)

---

## 🎯 Common Use Cases

### Use Case 1: Daily Testing

**Goal**: Test analytics with fresh data every day

```bash
# Run this every morning
cd /home/shadrach/Restaurant_management/scripts
python3 generate_daily_orders_sql.py
```

### Use Case 2: Demo Preparation

**Goal**: Populate system with realistic data for demo

```bash
# Generate 30 days of history
python3 generate_fake_orders.py --days 30 --orders 2000

# Generate today's orders
python3 generate_daily_orders_sql.py

# Verify
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*) FROM orders;"
```

### Use Case 3: ML Training

**Goal**: Train prediction models with lots of data

```bash
# Generate 90 days of data
python3 generate_fake_orders.py --days 90 --orders 5000

# Train model
curl -X POST https://restaurant.corpv3.com/api/v1/analytics/train
```

### Use Case 4: Load Testing

**Goal**: Test system performance with high volume

```bash
# Generate many orders at once
for i in {1..10}; do
  python3 generate_daily_orders_sql.py &
done
wait

# Check performance
kubectl top pods -n restaurant-system
```

---

## 📈 Expected Results

### After First Run (250 orders today)

**Database**:
```
Orders: 250
Revenue: ~$5,000-6,000
Average Order: ~$20-25
```

**Hourly Distribution**:
```
06:00-07:00:   3 orders   ($80)
07:00-08:00:   8 orders   ($180)
08:00-09:00:  12 orders   ($250)
09:00-10:00:  11 orders   ($230)
10:00-11:00:   8 orders   ($160)
11:00-12:00:  14 orders   ($280)
12:00-13:00:  27 orders   ($700)  ⭐ LUNCH PEAK
13:00-14:00:  28 orders   ($600)  ⭐ LUNCH PEAK
14:00-15:00:  16 orders   ($330)
15:00-16:00:   6 orders   ($120)
16:00-17:00:   4 orders   ($80)
17:00-18:00:   8 orders   ($190)
18:00-19:00:  19 orders   ($480)
19:00-20:00:  30 orders   ($620)  ⭐ DINNER PEAK
20:00-21:00:  26 orders   ($510)  ⭐ DINNER PEAK
21:00-22:00:  17 orders   ($330)
22:00-23:00:   9 orders   ($190)
23:00-00:00:   4 orders   ($45)
```

**Popular Items**:
```
1. Biriyani - 30 orders
2. Craft Beer - 24 orders
3. Salad Bites - 19 orders
4. Salad - 17 orders
5. Green Radish Salad - 13 orders
```

---

## 🛠️ Troubleshooting

### Problem: Script doesn't run

**Solution**:
```bash
# Make script executable
chmod +x /home/shadrach/Restaurant_management/scripts/generate_daily_orders_sql.py

# Check Python version
python3 --version  # Should be 3.8+

# Run with full path
/usr/bin/python3 /home/shadrach/Restaurant_management/scripts/generate_daily_orders_sql.py
```

### Problem: Database connection failed

**Solution**:
```bash
# Check postgres pod
kubectl get pods -n restaurant-system | grep postgres

# Test connection
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT 1;"

# Check database credentials
kubectl get secret -n restaurant-system restaurant-secrets -o yaml
```

### Problem: No orders showing in analytics

**Solution**:
```bash
# Verify orders in database
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE;"

# Check if restaurant ID is correct
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT id, name FROM restaurants;"

# Restart analytics service
kubectl rollout restart deployment/order-service -n restaurant-system
```

### Problem: Menu items not found

**Solution**:
```bash
# Check menu items exist
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*) FROM menu_items WHERE restaurant_id = '6956017d-3aea-4ae2-9709-0ca0ac0a1a09';"

# If no items, add them first via admin dashboard:
# https://restaurant.corpv3.com/admin/menu
```

### Problem: Duplicate order numbers

**Solution**:
```bash
# Clear today's orders and regenerate
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "DELETE FROM orders WHERE DATE(created_at) = CURRENT_DATE;"

# Run script again
python3 generate_daily_orders_sql.py
```

---

## 📝 Configuration

### Customize Order Volume

Edit `generate_daily_orders_sql.py`:

```python
# Line ~240
target_orders = 250  # Change to 100, 500, 1000, etc.
```

### Customize Restaurant ID

Edit script and change:

```python
# Line ~14
RESTAURANT_ID = "6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
TABLE_ID = "3aaf3785-cf1d-4633-891f-69e7a4dec0d5"
```

### Customize Menu Items

Edit the `MENU_ITEMS` array to match your menu:

```python
MENU_ITEMS = [
    {"id": "uuid-here", "name": "Item Name", "price": 10.0},
    # Add your menu items
]
```

### Customize Time Distribution

Edit `HOUR_WEIGHTS` dictionary:

```python
HOUR_WEIGHTS = {
    6: 1.0,   # 6 AM - low traffic
    12: 8.0,  # 12 PM - high traffic (lunch)
    19: 8.5,  # 7 PM - highest traffic (dinner)
    # Adjust weights as needed
}
```

---

## 🔐 Security Notes

- ✅ Scripts use local database connection (no external API)
- ✅ No sensitive data exposed
- ✅ Customer names/phones are randomly generated
- ✅ Safe to run in production (only inserts data, doesn't delete)

---

## 📞 Support

### Check Logs

```bash
# If using cron
tail -f /tmp/daily_orders.log

# Check Kubernetes logs
kubectl logs -n restaurant-system -l app=order-service --tail=50

# Check postgres logs
kubectl logs -n restaurant-system postgres-0 --tail=50
```

### Get Help

```bash
# Script help
python3 generate_daily_orders_sql.py --help

# Database stats
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "\dt"
```

---

## ✅ Quick Command Reference

### One-Time Setup
```bash
cd /home/shadrach/Restaurant_management/scripts
python3 generate_fake_orders.py --days 30 --orders 1000
```

### Daily Run
```bash
python3 generate_daily_orders_sql.py
```

### Verify
```bash
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -c "SELECT COUNT(*), SUM(total) FROM orders WHERE DATE(created_at) = CURRENT_DATE;"
```

### View Dashboard
```
https://restaurant.corpv3.com/analytics
```

---

## 🎉 Success Indicators

After running scripts, you should see:

✅ **Database**: 250+ new orders for today
✅ **Analytics Dashboard**: Charts with data
✅ **Predictions API**: 28+ predictions available
✅ **Popular Items**: Top 5 items ranked
✅ **Revenue Tracking**: Today's revenue calculated
✅ **Hourly Distribution**: Peak hours identified

---

**Last Updated**: 2026-01-13
**Version**: 1.0
**Author**: Restaurant Management System
