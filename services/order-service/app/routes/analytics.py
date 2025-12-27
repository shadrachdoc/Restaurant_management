"""
Analytics Routes for Order Service
REST API endpoints for analytics and reporting
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, timedelta
from uuid import UUID

from ..database import get_db
from ..analytics_schemas.analytics import (
    RevenueAnalyticsResponse,
    PopularItemsResponse,
    DayPatternsResponse,
    CustomerPreferencesResponse,
    PredictionResponse,
    OrderVolumeResponse,
    CategoryPerformanceResponse,
    PeakHoursResponse,
    PeriodComparison,
    TopPerformersResponse,
    OrderTypeAnalysisResponse,
    CustomerBehaviorMetrics,
    AnalyticsErrorResponse
)
from ..services import analytics_service
from shared.utils.logger import setup_logger

logger = setup_logger("analytics-routes")

router = APIRouter()


# ============================================================================
# 1. Revenue Analytics
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/revenue",
    response_model=RevenueAnalyticsResponse,
    summary="Get revenue analytics",
    description="Retrieve revenue metrics grouped by day, week, or month"
)
async def get_revenue_analytics(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    group_by: str = Query("daily", regex="^(daily|weekly|monthly)$", description="Grouping method"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get revenue analytics with flexible grouping.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)
    - **group_by**: daily, weekly, or monthly

    **Returns:** Revenue metrics grouped by period
    """
    try:
        result = await analytics_service.get_revenue_analytics(
            db, restaurant_id, start_date, end_date, group_by
        )
        return result
    except Exception as e:
        logger.error(f"Revenue analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch revenue analytics: {str(e)}"
        )


# ============================================================================
# 2. Popular Items
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/popular-items",
    response_model=PopularItemsResponse,
    summary="Get popular menu items",
    description="Retrieve top-selling items with trend analysis"
)
async def get_popular_items(
    restaurant_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get popular menu items ranked by sales with trend indicators.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **days**: Number of days to analyze (1-365)
    - **limit**: Maximum items to return (1-50)

    **Returns:** List of popular items with sales metrics and trends
    """
    try:
        items = await analytics_service.get_popular_items(
            db, restaurant_id, days, limit
        )
        return {
            "days": days,
            "items": items
        }
    except Exception as e:
        logger.error(f"Popular items error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch popular items: {str(e)}"
        )


# ============================================================================
# 3. Day-of-Week Patterns
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/day-patterns",
    response_model=DayPatternsResponse,
    summary="Get day-of-week patterns",
    description="Analyze sales patterns by day of week"
)
async def get_day_patterns(
    restaurant_id: UUID,
    weeks: int = Query(8, ge=4, le=52, description="Number of weeks to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze sales patterns for each day of the week.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **weeks**: Number of weeks to analyze (4-52)

    **Returns:** Sales patterns for Monday through Sunday
    """
    try:
        patterns = await analytics_service.get_day_patterns(
            db, restaurant_id, weeks
        )
        return {
            "weeks_analyzed": weeks,
            "patterns": patterns
        }
    except Exception as e:
        logger.error(f"Day patterns error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch day patterns: {str(e)}"
        )


# ============================================================================
# 4. Customer Preferences (Placeholder - requires customer_identification)
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/customer-preferences/{customer_id}",
    response_model=CustomerPreferencesResponse,
    summary="Get customer preferences",
    description="Retrieve customer's order history and personalized recommendations"
)
async def get_customer_preferences(
    restaurant_id: UUID,
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get customer preferences and personalized recommendations.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **customer_id**: Customer UUID, email, or phone

    **Returns:** Customer preferences and recommendations
    """
    # TODO: Implement after creating customer_identification utility
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Customer preferences endpoint will be implemented with prediction service"
    )


# ============================================================================
# 5. Demand Predictions (Placeholder - requires prediction_service)
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/predictions/demand",
    response_model=PredictionResponse,
    summary="Get demand predictions",
    description="Predict demand for menu items using ML (dynamic periods: 1 week to 12 months)"
)
async def get_demand_predictions(
    restaurant_id: UUID,
    period: str = Query(
        "2_weeks",
        regex="^(1_week|2_weeks|1_month|3_months|6_months|12_months)$",
        description="Prediction period"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict demand for menu items using Facebook Prophet ML.

    **Prediction Periods:**
    - **1_week**: 7 days ahead (requires 60 days history)
    - **2_weeks**: 14 days ahead (requires 90 days history)
    - **1_month**: 30 days ahead (requires 120 days history)
    - **3_months**: 90 days ahead (requires 180 days history)
    - **6_months**: 180 days ahead (requires 365 days history)
    - **12_months**: 365 days ahead (requires 730 days history)

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **period**: Prediction period (1_week to 12_months)

    **Returns:** Predicted quantities with confidence intervals
    """
    # TODO: Implement with prediction_service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Demand predictions endpoint will be implemented with ML prediction service"
    )


# ============================================================================
# 6. Order Volume Trends
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/order-volume",
    response_model=OrderVolumeResponse,
    summary="Get order volume trends",
    description="Analyze order volume trends with growth rates"
)
async def get_order_volume(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    group_by: str = Query(
        "daily",
        regex="^(hourly|daily|weekly|monthly)$",
        description="Grouping method"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order volume trends with period-over-period growth rates.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)
    - **group_by**: hourly, daily, weekly, or monthly

    **Returns:** Order volume metrics with growth rates
    """
    try:
        result = await analytics_service.get_order_volume(
            db, restaurant_id, start_date, end_date, group_by
        )
        return result
    except Exception as e:
        logger.error(f"Order volume error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order volume: {str(e)}"
        )


# ============================================================================
# 7. Category Performance
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/category-performance",
    response_model=CategoryPerformanceResponse,
    summary="Get category performance",
    description="Analyze performance by menu category"
)
async def get_category_performance(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance metrics for each menu category.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)

    **Returns:** Category performance metrics
    """
    try:
        categories = await analytics_service.get_category_performance(
            db, restaurant_id, start_date, end_date
        )
        return {
            "start_date": start_date,
            "end_date": end_date,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Category performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch category performance: {str(e)}"
        )


# ============================================================================
# 8. Peak Hours Analysis
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/peak-hours",
    response_model=PeakHoursResponse,
    summary="Get peak hours analysis",
    description="Analyze order patterns by hour of day"
)
async def get_peak_hours(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze order patterns by hour of day to identify peak times.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)

    **Returns:** Hourly metrics with busiest and slowest hours
    """
    try:
        result = await analytics_service.get_peak_hours(
            db, restaurant_id, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Peak hours error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch peak hours: {str(e)}"
        )


# ============================================================================
# 9. Sales Comparison
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/sales-comparison",
    response_model=PeriodComparison,
    summary="Get sales comparison",
    description="Compare current period with previous period"
)
async def get_sales_comparison(
    restaurant_id: UUID,
    period: str = Query(
        "week",
        regex="^(week|month|quarter|year)$",
        description="Comparison period"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare sales metrics between current and previous period.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **period**: week, month, quarter, or year

    **Returns:** Comparison metrics with growth percentages
    """
    try:
        result = await analytics_service.get_sales_comparison(
            db, restaurant_id, period
        )
        return result
    except Exception as e:
        logger.error(f"Sales comparison error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sales comparison: {str(e)}"
        )


# ============================================================================
# 10. Top Performers
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/top-performers",
    response_model=TopPerformersResponse,
    summary="Get top performing items",
    description="Get top items ranked by revenue, quantity, or orders"
)
async def get_top_performers(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    rank_by: str = Query(
        "revenue",
        regex="^(revenue|quantity|orders)$",
        description="Ranking method"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top performing items with detailed metrics.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)
    - **rank_by**: revenue, quantity, or orders
    - **limit**: Maximum items to return (1-100)

    **Returns:** Ranked list of top performing items
    """
    try:
        items = await analytics_service.get_top_performers(
            db, restaurant_id, start_date, end_date, rank_by, limit
        )
        return {
            "start_date": start_date,
            "end_date": end_date,
            "rank_by": rank_by,
            "items": items
        }
    except Exception as e:
        logger.error(f"Top performers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch top performers: {str(e)}"
        )


# ============================================================================
# 11. Order Type Analysis
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/order-type-breakdown",
    response_model=OrderTypeAnalysisResponse,
    summary="Get order type breakdown",
    description="Analyze orders by type (table vs online)"
)
async def get_order_type_breakdown(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze order distribution between table and online orders.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)

    **Returns:** Breakdown by order type with percentages
    """
    try:
        breakdown = await analytics_service.get_order_type_breakdown(
            db, restaurant_id, start_date, end_date
        )
        return {
            "start_date": start_date,
            "end_date": end_date,
            "breakdown": breakdown
        }
    except Exception as e:
        logger.error(f"Order type breakdown error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order type breakdown: {str(e)}"
        )


# ============================================================================
# 12. Customer Behavior
# ============================================================================

@router.get(
    "/restaurants/{restaurant_id}/analytics/customer-behavior",
    response_model=CustomerBehaviorMetrics,
    summary="Get customer behavior metrics",
    description="Analyze customer behavior patterns"
)
async def get_customer_behavior(
    restaurant_id: UUID,
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze customer behavior including new vs returning customers.

    **Parameters:**
    - **restaurant_id**: Restaurant UUID
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)

    **Returns:** Customer behavior metrics
    """
    try:
        result = await analytics_service.get_customer_behavior(
            db, restaurant_id, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Customer behavior error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer behavior: {str(e)}"
        )
