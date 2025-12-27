-- Backdate Orders Over 60 Days with Weekend Peaks
-- Run this script AFTER creating 200 orders with Collection 2

-- This script updates order timestamps to spread them over 60 days
-- with more orders on Friday/Saturday (weekend peak pattern)

WITH numbered_orders AS (
  SELECT
    id,
    created_at,
    ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
    COUNT(*) OVER () as total_orders
  FROM orders
  WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
    AND created_at >= NOW() - INTERVAL '1 hour'  -- Only recent orders from Postman
),
historical_dates AS (
  SELECT
    id,
    created_at,
    row_num,
    -- Calculate days ago (0-59)
    FLOOR((row_num::float / total_orders) * 60)::int as days_ago,
    -- Calculate day of week (0=Sunday, 5=Friday, 6=Saturday)
    EXTRACT(DOW FROM (NOW() - (FLOOR((row_num::float / total_orders) * 60)::int || ' days')::interval)) as day_of_week
  FROM numbered_orders
),
final_timestamps AS (
  SELECT
    id,
    created_at,
    days_ago,
    day_of_week,
    -- Calculate new timestamp
    -- Weekends get more density, so we adjust the distribution
    CASE
      -- Friday (5) or Saturday (6) - concentrate orders
      WHEN day_of_week IN (5, 6) THEN
        NOW() - (days_ago || ' days')::interval +
        (FLOOR(RANDOM() * 12) + 10 || ' hours')::interval  -- 10am-10pm
      -- Weekdays - spread them out more
      ELSE
        NOW() - (days_ago || ' days')::interval +
        (FLOOR(RANDOM() * 10) + 11 || ' hours')::interval  -- 11am-9pm
    END as new_created_at
  FROM historical_dates
)
UPDATE orders o
SET
  created_at = f.new_created_at,
  updated_at = f.new_created_at
FROM final_timestamps f
WHERE o.id = f.id;

-- Verify the update
SELECT
  DATE(created_at) as order_date,
  EXTRACT(DOW FROM created_at) as day_of_week,
  TO_CHAR(created_at, 'Day') as day_name,
  COUNT(*) as order_count
FROM orders
WHERE restaurant_id = '73332393-3c58-47c1-b58e-6d2ab59e96bb'
  AND created_at >= NOW() - INTERVAL '60 days'
GROUP BY DATE(created_at), EXTRACT(DOW FROM created_at), TO_CHAR(created_at, 'Day')
ORDER BY order_date DESC;
