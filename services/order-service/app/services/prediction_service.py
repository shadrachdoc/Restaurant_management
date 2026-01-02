"""
Prediction Service for Order Service
Machine Learning predictions using Facebook Prophet for demand forecasting
"""
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

# ML Libraries
try:
    import pandas as pd
    import numpy as np
    from prophet import Prophet
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    Prophet = None
    pd = None
    np = None
    cosine_similarity = None

from shared.utils.logger import setup_logger

logger = setup_logger("prediction-service")

# Redis for caching (optional - will gracefully degrade if not available)
try:
    import redis.asyncio as redis
    from shared.config.settings import settings

    # Initialize Redis client
    redis_client = redis.Redis(
        host=getattr(settings, 'redis_host', 'localhost'),
        port=getattr(settings, 'redis_port', 6379),
        db=0,
        decode_responses=True
    )
    REDIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Redis not available for caching: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


# Semaphore to limit concurrent ML model training (prevent memory overload)
ML_TRAINING_SEMAPHORE = asyncio.Semaphore(1)  # Laptop: only 1 concurrent training


# ============================================================================
# Period Configuration
# ============================================================================

PERIOD_CONFIG = {
    "1_week": {
        "days": 7,
        "min_history_days": 60,
        "cache_ttl": 86400  # 24 hours
    },
    "2_weeks": {
        "days": 14,
        "min_history_days": 90,
        "cache_ttl": 86400
    },
    "1_month": {
        "days": 30,
        "min_history_days": 120,
        "cache_ttl": 86400
    },
    "3_months": {
        "days": 90,
        "min_history_days": 180,
        "cache_ttl": 86400 * 2  # 48 hours
    },
    "6_months": {
        "days": 180,
        "min_history_days": 365,
        "cache_ttl": 86400 * 3  # 72 hours
    },
    "12_months": {
        "days": 365,
        "min_history_days": 730,
        "cache_ttl": 86400 * 7  # 1 week
    }
}


def parse_period_to_days(period: str) -> int:
    """Convert period string to number of days"""
    return PERIOD_CONFIG.get(period, {}).get("days", 14)


def get_min_history_days(period: str) -> int:
    """Get minimum required history days for a period"""
    return PERIOD_CONFIG.get(period, {}).get("min_history_days", 90)


def get_cache_ttl(period: str) -> int:
    """Get cache TTL for a period"""
    return PERIOD_CONFIG.get(period, {}).get("cache_ttl", 86400)


# ============================================================================
# Data Validation
# ============================================================================

async def validate_historical_data(
    db: AsyncSession,
    restaurant_id: UUID,
    period: str
) -> Tuple[bool, int, str]:
    """
    Validate that restaurant has sufficient historical data for predictions

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        period: Prediction period (1_week, 2_weeks, etc.)

    Returns:
        Tuple of (is_valid, days_available, message)
    """
    min_days = get_min_history_days(period)

    # Count unique days with orders in the past period
    query = text("""
        SELECT
            COUNT(DISTINCT DATE(created_at)) as order_days,
            MIN(created_at) as first_order,
            MAX(created_at) as last_order,
            COUNT(id) as total_orders
        FROM orders
        WHERE restaurant_id = :restaurant_id
            AND status NOT IN ('CANCELLED')
            AND created_at >= NOW() - INTERVAL ':lookback days'
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "lookback": min_days * 2  # Look back 2x the requirement for better accuracy
    })

    row = result.fetchone()

    if not row or not row.order_days:
        return False, 0, "No order history found"

    order_days = int(row.order_days)
    total_orders = int(row.total_orders or 0)

    # Check if we have enough unique days with orders
    if order_days < min_days:
        return False, order_days, f"Need {min_days} days of history, only {order_days} days available"

    # Check if we have sufficient order volume
    avg_orders_per_day = total_orders / order_days if order_days > 0 else 0
    if avg_orders_per_day < 2:
        return False, order_days, f"Order volume too low for reliable predictions (avg {avg_orders_per_day:.1f} orders/day)"

    return True, order_days, "Sufficient data available"


# ============================================================================
# Historical Data Loading
# ============================================================================

async def load_historical_order_data(
    db: AsyncSession,
    restaurant_id: UUID,
    period: str
) -> pd.DataFrame:
    """
    Load historical order data for ML training

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        period: Prediction period

    Returns:
        Pandas DataFrame with columns: ds (date), menu_item_id, item_name, y (quantity)
    """
    if not ML_AVAILABLE:
        raise RuntimeError("ML libraries (pandas, prophet) not available")

    min_history_days = get_min_history_days(period)
    lookback_days = min_history_days * 2  # Use 2x data for better training

    query = text("""
        SELECT
            DATE(o.created_at) as order_date,
            oi.menu_item_id,
            oi.item_name,
            SUM(oi.quantity) as total_quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.restaurant_id = :restaurant_id
            AND o.created_at >= NOW() - INTERVAL ':days days'
            AND o.status NOT IN ('CANCELLED')
        GROUP BY DATE(o.created_at), oi.menu_item_id, oi.item_name
        ORDER BY order_date ASC
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "days": lookback_days
    })

    rows = result.fetchall()

    if not rows:
        return pd.DataFrame(columns=['ds', 'menu_item_id', 'item_name', 'y'])

    # Convert to pandas DataFrame
    data = []
    for row in rows:
        data.append({
            'ds': row.order_date,
            'menu_item_id': str(row.menu_item_id),
            'item_name': row.item_name,
            'y': int(row.total_quantity)
        })

    df = pd.DataFrame(data)
    return df


# ============================================================================
# Prophet Model Training and Prediction
# ============================================================================

async def train_prophet_model_for_item(
    item_data: pd.DataFrame,
    period_days: int
) -> Optional[pd.DataFrame]:
    """
    Train Prophet model for a single menu item and generate predictions

    Args:
        item_data: DataFrame with columns ds (date) and y (quantity)
        period_days: Number of days to predict ahead

    Returns:
        DataFrame with predictions or None if training fails
    """
    if not ML_AVAILABLE:
        raise RuntimeError("Prophet not available")

    # Need at least 10 data points for Prophet
    if len(item_data) < 10:
        logger.warning(f"Insufficient data points for training: {len(item_data)}")
        return None

    try:
        # Configure Prophet based on period
        prophet_config = {
            'daily_seasonality': False,
            'weekly_seasonality': period_days <= 90,  # Use weekly for up to 3 months
            'yearly_seasonality': period_days >= 180,  # Use yearly for 6+ months
            'seasonality_mode': 'multiplicative',  # Better for sales data
            'changepoint_prior_scale': 0.05,  # Conservative - less sensitive to noise
            'interval_width': 0.80  # 80% confidence interval
        }

        # Initialize and train Prophet model
        model = Prophet(**prophet_config)

        # Add monthly seasonality for longer periods
        if period_days >= 30:
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)

        # Train model (this is CPU-intensive)
        model.fit(item_data)

        # Generate future dates for prediction
        future = model.make_future_dataframe(periods=period_days, freq='D')

        # Generate predictions with confidence intervals
        forecast = model.predict(future)

        # Return only future predictions (not historical fit)
        future_forecast = forecast[forecast['ds'] > item_data['ds'].max()]

        return future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    except Exception as e:
        logger.error(f"Prophet model training failed: {e}")
        return None


async def predict_demand_ml(
    db: AsyncSession,
    restaurant_id: UUID,
    period: str = "2_weeks"
) -> Dict[str, Any]:
    """
    Predict demand using Facebook Prophet ML with DYNAMIC periods

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        period: Prediction period (1_week, 2_weeks, 1_month, 3_months, 6_months, 12_months)

    Returns:
        Dictionary with predictions for all menu items
    """
    if not ML_AVAILABLE:
        raise RuntimeError(
            "ML libraries not installed. Please install: pip install prophet pandas numpy scikit-learn"
        )

    period_days = parse_period_to_days(period)
    cache_key = f"predictions:{restaurant_id}:{period}"

    # Try to get from cache first
    if REDIS_AVAILABLE:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info(f"Returning cached predictions for {period}")
                return {
                    **json.loads(cached),
                    "cached": True
                }
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")

    # Validate historical data availability
    is_valid, days_available, message = await validate_historical_data(
        db, restaurant_id, period
    )

    if not is_valid:
        raise ValueError({
            "error": "INSUFFICIENT_DATA",
            "message": message,
            "required_days": get_min_history_days(period),
            "available_days": days_available
        })

    # Acquire semaphore to limit concurrent training
    async with ML_TRAINING_SEMAPHORE:
        logger.info(f"Training Prophet model for {period} prediction (this may take 10-90 seconds)")

        # Load historical data
        df = await load_historical_order_data(db, restaurant_id, period)

        if df.empty:
            return {
                "period": period,
                "days_ahead": period_days,
                "predictions": [],
                "model_accuracy": None,
                "cached": False
            }

        # Get unique menu items
        menu_items = df[['menu_item_id', 'item_name']].drop_duplicates()

        predictions = []

        # Train model for each menu item
        for _, item in menu_items.iterrows():
            item_id = item['menu_item_id']
            item_name = item['item_name']

            # Filter data for this item
            item_data = df[df['menu_item_id'] == item_id][['ds', 'y']].copy()

            # Train Prophet model
            forecast = await train_prophet_model_for_item(item_data, period_days)

            if forecast is None:
                continue

            # Convert predictions to response format
            for _, pred_row in forecast.iterrows():
                predictions.append({
                    "date": pred_row['ds'].date().isoformat(),
                    "menu_item_id": item_id,
                    "item_name": item_name,
                    "predicted_quantity": max(0, int(round(pred_row['yhat']))),  # Can't predict negative
                    "confidence_lower": max(0, int(round(pred_row['yhat_lower']))),
                    "confidence_upper": max(0, int(round(pred_row['yhat_upper']))),
                    "confidence_level": 0.80  # 80% confidence interval
                })

        result = {
            "period": period,
            "days_ahead": period_days,
            "predictions": predictions,
            "model_accuracy": None,  # TODO: Calculate MAPE if historical actuals available
            "cached": False
        }

        # Cache results
        if REDIS_AVAILABLE:
            try:
                cache_ttl = get_cache_ttl(period)
                await redis_client.setex(
                    cache_key,
                    cache_ttl,
                    json.dumps(result)
                )
                logger.info(f"Cached predictions for {period} (TTL: {cache_ttl}s)")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

        return result


# ============================================================================
# Collaborative Filtering for Recommendations
# ============================================================================

async def calculate_customer_recommendations(
    db: AsyncSession,
    restaurant_id: UUID,
    customer_identifier: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate personalized recommendations using item-based collaborative filtering

    Algorithm:
    1. Get customer's order history (items + frequencies)
    2. Find similar items based on co-occurrence patterns
       "Customers who ordered X also ordered Y"
    3. Identify items customer hasn't ordered recently
    4. Rank by: similarity_score × item_popularity
    5. Return top N personalized recommendations

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        customer_identifier: Customer identifier (from customer_identification utility)
        limit: Maximum recommendations to return

    Returns:
        List of recommendations with confidence scores
    """
    if not ML_AVAILABLE:
        logger.warning("Scikit-learn not available for collaborative filtering")
        return []

    # Get customer's order history
    customer_items_query = text("""
        SELECT
            menu_item_id,
            item_name,
            order_count,
            total_quantity
        FROM customer_item_preferences
        WHERE customer_identifier = :customer_identifier
            AND restaurant_id = :restaurant_id
            AND order_count >= 2  # Only consider items ordered 2+ times
        ORDER BY order_count DESC
        LIMIT 10
    """)

    result = await db.execute(customer_items_query, {
        "customer_identifier": customer_identifier,
        "restaurant_id": str(restaurant_id)
    })

    customer_items = result.fetchall()

    if not customer_items:
        # New customer - return popular items instead
        return await get_popular_items_fallback(db, restaurant_id, limit)

    # Build item-item similarity matrix based on co-occurrence
    # Find items frequently ordered together
    similarity_query = text("""
        WITH customer_orders AS (
            SELECT DISTINCT
                oi1.menu_item_id as item1,
                oi2.menu_item_id as item2
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id
            JOIN orders o ON oi1.order_id = o.id
            WHERE o.restaurant_id = :restaurant_id
                AND oi1.menu_item_id != oi2.menu_item_id
                AND o.status NOT IN ('CANCELLED')
                AND o.created_at >= NOW() - INTERVAL '90 days'
        )
        SELECT
            item1,
            item2,
            COUNT(*) as co_occurrence
        FROM customer_orders
        WHERE item1 = ANY(:customer_item_ids)
        GROUP BY item1, item2
        ORDER BY co_occurrence DESC
        LIMIT 100
    """)

    customer_item_ids = [str(row.menu_item_id) for row in customer_items]

    result = await db.execute(similarity_query, {
        "restaurant_id": str(restaurant_id),
        "customer_item_ids": customer_item_ids
    })

    similar_items = result.fetchall()

    # Calculate recommendation scores
    recommendations = {}

    for row in similar_items:
        item2 = str(row.item2)
        co_occurrence = int(row.co_occurrence)

        # Skip items customer already ordered
        if item2 in customer_item_ids:
            continue

        # Calculate similarity score (normalized by customer's order count)
        if item2 not in recommendations:
            recommendations[item2] = {
                "score": 0,
                "reasons": []
            }

        recommendations[item2]["score"] += co_occurrence
        recommendations[item2]["reasons"].append(str(row.item1))

    # Get item details and popularity for recommendations
    if not recommendations:
        return await get_popular_items_fallback(db, restaurant_id, limit)

    item_details_query = text("""
        SELECT
            oi.menu_item_id,
            oi.item_name,
            COUNT(DISTINCT oi.order_id) as popularity
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.restaurant_id = :restaurant_id
            AND oi.menu_item_id = ANY(:item_ids)
            AND o.status NOT IN ('CANCELLED')
            AND o.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY oi.menu_item_id, oi.item_name
    """)

    result = await db.execute(item_details_query, {
        "restaurant_id": str(restaurant_id),
        "item_ids": list(recommendations.keys())
    })

    final_recommendations = []

    for row in result.fetchall():
        item_id = str(row.menu_item_id)
        if item_id in recommendations:
            # Combine similarity score with popularity
            similarity_score = recommendations[item_id]["score"]
            popularity = int(row.popularity or 1)
            combined_score = similarity_score * (1 + np.log(popularity))

            final_recommendations.append({
                "menu_item_id": item_id,
                "item_name": row.item_name,
                "confidence": min(1.0, combined_score / 100),  # Normalize to 0-1
                "reason": f"Customers who liked your favorites also love this"
            })

    # Sort by confidence and return top N
    final_recommendations.sort(key=lambda x: x["confidence"], reverse=True)
    return final_recommendations[:limit]


async def get_popular_items_fallback(
    db: AsyncSession,
    restaurant_id: UUID,
    limit: int
) -> List[Dict[str, Any]]:
    """
    Fallback to popular items when collaborative filtering not possible

    Args:
        db: Database session
        restaurant_id: Restaurant UUID
        limit: Number of items to return

    Returns:
        List of popular items as recommendations
    """
    query = text("""
        SELECT
            oi.menu_item_id,
            oi.item_name,
            COUNT(DISTINCT oi.order_id) as order_count
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.restaurant_id = :restaurant_id
            AND o.status NOT IN ('CANCELLED')
            AND o.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY oi.menu_item_id, oi.item_name
        ORDER BY order_count DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {
        "restaurant_id": str(restaurant_id),
        "limit": limit
    })

    recommendations = []
    for row in result.fetchall():
        recommendations.append({
            "menu_item_id": str(row.menu_item_id),
            "item_name": row.item_name,
            "confidence": 0.5,  # Medium confidence for popular items
            "reason": "Popular item at this restaurant"
        })

    return recommendations
