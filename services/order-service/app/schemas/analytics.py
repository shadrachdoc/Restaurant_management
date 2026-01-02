"""
Analytics and prediction response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID


class RevenueMetrics(BaseModel):
    """Revenue analytics for a specific period"""
    period: str = Field(..., description="Period identifier (e.g., '2025-12-27', 'Week 52')")
    total_revenue: float = Field(..., description="Total revenue for the period")
    order_count: int = Field(..., description="Number of orders in the period")
    avg_order_value: float = Field(..., description="Average order value")
    growth_rate: Optional[float] = Field(None, description="Growth rate vs previous period")


class PopularItem(BaseModel):
    """Popular menu item analytics"""
    menu_item_id: UUID
    item_name: str
    category: str
    order_count: int = Field(..., description="Number of times ordered")
    quantity_sold: int = Field(..., description="Total quantity sold")
    revenue: float = Field(..., description="Total revenue generated")
    avg_price: float = Field(..., description="Average price per unit")
    trend: str = Field(..., description="Trend direction: up, down, stable")


class DayPattern(BaseModel):
    """Day of week pattern analysis"""
    day_of_week: int = Field(..., description="0=Sunday, 1=Monday, ..., 6=Saturday")
    day_name: str
    avg_orders: float = Field(..., description="Average orders for this day")
    avg_revenue: float = Field(..., description="Average revenue for this day")
    popular_items: List[str] = Field(default_factory=list, description="Most ordered items")


class DemandPrediction(BaseModel):
    """Predicted demand for a menu item"""
    date: date
    menu_item_id: UUID
    item_name: str
    predicted_quantity: int = Field(..., description="Predicted quantity to prepare")
    confidence_lower: int = Field(..., description="Lower bound of 80% confidence interval")
    confidence_upper: int = Field(..., description="Upper bound of 80% confidence interval")
    confidence_level: float = Field(..., description="Confidence level (0.0-1.0)")
    trend: str = Field(..., description="Trend: increasing, decreasing, stable")


class PredictionSummary(BaseModel):
    """Summary of predictions for a period"""
    period: str = Field(..., description="Prediction period (e.g., '1_week', '1_month')")
    start_date: date
    end_date: date
    predictions: List[DemandPrediction]
    total_predicted_orders: int
    data_quality: str = Field(..., description="Data quality: excellent, good, fair, insufficient")
    min_history_days: int = Field(..., description="Minimum history days required")
    available_history_days: int = Field(..., description="Available history days")


class OrderVolumeMetrics(BaseModel):
    """Order volume metrics over time"""
    period: str
    order_count: int
    avg_order_value: float
    total_revenue: float
    growth_rate: Optional[float] = None


class CategoryPerformance(BaseModel):
    """Performance metrics by category"""
    category: str
    revenue: float
    order_count: int
    item_count: int
    avg_price: float
    growth_rate: Optional[float] = None


class PeakHoursAnalysis(BaseModel):
    """Peak hours analysis"""
    hour: int
    avg_orders: float
    avg_revenue: float
    day_of_week: Optional[int] = None


class AnalyticsSummary(BaseModel):
    """Comprehensive analytics summary"""
    total_revenue: float
    total_orders: int
    avg_order_value: float
    top_items: List[PopularItem]
    revenue_by_day: List[DayPattern]
    period_start: date
    period_end: date
