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
from ..database import get_db
from ..models import Order, OrderItem
from ..schemas import (
    OrderCreate,
    OrderResponse,
    OrderUpdateStatus,
    MessageResponse
)
from shared.models.enums import OrderStatus
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("order-routes")


def generate_order_number() -> str:
    """Generate a unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3).upper()
    return f"ORD-{timestamp}-{random_suffix}"


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
    total_amount = 0.0
    order_items_data = []

    for item in order_data.items:
        # Calculate item subtotal
        item_subtotal = item.quantity * 0.0  # Price will be fetched from restaurant-service

        order_items_data.append({
            "menu_item_id": item.menu_item_id,
            "menu_item_name": "",  # Will be filled by restaurant-service
            "unit_price": 0.0,  # Will be filled by restaurant-service
            "quantity": item.quantity,
            "subtotal": item_subtotal,
            "special_requests": item.special_requests,
            "contributor_name": item.contributor_name
        })

    # Create order
    new_order = Order(
        restaurant_id=order_data.restaurant_id,
        table_id=order_data.table_id,
        order_number=generate_order_number(),
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        session_id=order_data.session_id,
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

    return order


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status (CHEF/ADMIN only)
    Status flow: PENDING → CONFIRMED → PREPARING → READY → SERVED → COMPLETED
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
