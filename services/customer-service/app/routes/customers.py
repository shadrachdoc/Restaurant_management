"""
Customer authentication and profile management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import UUID

from ..database import get_db
from ..models import Customer
from ..schemas import (
    CustomerRegister,
    CustomerLogin,
    GuestCheckout,
    CustomerUpdate,
    CustomerResponse,
    TokenResponse,
    MessageResponse
)
from ..utils.auth import (
    hash_password,
    verify_password,
    create_tokens_for_customer
)
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("customer-routes")


async def get_restaurant_id_from_slug(db: AsyncSession, slug: str) -> UUID:
    """
    Helper to get restaurant_id from slug
    This would normally call the restaurant service, but for now we'll query directly
    """
    from sqlalchemy import text

    query = text("SELECT id FROM restaurants WHERE slug = :slug AND is_active = TRUE")
    result = await db.execute(query, {"slug": slug})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{slug}' not found or inactive"
        )

    return row[0]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(
    customer_data: CustomerRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new customer for a specific restaurant

    Example:
        POST /api/v1/customers/register
        {
            "restaurant_slug": "pizza-palace",
            "email": "john@example.com",
            "phone_number": "+1234567890",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe"
        }
    """
    # Get restaurant ID from slug
    restaurant_id = await get_restaurant_id_from_slug(db, customer_data.restaurant_slug)

    # Check if customer already exists for this restaurant
    stmt = select(Customer).where(
        Customer.restaurant_id == restaurant_id,
        Customer.email == customer_data.email
    )
    result = await db.execute(stmt)
    existing_customer = result.scalar_one_or_none()

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists for this restaurant"
        )

    # Create new customer
    hashed_password = hash_password(customer_data.password)

    new_customer = Customer(
        restaurant_id=restaurant_id,
        email=customer_data.email,
        phone_number=customer_data.phone_number,
        password_hash=hashed_password,
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        accepts_marketing=customer_data.accepts_marketing,
        is_active=True,
        is_verified=False
    )

    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    logger.info(f"Customer registered: {new_customer.email} for restaurant {restaurant_id}")

    # Generate JWT tokens
    tokens = create_tokens_for_customer(
        str(new_customer.id),
        str(new_customer.restaurant_id),
        new_customer.email
    )

    # Return tokens and customer profile
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        customer=CustomerResponse.model_validate(new_customer)
    )


@router.post("/login", response_model=TokenResponse)
async def login_customer(
    login_data: CustomerLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login customer for a specific restaurant

    Example:
        POST /api/v1/customers/login
        {
            "restaurant_slug": "pizza-palace",
            "email": "john@example.com",
            "password": "SecurePass123!"
        }
    """
    # Get restaurant ID from slug
    restaurant_id = await get_restaurant_id_from_slug(db, login_data.restaurant_slug)

    # Find customer
    stmt = select(Customer).where(
        Customer.restaurant_id == restaurant_id,
        Customer.email == login_data.email
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if customer has password (not a guest)
    if not customer.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was created as guest. Please register to set a password."
        )

    # Verify password
    if not verify_password(login_data.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is active
    if not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support."
        )

    logger.info(f"Customer logged in: {customer.email} for restaurant {restaurant_id}")

    # Generate JWT tokens
    tokens = create_tokens_for_customer(
        str(customer.id),
        str(customer.restaurant_id),
        customer.email
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        customer=CustomerResponse.model_validate(customer)
    )


@router.post("/guest-checkout", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def guest_checkout(
    guest_data: GuestCheckout,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a guest customer account (no password required)
    Used for quick checkout without registration

    Example:
        POST /api/v1/customers/guest-checkout
        {
            "restaurant_slug": "pizza-palace",
            "email": "guest@example.com",
            "phone_number": "+1234567890",
            "first_name": "Guest",
            "last_name": "User",
            "delivery_address": "123 Main St"
        }
    """
    # Get restaurant ID from slug
    restaurant_id = await get_restaurant_id_from_slug(db, guest_data.restaurant_slug)

    # Check if customer already exists
    stmt = select(Customer).where(
        Customer.restaurant_id == restaurant_id,
        Customer.email == guest_data.email
    )
    result = await db.execute(stmt)
    existing_customer = result.scalar_one_or_none()

    if existing_customer:
        # Return existing customer if guest, otherwise ask to login
        if not existing_customer.password_hash:
            return CustomerResponse.model_validate(existing_customer)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account already exists. Please login instead."
            )

    # Create guest customer (no password)
    guest_customer = Customer(
        restaurant_id=restaurant_id,
        email=guest_data.email,
        phone_number=guest_data.phone_number,
        password_hash=None,  # Guest - no password
        first_name=guest_data.first_name,
        last_name=guest_data.last_name,
        default_delivery_address=guest_data.delivery_address,
        is_active=True,
        is_verified=False
    )

    db.add(guest_customer)
    await db.commit()
    await db.refresh(guest_customer)

    logger.info(f"Guest customer created: {guest_customer.email} for restaurant {restaurant_id}")

    return CustomerResponse.model_validate(guest_customer)


@router.get("/me", response_model=CustomerResponse)
async def get_customer_profile(
    db: AsyncSession = Depends(get_db)
    # TODO: Add JWT authentication dependency
):
    """
    Get current customer profile (requires authentication)
    """
    # This would use JWT to get customer_id
    # For now, return a placeholder error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication middleware not yet implemented"
    )


@router.put("/me", response_model=CustomerResponse)
async def update_customer_profile(
    update_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add JWT authentication dependency
):
    """
    Update customer profile (requires authentication)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication middleware not yet implemented"
    )
