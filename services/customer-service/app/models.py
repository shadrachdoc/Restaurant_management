"""
Customer models for multi-tenant SaaS
Each customer belongs to a specific restaurant (tenant isolation)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base


class Customer(Base):
    """
    Customer model - scoped to restaurant for multi-tenancy

    Key Features:
    - Customers are unique per restaurant (same email can exist in different restaurants)
    - Supports both registered customers and guest checkout
    - Tracks delivery addresses and preferences
    - Loyalty points for future rewards
    """

    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Restaurant ID - references Restaurant Service's restaurants table
    # Note: No FK constraint for microservices boundary (soft reference)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Authentication
    email = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for guest checkout

    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Delivery Info
    default_delivery_address = Column(String(500))
    city = Column(String(100))
    postal_code = Column(String(20))

    # Account Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)

    # Marketing
    accepts_marketing = Column(Boolean, default=False)

    # Loyalty (Future)
    loyalty_points = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_order_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique constraints
    # Same email can exist across different restaurants
    __table_args__ = (
        UniqueConstraint('restaurant_id', 'email', name='uq_restaurant_email'),
        UniqueConstraint('restaurant_id', 'phone_number', name='uq_restaurant_phone'),
    )

    def __repr__(self):
        return f"<Customer {self.email} ({self.restaurant_id})>"


class CustomerSession(Base):
    """
    Customer session tracking for analytics and security
    """

    __tablename__ = "customer_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    # Restaurant ID - soft reference (no FK for microservices boundary)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Session info
    session_token = Column(String(500), nullable=False, unique=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CustomerSession {self.customer_id}>"
