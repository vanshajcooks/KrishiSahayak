"""
FastAPI Authentication Dependencies (SIH 26180)
Provides `get_current_active_farmer` security dependency for protecting farmer-scoped routes.
Validates JWT session signatures, expiry, token_version, and account active state.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status

try:
    from backend.database import get_db_path
    from backend.auth.security import (
        AUTH_COOKIE_NAME,
        decode_token,
    )
    from backend.auth.service import get_farmer_by_id
except ImportError:
    from database import get_db_path
    from auth.security import (
        AUTH_COOKIE_NAME,
        decode_token,
    )
    from auth.service import get_farmer_by_id

logger = logging.getLogger("smart_farming.auth.dependencies")


def get_token_from_request(
    session_cookie: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    authorization: Optional[str] = Header(default=None),
) -> str:
    """
    Extracts the session token from either:
    1. HttpOnly cookie (recommended for web UI)
    2. Authorization: Bearer <token> header (standard for mobile/scripts)
    Raises HTTP 401 if neither is present.
    """
    if session_cookie:
        return session_cookie

    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Session cookie or Bearer token required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_farmer(
    token: str = Depends(get_token_from_request),
    db_path: Path = Depends(get_db_path),
) -> Dict[str, Any]:
    """
    Decodes and verifies JWT session token.
    Validates token signature, expiration, type, and farmer identity.
    Validates that token_version matches the current version in SQLite (revocation check).
    """
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for session access.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    farmer_id = payload.get("farmer_id")
    if not farmer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    farmer = get_farmer_by_id(farmer_id, db_path=db_path)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token version check (revokes sessions when user logs out)
    token_version = payload.get("token_version")
    if token_version != farmer.get("token_version"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or logged out. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return farmer


def get_current_active_farmer(
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
) -> Dict[str, Any]:
    """
    Ensures that the authenticated farmer's account is currently active.
    Returns HTTP 403 Forbidden if account is inactive or deactivated.
    """
    if not current_farmer.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmer account is inactive or suspended.",
        )
    return current_farmer
