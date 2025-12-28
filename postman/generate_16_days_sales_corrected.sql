- Generate 16 days of sales data for phalwan Briyani restaurant
-- Each day: 15 orders
-- All orders are marked as completed

-- Restaurant ID
\set restaurant_id '52c0d315-b894-40c6-be52-3416a9d0a1e7'

-- 1. Create Menu Items if they don't exist
INSERT INTO menu_items (id, restaurant_id, name, description, category, price, is_available, is_vegetarian, ingredients, allergens, display_order, created_at, updated_at)
VALUES
  (gen_random_uuid(), :'restaurant_id', 'Chicken Biryani', 'Aromatic basmati rice with tender chicken', 'MAIN_COURSE', 299.00, true, false, '["basmati rice","chicken","spices","saffron"]', '["dairy"]', 1, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Mutton Biryani', 'Slow-cooked mutton with fragrant rice', 'MAIN_COURSE', 399.00, true, false, '["basmati rice","mutton","spices","saffron"]', '["dairy"]', 2, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Veg Biryani', 'Mixed vegetables with aromatic rice', 'MAIN_COURSE', 199.00, true, true, '["basmati rice","vegetables","spices"]', '[]', 3, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Hyderabadi Biryani', 'Special Hyderabadi style biryani', 'MAIN_COURSE', 449.00, true, false, '["basmati rice","chicken","spices","saffron","fried onions"]', '["dairy"]', 4, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Raita', 'Cooling yogurt with cucumber', 'SIDE_DISH', 49.00, true, true, '["yogurt","cucumber","spices"]', '["dairy"]', 5, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Gulab Jamun', 'Sweet milk dumplings in syrup', 'DESSERT', 79.00, true, true, '["milk solids","sugar","cardamom"]', '["dairy"]', 6, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Lassi', 'Traditional yogurt drink', 'BEVERAGE', 59.00, true, true, '["yogurt","sugar","cardamom"]', '["dairy"]', 7, NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'Tandoori Chicken', 'Grilled marinated chicken', 'APPETIZER', 249.00, true, false, '["chicken","yogurt","spices"]', '["dairy"]', 8, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- 2. Create Tables if they don't exist
INSERT INTO tables (id, restaurant_id, table_number, seat_count, status, floor, section, created_at, updated_at)
VALUES
  (gen_random_uuid(), :'restaurant_id', 'T1', 4, 'AVAILABLE', 'Ground Floor', 'Main Hall', NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'T2', 4, 'AVAILABLE', 'Ground Floor', 'Main Hall', NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'T3', 2, 'AVAILABLE', 'Ground Floor', 'Window', NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'T4', 6, 'AVAILABLE', 'Ground Floor', 'Family', NOW(), NOW()),
  (gen_random_uuid(), :'restaurant_id', 'T5', 4, 'AVAILABLE', 'First Floor', 'VIP', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Get menu item IDs for later use
CREATE TEMP TABLE temp_menu AS
SELECT id, name, price FROM menu_items WHERE restaurant_id = :'restaurant_id';

CREATE TEMP TABLE temp_tables AS
SELECT id, table_number FROM tables WHERE restaurant_id = :'restaurant_id';

-- 3. Generate 16 days of orders (15 orders per day)
DO $$
DECLARE
  v_day_offset INT;
  v_order_num INT;
  v_order_date TIMESTAMP;
  v_order_id UUID;
  v_table_id UUID;
  v_order_number TEXT;
  v_item_count INT;
  v_menu_item RECORD;
  v_subtotal FLOAT;
  v_tax FLOAT;
  v_total FLOAT;
  v_quantity INT;
  v_customer_names TEXT[] := ARRAY['Rajesh Kumar', 'Priya Sharma', 'Amit Patel', 'Sneha Reddy', 'Vikram Singh', 'Anjali Mehta', 'Rahul Gupta', 'Deepa Krishnan', 'Arjun Nair', 'Kavita Joshi'];
  v_customer_phones TEXT[] := ARRAY['9876543210', '9876543211', '9876543212', '9876543213', '9876543214', '9876543215', '9876543216', '9876543217', '9876543218', '9876543219'];
BEGIN
  -- Loop through 16 days
  FOR v_day_offset IN 0..15 LOOP
    -- 15 orders per day
    FOR v_order_num IN 1..15 LOOP
      -- Calculate order date (spread throughout the day)
      v_order_date := (CURRENT_DATE - v_day_offset) + (v_order_num || ' hours')::INTERVAL + (FLOOR(RANDOM() * 60) || ' minutes')::INTERVAL;

      -- Pick random table for all orders (restaurant-service orders are table-based)
      SELECT id INTO v_table_id FROM temp_tables ORDER BY RANDOM() LIMIT 1;

      -- Generate order number
      v_order_number := 'ORD-' || TO_CHAR(v_order_date, 'YYYYMMDD') || '-' || LPAD((v_day_offset * 15 + v_order_num)::TEXT, 4, '0');

      -- Create order
      v_order_id := gen_random_uuid();
      v_subtotal := 0;

      -- Determine number of items (1-4 items per order)
      v_item_count := 1 + FLOOR(RANDOM() * 4);

      -- Insert order first
      INSERT INTO orders (
        id, restaurant_id, table_id, order_number, status,
        customer_name, customer_phone, subtotal, tax, total,
        created_at, updated_at, completed_at
      ) VALUES (
        v_order_id,
        '52c0d315-b894-40c6-be52-3416a9d0a1e7',
        v_table_id,
        v_order_number,
        'COMPLETED',  -- All orders completed
        v_customer_names[1 + FLOOR(RANDOM() * 10)],
        v_customer_phones[1 + FLOOR(RANDOM() * 10)],
        0,  -- Will update after items
        0,
        0,
        v_order_date,
        v_order_date + (30 || ' minutes')::INTERVAL,
        v_order_date + (45 || ' minutes')::INTERVAL
      );

      -- Add random menu items
      FOR i IN 1..v_item_count LOOP
        SELECT * INTO v_menu_item FROM temp_menu ORDER BY RANDOM() LIMIT 1;
        v_quantity := 1 + FLOOR(RANDOM() * 3);  -- 1-3 quantity

        INSERT INTO order_items (
          id, order_id, menu_item_id, item_name, item_price, quantity, created_at
        ) VALUES (
          gen_random_uuid(),
          v_order_id,
          v_menu_item.id,
          v_menu_item.name,
          v_menu_item.price,
          v_quantity,
          v_order_date
        );

        v_subtotal := v_subtotal + (v_menu_item.price * v_quantity);
      END LOOP;

      -- Calculate tax and total
      v_tax := v_subtotal * 0.05;  -- 5% tax
      v_total := v_subtotal + v_tax;

      -- Update order with totals
      UPDATE orders
      SET subtotal = v_subtotal, tax = v_tax, total = v_total
      WHERE id = v_order_id;

    END LOOP;
  END LOOP;

  RAISE NOTICE 'Created 240 orders (16 days × 15 orders) for phalwan Briyani';
END $$;

-- Summary
SELECT
  DATE(created_at) as order_date,
  COUNT(*) as order_count,
  SUM(total)::NUMERIC(10,2) as daily_revenue
FROM orders
WHERE restaurant_id = '52c0d315-b894-40c6-be52-3416a9d0a1e7'
  AND created_at >= CURRENT_DATE - 16
GROUP BY DATE(created_at)
ORDER BY order_date DESC;
