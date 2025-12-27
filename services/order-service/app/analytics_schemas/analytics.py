"""
Analytics Schemas for Order Service
Pydantic models for analytics API responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID


# ============================================================================
# Revenue Analytics Schemas
# ============================================================================

class RevenueMetrics(BaseModel):
    """Revenue metrics for a specific period"""
    period: str = Field(..., description="Time period (e.g., '2025-12-27', '2025-W52', '2025-12')")
    total_revenue: float = Field(..., description="Total revenue for the period")
    order_count: int = Field(..., description="Number of orders in the period")
    avg_order_value: float = Field(..., description="Average order value")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "2025-12-27",
                "total_revenue": 15420.50,
                "order_count": 87,
                "avg_order_value": 177.25
            }
        }


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response with multiple periods"""
    start_date: date
    end_date: date
    group_by: str = Field(..., description="Grouping method: daily, weekly, monthly")
    metrics: List[RevenueMetrics]
    total_revenue: float
    total_orders: int
    overall_avg_order_value: float

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "group_by": "daily",
                "metrics": [],
                "total_revenue": 125430.00,
                "total_orders": 842,
                "overall_avg_order_value": 149.01
            }
        }


# ============================================================================
# Popular Items Schemas
# ============================================================================

class PopularItem(BaseModel):
    """Popular menu item with sales metrics"""
    menu_item_id: UUID
    item_name: str
    order_count: int = Field(..., description="Number of orders containing this item")
    quantity_sold: int = Field(..., description="Total quantity sold")
    revenue: float = Field(..., description="Total revenue from this item")
    avg_price: float = Field(..., description="Average price per unit")
    trend: str = Field(..., description="Trend direction: up, down, stable")
    trend_percentage: Optional[float] = Field(None, description="Percentage change from previous period")

    class Config:
        json_schema_extra = {
            "example": {
                "menu_item_id": "123e4567-e89b-12d3-a456-426614174000",
                "item_name": "Margherita Pizza",
                "order_count": 145,
                "quantity_sold": 187,
                "revenue": 2805.00,
                "avg_price": 15.00,
                "trend": "up",
                "trend_percentage": 12.5
            }
        }


class PopularItemsResponse(BaseModel):
    """Response for popular items query"""
    days: int = Field(..., description="Number of days analyzed")
    items: List[PopularItem]

    class Config:
        json_schema_extra = {
            "example": {
                "days": 30,
                "items": []
            }
        }


# ============================================================================
# Day-of-Week Pattern Schemas
# ============================================================================

class DayPattern(BaseModel):
    """Sales pattern for a specific day of week"""
    day_of_week: str = Field(..., description="Monday, Tuesday, etc.")
    day_number: int = Field(..., description="0=Monday, 6=Sunday")
    avg_orders: float = Field(..., description="Average number of orders on this day")
    avg_revenue: float = Field(..., description="Average revenue on this day")
    popular_items: List[str] = Field(..., description="Most popular items on this day")

    class Config:
        json_schema_extra = {
            "example": {
                "day_of_week": "Friday",
                "day_number": 4,
                "avg_orders": 52.3,
                "avg_revenue": 7845.20,
                "popular_items": ["Margherita Pizza", "Caesar Salad", "Tiramisu"]
            }
        }


class DayPatternsResponse(BaseModel):
    """Day-of-week analysis response"""
    weeks_analyzed: int
    patterns: List[DayPattern]

    class Config:
        json_schema_extra = {
            "example": {
                "weeks_analyzed": 8,
                "patterns": []
            }
        }


# ============================================================================
# Customer Preference Schemas
# ============================================================================

class CustomerPreference(BaseModel):
    """Customer's preference for a specific menu item"""
    menu_item_id: UUID
    item_name: str
    order_count: int = Field(..., description="How many times customer ordered this item")
    total_quantity: int = Field(..., description="Total quantity ordered")
    total_spent: float = Field(..., description="Total amount spent on this item")
    last_ordered_at: datetime = Field(..., description="When customer last ordered this item")
    recency_score: float = Field(..., description="Recency score (lower = more recent)")
    frequency_score: float = Field(..., description="Frequency score (orders per month)")

    class Config:
        json_schema_extra = {
            "example": {
                "menu_item_id": "123e4567-e89b-12d3-a456-426614174000",
                "item_name": "Margherita Pizza",
                "order_count": 12,
                "total_quantity": 15,
                "total_spent": 225.00,
                "last_ordered_at": "2025-12-20T19:30:00",
                "recency_score": 7.0,
                "frequency_score": 2.4
            }
        }


class CustomerRecommendation(BaseModel):
    """Personalized recommendation for a customer"""
    menu_item_id: UUID
    item_name: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recommendation confidence score")
    reason: str = Field(..., description="Why this item is recommended")

    class Config:
        json_schema_extra = {
            "example": {
                "menu_item_id": "123e4567-e89b-12d3-a456-426614174000",
                "item_name": "Quattro Formaggi Pizza",
                "confidence": 0.87,
                "reason": "Similar to Margherita Pizza which you love"
            }
        }


class CustomerPreferencesResponse(BaseModel):
    """Customer preference and recommendation response"""
    customer_identifier: str
    preferences: List[CustomerPreference]
    recommendations: List[CustomerRecommendation]
    total_orders: int
    total_spent: float

    class Config:
        json_schema_extra = {
            "example": {
                "customer_identifier": "customer@example.com",
                "preferences": [],
                "recommendations": [],
                "total_orders": 24,
                "total_spent": 3580.50
            }
        }


# ============================================================================
# Demand Prediction Schemas
# ============================================================================

class DemandPrediction(BaseModel):
    """Predicted demand for a specific menu item on a specific date"""
    date: date
    menu_item_id: UUID
    item_name: str
    predicted_quantity: int = Field(..., description="Predicted quantity to prepare")
    confidence_lower: int = Field(..., description="Lower bound of confidence interval")
    confidence_upper: int = Field(..., description="Upper bound of confidence interval")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0.0 to 1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-30",
                "menu_item_id": "123e4567-e89b-12d3-a456-426614174000",
                "item_name": "Margherita Pizza",
                "predicted_quantity": 42,
                "confidence_lower": 35,
                "confidence_upper": 49,
                "confidence_level": 0.85
            }
        }


class PredictionResponse(BaseModel):
    """Demand prediction response for a period"""
    period: str = Field(..., description="Prediction period: 1_week, 2_weeks, 1_month, 3_months, 6_months, 12_months")
    days_ahead: int = Field(..., description="Number of days predicted")
    predictions: List[DemandPrediction]
    model_accuracy: Optional[float] = Field(None, description="Model accuracy score if available")
    cached: bool = Field(..., description="Whether results were served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "1_week",
                "days_ahead": 7,
                "predictions": [],
                "model_accuracy": 0.82,
                "cached": False
            }
        }


# ============================================================================
# Order Volume Analysis Schemas
# ============================================================================

class OrderVolumeMetrics(BaseModel):
    """Order volume metrics for a period"""
    period: str
    order_count: int
    avg_order_value: float
    growth_rate: Optional[float] = Field(None, description="Growth rate compared to previous period")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "2025-12-27",
                "order_count": 87,
                "avg_order_value": 177.25,
                "growth_rate": 5.2
            }
        }


class OrderVolumeResponse(BaseModel):
    """Order volume trends response"""
    start_date: date
    end_date: date
    group_by: str
    metrics: List[OrderVolumeMetrics]

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "group_by": "daily",
                "metrics": []
            }
        }


# ============================================================================
# Category Performance Schemas
# ============================================================================

class CategoryPerformance(BaseModel):
    """Performance metrics for a menu category"""
    category: str
    revenue: float
    order_count: int
    avg_price: float
    growth_percentage: Optional[float] = Field(None, description="Growth compared to previous period")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "main_course",
                "revenue": 45230.00,
                "order_count": 342,
                "avg_price": 132.25,
                "growth_percentage": 8.5
            }
        }


class CategoryPerformanceResponse(BaseModel):
    """Category performance analysis response"""
    start_date: date
    end_date: date
    categories: List[CategoryPerformance]

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "categories": []
            }
        }


# ============================================================================
# Peak Hours Analysis Schemas
# ============================================================================

class HourMetrics(BaseModel):
    """Metrics for a specific hour"""
    hour: int = Field(..., ge=0, le=23)
    avg_orders: float
    avg_revenue: float

    class Config:
        json_schema_extra = {
            "example": {
                "hour": 19,
                "avg_orders": 15.2,
                "avg_revenue": 2280.50
            }
        }


class PeakHoursResponse(BaseModel):
    """Peak hours analysis response"""
    start_date: date
    end_date: date
    hourly_metrics: List[HourMetrics]
    busiest_hour: int
    slowest_hour: int

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "hourly_metrics": [],
                "busiest_hour": 19,
                "slowest_hour": 15
            }
        }


# ============================================================================
# Sales Comparison Schemas
# ============================================================================

class PeriodComparison(BaseModel):
    """Comparison between current and previous period"""
    current_revenue: float
    previous_revenue: float
    current_orders: int
    previous_orders: int
    current_avg_order_value: float
    previous_avg_order_value: float
    revenue_growth_percentage: float
    orders_growth_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "current_revenue": 125430.00,
                "previous_revenue": 118250.00,
                "current_orders": 842,
                "previous_orders": 798,
                "current_avg_order_value": 149.01,
                "previous_avg_order_value": 148.18,
                "revenue_growth_percentage": 6.07,
                "orders_growth_percentage": 5.51
            }
        }


# ============================================================================
# Top Performers Schemas
# ============================================================================

class TopPerformer(BaseModel):
    """Top performing item details"""
    rank: int
    menu_item_id: UUID
    item_name: str
    category: str
    revenue: float
    quantity_sold: int
    order_count: int
    trend: str
    trend_percentage: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "menu_item_id": "123e4567-e89b-12d3-a456-426614174000",
                "item_name": "Margherita Pizza",
                "category": "main_course",
                "revenue": 5610.00,
                "quantity_sold": 374,
                "order_count": 312,
                "trend": "up",
                "trend_percentage": 12.5
            }
        }


class TopPerformersResponse(BaseModel):
    """Top performers analysis response"""
    start_date: date
    end_date: date
    rank_by: str = Field(..., description="revenue, quantity, or orders")
    items: List[TopPerformer]

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "rank_by": "revenue",
                "items": []
            }
        }


# ============================================================================
# Order Type Analysis Schemas
# ============================================================================

class OrderTypeBreakdown(BaseModel):
    """Breakdown by order type (table vs online)"""
    order_type: str
    revenue: float
    order_count: int
    avg_order_value: float
    percentage_of_total: float

    class Config:
        json_schema_extra = {
            "example": {
                "order_type": "TABLE",
                "revenue": 95430.00,
                "order_count": 642,
                "avg_order_value": 148.64,
                "percentage_of_total": 76.1
            }
        }


class OrderTypeAnalysisResponse(BaseModel):
    """Order type analysis response"""
    start_date: date
    end_date: date
    breakdown: List[OrderTypeBreakdown]

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "breakdown": []
            }
        }


# ============================================================================
# Customer Behavior Schemas
# ============================================================================

class CustomerBehaviorMetrics(BaseModel):
    """Customer behavior metrics"""
    new_customers: int
    returning_customers: int
    repeat_rate: float = Field(..., description="Percentage of returning customers")
    avg_orders_per_customer: float
    avg_customer_lifetime_value: float

    class Config:
        json_schema_extra = {
            "example": {
                "new_customers": 142,
                "returning_customers": 89,
                "repeat_rate": 38.5,
                "avg_orders_per_customer": 2.7,
                "avg_customer_lifetime_value": 402.50
            }
        }


# ============================================================================
# Error Response Schema
# ============================================================================

class AnalyticsErrorResponse(BaseModel):
    """Error response for analytics endpoints"""
    error: str
    message: str
    required_days: Optional[int] = None
    available_days: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "INSUFFICIENT_DATA",
                "message": "Need 90 days of historical data, only 45 days available",
                "required_days": 90,
                "available_days": 45
            }
        }
