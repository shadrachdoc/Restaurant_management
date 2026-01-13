#!/bin/bash
# Generate 1 month of fake order data using SQL

echo "🍽️  Generating fake order data for 1 month..."
echo "============================================================"

# Get restaurant and table info
RESTAURANT_ID="6956017d-3aea-4ae2-9709-0ca0ac0a1a09"
TABLE_ID="3aaf3785-cf1d-4633-891f-69e7a4dec0d5"

# Menu items
declare -a MENU_IDS=(
    "aaf9ad8c-ee6a-4bb6-84f9-4f0f7cf3f11e"  # biriyani - 6.5
    "898ff00e-ff95-41fe-b15f-121ccb619be9"  # Green Radish Salad - 5
    "18386a1a-89a8-497d-b90b-02d0cf33b48a"  # Salad - 3
    "2fd2992b-07f3-443f-84b1-205886fad55e"  # Coke Zero - 3
    "0e29036f-e2d6-449d-95e5-72f610b0535c"  # Craft Beer - 5
    "3681df63-ab0c-41c8-984b-509780450901"  # HereNow Creme Caramel - 5
    "e51bc2df-de77-47da-b44c-68b10e5f35d9"  # Pan Fried Salmon - 12
    "1e01fbfa-96b0-450f-b46f-661dc65bc3d1"  # Salad Bites - 7
    "b43974b8-65c5-43d4-b92c-c42751f07d2d"  # Birthday Cake - 1
)

declare -a MENU_NAMES=(
    "biriyani"
    "Green Radish Salad"
    "Salad"
    "Coke Zero"
    "Craft Beer"
    "HereNow Creme Caramel"
    "Pan Fried Salmon"
    "Salad Bites"
    "Birthday Cake"
)

declare -a MENU_PRICES=(6.5 5 3 3 5 5 12 7 1)

# Customer names
declare -a NAMES=("John Doe" "Jane Smith" "Bob Wilson" "Alice Brown" "Charlie Davis" "Eva Martinez" "Frank Johnson" "Grace Lee")

# Function to generate random order
generate_orders_sql() {
    local num_orders=$1
    local sql_file="/tmp/fake_orders.sql"

    echo "-- Generated fake orders for testing ML predictions" > $sql_file
    echo "BEGIN;" >> $sql_file

    total_orders=0

    # Generate orders for past 30 days
    for day in {0..30}; do
        # Calculate orders for this day (weekends have more)
        dow=$(date -d "30 days ago + $day days" +%u)
        if [ $dow -ge 5 ]; then
            # Weekend: 40-60 orders
            day_orders=$((40 + RANDOM % 21))
        else
            # Weekday: 25-40 orders
            day_orders=$((25 + RANDOM % 16))
        fi

        for ((i=1; i<=day_orders; i++)); do
            # Generate random timestamp
            hour=$((RANDOM % 24))
            # Weight towards lunch (12-14) and dinner (18-21)
            if [ $((RANDOM % 100)) -lt 40 ]; then
                if [ $((RANDOM % 2)) -eq 0 ]; then
                    hour=$((12 + RANDOM % 3))  # Lunch: 12-14
                else
                    hour=$((18 + RANDOM % 4))  # Dinner: 18-21
                fi
            fi

            minute=$((RANDOM % 60))
            second=$((RANDOM % 60))

            # Calculate timestamp
            timestamp=$(date -d "30 days ago + $day days $hour:$minute:$second" '+%Y-%m-%d %H:%M:%S')

            # Random order details
            order_id=$(uuidgen)
            order_number="ORD-$(date +%Y%m%d%H%M%S)-$(openssl rand -hex 3 | tr '[:lower:]' '[:upper:]')"
            customer_name="${NAMES[$((RANDOM % ${#NAMES[@]}))]}"
            customer_phone="+1$((1000000000 + RANDOM % 9000000000))"

            # Select 1-3 menu items
            num_items=$((1 + RANDOM % 3))
            subtotal=0

            # Create order
            echo "INSERT INTO orders (id, restaurant_id, table_id, order_number, status, order_type, customer_name, customer_phone, subtotal, tax, total, created_at, updated_at, completed_at) VALUES" >> $sql_file

            # Calculate subtotal (will update later)
            echo "('$order_id', '$RESTAURANT_ID', '$TABLE_ID', '$order_number', 'COMPLETED', 'TABLE', '$customer_name', '$customer_phone', 0, 0, 0, '$timestamp', '$timestamp', '$timestamp');" >> $sql_file

            # Add order items
            for ((j=0; j<num_items; j++)); do
                idx=$((RANDOM % ${#MENU_IDS[@]}))
                menu_id="${MENU_IDS[$idx]}"
                menu_name="${MENU_NAMES[$idx]}"
                menu_price="${MENU_PRICES[$idx]}"
                quantity=$((1 + RANDOM % 2))

                item_id=$(uuidgen)

                echo "INSERT INTO order_items (id, order_id, menu_item_id, item_name, item_price, quantity) VALUES" >> $sql_file
                echo "('$item_id', '$order_id', '$menu_id', '$menu_name', $menu_price, $quantity);" >> $sql_file
            done

            total_orders=$((total_orders + 1))
        done

        day_date=$(date -d "30 days ago + $day days" '+%Y-%m-%d (%A)')
        echo "Generated $day_orders orders for $day_date"
    done

    # Update order totals based on items
    echo "" >> $sql_file
    echo "-- Update order totals from items" >> $sql_file
    echo "UPDATE orders SET" >> $sql_file
    echo "  subtotal = (SELECT SUM(item_price * quantity) FROM order_items WHERE order_items.order_id = orders.id)," >> $sql_file
    echo "  tax = (SELECT SUM(item_price * quantity) * 0.10 FROM order_items WHERE order_items.order_id = orders.id)," >> $sql_file
    echo "  total = (SELECT SUM(item_price * quantity) * 1.10 FROM order_items WHERE order_items.order_id = orders.id)" >> $sql_file
    echo "WHERE created_at >= NOW() - INTERVAL '31 days';" >> $sql_file

    echo "COMMIT;" >> $sql_file

    echo ""
    echo "============================================================"
    echo "✓ Total orders generated: $total_orders"
    echo "✓ SQL file created: $sql_file"
    echo ""
    echo "Executing SQL..."

    # Execute SQL
    kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db < $sql_file

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Fake data generation complete!"
        echo ""
        echo "Next steps:"
        echo "1. Access order-service to trigger ML training:"
        echo "   kubectl port-forward -n restaurant-system svc/order-service 8004:8004"
        echo "   curl -X POST http://localhost:8004/api/v1/analytics/train"
        echo "2. Get predictions:"
        echo "   curl http://localhost:8004/api/v1/analytics/predictions"
        echo "3. View analytics in admin dashboard"
    else
        echo "❌ Failed to execute SQL"
    fi
}

# Generate 900-1200 orders over 30 days
generate_orders_sql 1000
