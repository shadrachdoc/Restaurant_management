"""
Table session management routes for collaborative ordering
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
import secrets
from ..database import get_db
from ..models import TableSession, Order
from ..schemas import (
    TableSessionCreate,
    TableSessionJoin,
    TableSessionAddItem,
    TableSessionResponse,
    MessageResponse,
    OrderCreate,
    OrderResponse
)
from shared.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("session-routes")


def generate_session_token() -> str:
    """Generate a unique session token"""
    return secrets.token_urlsafe(32)


@router.post("/sessions", response_model=TableSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: TableSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new table session for collaborative ordering
    First customer at table scans QR code and starts session
    """
    # Check if there's already an active session for this table
    result = await db.execute(
        select(TableSession).where(
            TableSession.table_id == session_data.table_id,
            TableSession.is_active == True
        )
    )
    existing_session = result.scalar_one_or_none()

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active session already exists for this table"
        )

    # Create new session
    new_session = TableSession(
        restaurant_id=session_data.restaurant_id,
        table_id=session_data.table_id,
        session_token=generate_session_token(),
        is_active=True,
        is_locked=False,
        participants=[{
            "name": session_data.participant_name,
            "joined_at": datetime.utcnow().isoformat()
        }],
        pending_items=[],
        expires_at=datetime.utcnow() + timedelta(hours=4)  # 4 hour expiry
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    logger.info(f"Table session created: {new_session.id} for table {session_data.table_id}")

    return new_session


@router.post("/sessions/{session_token}/join", response_model=TableSessionResponse)
async def join_session(
    session_token: str,
    join_data: TableSessionJoin,
    db: AsyncSession = Depends(get_db)
):
    """
    Join an existing table session
    Other customers at same table scan QR code and join session
    """
    result = await db.execute(
        select(TableSession).where(
            TableSession.session_token == session_token,
            TableSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

    if session.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is locked (order already submitted)"
        )

    # Add participant
    participants = session.participants or []
    participants.append({
        "name": join_data.participant_name,
        "joined_at": datetime.utcnow().isoformat()
    })
    session.participants = participants

    await db.commit()
    await db.refresh(session)

    logger.info(f"Participant {join_data.participant_name} joined session {session.id}")

    return session


@router.post("/sessions/{session_token}/items", response_model=TableSessionResponse)
async def add_item_to_session(
    session_token: str,
    item_data: TableSessionAddItem,
    db: AsyncSession = Depends(get_db)
):
    """
    Add an item to the pending order in the session
    Each customer can add their items before final submission
    """
    result = await db.execute(
        select(TableSession).where(
            TableSession.session_token == session_token,
            TableSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

    if session.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is locked (order already submitted)"
        )

    # Add item to pending items
    pending_items = session.pending_items or []
    pending_items.append({
        "menu_item_id": str(item_data.menu_item_id),
        "quantity": item_data.quantity,
        "special_requests": item_data.special_requests,
        "contributor_name": item_data.contributor_name,
        "added_at": datetime.utcnow().isoformat()
    })
    session.pending_items = pending_items

    await db.commit()
    await db.refresh(session)

    logger.info(f"Item added to session {session.id} by {item_data.contributor_name}")

    return session


@router.get("/sessions/{session_token}", response_model=TableSessionResponse)
async def get_session(
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current session status
    """
    result = await db.execute(
        select(TableSession).where(
            TableSession.session_token == session_token
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.post("/sessions/{session_token}/submit", response_model=MessageResponse)
async def submit_session_order(
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit the collaborative order and lock the session
    Converts pending items into a real order
    """
    result = await db.execute(
        select(TableSession).where(
            TableSession.session_token == session_token,
            TableSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

    if session.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already submitted"
        )

    if not session.pending_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items in session to submit"
        )

    # Lock the session
    session.is_locked = True
    await db.commit()

    logger.info(f"Session {session.id} submitted and locked")

    return MessageResponse(message="Order submitted successfully")


@router.delete("/sessions/{session_token}", response_model=MessageResponse)
async def close_session(
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Close/end a table session
    """
    result = await db.execute(
        select(TableSession).where(
            TableSession.session_token == session_token
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.is_active = False
    await db.commit()

    logger.info(f"Session {session.id} closed")

    return MessageResponse(message="Session closed successfully")
