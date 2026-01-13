#!/bin/bash
#
# Master Script to Generate All Fake Data
# This script runs all data generation tasks in the correct order
#

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================================="
echo "🚀 FAKE DATA GENERATION - MASTER SCRIPT"
echo "============================================================================="
echo "Location: $SCRIPT_DIR"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================================="
echo ""

# Function to run command with status
run_step() {
    local step_name="$1"
    local step_cmd="$2"

    echo "⏳ $step_name..."
    if eval "$step_cmd"; then
        echo "✅ $step_name - SUCCESS"
        echo ""
    else
        echo "❌ $step_name - FAILED"
        echo ""
        return 1
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi
echo "✅ kubectl: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

# Check postgres pod
if ! kubectl get pod postgres-0 -n restaurant-system &> /dev/null; then
    echo "❌ PostgreSQL pod not found"
    exit 1
fi
echo "✅ PostgreSQL pod: Running"
echo ""

# Get user input
echo "============================================================================="
echo "📊 CONFIGURATION"
echo "============================================================================="
echo ""
echo "What would you like to generate?"
echo ""
echo "1. Quick Test (10 orders today)"
echo "2. Daily Orders (250 orders today) ⭐ RECOMMENDED"
echo "3. Historical Data (30 days, 1000 orders)"
echo "4. Full Setup (30 days history + today's orders)"
echo "5. Custom"
echo ""
read -p "Choose option [1-5]: " option

case $option in
    1)
        echo ""
        echo "🎯 Quick Test: Generating 10 orders for today..."
        echo ""
        python3 generate_daily_orders_sql.py
        # Modify script temporarily (quick hack)
        python3 -c "
import subprocess
orders = 10
exec(open('generate_daily_orders_sql.py').read().replace('target_orders = 250', f'target_orders = {orders}'))
"
        ;;

    2)
        echo ""
        echo "🎯 Daily Orders: Generating 250 orders for today..."
        echo ""
        run_step "Generate 250 orders" "python3 generate_daily_orders_sql.py"
        ;;

    3)
        echo ""
        echo "🎯 Historical Data: Generating 1000 orders over 30 days..."
        echo ""
        if [ -f "generate_fake_orders.py" ]; then
            run_step "Generate historical data" "python3 generate_fake_orders.py --days 30 --orders 1000"
        else
            echo "⚠️  Historical data script not found, skipping..."
        fi
        ;;

    4)
        echo ""
        echo "🎯 Full Setup: Historical + Today's orders..."
        echo ""

        if [ -f "generate_fake_orders.py" ]; then
            run_step "Step 1: Generate 30 days of historical data (1000 orders)" \
                     "python3 generate_fake_orders.py --days 30 --orders 1000"
        fi

        run_step "Step 2: Generate today's orders (250 orders)" \
                 "python3 generate_daily_orders_sql.py"
        ;;

    5)
        echo ""
        read -p "How many orders for today? [1-1000]: " custom_orders

        if [ "$custom_orders" -lt 1 ] || [ "$custom_orders" -gt 1000 ]; then
            echo "❌ Invalid number. Must be between 1 and 1000"
            exit 1
        fi

        echo ""
        echo "🎯 Custom: Generating $custom_orders orders for today..."
        echo ""

        # Create temp script with custom order count
        tmp_script=$(mktemp)
        sed "s/target_orders = 250/target_orders = $custom_orders/" generate_daily_orders_sql.py > "$tmp_script"
        run_step "Generate $custom_orders orders" "python3 $tmp_script"
        rm "$tmp_script"
        ;;

    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "============================================================================="
echo "📈 VERIFICATION"
echo "============================================================================="
echo ""

# Verify results
echo "🔍 Checking database..."
echo ""

# Get today's stats
TODAY_STATS=$(kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -t -c \
    "SELECT COUNT(*), ROUND(CAST(SUM(total) as numeric), 2) FROM orders WHERE DATE(created_at) = CURRENT_DATE;" 2>/dev/null | xargs)

TODAY_ORDERS=$(echo $TODAY_STATS | awk '{print $1}')
TODAY_REVENUE=$(echo $TODAY_STATS | awk '{print $2}')

echo "📊 Today's Orders: $TODAY_ORDERS"
echo "💰 Today's Revenue: \$$TODAY_REVENUE"
echo ""

# Get total stats
TOTAL_STATS=$(kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -t -c \
    "SELECT COUNT(*), ROUND(CAST(SUM(total) as numeric), 2) FROM orders;" 2>/dev/null | xargs)

TOTAL_ORDERS=$(echo $TOTAL_STATS | awk '{print $1}')
TOTAL_REVENUE=$(echo $TOTAL_STATS | awk '{print $2}')

echo "📊 Total Orders: $TOTAL_ORDERS"
echo "💰 Total Revenue: \$$TOTAL_REVENUE"
echo ""

# Get popular items
echo "🏆 Top 5 Popular Items Today:"
kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db -t -c \
    "SELECT ROW_NUMBER() OVER (ORDER BY SUM(oi.quantity) DESC) as rank,
            mi.name,
            SUM(oi.quantity) as total_qty
     FROM order_items oi
     JOIN menu_items mi ON oi.menu_item_id = mi.id
     JOIN orders o ON oi.order_id = o.id
     WHERE DATE(o.created_at) = CURRENT_DATE
     GROUP BY mi.name
     ORDER BY total_qty DESC
     LIMIT 5;" 2>/dev/null | awk '{print "   " $0}'

echo ""

# Check predictions API
echo "🔮 Testing Predictions API..."
PREDICTIONS=$(curl -s "https://restaurant.corpv3.com/api/v1/restaurants/6956017d-3aea-4ae2-9709-0ca0ac0a1a09/analytics/predictions/demand" | grep -o '"menu_item_id"' | wc -l)
echo "   Available predictions: $PREDICTIONS"
echo ""

echo "============================================================================="
echo "✅ COMPLETE"
echo "============================================================================="
echo ""
echo "🌐 View Analytics Dashboard:"
echo "   https://restaurant.corpv3.com/analytics"
echo ""
echo "📊 Check Predictions:"
echo "   curl -s 'https://restaurant.corpv3.com/api/v1/restaurants/6956017d-3aea-4ae2-9709-0ca0ac0a1a09/analytics/predictions/demand'"
echo ""
echo "🗄️  Query Database:"
echo "   kubectl exec -i postgres-0 -n restaurant-system -- psql -U restaurant_admin -d restaurant_db"
echo ""
echo "============================================================================="
echo ""

# Log results
LOG_FILE="/tmp/fake_data_generation_$(date +%Y%m%d_%H%M%S).log"
{
    echo "Fake Data Generation Log"
    echo "Date: $(date)"
    echo "Today's Orders: $TODAY_ORDERS"
    echo "Today's Revenue: \$$TODAY_REVENUE"
    echo "Total Orders: $TOTAL_ORDERS"
    echo "Total Revenue: \$$TOTAL_REVENUE"
} > "$LOG_FILE"

echo "📝 Log saved to: $LOG_FILE"
echo ""
