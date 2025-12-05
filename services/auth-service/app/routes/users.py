"""
User management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserUpdate, StaffUpdate, MessageResponse
from ..security import get_current_user_id, require_role
from shared.models.enums import UserRole
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("user-routes")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get current user profile
    """
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update current user profile
    """
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.email is not None:
        # Check if email is already taken
        email_check = await db.execute(
            select(User).where(User.email == user_data.email, User.id != current_user_id)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email

    await db.commit()
    await db.refresh(user)

    logger.info(f"User updated: {user.username}")

    return user


@router.patch("/me/restaurant", response_model=UserResponse)
async def update_user_restaurant(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update current user's restaurant_id (called when user creates a restaurant)
    """
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.restaurant_id = restaurant_id
    await db.commit()
    await db.refresh(user)

    logger.info(f"User restaurant_id updated: {user.username} -> {restaurant_id}")

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role(UserRole.MASTER_ADMIN, UserRole.RESTAURANT_ADMIN))
):
    """
    Get user by ID (Admin only)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role(UserRole.MASTER_ADMIN))
):
    """
    List all users (Master Admin only)
    """
    query = select(User)

    if role:
        query = query.where(User.role == role)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return users


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role(UserRole.MASTER_ADMIN))
):
    """
    Delete user (Master Admin only)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    logger.info(f"User deleted: {user.username} (ID: {user_id})")

    return MessageResponse(message="User deleted successfully")


@router.patch("/{user_id}/toggle-status", response_model=UserResponse)
async def toggle_user_status(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role(UserRole.MASTER_ADMIN, UserRole.RESTAURANT_ADMIN))
):
    """
    Toggle user active status (Admin only)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)

    logger.info(f"User status toggled: {user.username} -> {'active' if user.is_active else 'inactive'}")

    return user


# Chef Management Endpoints (for Restaurant Admin)

@router.post("/chef", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_chef(
    chef_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN))
):
    """
    Create a new chef account (Restaurant Admin only)
    """
    from ..security import hash_password

    # Check if username already exists
    username_check = await db.execute(
        select(User).where(User.username == chef_data.get('username'))
    )
    if username_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    if chef_data.get('email'):
        email_check = await db.execute(
            select(User).where(User.email == chef_data.get('email'))
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Create chef user
    new_chef = User(
        username=chef_data['username'],
        email=chef_data.get('email'),
        full_name=chef_data.get('full_name'),
        hashed_password=hash_password(chef_data['password']),
        role=UserRole.CHEF,
        restaurant_id=chef_data.get('restaurant_id'),
        is_active=True
    )

    db.add(new_chef)
    await db.commit()
    await db.refresh(new_chef)

    logger.info(f"Chef created: {new_chef.username} for restaurant {chef_data.get('restaurant_id')}")

    return new_chef


@router.get("/chefs/{restaurant_id}", response_model=List[UserResponse])
async def list_chefs_by_restaurant(
    restaurant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN, UserRole.MASTER_ADMIN))
):
    """
    List all chefs for a specific restaurant (Restaurant Admin/Master Admin only)
    """
    result = await db.execute(
        select(User).where(
            User.restaurant_id == restaurant_id,
            User.role == UserRole.CHEF
        ).order_by(User.created_at.desc())
    )
    chefs = result.scalars().all()

    return chefs


@router.delete("/chef/{chef_id}", response_model=MessageResponse)
async def delete_chef(
    chef_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN))
):
    """
    Delete a chef account (Restaurant Admin only)
    """
    result = await db.execute(
        select(User).where(User.id == chef_id, User.role == UserRole.CHEF)
    )
    chef = result.scalar_one_or_none()

    if not chef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chef not found"
        )

    # Verify the chef belongs to the current user's restaurant
    current_restaurant_id_str = current_user.get('restaurant_id')
    if current_restaurant_id_str:
        current_restaurant_id = UUID(current_restaurant_id_str)
    else:
        current_restaurant_id = None

    if chef.restaurant_id != current_restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete chefs from your own restaurant"
        )

    await db.delete(chef)
    await db.commit()

    logger.info(f"Chef deleted: {chef.username} (ID: {chef_id})")

    return MessageResponse(message="Chef account deleted successfully")


@router.get("/staff/{restaurant_id}", response_model=List[UserResponse])
async def list_restaurant_staff(
    restaurant_id: UUID,
    role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN, UserRole.MASTER_ADMIN))
):
    """
    List all staff for a specific restaurant (chefs and customers)
    Optional role filter: 'chef' or 'customer'
    """
    query = select(User).where(User.restaurant_id == restaurant_id)

    if role:
        if role.lower() == 'chef':
            query = query.where(User.role == UserRole.CHEF)
        elif role.lower() == 'customer':
            query = query.where(User.role == UserRole.CUSTOMER)
    else:
        # Get both chefs and customers
        query = query.where(User.role.in_([UserRole.CHEF, UserRole.CUSTOMER]))

    query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    staff = result.scalars().all()

    return staff


@router.post("/customer", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN))
):
    """
    Create a new customer account (Restaurant Admin only)
    """
    from ..security import hash_password

    # Check if username already exists
    username_check = await db.execute(
        select(User).where(User.username == customer_data.get('username'))
    )
    if username_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    if customer_data.get('email'):
        email_check = await db.execute(
            select(User).where(User.email == customer_data.get('email'))
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Create customer user
    new_customer = User(
        username=customer_data['username'],
        email=customer_data.get('email'),
        full_name=customer_data.get('full_name'),
        hashed_password=hash_password(customer_data['password']),
        role=UserRole.CUSTOMER,
        restaurant_id=customer_data.get('restaurant_id'),
        is_active=True
    )

    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    logger.info(f"Customer created: {new_customer.username} for restaurant {customer_data.get('restaurant_id')}")

    return new_customer


@router.delete("/customer/{customer_id}", response_model=MessageResponse)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.RESTAURANT_ADMIN))
):
    """
    Delete a customer account (Restaurant Admin only)
    """
    result = await db.execute(
        select(User).where(User.id == customer_id, User.role == UserRole.CUSTOMER)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Verify the customer belongs to the current user's restaurant
    current_restaurant_id_str = current_user.get('restaurant_id')
    if current_restaurant_id_str:
        current_restaurant_id = UUID(current_restaurant_id_str)
    else:
        current_restaurant_id = None

    if customer.restaurant_id != current_restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete customers from your own restaurant"
        )

    await db.delete(customer)
    await db.commit()

    logger.info(f"Customer deleted: {customer.username} (ID: {customer_id})")

    return MessageResponse(message="Customer account deleted successfully")
