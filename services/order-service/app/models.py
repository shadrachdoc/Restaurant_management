"""
Database models for Order Service
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.ext.declarative import declarative_base
from shared.models.enums import OrderStatus, OrderType

Base = declarative_base()


class Order(Base):
    """Order model"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    table_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    order_type = Column(SQLEnum(OrderType), nullable=False, server_default='TABLE', index=True)

    # Customer info
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Soft reference (no FK)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True, index=True)  # For guest tracking
    customer_phone = Column(String(20), nullable=True, index=True)  # Added index for analytics

    # Delivery info (for online orders)
    delivery_address = Column(Text, nullable=True)

    # Pricing
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    # Special instructions
    special_instructions = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status})>"


class OrderItem(Base):
    """Order item model"""

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    # Menu item reference
    menu_item_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)  # Snapshot of name
    item_price = Column(Float, nullable=False)  # Snapshot of price
    item_image_url = Column(String(500), nullable=True)  # Snapshot of image URL

    # Order details
    quantity = Column(Integer, nullable=False, default=1)

    # Special instructions
    special_instructions = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, item={self.item_name}, qty={self.quantity})>"


class TableSession(Base):
    """
    Table session for tracking collaborative ordering
    Allows multiple customers at same table to contribute to order
    """

    __tablename__ = "table_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    table_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    session_token = Column(String(255), unique=True, nullable=False, index=True)

    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)  # Locked when order submitted

    # Participants
    participants = Column(JSONB, default=list)  # List of participant objects with names

    # Pending items (before order submission)
    pending_items = Column(JSONB, default=list)  # List of pending order items

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TableSession(id={self.id}, table_id={self.table_id}, active={self.is_active})>"


class AssistanceRequest(Base):
    """Customer assistance request model"""

    __tablename__ = "assistance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    table_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Request details
    request_type = Column(String(50), nullable=False)  # e.g., "waiter", "bill", "complaint"
    message = Column(Text, nullable=True)

    # Status
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who resolved
    resolved_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AssistanceRequest(id={self.id}, table_id={self.table_id}, type={self.request_type})>"


class CustomerItemPreference(Base):
    """
    Customer item preference model for tracking RFM metrics
    Tracks customer preferences for personalized recommendations
    """

    __tablename__ = "customer_item_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_identifier = Column(String(255), nullable=False, index=True)  # email or customer_id
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    menu_item_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # RFM Metrics (Recency, Frequency, Monetary)
    order_count = Column(Integer, default=0, nullable=False)
    total_quantity = Column(Integer, default=0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    recency_score = Column(Float, default=0.0, nullable=False)  # Days since last order
    frequency_score = Column(Float, default=0.0, nullable=False)  # Orders per month
    monetary_score = Column(Float, default=0.0, nullable=False)  # Total spent

    # Timestamps
    first_ordered_at = Column(DateTime, nullable=True)
    last_ordered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Composite index for faster queries
    __table_args__ = (
        Index('idx_customer_restaurant', 'customer_identifier', 'restaurant_id'),
        Index('idx_customer_menu_item', 'customer_identifier', 'menu_item_id'),
    )

    def __repr__(self):
        return f"<CustomerItemPreference(customer={self.customer_identifier}, item={self.menu_item_id}, orders={self.order_count})>"
