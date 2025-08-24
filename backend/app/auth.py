from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from .database import get_db_session
from .models import User
from sqlalchemy.orm import Session

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Get current authenticated user.
    
    This is a stub implementation that returns a default user.
    In production, this would validate JWT tokens and return the actual user.
    """
    # For development, always return a consistent default user ID
    # In production, this would validate JWT tokens and return the actual user
    return User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="default@example.com",
        name="Default User",
        is_active=True
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_auth() -> bool:
    """Check if authentication is required."""
    # For development, authentication is optional
    # In production, this would return True
    return False
