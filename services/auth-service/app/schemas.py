"""
Pydantic schemas for Auth Service
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4
from shared.models.enums import UserRole


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole
    restaurant_id: Optional[UUID4] = None


class StaffCreate(UserBase):
    """Schema for staff creation (chef/customer) by restaurant admin"""
    password: str = Field(..., min_length=8, max_length=100)
    restaurant_id: UUID4


class UserUpdate(BaseModel):
    """Schema for user update"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    restaurant_id: Optional[UUID4] = None
    is_active: Optional[bool] = None


class StaffUpdate(BaseModel):
    """Schema for staff update by admin (includes password)"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID4
    role: UserRole
    restaurant_id: Optional[UUID4] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Authentication Schemas
class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordVerifyRequest(BaseModel):
    """Schema for password verification"""
    password: str


# Response Schemas
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class PasswordVerifyResponse(BaseModel):
    """Schema for password verification response"""
    valid: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    status_code: int
