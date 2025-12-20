"""
Customer assistance request routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from ..database import get_db
from ..models import AssistanceRequest
from ..schemas import (
    AssistanceRequestCreate,
    AssistanceRequestResolve,
    AssistanceRequestResponse,
    MessageResponse
)
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("assistance-routes")


@router.post("/assistance", response_model=AssistanceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_assistance_request(
    request_data: AssistanceRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new assistance request (PUBLIC - no authentication)
    Customers can request waiter, bill, or report issues
    """
    new_request = AssistanceRequest(
        restaurant_id=request_data.restaurant_id,
        table_id=request_data.table_id,
        request_type=request_data.request_type,
        message=request_data.message,
        is_resolved=False
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    logger.info(f"Assistance request created: {new_request.id} - Type: {new_request.request_type}")

    return new_request


@router.get("/restaurants/{restaurant_id}/assistance", response_model=List[AssistanceRequestResponse])
async def list_assistance_requests(
    restaurant_id: UUID,
    resolved: Optional[bool] = Query(None),
    table_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    List assistance requests for a restaurant (STAFF/ADMIN)
    Filterable by resolved status and table
    """
    # Build query
    query = select(AssistanceRequest).where(
        AssistanceRequest.restaurant_id == restaurant_id
    )

    if resolved is not None:
        query = query.where(AssistanceRequest.is_resolved == resolved)

    if table_id:
        query = query.where(AssistanceRequest.table_id == table_id)

    # Order by creation time (newest first)
    query = query.order_by(AssistanceRequest.created_at.desc()).limit(limit)

    result = await db.execute(query)
    requests = result.scalars().all()

    return requests


@router.get("/assistance/{request_id}", response_model=AssistanceRequestResponse)
async def get_assistance_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific assistance request
    """
    result = await db.execute(
        select(AssistanceRequest).where(AssistanceRequest.id == request_id)
    )
    assistance_request = result.scalar_one_or_none()

    if not assistance_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistance request not found"
        )

    return assistance_request


@router.patch("/assistance/{request_id}/resolve", response_model=AssistanceRequestResponse)
async def resolve_assistance_request(
    request_id: UUID,
    resolve_data: AssistanceRequestResolve,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an assistance request as resolved (STAFF/ADMIN)
    """
    result = await db.execute(
        select(AssistanceRequest).where(AssistanceRequest.id == request_id)
    )
    assistance_request = result.scalar_one_or_none()

    if not assistance_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistance request not found"
        )

    if assistance_request.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already resolved"
        )

    assistance_request.is_resolved = True
    assistance_request.resolved_by = resolve_data.resolved_by
    assistance_request.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(assistance_request)

    logger.info(f"Assistance request {request_id} resolved by user {resolve_data.resolved_by}")

    return assistance_request


@router.delete("/assistance/{request_id}", response_model=MessageResponse)
async def delete_assistance_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an assistance request (ADMIN only)
    """
    result = await db.execute(
        select(AssistanceRequest).where(AssistanceRequest.id == request_id)
    )
    assistance_request = result.scalar_one_or_none()

    if not assistance_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistance request not found"
        )

    await db.delete(assistance_request)
    await db.commit()

    logger.info(f"Assistance request {request_id} deleted")

    return MessageResponse(message="Assistance request deleted successfully")
