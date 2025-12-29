"""
Order management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import secrets
import httpx
import os
from ..database import get_db
from ..models import Order, OrderItem
from ..schemas import (
    OrderCreate,
    OrderResponse,
    OrderUpdateStatus,
    MessageResponse
)
from shared.models.enums import OrderStatus, OrderType
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("order-routes")

# Restaurant service URL
RESTAURANT_SERVICE_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://restaurant-service:8003")


def generate_order_number() -> str:
    """Generate a unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3).upper()
    return f"ORD-{timestamp}-{random_suffix}"


async def fetch_menu_item(restaurant_id: UUID, menu_item_id: UUID) -> dict:
    """Fetch menu item details from restaurant service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RESTAURANT_SERVICE_URL}/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch menu item {menu_item_id}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error fetching menu item {menu_item_id}: {e}")
        return None


async def fetch_restaurant_slug(restaurant_id: UUID) -> Optional[str]:
    """Fetch restaurant slug from restaurant service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RESTAURANT_SERVICE_URL}/api/v1/restaurants/{restaurant_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("slug")
            else:
                logger.warning(f"Failed to fetch restaurant {restaurant_id}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error fetching restaurant {restaurant_id}: {e}")
        return None


async def lock_table(restaurant_id: UUID, table_id: UUID) -> bool:
    """Lock table by setting status to OCCUPIED"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{RESTAURANT_SERVICE_URL}/api/v1/restaurants/{restaurant_id}/tables/{table_id}",
                json={"status": "occupied"},
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Table {table_id} locked successfully")
                return True
            else:
                logger.warning(f"Failed to lock table {table_id}: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error locking table {table_id}: {e}")
        return False


async def unlock_table(restaurant_id: UUID, table_id: UUID) -> bool:
    """Unlock table by setting status to AVAILABLE"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{RESTAURANT_SERVICE_URL}/api/v1/restaurants/{restaurant_id}/tables/{table_id}",
                json={"status": "available"},
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Table {table_id} unlocked successfully")
                return True
            else:
                logger.warning(f"Failed to unlock table {table_id}: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error unlocking table {table_id}: {e}")
        return False


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order (PUBLIC - no authentication required)
    Customers can place orders directly via QR code or table session
    """
    # Calculate order totals
    subtotal = 0.0
    order_items_data = []

    for item in order_data.items:
        # Fetch menu item details from restaurant service
        menu_item = await fetch_menu_item(order_data.restaurant_id, item.menu_item_id)

        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item {item.menu_item_id} not found"
            )

        item_name = menu_item.get("name", "Unknown Item")
        item_price = float(menu_item.get("price", 0.0))
        item_subtotal = item_price * item.quantity
        subtotal += item_subtotal

        order_items_data.append({
            "menu_item_id": item.menu_item_id,
            "item_name": item_name,
            "item_price": item_price,
            "quantity": item.quantity,
            "special_instructions": item.special_requests
        })

    # Calculate tax (10%)
    tax = subtotal * 0.10
    total = subtotal + tax

    # Create order
    new_order = Order(
        restaurant_id=order_data.restaurant_id,
        table_id=order_data.table_id,
        order_number=generate_order_number(),
        status=OrderStatus.PENDING,
        order_type=order_data.order_type if order_data.order_type else OrderType.TABLE,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        customer_email=order_data.customer_email,
        delivery_address=order_data.delivery_address,
        subtotal=subtotal,
        tax=tax,
        total=total,
        special_instructions=order_data.special_instructions
    )

    db.add(new_order)
    await db.flush()  # Get order ID before adding items

    # Add order items
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            **item_data
        )
        db.add(order_item)

    await db.commit()
    await db.refresh(new_order)

    # Lock the table when order is created
    if new_order.table_id:
        await lock_table(new_order.restaurant_id, new_order.table_id)
        logger.info(f"Table {new_order.table_id} locked for order {new_order.order_number}")

    # Load items relationship
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == new_order.id)
    )
    order_with_items = result.scalar_one()

    logger.info(f"Order created: {new_order.order_number}")

    return order_with_items


@router.get("/restaurants/{restaurant_id}/orders", response_model=List[OrderResponse])
async def list_orders(
    restaurant_id: UUID,
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    table_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    List all orders for a restaurant (CHEF/ADMIN)
    Filterable by status and table
    """
    # Build query
    query = select(Order).options(selectinload(Order.items)).where(
        Order.restaurant_id == restaurant_id
    )

    if status_filter:
        query = query.where(Order.status == status_filter)

    if table_id:
        query = query.where(Order.table_id == table_id)

    # Order by creation time (newest first)
    query = query.order_by(Order.created_at.desc()).limit(limit)

    result = await db.execute(query)
    orders = result.scalars().all()

    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific order by ID (PUBLIC - for order tracking)
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Fetch restaurant slug for frontend navigation
    restaurant_slug = await fetch_restaurant_slug(order.restaurant_id)

    # Convert to dict and add slug
    order_dict = {
        "id": order.id,
        "restaurant_id": order.restaurant_id,
        "restaurant_slug": restaurant_slug,
        "table_id": order.table_id,
        "order_number": order.order_number,
        "status": order.status,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_email": getattr(order, "customer_email", None),
        "order_type": getattr(order, "order_type", None),
        "delivery_address": getattr(order, "delivery_address", None),
        "subtotal": order.subtotal,
        "tax": order.tax,
        "total": order.total,
        "special_instructions": order.special_instructions,
        "items": order.items,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "completed_at": order.completed_at
    }

    return order_dict


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status (CHEF/ADMIN only)
    Status flow: PENDING → CONFIRMED → PREPARING → READY → SERVED → COMPLETED
    When order is marked as SERVED or COMPLETED, the table is automatically unlocked
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Update status
    order.status = status_update.status

    # Set timestamps based on status
    if status_update.status == OrderStatus.CONFIRMED:
        order.confirmed_at = datetime.utcnow()
    elif status_update.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
        order.completed_at = datetime.utcnow()

    # When order is served or completed, unlock the table
    if status_update.status in [OrderStatus.SERVED, OrderStatus.COMPLETED] and order.table_id:
        await unlock_table(order.restaurant_id, order.table_id)
        logger.info(f"Table {order.table_id} unlocked after order {order.order_number} marked as {status_update.status}")

    await db.commit()
    await db.refresh(order)

    logger.info(f"Order {order.order_number} status updated to {status_update.status}")

    return order


@router.delete("/orders/{order_id}", response_model=MessageResponse)
async def cancel_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an order (mark as CANCELLED)
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status in [OrderStatus.COMPLETED, OrderStatus.SERVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed or served order"
        )

    order.status = OrderStatus.CANCELLED
    order.completed_at = datetime.utcnow()

    await db.commit()

    logger.info(f"Order {order.order_number} cancelled")

    return MessageResponse(message="Order cancelled successfully")
