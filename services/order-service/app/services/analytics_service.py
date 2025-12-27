"""
Analytics Service for Order Service
Business logic for analytics queries with optimized SQL
"""
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, func
from shared.utils.logger import setup_logger

logger = setup_logger("analytics-service")


# ============================================================================
# Revenue Analytics
# ============================================================================

async def get_revenue_analytics(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date,
    group_by: str = "daily"
) -> Dict[str, Any]:
    """
    Get revenue analytics for a restaurant with grouping

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        start_date: Start date for analysis
        end_date: End date for analysis
        group_by: Grouping method (daily, weekly, monthly)

    Returns:
        Dictionary with revenue metrics grouped by period
    """
    # Determine date_trunc format based on grouping
    trunc_format = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month"
    }.get(group_by, "day")

    query = text("""
        SELECT
            DATE_TRUNC(:trunc_format, o.created_at) as period,
            SUM(o.total) as total_revenue,
            COUNT(o.id) as order_count,
            AVG(o.total) as avg_order_value
        FROM orders o
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= :end_date
            AND o.status NOT IN ('CANCELLED')
        GROUP BY DATE_TRUNC(:trunc_format, o.created_at)
        ORDER BY period ASC
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date,
        "trunc_format": trunc_format
    })

    metrics = []
    total_revenue = 0.0
    total_orders = 0

    for row in result.fetchall():
        period_revenue = float(row.total_revenue or 0)
        period_orders = int(row.order_count or 0)

        metrics.append({
            "period": row.period.date().isoformat() if row.period else "",
            "total_revenue": round(period_revenue, 2),
            "order_count": period_orders,
            "avg_order_value": round(float(row.avg_order_value or 0), 2)
        })

        total_revenue += period_revenue
        total_orders += period_orders

    return {
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "metrics": metrics,
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "overall_avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    }


# ============================================================================
# Popular Items Analysis
# ============================================================================

async def get_popular_items(
    db: AsyncSession,
    restaurant_id: UUID,
    days: int = 30,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get popular menu items ranked by various metrics

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        days: Number of days to analyze
        limit: Maximum number of items to return

    Returns:
        List of popular items with metrics and trends
    """
    # Calculate trend by comparing recent period to previous period
    half_days = days // 2

    query = text("""
        WITH recent_period AS (
            SELECT
                oi.menu_item_id,
                oi.item_name,
                SUM(oi.quantity) as quantity_sold,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.item_price * oi.quantity) as revenue,
                AVG(oi.item_price) as avg_price
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.restaurant_id = :restaurant_id
                AND o.created_at >= NOW() - make_interval(days => :days)
                AND o.status NOT IN ('CANCELLED')
            GROUP BY oi.menu_item_id, oi.item_name
        ),
        previous_period AS (
            SELECT
                oi.menu_item_id,
                SUM(oi.quantity) as quantity_sold
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.restaurant_id = :restaurant_id
                AND o.created_at >= NOW() - make_interval(days => :days)
                AND o.created_at < NOW() - make_interval(days => :half_days)
                AND o.status NOT IN ('CANCELLED')
            GROUP BY oi.menu_item_id
        )
        SELECT
            r.menu_item_id,
            r.item_name,
            r.order_count,
            r.quantity_sold,
            r.revenue,
            r.avg_price,
            CASE
                WHEN p.quantity_sold IS NULL OR p.quantity_sold = 0 THEN 'new'
                WHEN r.quantity_sold > p.quantity_sold * 1.1 THEN 'up'
                WHEN r.quantity_sold < p.quantity_sold * 0.9 THEN 'down'
                ELSE 'stable'
            END as trend,
            CASE
                WHEN p.quantity_sold IS NOT NULL AND p.quantity_sold > 0
                THEN ROUND(((r.quantity_sold - p.quantity_sold)::numeric / p.quantity_sold * 100), 2)
                ELSE NULL
            END as trend_percentage
        FROM recent_period r
        LEFT JOIN previous_period p ON r.menu_item_id = p.menu_item_id
        ORDER BY r.quantity_sold DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "days": days,
        "half_days": half_days,
        "limit": limit
    })

    items = []
    for row in result.fetchall():
        items.append({
            "menu_item_id": row.menu_item_id,
            "item_name": row.item_name,
            "order_count": row.order_count,
            "quantity_sold": row.quantity_sold,
            "revenue": round(float(row.revenue or 0), 2),
            "avg_price": round(float(row.avg_price or 0), 2),
            "trend": row.trend,
            "trend_percentage": float(row.trend_percentage) if row.trend_percentage is not None else None
        })

    return items


# ============================================================================
# Day-of-Week Pattern Analysis
# ============================================================================

async def get_day_patterns(
    db: AsyncSession,
    restaurant_id: UUID,
    weeks: int = 8
) -> List[Dict[str, Any]]:
    """
    Analyze sales patterns by day of week

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        weeks: Number of weeks to analyze

    Returns:
        List of day patterns with metrics
    """
    query = text("""
        WITH day_sales AS (
            SELECT
                EXTRACT(DOW FROM o.created_at) as day_number,
                TO_CHAR(o.created_at, 'Day') as day_name,
                COUNT(o.id) as orders,
                SUM(o.total) as revenue
            FROM orders o
            WHERE o.restaurant_id = :restaurant_id
                AND o.created_at >= NOW() - make_interval(weeks => :weeks)
                AND o.status NOT IN ('CANCELLED')
            GROUP BY EXTRACT(DOW FROM o.created_at), TO_CHAR(o.created_at, 'Day')
        ),
        popular_by_day AS (
            SELECT
                EXTRACT(DOW FROM o.created_at) as day_number,
                oi.item_name,
                SUM(oi.quantity) as quantity,
                ROW_NUMBER() OVER (PARTITION BY EXTRACT(DOW FROM o.created_at) ORDER BY SUM(oi.quantity) DESC) as rank
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE o.restaurant_id = :restaurant_id
                AND o.created_at >= NOW() - make_interval(weeks => :weeks)
                AND o.status NOT IN ('CANCELLED')
            GROUP BY EXTRACT(DOW FROM o.created_at), oi.item_name
        )
        SELECT
            ds.day_number,
            TRIM(ds.day_name) as day_of_week,
            ROUND(ds.orders::numeric / :weeks, 2) as avg_orders,
            ROUND(ds.revenue::numeric / :weeks, 2) as avg_revenue,
            ARRAY_AGG(pd.item_name ORDER BY pd.rank) FILTER (WHERE pd.rank <= 3) as popular_items
        FROM day_sales ds
        LEFT JOIN popular_by_day pd ON ds.day_number = pd.day_number
        GROUP BY ds.day_number, ds.day_name, ds.orders, ds.revenue
        ORDER BY ds.day_number
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "weeks": weeks
    })

    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    patterns = []

    for row in result.fetchall():
        patterns.append({
            "day_of_week": day_names[int(row.day_number)],
            "day_number": int(row.day_number),
            "avg_orders": float(row.avg_orders or 0),
            "avg_revenue": float(row.avg_revenue or 0),
            "popular_items": row.popular_items or []
        })

    return patterns


# ============================================================================
# Order Volume Analysis
# ============================================================================

async def get_order_volume(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date,
    group_by: str = "daily"
) -> Dict[str, Any]:
    """
    Get order volume trends with growth rates
    """
    trunc_format = {
        "hourly": "hour",
        "daily": "day",
        "weekly": "week",
        "monthly": "month"
    }.get(group_by, "day")

    query = text("""
        SELECT
            DATE_TRUNC(:trunc_format, o.created_at) as period,
            COUNT(o.id) as order_count,
            AVG(o.total) as avg_order_value
        FROM orders o
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= CAST(:end_date AS DATE)
            AND o.status NOT IN ('CANCELLED')
        GROUP BY DATE_TRUNC(:trunc_format, o.created_at)
        ORDER BY period ASC
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date,
        "trunc_format": trunc_format
    })

    metrics = []
    previous_count = None

    for row in result.fetchall():
        current_count = int(row.order_count or 0)
        growth_rate = None

        if previous_count is not None and previous_count > 0:
            growth_rate = round(((current_count - previous_count) / previous_count) * 100, 2)

        metrics.append({
            "period": row.period.isoformat() if row.period else "",
            "order_count": current_count,
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "growth_rate": growth_rate
        })

        previous_count = current_count

    return {
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "metrics": metrics
    }


# ============================================================================
# Category Performance
# ============================================================================

async def get_category_performance(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Get performance metrics by menu category

    Note: This requires menu_items table with category field
    Returns empty list if menu_items table not available
    """
    # This query assumes there's a menu_items table with category
    # If not available, we'll need to add category to order_items as snapshot
    query = text("""
        SELECT
            'main_course' as category,
            SUM(oi.item_price * oi.quantity) as revenue,
            COUNT(DISTINCT oi.order_id) as order_count,
            AVG(oi.item_price) as avg_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= CAST(:end_date AS DATE)
            AND o.status NOT IN ('CANCELLED')
        GROUP BY category
    """)

    try:
        result = await db.execute(query, {
            "restaurant_id": str(restaurant_id),
            "start_date": start_date,
            "end_date": end_date
        })

        categories = []
        for row in result.fetchall():
            categories.append({
                "category": row.category,
                "revenue": round(float(row.revenue or 0), 2),
                "order_count": int(row.order_count or 0),
                "avg_price": round(float(row.avg_price or 0), 2),
                "growth_percentage": None  # TODO: Calculate from previous period
            })

        return categories
    except Exception as e:
        logger.warning(f"Category performance query failed: {e}")
        return []


# ============================================================================
# Peak Hours Analysis
# ============================================================================

async def get_peak_hours(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Analyze order patterns by hour of day
    """
    query = text("""
        SELECT
            EXTRACT(HOUR FROM o.created_at) as hour,
            COUNT(o.id) as orders,
            SUM(o.total) as revenue
        FROM orders o
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= CAST(:end_date AS DATE)
            AND o.status NOT IN ('CANCELLED')
        GROUP BY EXTRACT(HOUR FROM o.created_at)
        ORDER BY hour
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date
    })

    # Calculate number of days for averaging
    days = (end_date - start_date).days + 1

    hourly_metrics = []
    busiest_hour = 0
    slowest_hour = 0
    max_orders = 0
    min_orders = float('inf')

    for row in result.fetchall():
        hour = int(row.hour)
        orders = int(row.orders or 0)
        avg_orders = orders / days if days > 0 else 0

        hourly_metrics.append({
            "hour": hour,
            "avg_orders": round(avg_orders, 2),
            "avg_revenue": round(float(row.revenue or 0) / days, 2)
        })

        if orders > max_orders:
            max_orders = orders
            busiest_hour = hour
        if orders < min_orders:
            min_orders = orders
            slowest_hour = hour

    return {
        "start_date": start_date,
        "end_date": end_date,
        "hourly_metrics": hourly_metrics,
        "busiest_hour": busiest_hour,
        "slowest_hour": slowest_hour
    }


# ============================================================================
# Sales Comparison
# ============================================================================

async def get_sales_comparison(
    db: AsyncSession,
    restaurant_id: UUID,
    period: str = "week"
) -> Dict[str, Any]:
    """
    Compare current period with previous period

    Args:
        period: week, month, quarter, year
    """
    interval_map = {
        "week": "7 days",
        "month": "1 month",
        "quarter": "3 months",
        "year": "1 year"
    }

    interval = interval_map.get(period, "7 days")

    # Use string formatting for INTERVAL since it can't be bound as parameter
    query = text(f"""
        WITH current_period AS (
            SELECT
                SUM(total) as revenue,
                COUNT(id) as orders,
                AVG(total) as avg_order_value
            FROM orders
            WHERE restaurant_id = :restaurant_id
                AND created_at >= NOW() - INTERVAL '{interval}'
                AND status NOT IN ('CANCELLED')
        ),
        previous_period AS (
            SELECT
                SUM(total) as revenue,
                COUNT(id) as orders,
                AVG(total) as avg_order_value
            FROM orders
            WHERE restaurant_id = :restaurant_id
                AND created_at >= NOW() - INTERVAL '{interval}' - INTERVAL '{interval}'
                AND created_at < NOW() - INTERVAL '{interval}'
                AND status NOT IN ('CANCELLED')
        )
        SELECT
            c.revenue as current_revenue,
            p.revenue as previous_revenue,
            c.orders as current_orders,
            p.orders as previous_orders,
            c.avg_order_value as current_avg,
            p.avg_order_value as previous_avg
        FROM current_period c, previous_period p
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id)
    })

    row = result.fetchone()

    if not row:
        return {}

    current_revenue = float(row.current_revenue or 0)
    previous_revenue = float(row.previous_revenue or 0)
    current_orders = int(row.current_orders or 0)
    previous_orders = int(row.previous_orders or 0)

    revenue_growth = 0.0
    if previous_revenue > 0:
        revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100

    orders_growth = 0.0
    if previous_orders > 0:
        orders_growth = ((current_orders - previous_orders) / previous_orders) * 100

    return {
        "current_revenue": round(current_revenue, 2),
        "previous_revenue": round(previous_revenue, 2),
        "current_orders": current_orders,
        "previous_orders": previous_orders,
        "current_avg_order_value": round(float(row.current_avg or 0), 2),
        "previous_avg_order_value": round(float(row.previous_avg or 0), 2),
        "revenue_growth_percentage": round(revenue_growth, 2),
        "orders_growth_percentage": round(orders_growth, 2)
    }


# ============================================================================
# Top Performers
# ============================================================================

async def get_top_performers(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date,
    rank_by: str = "revenue",
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get top performing items ranked by revenue, quantity, or orders
    """
    order_by_map = {
        "revenue": "revenue DESC",
        "quantity": "quantity_sold DESC",
        "orders": "order_count DESC"
    }

    order_by = order_by_map.get(rank_by, "revenue DESC")

    query = text(f"""
        SELECT
            oi.menu_item_id,
            oi.item_name,
            SUM(oi.quantity) as quantity_sold,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.item_price * oi.quantity) as revenue,
            AVG(oi.item_price) as avg_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= CAST(:end_date AS DATE)
            AND o.status NOT IN ('CANCELLED')
        GROUP BY oi.menu_item_id, oi.item_name
        ORDER BY {order_by}
        LIMIT :limit
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit
    })

    items = []
    rank = 1

    for row in result.fetchall():
        items.append({
            "rank": rank,
            "menu_item_id": row.menu_item_id,
            "item_name": row.item_name,
            "category": "unknown",  # TODO: Add category when available
            "revenue": round(float(row.revenue or 0), 2),
            "quantity_sold": int(row.quantity_sold or 0),
            "order_count": int(row.order_count or 0),
            "trend": "stable",  # TODO: Calculate trend
            "trend_percentage": None
        })
        rank += 1

    return items


# ============================================================================
# Order Type Breakdown
# ============================================================================

async def get_order_type_breakdown(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Analyze orders by type (table vs online)
    """
    query = text("""
        WITH totals AS (
            SELECT
                SUM(total) as total_revenue,
                COUNT(id) as total_orders
            FROM orders
            WHERE restaurant_id = :restaurant_id
                AND created_at >= CAST(:start_date AS DATE)
                AND created_at <= CAST(:end_date AS DATE)
                AND status NOT IN ('CANCELLED')
        )
        SELECT
            o.order_type,
            SUM(o.total) as revenue,
            COUNT(o.id) as order_count,
            AVG(o.total) as avg_order_value,
            (SUM(o.total) / t.total_revenue * 100) as percentage
        FROM orders o, totals t
        WHERE o.restaurant_id = :restaurant_id
            AND DATE(o.created_at) >= CAST(:start_date AS DATE)
            AND DATE(o.created_at) <= CAST(:end_date AS DATE)
            AND o.status NOT IN ('CANCELLED')
        GROUP BY o.order_type, t.total_revenue
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date
    })

    breakdown = []
    for row in result.fetchall():
        breakdown.append({
            "order_type": row.order_type,
            "revenue": round(float(row.revenue or 0), 2),
            "order_count": int(row.order_count or 0),
            "avg_order_value": round(float(row.avg_order_value or 0), 2),
            "percentage_of_total": round(float(row.percentage or 0), 2)
        })

    return breakdown


# ============================================================================
# Customer Behavior Metrics
# ============================================================================

async def get_customer_behavior(
    db: AsyncSession,
    restaurant_id: UUID,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Analyze customer behavior patterns
    """
    query = text("""
        WITH customer_orders AS (
            SELECT
                COALESCE(customer_id::text, customer_email, customer_phone) as customer_identifier,
                COUNT(id) as order_count,
                SUM(total) as total_spent,
                MIN(created_at) as first_order
            FROM orders
            WHERE restaurant_id = :restaurant_id
                AND created_at >= CAST(:start_date AS DATE)
                AND created_at <= CAST(:end_date AS DATE)
                AND status NOT IN ('CANCELLED')
                AND (customer_id IS NOT NULL OR customer_email IS NOT NULL OR customer_phone IS NOT NULL)
            GROUP BY COALESCE(customer_id::text, customer_email, customer_phone)
        )
        SELECT
            COUNT(DISTINCT customer_identifier) as total_customers,
            COUNT(CASE WHEN first_order >= CAST(:start_date AS DATE) THEN 1 END) as new_customers,
            COUNT(CASE WHEN first_order < :start_date THEN 1 END) as returning_customers,
            AVG(order_count) as avg_orders_per_customer,
            AVG(total_spent) as avg_lifetime_value
        FROM customer_orders
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "start_date": start_date,
        "end_date": end_date
    })

    row = result.fetchone()

    if not row:
        return {}

    total_customers = int(row.total_customers or 0)
    new_customers = int(row.new_customers or 0)
    returning_customers = int(row.returning_customers or 0)

    repeat_rate = 0.0
    if total_customers > 0:
        repeat_rate = (returning_customers / total_customers) * 100

    return {
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "repeat_rate": round(repeat_rate, 2),
        "avg_orders_per_customer": round(float(row.avg_orders_per_customer or 0), 2),
        "avg_customer_lifetime_value": round(float(row.avg_lifetime_value or 0), 2)
    }
