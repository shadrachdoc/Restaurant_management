#!/usr/bin/env python3
"""
Daily Order Generator with Realistic Patterns
Generates 250 orders for the current day with:
- Realistic time distribution (breakfast, lunch, dinner peaks)
- Multiple payment methods (cash, card, mobile)
- Varied order sizes (1-8 items)
- Different customer types
- Proper billing with tax, discounts, tips
- Order status progression
"""

import requests
import random
import string
from datetime import datetime, timedelta
import time
import sys

# API Configuration
API_BASE_URL = "https://restaurant.corpv3.com/api/v1"
# Fallback to localhost if needed
# API_BASE_URL = "http://localhost:8000/api/v1"

# Restaurant Configuration
RESTAURANT_ID = "6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
RESTAURANT_NAME = "Chai Kadai"
TABLE_ID = "3aaf3785-cf1d-4633-891f-69e7a4dec0d5"

# Menu Items from Database
MENU_ITEMS = [
    # Appetizers
    {"id": "1e01fbfa-96b0-450f-b46f-661dc65bc3d1", "name": "Salad Bites", "category": "APPETIZER", "price": 7.0},

    # Main Courses
    {"id": "aaf9ad8c-ee6a-4bb6-84f9-4f0f7cf3f11e", "name": "Biriyani", "category": "MAIN_COURSE", "price": 6.5},
    {"id": "898ff00e-ff95-41fe-b15f-121ccb619be9", "name": "Green Radish Salad", "category": "MAIN_COURSE", "price": 5.0},
    {"id": "18386a1a-89a8-497d-b90b-02d0cf33b48a", "name": "Salad", "category": "MAIN_COURSE", "price": 3.0},

    # Side Dishes
    {"id": "e51bc2df-de77-47da-b44c-68b10e5f35d9", "name": "Pan Fried Salmon", "category": "SIDE_DISH", "price": 12.0},

    # Beverages
    {"id": "2fd2992b-07f3-443f-84b1-205886fad55e", "name": "Coke Zero", "category": "BEVERAGE", "price": 3.0},
    {"id": "0e29036f-e2d6-449d-95e5-72f610b0535c", "name": "Craft Beer", "category": "BEVERAGE", "price": 5.0},

    # Desserts
    {"id": "3681df63-ab0c-41c8-984b-509780450901", "name": "HereNow Creme Caramel", "category": "DESSERT", "price": 5.0},
    {"id": "b43974b8-65c5-43d4-b92c-c42751f07d2d", "name": "Birthday Cake", "category": "SPECIAL", "price": 1.0},
]

# Categorize menu items for realistic ordering
APPETIZERS = [item for item in MENU_ITEMS if item["category"] == "APPETIZER"]
MAIN_COURSES = [item for item in MENU_ITEMS if item["category"] == "MAIN_COURSE"]
SIDE_DISHES = [item for item in MENU_ITEMS if item["category"] == "SIDE_DISH"]
BEVERAGES = [item for item in MENU_ITEMS if item["category"] == "BEVERAGE"]
DESSERTS = [item for item in MENU_ITEMS if item["category"] == "DESSERT"]

# Realistic time distribution (hours 0-23, weights represent order frequency)
HOUR_DISTRIBUTION = {
    0: 0.1, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.1, 5: 0.3,   # Night (almost no orders)
    6: 1.0, 7: 2.5, 8: 4.0, 9: 3.5, 10: 2.5, 11: 4.5,    # Morning/Brunch
    12: 8.0, 13: 7.5, 14: 5.0,                            # Lunch peak
    15: 2.0, 16: 1.5, 17: 2.5,                            # Afternoon slow
    18: 6.0, 19: 8.5, 20: 7.5, 21: 5.5,                  # Dinner peak
    22: 3.0, 23: 1.5                                      # Late night
}

# Payment methods with distribution
PAYMENT_METHODS = [
    {"method": "cash", "weight": 0.30},      # 30% cash
    {"method": "card", "weight": 0.50},      # 50% card
    {"method": "mobile_payment", "weight": 0.15},  # 15% mobile (Apple Pay, Google Pay)
    {"method": "gift_card", "weight": 0.05}, # 5% gift cards
]

# Customer name pools
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica",
    "Ahmed", "Mohammed", "Fatima", "Ali", "Hassan", "Sarah", "Aisha", "Omar",
    "Wei", "Yan", "Fang", "Lei", "Ming", "Jing", "Hui", "Ling",
    "Carlos", "Jose", "Maria", "Antonio", "Luis", "Ana", "Rosa", "Manuel",
    "Raj", "Priya", "Amit", "Anita", "Ravi", "Sita", "Kumar", "Maya"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Khan", "Ali", "Hassan", "Ahmed", "Hussain", "Shah", "Malik", "Rahman",
    "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao",
    "Kumar", "Singh", "Patel", "Sharma", "Gupta", "Reddy", "Desai", "Mehta"
]

# Special requests pool
SPECIAL_REQUESTS = [
    "", "", "", "", "",  # 50% no special requests
    "Extra spicy", "Mild spice", "No onions", "No garlic", "Extra sauce",
    "Well done", "Less oil", "No salt", "Gluten free option", "Vegan option",
    "Extra vegetables", "No cilantro", "Extra cheese", "Light portion", "Extra portion"
]

# Order type distribution
ORDER_TYPES = [
    {"type": "TABLE", "weight": 0.50},      # 50% dine-in
    {"type": "ONLINE", "weight": 0.50},     # 50% online orders
]

# Tax rate
TAX_RATE = 0.10  # 10% tax

# Stats tracking
stats = {
    "orders_created": 0,
    "orders_failed": 0,
    "total_revenue": 0.0,
    "by_payment_method": {},
    "by_hour": {},
    "by_order_type": {}
}

def generate_random_name():
    """Generate realistic customer name"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    return f"{first_name} {last_name}"

def generate_phone():
    """Generate realistic phone number"""
    area_code = random.choice([201, 202, 203, 212, 213, 214, 215, 216, 305, 310, 312, 404, 415, 510, 617, 650, 702, 713, 718, 808, 916])
    number = f"+1{area_code}{random.randint(1000000, 9999999)}"
    return number

def generate_email(name):
    """Generate realistic email"""
    first, last = name.lower().split()
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "mail.com"]
    formats = [
        f"{first}.{last}@{random.choice(domains)}",
        f"{first}{last}@{random.choice(domains)}",
        f"{first}{random.randint(1, 999)}@{random.choice(domains)}",
        f"{first[0]}{last}@{random.choice(domains)}"
    ]
    return random.choice(formats)

def select_payment_method():
    """Select payment method based on distribution"""
    methods = [pm["method"] for pm in PAYMENT_METHODS]
    weights = [pm["weight"] for pm in PAYMENT_METHODS]
    return random.choices(methods, weights=weights, k=1)[0]

def select_order_type():
    """Select order type based on distribution"""
    types = [ot["type"] for ot in ORDER_TYPES]
    weights = [ot["weight"] for ot in ORDER_TYPES]
    return random.choices(types, weights=weights, k=1)[0]

def generate_order_items():
    """Generate realistic order items based on meal patterns"""
    items = []

    # Determine order size (1-8 items, most common: 2-4)
    num_items = random.choices(
        [1, 2, 3, 4, 5, 6, 7, 8],
        weights=[0.10, 0.20, 0.25, 0.20, 0.12, 0.08, 0.03, 0.02],
        k=1
    )[0]

    # Build meal based on categories
    # 70% chance of appetizer for larger orders
    if num_items >= 3 and random.random() < 0.7 and APPETIZERS:
        appetizer = random.choice(APPETIZERS)
        quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
        items.append({
            "menu_item_id": appetizer["id"],
            "quantity": quantity,
            "special_instructions": random.choice(SPECIAL_REQUESTS)
        })

    # Always add 1-2 main courses
    num_mains = min(random.choices([1, 2, 3], weights=[0.60, 0.35, 0.05])[0], num_items - len(items))
    for _ in range(num_mains):
        if MAIN_COURSES:
            main = random.choice(MAIN_COURSES)
            quantity = random.choices([1, 2, 3], weights=[0.70, 0.25, 0.05])[0]
            items.append({
                "menu_item_id": main["id"],
                "quantity": quantity,
                "special_instructions": random.choice(SPECIAL_REQUESTS)
            })

    # 40% chance of side dish
    if num_items > len(items) and random.random() < 0.4 and SIDE_DISHES:
        side = random.choice(SIDE_DISHES)
        quantity = random.choices([1, 2], weights=[0.85, 0.15])[0]
        items.append({
            "menu_item_id": side["id"],
            "quantity": quantity,
            "special_instructions": random.choice(SPECIAL_REQUESTS)
        })

    # Add beverages (80% of orders have at least one drink)
    num_beverages = min(
        random.choices([0, 1, 2, 3], weights=[0.20, 0.50, 0.25, 0.05])[0],
        num_items - len(items)
    )
    for _ in range(num_beverages):
        if BEVERAGES:
            beverage = random.choice(BEVERAGES)
            quantity = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
            items.append({
                "menu_item_id": beverage["id"],
                "quantity": quantity,
                "special_instructions": ""
            })

    # 30% chance of dessert
    if num_items > len(items) and random.random() < 0.3 and DESSERTS:
        dessert = random.choice(DESSERTS)
        quantity = random.choices([1, 2], weights=[0.80, 0.20])[0]
        items.append({
            "menu_item_id": dessert["id"],
            "quantity": quantity,
            "special_instructions": random.choice(SPECIAL_REQUESTS)
        })

    # Ensure we have at least 1 item
    if not items and MENU_ITEMS:
        item = random.choice(MENU_ITEMS)
        items.append({
            "menu_item_id": item["id"],
            "quantity": 1,
            "special_instructions": ""
        })

    return items

def calculate_order_total(items):
    """Calculate order subtotal based on items"""
    subtotal = 0.0
    for item in items:
        menu_item = next((m for m in MENU_ITEMS if m["id"] == item["menu_item_id"]), None)
        if menu_item:
            subtotal += menu_item["price"] * item["quantity"]
    return subtotal

def create_order(order_data):
    """Create order via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/orders",
            json=order_data,
            timeout=15,
            verify=True
        )

        if response.status_code == 201:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)[:200]}"
    except Exception as e:
        return False, f"Error: {str(e)[:200]}"

def update_order_status(order_id, status):
    """Update order status via API"""
    try:
        response = requests.patch(
            f"{API_BASE_URL}/orders/{order_id}/status",
            json={"status": status},
            timeout=10,
            verify=True
        )
        return response.status_code == 200
    except:
        return False

def generate_orders_for_today(target_orders=250):
    """Generate orders for today with realistic time distribution"""

    print(f"\n{'='*80}")
    print(f"📊 DAILY ORDER GENERATOR - {RESTAURANT_NAME}")
    print(f"{'='*80}")
    print(f"Target Orders: {target_orders}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %A')}")
    print(f"API: {API_BASE_URL}")
    print(f"{'='*80}\n")

    # Test API connection
    print("🔍 Testing API connection...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5, verify=True)
        if response.status_code == 200:
            print("✅ API is accessible\n")
        else:
            print(f"⚠️  API returned status {response.status_code}\n")
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        print("\nTroubleshooting:")
        print("1. Check if services are running: kubectl get pods -n restaurant-system")
        print("2. Verify API gateway is accessible")
        print("3. Check network connectivity\n")
        return

    print(f"🚀 Starting order generation...\n")

    # Generate orders distributed across the day
    orders_by_hour = {}
    total_weight = sum(HOUR_DISTRIBUTION.values())

    # Calculate how many orders per hour
    for hour, weight in HOUR_DISTRIBUTION.items():
        num_orders = int((weight / total_weight) * target_orders)
        orders_by_hour[hour] = num_orders

    # Adjust to hit exact target
    current_total = sum(orders_by_hour.values())
    if current_total < target_orders:
        # Add remaining orders to peak hours (12, 19)
        peak_hours = [12, 13, 19, 20]
        for _ in range(target_orders - current_total):
            hour = random.choice(peak_hours)
            orders_by_hour[hour] += 1

    # Generate orders
    for hour in range(24):
        num_orders = orders_by_hour.get(hour, 0)
        if num_orders == 0:
            continue

        print(f"⏰ Hour {hour:02d}:00 - Generating {num_orders} orders...")
        hour_revenue = 0.0

        for order_num in range(num_orders):
            # Generate order details
            customer_name = generate_random_name()
            customer_phone = generate_phone()
            order_type = select_order_type()
            payment_method = select_payment_method()
            items = generate_order_items()

            # Calculate totals
            subtotal = calculate_order_total(items)
            tax = round(subtotal * TAX_RATE, 2)

            # Random discount (10% of orders get 5-20% discount)
            discount = 0.0
            if random.random() < 0.10:
                discount_percent = random.choice([0.05, 0.10, 0.15, 0.20])
                discount = round(subtotal * discount_percent, 2)

            total = round(subtotal + tax - discount, 2)

            # Build order payload
            order_data = {
                "restaurant_id": RESTAURANT_ID,
                "table_id": TABLE_ID if order_type == "TABLE" else None,
                "order_type": order_type,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "special_instructions": random.choice([
                    "", "", "", "",  # 40% no instructions
                    "Please deliver to room 205",
                    "Call on arrival",
                    "Ring doorbell",
                    "Leave at door",
                    "Contactless delivery",
                    "ASAP please"
                ]),
                "items": items,
                "payment_method": payment_method,
            }

            # Create order
            success, result = create_order(order_data)

            if success:
                stats["orders_created"] += 1
                stats["total_revenue"] += total
                hour_revenue += total

                # Track by payment method
                stats["by_payment_method"][payment_method] = stats["by_payment_method"].get(payment_method, 0) + 1

                # Track by order type
                stats["by_order_type"][order_type] = stats["by_order_type"].get(order_type, 0) + 1

                order_id = result.get("id")

                # Progress order through statuses (90% complete, 10% stay in progress)
                if random.random() < 0.90:
                    # Complete the order
                    statuses = ["CONFIRMED", "PREPARING", "READY", "SERVED", "COMPLETED"]
                    for status in statuses:
                        update_order_status(order_id, status)
                        time.sleep(0.05)  # Small delay between status updates
                else:
                    # Leave in progress
                    statuses = random.choice([
                        ["CONFIRMED"],
                        ["CONFIRMED", "PREPARING"],
                        ["CONFIRMED", "PREPARING", "READY"],
                        ["CONFIRMED", "PREPARING", "READY", "SERVED"]
                    ])
                    for status in statuses:
                        update_order_status(order_id, status)
                        time.sleep(0.05)

                # Progress indicator
                if (order_num + 1) % 5 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()

                # Small delay to avoid rate limiting
                time.sleep(0.1)
            else:
                stats["orders_failed"] += 1
                if stats["orders_failed"] <= 3:
                    print(f"\n   ❌ Order failed: {result}")

        # Track by hour
        stats["by_hour"][hour] = {
            "orders": num_orders,
            "revenue": hour_revenue
        }

        print(f" ✓ ${hour_revenue:.2f} revenue")

    # Print summary
    print(f"\n{'='*80}")
    print(f"📈 GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Orders Created: {stats['orders_created']}")
    print(f"❌ Orders Failed: {stats['orders_failed']}")
    print(f"💰 Total Revenue: ${stats['total_revenue']:.2f}")
    print(f"💵 Average Order: ${stats['total_revenue']/max(stats['orders_created'], 1):.2f}")

    print(f"\n📊 BY PAYMENT METHOD:")
    for method, count in sorted(stats["by_payment_method"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['orders_created']) * 100
        print(f"   {method.replace('_', ' ').title():<20} {count:>4} orders ({percentage:>5.1f}%)")

    print(f"\n🍽️  BY ORDER TYPE:")
    for order_type, count in sorted(stats["by_order_type"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['orders_created']) * 100
        print(f"   {order_type.title():<20} {count:>4} orders ({percentage:>5.1f}%)")

    print(f"\n⏰ PEAK HOURS:")
    sorted_hours = sorted(stats["by_hour"].items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]
    for hour, data in sorted_hours:
        print(f"   {hour:02d}:00-{hour+1:02d}:00  {data['orders']:>3} orders  ${data['revenue']:>8.2f}")

    print(f"\n{'='*80}")
    print(f"✨ Success Rate: {(stats['orders_created']/(stats['orders_created']+stats['orders_failed'])*100):.1f}%")
    print(f"{'='*80}\n")

    print("📊 Analytics Ready!")
    print(f"View analytics: {API_BASE_URL.replace('/api/v1', '')}/analytics")
    print(f"View predictions: GET {API_BASE_URL}/restaurants/{RESTAURANT_ID}/analytics/predictions/demand")
    print(f"View revenue: GET {API_BASE_URL}/restaurants/{RESTAURANT_ID}/analytics/revenue\n")

def main():
    """Main entry point"""
    target_orders = 250

    # Allow custom number via command line
    if len(sys.argv) > 1:
        try:
            target_orders = int(sys.argv[1])
            if target_orders < 1 or target_orders > 1000:
                print("❌ Please provide a number between 1 and 1000")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid number. Usage: python generate_daily_orders.py [number_of_orders]")
            sys.exit(1)

    generate_orders_for_today(target_orders)

if __name__ == "__main__":
    main()
