"""
Security utilities for authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.config.settings import settings
from shared.models.enums import UserRole
import uuid

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """
    Create a JWT refresh token

    Args:
        user_id: User ID

    Returns:
        Tuple of (encoded token, expiration datetime)
    """
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid.uuid4())  # JWT ID for token revocation
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt, expire


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> uuid.UUID:
    """
    Get current user ID from JWT token

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )


def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserRole:
    """
    Get current user role from JWT token

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User role

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = decode_token(token)

    role = payload.get("role")
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return UserRole(role)


def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific roles

    Args:
        allowed_roles: Roles that are allowed

    Returns:
        Dependency function
    """
    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        token = credentials.credentials
        payload = decode_token(token)

        user_role = payload.get("role")
        if not user_role or UserRole(user_role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return payload

    return role_checker
