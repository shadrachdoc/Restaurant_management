#!/usr/bin/env python3
"""
Generate fake order data for 1 month using the API
Uses actual menu items from the database
"""
import requests
import random
from datetime import datetime, timedelta
import json

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Restaurant and menu configuration
RESTAURANT_ID = "6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
TABLE_ID = "3aaf3785-cf1d-4633-891f-69e7a4dec0d5"

# Menu items from your database
MENU_ITEMS = [
    {"id": "aaf9ad8c-ee6a-4bb6-84f9-4f0f7cf3f11e", "name": "biriyani", "category": "MAIN_COURSE", "price": 6.5},
    {"id": "898ff00e-ff95-41fe-b15f-121ccb619be9", "name": "Green Radish Salad", "category": "MAIN_COURSE", "price": 5},
    {"id": "18386a1a-89a8-497d-b90b-02d0cf33b48a", "name": "Salad", "category": "MAIN_COURSE", "price": 3},
    {"id": "2fd2992b-07f3-443f-84b1-205886fad55e", "name": "Coke Zero", "category": "BEVERAGE", "price": 3},
    {"id": "0e29036f-e2d6-449d-95e5-72f610b0535c", "name": "Craft Beer", "category": "BEVERAGE", "price": 5},
    {"id": "3681df63-ab0c-41c8-984b-509780450901", "name": "HereNow Creme Caramel", "category": "DESSERT", "price": 5},
    {"id": "e51bc2df-de77-47da-b44c-68b10e5f35d9", "name": "Pan Fried Salmon", "category": "SIDE_DISH", "price": 12},
    {"id": "1e01fbfa-96b0-450f-b46f-661dc65bc3d1", "name": "Salad Bites", "category": "APPETIZER", "price": 7},
    {"id": "b43974b8-65c5-43d4-b92c-c42751f07d2d", "name": "Birthday Cake", "category": "SPECIAL", "price": 1},
]

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

def create_order(order_data):
    """Create order via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/orders",
            json=order_data,
            timeout=10
        )
        return response.status_code == 201, response.json() if response.status_code == 201 else response.text
    except Exception as e:
        return False, str(e)

def update_order_status(order_id, status):
    """Update order status via API"""
    try:
        response = requests.patch(
            f"{API_BASE_URL}/orders/{order_id}/status",
            json={"status": status},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to update order status: {e}")
        return False

def generate_orders_for_day(date, base_orders_per_day=30):
    """Generate orders for a specific day with realistic patterns"""
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

        # Select 1-5 menu items
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.2, 0.3, 0.3, 0.15, 0.05])[0]
        selected_items = random.sample(MENU_ITEMS, min(num_items, len(MENU_ITEMS)))

        # Create order items
        order_items = []
        for item in selected_items:
            quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            order_items.append({
                "menu_item_id": item["id"],
                "quantity": quantity,
                "special_requests": random.choice(["", "", "", "Extra spicy", "No onions", "Well done"])
            })

        # Random customer names
        customer_names = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown',
                         'Charlie Davis', 'Eva Martinez', 'Frank Johnson', 'Grace Lee']
        customer_name = random.choice(customer_names)
        customer_phone = f"+1{random.randint(1000000000, 9999999999)}"

        # Create order payload
        order_data = {
            "restaurant_id": RESTAURANT_ID,
            "table_id": TABLE_ID,
            "order_type": "TABLE",
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "items": order_items
        }

        # Create order
        success, result = create_order(order_data)

        if success:
            orders_created += 1
            order_id = result.get("id")

            # Update to completed status (85% of orders)
            if random.random() < 0.85:
                # Progress through statuses
                for status in ["CONFIRMED", "PREPARING", "READY", "SERVED", "COMPLETED"]:
                    update_order_status(order_id, status)
            elif random.random() < 0.9:
                # 10% stay at SERVED
                for status in ["CONFIRMED", "PREPARING", "READY", "SERVED"]:
                    update_order_status(order_id, status)
        else:
            print(f"Failed to create order: {result}")

    return orders_created

def main():
    print("🍽️  Generating fake order data for 1 month via API...")
    print("=" * 60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Restaurant ID: {RESTAURANT_ID}")
    print(f"Menu items: {len(MENU_ITEMS)}")
    print()

    # Test API connection
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not accessible. Make sure port forwarding is running:")
            print("   kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000")
            return
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        print("Make sure port forwarding is running:")
        print("   kubectl port-forward -n restaurant-system svc/api-gateway 8000:8000")
        return

    # Generate orders for past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    total_orders = 0
    current_date = start_date

    print("Generating orders by day:")
    print("-" * 60)

    while current_date <= end_date:
        orders_count = generate_orders_for_day(current_date)
        total_orders += orders_count

        day_name = current_date.strftime("%A")
        print(f"{current_date.strftime('%Y-%m-%d')} ({day_name}): {orders_count} orders")

        current_date += timedelta(days=1)

    print()
    print("=" * 60)
    print(f"✓ Total orders generated: {total_orders}")
    print(f"✓ Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"✓ Average orders per day: {total_orders / 31:.1f}")
    print()
    print("🎉 Fake data generation complete!")
    print()
    print("Next steps:")
    print("1. Trigger ML training: POST /api/v1/analytics/train")
    print("2. Get predictions: GET /api/v1/analytics/predictions")
    print("3. View popular items: GET /api/v1/analytics/popular-items")

if __name__ == "__main__":
    main()
