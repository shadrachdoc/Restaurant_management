#!/usr/bin/env python3
"""
Daily Order Generator - Direct SQL Version
Generates 250 orders for TODAY by inserting directly into database
Bypasses API rate limiting issues
"""

import random
import string
from datetime import datetime, timedelta
import subprocess
import json

# Restaurant Configuration
RESTAURANT_ID = "6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
TABLE_ID = "3aaf3785-cf1d-4633-891f-69e7a4dec0d5"

# Menu Items
MENU_ITEMS = [
    {"id": "1e01fbfa-96b0-450f-b46f-661dc65bc3d1", "name": "Salad Bites", "price": 7.0},
    {"id": "aaf9ad8c-ee6a-4bb6-84f9-4f0f7cf3f11e", "name": "Biriyani", "price": 6.5},
    {"id": "898ff00e-ff95-41fe-b15f-121ccb619be9", "name": "Green Radish Salad", "price": 5.0},
    {"id": "18386a1a-89a8-497d-b90b-02d0cf33b48a", "name": "Salad", "price": 3.0},
    {"id": "e51bc2df-de77-47da-b44c-68b10e5f35d9", "name": "Pan Fried Salmon", "price": 12.0},
    {"id": "2fd2992b-07f3-443f-84b1-205886fad55e", "name": "Coke Zero", "price": 3.0},
    {"id": "0e29036f-e2d6-449d-95e5-72f610b0535c", "name": "Craft Beer", "price": 5.0},
    {"id": "3681df63-ab0c-41c8-984b-509780450901", "name": "HereNow Creme Caramel", "price": 5.0},
    {"id": "b43974b8-65c5-43d4-b92c-c42751f07d2d", "name": "Birthday Cake", "price": 1.0},
]

# Time distribution
HOUR_WEIGHTS = {
    0: 0.1, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.1, 5: 0.3,
    6: 1.0, 7: 2.5, 8: 4.0, 9: 3.5, 10: 2.5, 11: 4.5,
    12: 8.0, 13: 7.5, 14: 5.0,
    15: 2.0, 16: 1.5, 17: 2.5,
    18: 6.0, 19: 8.5, 20: 7.5, 21: 5.5,
    22: 3.0, 23: 1.5
}

ORDER_TYPES = ["TABLE", "ONLINE"]
STATUSES = ["PENDING", "CONFIRMED", "PREPARING", "READY", "SERVED", "COMPLETED"]

NAMES = ["James Smith", "Mary Johnson", "Robert Williams", "Patricia Brown", "Michael Jones",
         "Jennifer Garcia", "William Miller", "Linda Davis", "David Rodriguez", "Barbara Martinez"]

TAX_RATE = 0.10

def generate_order_number():
    """Generate unique order number"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

def generate_items():
    """Generate 1-5 items"""
    num_items = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.25, 0.30, 0.20, 0.10])[0]
    selected = random.sample(MENU_ITEMS, min(num_items, len(MENU_ITEMS)))

    items = []
    for item in selected:
        quantity = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
        items.append({
            "id": item["id"],
            "name": item["name"],
            "quantity": quantity,
            "price": item["price"],
            "subtotal": item["price"] * quantity
        })
    return items

def exec_psql(sql):
    """Execute SQL in postgres pod"""
    cmd = [
        "kubectl", "exec", "-i", "postgres-0", "-n", "restaurant-system", "--",
        "psql", "-U", "restaurant_admin", "-d", "restaurant_db", "-c", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    target_orders = 250

    print(f"\n{'='*80}")
    print(f"📊 DAILY ORDER GENERATOR - SQL Direct Insert")
    print(f"{'='*80}")
    print(f"Target: {target_orders} orders for {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    # Calculate orders per hour
    total_weight = sum(HOUR_WEIGHTS.values())
    orders_by_hour = {}
    for hour, weight in HOUR_WEIGHTS.items():
        orders_by_hour[hour] = int((weight / total_weight) * target_orders)

    # Adjust to hit exact target
    current_total = sum(orders_by_hour.values())
    if current_total < target_orders:
        for _ in range(target_orders - current_total):
            hour = random.choice([12, 13, 19, 20])
            orders_by_hour[hour] += 1

    total_revenue = 0
    orders_created = 0

    # Generate all SQL in batches
    for hour in range(24):
        num_orders = orders_by_hour.get(hour, 0)
        if num_orders == 0:
            continue

        print(f"⏰ Hour {hour:02d}:00 - Generating {num_orders} orders...", end='', flush=True)
        hour_revenue = 0

        for _ in range(num_orders):
            # Generate order data
            order_id = f"gen_random_uuid()"
            order_number = generate_order_number()
            customer_name = random.choice(NAMES)
            customer_phone = f"+1{random.randint(1000000000, 9999999999)}"
            order_type = random.choice(ORDER_TYPES)
            status = random.choice(STATUSES)

            # Generate timestamp for this hour
            now = datetime.now()
            order_time = now.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
            timestamp = order_time.strftime("%Y-%m-%d %H:%M:%S")

            # Generate items
            items = generate_items()
            subtotal = sum(item["subtotal"] for item in items)
            tax = round(subtotal * TAX_RATE, 2)
            total = round(subtotal + tax, 2)

            # Insert order
            order_sql = f"""
            INSERT INTO orders (id, restaurant_id, table_id, order_number, status,
                customer_name, customer_phone, subtotal, tax, total, order_type,
                created_at, updated_at, special_instructions)
            VALUES (
                gen_random_uuid(),
                '{RESTAURANT_ID}',
                {'NULL' if order_type == 'ONLINE' else f"'{TABLE_ID}'"},
                '{order_number}',
                '{status}',
                '{customer_name}',
                '{customer_phone}',
                {subtotal},
                {tax},
                {total},
                '{order_type}',
                '{timestamp}',
                '{timestamp}',
                ''
            )
            RETURNING id;
            """

            success, stdout, stderr = exec_psql(order_sql.strip())

            if success and stdout.strip():
                # Extract order_id from output
                lines = stdout.strip().split('\n')
                order_id_value = None
                for line in lines:
                    line = line.strip()
                    if line and '-' in line and len(line) == 36:
                        order_id_value = line
                        break

                if order_id_value:
                    # Insert order items
                    for item in items:
                        item_sql = f"""
                        INSERT INTO order_items (id, order_id, menu_item_id, menu_item_name,
                            quantity, unit_price, subtotal, special_requests)
                        VALUES (
                            gen_random_uuid(),
                            '{order_id_value}',
                            '{item["id"]}',
                            '{item["name"]}',
                            {item["quantity"]},
                            {item["price"]},
                            {item["subtotal"]},
                            ''
                        );
                        """
                        exec_psql(item_sql.strip())

                    orders_created += 1
                    hour_revenue += total
                    total_revenue += total

        print(f" ✓ ${hour_revenue:.2f}")

    print(f"\n{'='*80}")
    print(f"📈 GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Orders Created: {orders_created}")
    print(f"💰 Total Revenue: ${total_revenue:.2f}")
    print(f"💵 Average Order: ${total_revenue/max(orders_created, 1):.2f}")
    print(f"{'='*80}\n")

    # Verify in database
    print("🔍 Verifying in database...")
    success, stdout, stderr = exec_psql(
        f"SELECT COUNT(*) as orders, SUM(total) as revenue FROM orders WHERE DATE(created_at) = CURRENT_DATE;"
    )
    if success:
        print(stdout)

    print("\n✨ Done! Check analytics now:")
    print(f"https://restaurant.corpv3.com/analytics\n")

if __name__ == "__main__":
    main()
