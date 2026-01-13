#!/usr/bin/env python3
"""
Generate fake order data for 1 month to test ML predictions
Uses actual menu items from the database
"""
import psycopg2
import random
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'restaurant_db',
    'user': 'restaurant_admin',
    'password': 'restaurant_pass_2024'
}

# Order status progression
ORDER_STATUSES = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED']

# Time patterns (realistic restaurant traffic)
HOUR_WEIGHTS = {
    0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.2,  # Night (very low)
    6: 0.5, 7: 1.0, 8: 2.0, 9: 1.5, 10: 1.0, 11: 3.0,  # Morning/Brunch
    12: 5.0, 13: 4.5, 14: 2.0,  # Lunch peak
    15: 1.0, 16: 0.8, 17: 1.5,  # Afternoon
    18: 4.0, 19: 5.0, 20: 4.5, 21: 3.0,  # Dinner peak
    22: 2.0, 23: 1.0  # Late night
}

# Day of week weights (1=Monday, 7=Sunday)
DAY_WEIGHTS = {
    1: 0.8, 2: 0.8, 3: 0.9, 4: 1.0,  # Monday-Thursday (normal)
    5: 1.5, 6: 2.0, 7: 1.8  # Friday-Sunday (busy)
}

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

def fetch_restaurant_data(conn):
    """Fetch restaurant, menu items, and tables"""
    cursor = conn.cursor()

    # Get restaurant
    cursor.execute("SELECT id, name FROM restaurants LIMIT 1")
    restaurant = cursor.fetchone()
    restaurant_id = restaurant[0]

    # Get all menu items
    cursor.execute("""
        SELECT id, name, category, price
        FROM menu_items
        WHERE restaurant_id = %s
    """, (restaurant_id,))
    menu_items = cursor.fetchall()

    # Get tables
    cursor.execute("""
        SELECT id, table_number
        FROM tables
        WHERE restaurant_id = %s
    """, (restaurant_id,))
    tables = cursor.fetchall()

    cursor.close()
    return restaurant_id, menu_items, tables

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    return f"ORD-{timestamp}-{random_suffix}"

def calculate_order_time_weight(dt):
    """Calculate probability weight for given datetime"""
    hour_weight = HOUR_WEIGHTS.get(dt.hour, 1.0)
    day_weight = DAY_WEIGHTS.get(dt.isoweekday(), 1.0)
    return hour_weight * day_weight

def generate_orders_for_day(conn, date, restaurant_id, menu_items, tables, base_orders_per_day=30):
    """Generate orders for a specific day with realistic patterns"""
    cursor = conn.cursor()
    orders_created = 0

    # Determine number of orders based on day of week
    day_weight = DAY_WEIGHTS.get(date.isoweekday(), 1.0)
    num_orders = int(base_orders_per_day * day_weight * random.uniform(0.8, 1.2))

    for _ in range(num_orders):
        # Generate random time with weighted distribution
        hour = random.choices(
            list(HOUR_WEIGHTS.keys()),
            weights=list(HOUR_WEIGHTS.values()),
            k=1
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        order_time = datetime(date.year, date.month, date.day, hour, minute, second)

        # Random table
        table = random.choice(tables)
        table_id = table[0]

        # Generate order
        order_id = str(uuid.uuid4())
        order_number = generate_order_number()

        # Select 1-5 menu items
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.2, 0.3, 0.3, 0.15, 0.05])[0]
        selected_items = random.sample(menu_items, min(num_items, len(menu_items)))

        # Calculate totals
        subtotal = Decimal('0.0')
        order_items_data = []

        for item in selected_items:
            item_id, item_name, item_category, item_price = item
            quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            item_subtotal = Decimal(str(item_price)) * quantity
            subtotal += item_subtotal

            order_items_data.append({
                'menu_item_id': item_id,
                'name': item_name,
                'price': item_price,
                'quantity': quantity
            })

        tax = subtotal * Decimal('0.10')
        total = subtotal + tax

        # Random customer names
        customer_names = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown',
                         'Charlie Davis', 'Eva Martinez', 'Frank Johnson', 'Grace Lee']
        customer_name = random.choice(customer_names)
        customer_phone = f"+1{random.randint(1000000000, 9999999999)}"

        # Order status (most orders should be completed)
        status = random.choices(
            ['COMPLETED', 'SERVED', 'PENDING'],
            weights=[0.85, 0.10, 0.05]
        )[0]

        # Completion time (if completed)
        completed_at = None
        if status in ['COMPLETED', 'SERVED']:
            completion_minutes = random.randint(20, 90)
            completed_at = order_time + timedelta(minutes=completion_minutes)

        # Insert order
        cursor.execute("""
            INSERT INTO orders (
                id, restaurant_id, table_id, order_number, status, order_type,
                customer_name, customer_phone, subtotal, tax, total,
                created_at, updated_at, completed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            order_id, restaurant_id, table_id, order_number, status, 'TABLE',
            customer_name, customer_phone, float(subtotal), float(tax), float(total),
            order_time, order_time, completed_at
        ))

        # Insert order items
        for item_data in order_items_data:
            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO order_items (
                    id, order_id, menu_item_id, item_name, item_price, quantity, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                item_id, order_id, item_data['menu_item_id'],
                item_data['name'], float(item_data['price']), item_data['quantity'],
                order_time
            ))

        orders_created += 1

    conn.commit()
    cursor.close()
    return orders_created

def main():
    print("🍽️  Generating fake order data for 1 month...")
    print("=" * 60)

    # Connect to database
    conn = connect_db()

    # Fetch restaurant data
    restaurant_id, menu_items, tables = fetch_restaurant_data(conn)
    print(f"✓ Restaurant ID: {restaurant_id}")
    print(f"✓ Menu items: {len(menu_items)}")
    print(f"✓ Tables: {len(tables)}")
    print()

    # Generate orders for past 90 days (to get before Dec 14)
    end_date = datetime(2025, 12, 13, 23, 59, 59)  # Day before our existing data
    start_date = end_date - timedelta(days=90)

    total_orders = 0
    current_date = start_date

    print("Generating orders by day:")
    print("-" * 60)

    while current_date <= end_date:
        orders_count = generate_orders_for_day(
            conn, current_date, restaurant_id, menu_items, tables
        )
        total_orders += orders_count

        day_name = current_date.strftime("%A")
        print(f"{current_date.strftime('%Y-%m-%d')} ({day_name}): {orders_count} orders")

        current_date += timedelta(days=1)

    conn.close()

    print()
    print("=" * 60)
    print(f"✓ Total orders generated: {total_orders}")
    print(f"✓ Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"✓ Average orders per day: {total_orders / 31:.1f}")
    print()
    print("🎉 Fake data generation complete!")
    print()
    print("Next steps:")
    print("1. Check order statistics in your admin dashboard")
    print("2. Trigger ML predictions via the analytics endpoint")
    print("3. View predictions for popular items and revenue forecasts")

if __name__ == "__main__":
    main()
