
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from app.config import get_settings

settings=get_settings()

def create_access_token(
    data: dict[str, Any],
) -> str:
    
    """
    Generate a JWT access token with an expiration time.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire,
            "type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(
    data: dict[str, Any],
) -> str:
    
    """
    Generate a JWT refresh token with a long-lived expiration time.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )



