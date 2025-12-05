"""
Pydantic schemas for Restaurant Service
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4, HttpUrl
from shared.models.enums import MenuItemCategory, TableStatus, SubscriptionStatus, PricingPlan, OrderStatus


# Restaurant Schemas
class RestaurantBase(BaseModel):
    """Base restaurant schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None
    theme_color: str = Field(default="#000000", pattern="^#[0-9A-Fa-f]{6}$")


class RestaurantCreate(RestaurantBase):
    """Schema for restaurant creation"""
    pricing_plan: PricingPlan = PricingPlan.BASIC
    max_tables: int = Field(default=10, ge=1, le=1000)


class RestaurantUpdate(BaseModel):
    """Schema for restaurant update"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None
    theme_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    max_tables: Optional[int] = Field(None, ge=1, le=1000)


class RestaurantBranding(BaseModel):
    """Schema for restaurant branding updates"""
    logo_url: Optional[str] = None
    theme_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    banner_images: Optional[List[str]] = None
    upcoming_events: Optional[List[Dict[str, Any]]] = None
    advertisements: Optional[List[Dict[str, Any]]] = None


class RestaurantResponse(RestaurantBase):
    """Schema for restaurant response"""
    id: UUID4
    logo_url: Optional[str] = None
    subscription_status: SubscriptionStatus
    pricing_plan: PricingPlan
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    banner_images: List[str] = []
    upcoming_events: List[Dict[str, Any]] = []
    advertisements: List[Dict[str, Any]] = []
    is_active: bool
    max_tables: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Menu Item Schemas
class MenuItemBase(BaseModel):
    """Base menu item schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: MenuItemCategory
    price: float = Field(..., gt=0)
    image_url: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_gluten_free: bool = False
    preparation_time: Optional[int] = Field(None, ge=0)  # minutes
    calories: Optional[int] = Field(None, ge=0)


class MenuItemCreate(MenuItemBase):
    """Schema for menu item creation"""
    ingredients: Optional[List[str]] = []
    allergens: Optional[List[str]] = []
    display_order: int = Field(default=0, ge=0)


class MenuItemUpdate(BaseModel):
    """Schema for menu item update"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[MenuItemCategory] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    is_gluten_free: Optional[bool] = None
    preparation_time: Optional[int] = Field(None, ge=0)
    calories: Optional[int] = Field(None, ge=0)
    ingredients: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    display_order: Optional[int] = Field(None, ge=0)


class MenuItemResponse(MenuItemBase):
    """Schema for menu item response"""
    id: UUID4
    restaurant_id: UUID4
    is_available: bool
    ingredients: List[str]
    allergens: List[str]
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Table Schemas
class TableBase(BaseModel):
    """Base table schema"""
    table_number: str = Field(..., min_length=1, max_length=50)
    seat_count: int = Field(..., ge=1, le=50)
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=50)


class TableCreate(TableBase):
    """Schema for table creation"""
    pass


class TableUpdate(BaseModel):
    """Schema for table update"""
    table_number: Optional[str] = Field(None, min_length=1, max_length=50)
    seat_count: Optional[int] = Field(None, ge=1, le=50)
    status: Optional[TableStatus] = None
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=50)


class TableResponse(TableBase):
    """Schema for table response"""
    id: UUID4
    restaurant_id: UUID4
    status: TableStatus
    qr_code_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for feedback creation"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_email: Optional[str] = Field(None, max_length=255)
    table_id: Optional[UUID4] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: UUID4
    restaurant_id: UUID4
    table_id: Optional[UUID4] = None
    rating: int
    comment: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# QR Code Schema
class QRCodeResponse(BaseModel):
    """Schema for QR code response"""
    table_id: UUID4
    table_number: str
    qr_code_url: str
    qr_code_data: str


# Order Schemas
class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    menu_item_id: UUID4
    quantity: int = Field(..., ge=1, le=100)
    special_instructions: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: UUID4
    order_id: UUID4
    menu_item_id: Optional[UUID4] = None
    item_name: str
    item_price: float
    quantity: int
    special_instructions: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Schema for creating an order (public - no auth required)"""
    table_id: UUID4
    items: List[OrderItemCreate] = Field(..., min_length=1)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=20)
    special_instructions: Optional[str] = None


class OrderUpdateStatus(BaseModel):
    """Schema for updating order status (chef/admin only)"""
    status: OrderStatus


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID4
    restaurant_id: UUID4
    table_id: Optional[UUID4] = None
    order_number: str
    status: OrderStatus
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    subtotal: float
    tax: float
    total: float
    special_instructions: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Analytics Schemas
class RestaurantAnalytics(BaseModel):
    """Schema for restaurant analytics"""
    total_menu_items: int
    total_tables: int
    available_tables: int
    occupied_tables: int
    total_feedback: int
    average_rating: float
    menu_items_by_category: Dict[str, int]


# Generic Response
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    status_code: int
