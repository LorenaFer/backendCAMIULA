from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    data: dict,
    expires_delta: timedelta,
    token_type: str,
) -> tuple[str, str, datetime]:
    """Issue a JWT carrying a unique jti + token_type claim.

    Returns (encoded_jwt, jti, expires_at). The jti is what callers persist
    to the revoked_tokens table when the token must be invalidated.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = data.copy()
    to_encode.update({"exp": expire, "jti": jti, "type": token_type})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expire


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    return _create_token(
        data,
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        REFRESH_TOKEN_TYPE,
    )


def decode_access_token(token: str) -> Optional[dict]:
    """Decode any app-issued JWT. Returns None on invalid/expired.

    Does NOT check revocation — callers must consult revoked_tokens separately.
    Also does not enforce token_type; callers must verify payload["type"].
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
