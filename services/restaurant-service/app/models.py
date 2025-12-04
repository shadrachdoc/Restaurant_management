"""
Database models for Restaurant Service
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from shared.models.enums import MenuItemCategory, TableStatus, SubscriptionStatus, PricingPlan
from .database import Base


class Restaurant(Base):
    """Restaurant model"""

    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    theme_color = Column(String(7), default="#000000")  # Hex color

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)

    # Subscription
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    pricing_plan = Column(SQLEnum(PricingPlan), default=PricingPlan.BASIC, nullable=False)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)

    # Branding & Marketing
    banner_images = Column(JSONB, default=list)  # List of image URLs
    upcoming_events = Column(JSONB, default=list)  # List of event objects
    advertisements = Column(JSONB, default=list)  # List of ad objects

    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    max_tables = Column(Integer, default=10, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Restaurant(id={self.id}, name={self.name})>"


class MenuItem(Base):
    """Menu item model"""

    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(MenuItemCategory), nullable=False, index=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)

    # Availability
    is_available = Column(Boolean, default=True, nullable=False)
    is_vegetarian = Column(Boolean, default=False, nullable=False)
    is_vegan = Column(Boolean, default=False, nullable=False)
    is_gluten_free = Column(Boolean, default=False, nullable=False)

    # Additional info
    preparation_time = Column(Integer, nullable=True)  # in minutes
    calories = Column(Integer, nullable=True)
    ingredients = Column(JSONB, default=list)  # List of ingredients
    allergens = Column(JSONB, default=list)  # List of allergens

    # Display order
    display_order = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")

    def __repr__(self):
        return f"<MenuItem(id={self.id}, name={self.name}, price={self.price})>"


class Table(Base):
    """Table model"""

    __tablename__ = "tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)

    table_number = Column(String(50), nullable=False)
    seat_count = Column(Integer, nullable=False)
    status = Column(SQLEnum(TableStatus), default=TableStatus.AVAILABLE, nullable=False, index=True)

    # QR Code
    qr_code_url = Column(String(500), nullable=True)
    qr_code_data = Column(Text, nullable=True)  # Unique identifier for table

    # Location (optional)
    floor = Column(String(50), nullable=True)
    section = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    restaurant = relationship("Restaurant", back_populates="tables")

    def __repr__(self):
        return f"<Table(id={self.id}, number={self.table_number}, seats={self.seat_count})>"


class Feedback(Base):
    """Customer feedback model"""

    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    table_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Feedback content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)

    # Customer info (optional)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Feedback(id={self.id}, restaurant_id={self.restaurant_id}, rating={self.rating})>"
