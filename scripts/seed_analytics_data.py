#!/usr/bin/env python3
"""
Generate comprehensive fake order data for analytics and ML predictions
Creates 1 month of realistic order data with proper price calculations
"""
import subprocess
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Restaurant configuration
RESTAURANT_ID = "6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
TABLE_ID = "3aaf3785-cf1d-4633-891f-69e7a4dec0d5"

# Menu items with prices
MENU_ITEMS = [
    {"id": "aaf9ad8c-ee6a-4bb6-84f9-4f0f7cf3f11e", "name": "Biriyani", "price": 6.5},
    {"id": "898ff00e-ff95-41fe-b15f-121ccb619be9", "name": "Green Radish Salad", "price": 5.0},
    {"id": "18386a1a-89a8-497d-b90b-02d0cf33b48a", "name": "Salad", "price": 3.0},
    {"id": "2fd2992b-07f3-443f-84b1-205886fad55e", "name": "Coke Zero", "price": 3.0},
    {"id": "0e29036f-e2d6-449d-95e5-72f610b0535c", "name": "Craft Beer", "price": 5.0},
    {"id": "3681df63-ab0c-41c8-984b-509780450901", "name": "HereNow Creme Caramel", "price": 5.0},
    {"id": "e51bc2df-de77-47da-b44c-68b10e5f35d9", "name": "Pan Fried Salmon", "price": 12.0},
    {"id": "1e01fbfa-96b0-450f-b46f-661dc65bc3d1", "name": "Salad Bites", "price": 7.0},
    {"id": "b43974b8-65c5-43d4-b92c-c42751f07d2d", "name": "Birthday Cake", "price": 1.0},
]

# Time patterns
HOUR_WEIGHTS = {
    6: 0.5, 7: 1.0, 8: 2.0, 9: 1.5, 10: 1.0, 11: 3.0,  # Morning/Brunch
    12: 5.0, 13: 4.5, 14: 2.0,  # Lunch peak
    15: 1.0, 16: 0.8, 17: 1.5,  # Afternoon
    18: 4.0, 19: 5.0, 20: 4.5, 21: 3.0,  # Dinner peak
    22: 2.0, 23: 1.0  # Late night
}

DAY_WEIGHTS = {1: 0.8, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.5, 6: 2.0, 7: 1.8}

CUSTOMER_NAMES = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown', 'Charlie Davis', 'Eva Martinez', 'Frank Johnson', 'Grace Lee']

def execute_sql(sql):
    """Execute SQL in postgres pod"""
    cmd = [
        'kubectl', 'exec', '-i', 'postgres-0', '-n', 'restaurant-system', '--',
        'psql', '-U', 'restaurant_admin', '-d', 'restaurant_db', '-c', sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def generate_uuid():
    """Generate UUID using uuidgen"""
    result = subprocess.run(['uuidgen'], capture_output=True, text=True)
    return result.stdout.strip().lower()

def generate_order_number():
    """Generate order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import string
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{timestamp}-{suffix}"

def generate_orders_for_day(date, base_orders=30):
    """Generate orders for a specific day"""
    day_weight = DAY_WEIGHTS.get(date.isoweekday(), 1.0)
    num_orders = int(base_orders * day_weight * random.uniform(0.8, 1.2))

    orders_created = 0

    for _ in range(num_orders):
        # Random hour with weight
        hour = random.choices(list(HOUR_WEIGHTS.keys()), weights=list(HOUR_WEIGHTS.values()))[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        order_time = datetime(date.year, date.month, date.day, hour, minute, second)
        timestamp_str = order_time.strftime("%Y-%m-%d %H:%M:%S")

        # Generate order
        order_id = generate_uuid()
        order_number = generate_order_number()
        customer_name = random.choice(CUSTOMER_NAMES)
        customer_phone = f"+1{random.randint(1000000000, 9999999999)}"

        # Select menu items (1-3 items)
        num_items = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        selected_items = random.sample(MENU_ITEMS, min(num_items, len(MENU_ITEMS)))

        # Calculate totals
        subtotal = 0.0
        for item in selected_items:
            quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
            subtotal += item["price"] * quantity

        tax = subtotal * 0.10
        total = subtotal + tax

        # Completion time
        completed_at = order_time + timedelta(minutes=random.randint(20, 90))
        completed_str = completed_at.strftime("%Y-%m-%d %H:%M:%S")

        # Insert order
        order_sql = f"""
        INSERT INTO orders (id, restaurant_id, table_id, order_number, status, order_type,
                           customer_name, customer_phone, subtotal, tax, total,
                           created_at, updated_at, completed_at)
        VALUES ('{order_id}', '{RESTAURANT_ID}', '{TABLE_ID}', '{order_number}', 'COMPLETED', 'TABLE',
                '{customer_name}', '{customer_phone}', {subtotal:.2f}, {tax:.2f}, {total:.2f},
                '{timestamp_str}', '{timestamp_str}', '{completed_str}');
        """

        success, stdout, stderr = execute_sql(order_sql)

        if success:
            # Insert order items
            for item in selected_items:
                quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
                item_id = generate_uuid()

                item_sql = f"""
                INSERT INTO order_items (id, order_id, menu_item_id, item_name, item_price, quantity)
                VALUES ('{item_id}', '{order_id}', '{item["id"]}', '{item["name"]}', {item["price"]:.2f}, {quantity});
                """
                execute_sql(item_sql)

            orders_created += 1
        else:
            print(f"Error creating order: {stderr}")

    return orders_created

def main():
    print("🍽️  Generating Comprehensive Order Data for Analytics")
    print("=" * 70)
    print(f"Restaurant ID: {RESTAURANT_ID}")
    print(f"Menu Items: {len(MENU_ITEMS)}")
    print(f"Date Range: Past 30 days")
    print()

    # Generate orders for past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    total_orders = 0
    total_revenue = 0.0

    current_date = start_date

    print("Generating orders by day:")
    print("-" * 70)

    while current_date <= end_date:
        orders_count = generate_orders_for_day(current_date)
        total_orders += orders_count

        day_name = current_date.strftime("%A")
        print(f"{current_date.strftime('%Y-%m-%d')} ({day_name:9s}): {orders_count:3d} orders")

        current_date += timedelta(days=1)

    # Calculate total revenue
    revenue_sql = """
    SELECT SUM(total) FROM orders
    WHERE created_at >= NOW() - INTERVAL '31 days' AND status = 'COMPLETED';
    """
    success, stdout, stderr = execute_sql(revenue_sql)
    if success:
        lines = stdout.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and line != 'sum' and '---' not in line and line != '(1 row)':
                try:
                    total_revenue = float(line)
                except:
                    pass

    print()
    print("=" * 70)
    print(f"✅ Total Orders Generated: {total_orders}")
    print(f"✅ Average Orders/Day: {total_orders / 31:.1f}")
    print(f"✅ Total Revenue (30 days): ${total_revenue:.2f}")
    print(f"✅ Average Order Value: ${total_revenue / total_orders if total_orders > 0 else 0:.2f}")
    print()
    print("📊 Analytics Data Ready!")
    print()
    print("Next Steps:")
    print("1. View analytics in admin dashboard")
    print("2. Trigger ML training: POST /api/v1/analytics/train")
    print("3. Get predictions: GET /api/v1/analytics/predictions")
    print("4. Check popular items: GET /api/v1/analytics/popular-items")
    print()
    print("Port forward commands:")
    print("  kubectl port-forward -n restaurant-system svc/order-service 8004:8004")
    print("  curl -X POST http://localhost:8004/api/v1/analytics/train")
    print("  curl http://localhost:8004/api/v1/analytics/predictions")

if __name__ == "__main__":
    main()
