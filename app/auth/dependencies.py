# api/dependencies/auth.py

import uuid

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.config import get_settings

settings=get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the JWT access token and return the authenticated user.

    Raises:
        HTTPException(401): If the token is invalid, expired,
        not an access token, or the user cannot be found.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await db.scalar(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.is_deleted.is_(False),
        )
    )

    if user is None:
        raise credentials_exception

    return user


async def get_current_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Validate that the authenticated user is a staff member.

    Returns:
        User: The authenticated staff user.

    Raises:
        HTTPException(403): If the user is not a staff member.
    """
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user



async def get_refresh_user(
    refresh_token: str,
    db: AsyncSession,
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await db.scalar(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.is_deleted.is_(False),
        )
    )

    if not user:
        raise credentials_exception

    return user