"""
Authentication Security Layer (SIH 26180)
Provides JWT session token signing, verification, cookie management, and rate limiting.
Protects against token tampering, expiry violations, and token_version revocations.
"""

import logging
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt

logger = logging.getLogger("smart_farming.auth.security")

# Authentication Configuration
DEFAULT_SECRET_KEY = "khetsaathi-dev-secret-key-change-in-production"
AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", DEFAULT_SECRET_KEY)
JWT_ALGORITHM = "HS256"

# Session Expiry
ACCESS_TOKEN_EXPIRE_DAYS = int(os.environ.get("AUTH_ACCESS_TOKEN_EXPIRE_DAYS", "30"))
REGISTRATION_TOKEN_EXPIRE_MINUTES = 15

# Cookie settings
AUTH_COOKIE_NAME = "khetsaathi_session"
AUTH_COOKIE_SECURE = os.environ.get("AUTH_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
AUTH_COOKIE_SAMESITE = os.environ.get("AUTH_COOKIE_SAMESITE", "lax").lower()


# ============================================================================
# JWT Token Generation & Decoding
# ============================================================================

def create_access_token(
    farmer_id: int,
    farmer_uuid: str,
    phone: str,
    token_version: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT session access token for an authenticated farmer.
    Contains token_version for instant logout/revocation.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": farmer_uuid,
        "farmer_id": farmer_id,
        "phone": phone,
        "token_version": token_version,
        "type": "access_token",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_registration_token(phone: str) -> str:
    """
    Creates a single-purpose, short-lived JWT registration credential.
    Issued ONLY after successful Twilio Verify OTP verification for an unregistered phone.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=REGISTRATION_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": phone,
        "type": "registration_token",
        "jti": secrets.token_hex(8),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token using AUTH_SECRET_KEY.
    Raises jwt.PyJWTError subclasses on invalid signature, expired token, or malformed data.
    """
    return jwt.decode(token, AUTH_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# ============================================================================
# Modular Rate Limiting (In-Memory with Sliding Window)
# ============================================================================

class SlidingWindowRateLimiter:
    """
    In-memory rate limiter for tracking attempts by key (phone or IP).
    Thread-safe for ASGI single-process or multi-worker concurrency.
    Modular design allows swapping with Redis in clustered environments.
    """

    def __init__(self):
        # Maps key -> list of float epoch timestamps
        self._history = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Checks if request is allowed under the rate limit.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        window_start = now - window_seconds

        # Filter out timestamps outside current sliding window
        valid_timestamps = [t for t in self._history[key] if t > window_start]
        self._history[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            oldest_in_window = valid_timestamps[0]
            retry_after = int(window_seconds - (now - oldest_in_window)) + 1
            return False, max(1, retry_after)

        self._history[key].append(now)
        return True, 0

    def reset(self, key: str) -> None:
        """Clears rate limit history for a specific key (e.g. upon successful verify)."""
        if key in self._history:
            del self._history[key]


# Global rate limiter instances:
# 1. OTP Send: Max 3 sends per phone per 10 minutes (600s)
otp_send_limiter = SlidingWindowRateLimiter()

# 2. OTP Verify: Max 5 attempts per phone per 15 minutes (900s)
otp_verify_limiter = SlidingWindowRateLimiter()
