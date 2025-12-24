"""
Pydantic schemas for Order Service
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from shared.models.enums import OrderStatus


# Order Item Schemas
class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    menu_item_id: UUID
    quantity: int = Field(ge=1, le=100)
    special_requests: Optional[str] = None
    contributor_name: Optional[str] = None  # For collaborative ordering


class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: UUID
    order_id: UUID
    menu_item_id: UUID
    menu_item_name: str
    unit_price: float
    quantity: int
    subtotal: float
    status: OrderStatus
    special_requests: Optional[str]
    contributor_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Order Schemas
class OrderCreate(BaseModel):
    """Schema for creating an order"""
    restaurant_id: UUID
    table_id: UUID
    items: List[OrderItemCreate] = Field(min_length=1)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    special_instructions: Optional[str] = None


class OrderUpdateStatus(BaseModel):
    """Schema for updating order status"""
    status: OrderStatus


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID
    restaurant_id: UUID
    table_id: UUID
    order_number: str
    status: OrderStatus
    customer_name: Optional[str]
    customer_phone: Optional[str]
    subtotal: float
    tax: float
    total: float
    special_instructions: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Table Session Schemas
class SessionParticipant(BaseModel):
    """Participant in a table session"""
    name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class SessionItemCreate(BaseModel):
    """Item being added to session"""
    menu_item_id: UUID
    menu_item_name: str
    unit_price: float
    quantity: int = Field(ge=1, le=100)
    special_requests: Optional[str] = None
    contributor_name: str


class TableSessionCreate(BaseModel):
    """Schema for creating a table session"""
    restaurant_id: UUID
    table_id: UUID
    participant_name: str


class TableSessionJoin(BaseModel):
    """Schema for joining a table session"""
    participant_name: str


class TableSessionAddItem(BaseModel):
    """Schema for adding item to session"""
    menu_item_id: UUID
    quantity: int = Field(ge=1, le=100)
    special_requests: Optional[str] = None
    contributor_name: str


class TableSessionResponse(BaseModel):
    """Schema for table session response"""
    id: UUID
    restaurant_id: UUID
    table_id: UUID
    session_token: str
    is_active: bool
    is_locked: bool
    participants: List[dict]
    pending_items: List[dict]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# Assistance Request Schemas
class AssistanceRequestCreate(BaseModel):
    """Schema for creating assistance request"""
    restaurant_id: UUID
    table_id: UUID
    request_type: str = Field(pattern="^(waiter|bill|complaint|other)$")
    message: Optional[str] = None


class AssistanceRequestResolve(BaseModel):
    """Schema for resolving assistance request"""
    resolved_by: UUID


class AssistanceRequestResponse(BaseModel):
    """Schema for assistance request response"""
    id: UUID
    restaurant_id: UUID
    table_id: UUID
    request_type: str
    message: Optional[str]
    is_resolved: bool
    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# General Response Schemas
class MessageResponse(BaseModel):
    """General message response"""
    message: str
