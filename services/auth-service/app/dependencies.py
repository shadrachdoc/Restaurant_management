"""Dependencies for auth service"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models import User
from .security import decode_token
from shared.models.enums import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def require_master_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require master admin role"""
    print(f"DEBUG require_master_admin: user={current_user.username}, role={current_user.role}, role_type={type(current_user.role)}")
    print(f"DEBUG require_master_admin: UserRole.MASTER_ADMIN={UserRole.MASTER_ADMIN}, type={type(UserRole.MASTER_ADMIN)}")
    print(f"DEBUG require_master_admin: Comparison result={current_user.role != UserRole.MASTER_ADMIN}")
    if current_user.role != UserRole.MASTER_ADMIN:
        print(f"DEBUG require_master_admin: RAISING 403")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Master admin access required."
        )
    print(f"DEBUG require_master_admin: SUCCESS")
    return current_user
