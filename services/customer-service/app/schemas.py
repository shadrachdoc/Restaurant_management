"""
Pydantic schemas for Customer Service
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4


# Customer Registration & Authentication
class CustomerRegister(BaseModel):
    """Customer registration schema"""
    restaurant_slug: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    accepts_marketing: bool = False


class CustomerLogin(BaseModel):
    """Customer login schema"""
    restaurant_slug: str
    email: EmailStr
    password: str


class GuestCheckout(BaseModel):
    """Guest checkout - create temporary customer"""
    restaurant_slug: str
    email: EmailStr
    phone_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    delivery_address: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Update customer profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    default_delivery_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    accepts_marketing: Optional[bool] = None


class PasswordChange(BaseModel):
    """Change password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr
    restaurant_slug: str


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# Response Schemas
class CustomerResponse(BaseModel):
    """Customer profile response"""
    id: UUID4
    restaurant_id: UUID4
    email: str
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
    default_delivery_address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    is_active: bool
    is_verified: bool
    loyalty_points: int
    accepts_marketing: bool
    created_at: datetime
    last_order_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    customer: CustomerResponse


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class LoyaltyResponse(BaseModel):
    """Loyalty points response"""
    customer_id: UUID4
    loyalty_points: int
    points_earned_today: int
    next_reward_at: int
    rewards_available: int
