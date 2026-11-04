"""
Authentication API Router (SIH 26180)
Implements Phone OTP Send, OTP Verification, Farmer Registration, Profile Query, and Logout.
Uses HttpOnly secure cookies for web clients while maintaining compatibility with Bearer tokens.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status

try:
    from backend.database import get_db_path
    from backend.auth.dependencies import get_current_active_farmer
    from backend.auth.schemas import (
        AuthMeResponse,
        AuthMessageResponse,
        FarmerProfile,
        FarmerRegisterRequest,
        OTPSendRequest,
        OTPSendResponse,
        OTPVerifyRequest,
        OTPVerifyResponse,
    )
    from backend.auth.security import (
        ACCESS_TOKEN_EXPIRE_DAYS,
        AUTH_COOKIE_NAME,
        AUTH_COOKIE_SAMESITE,
        AUTH_COOKIE_SECURE,
        create_access_token,
    )
    from backend.auth.service import (
        get_farmer_dashboard_summary,
        invalidate_farmer_sessions,
        register_farmer,
        send_otp_for_phone,
        verify_otp_for_phone,
    )
except ImportError:
    from database import get_db_path
    from auth.dependencies import get_current_active_farmer
    from auth.schemas import (
        AuthMeResponse,
        AuthMessageResponse,
        FarmerProfile,
        FarmerRegisterRequest,
        OTPSendRequest,
        OTPSendResponse,
        OTPVerifyRequest,
        OTPVerifyResponse,
    )
    from auth.security import (
        ACCESS_TOKEN_EXPIRE_DAYS,
        AUTH_COOKIE_NAME,
        AUTH_COOKIE_SAMESITE,
        AUTH_COOKIE_SECURE,
        create_access_token,
    )
    from auth.service import (
        get_farmer_dashboard_summary,
        invalidate_farmer_sessions,
        register_farmer,
        send_otp_for_phone,
        verify_otp_for_phone,
    )

logger = logging.getLogger("smart_farming.routers.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """Sets secure HttpOnly session cookie on the response."""
    max_age_seconds = ACCESS_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clears the session cookie on logout."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
    )


@router.post(
    "/otp/send",
    response_model=OTPSendResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Phone Verification Code",
)
def request_otp(payload: OTPSendRequest) -> OTPSendResponse:
    """
    Normalizes the phone number and dispatches an SMS verification code via Twilio Verify.
    Rate-limited. Does not disclose whether the phone belongs to an existing farmer.
    """
    success, message, retry_after = send_otp_for_phone(payload.phone)
    if not success:
        if retry_after > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
                headers={"Retry-After": str(retry_after)},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=message,
            )

    return OTPSendResponse(
        status="pending",
        message="Verification code sent if phone number is eligible.",
    )


@router.post(
    "/otp/verify",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Code and Authenticate or Initiate Registration",
)
def verify_otp(
    payload: OTPVerifyRequest,
    response: Response,
    db_path: Path = Depends(get_db_path),
) -> OTPVerifyResponse:
    """
    Verifies code against Twilio Verify.
    - If existing active farmer: Issues HttpOnly session cookie, updates last_login_at, returns profile.
    - If new farmer: Returns single-purpose short-lived registration token to complete profile setup.
    """
    is_valid, error_detail, farmer, reg_token = verify_otp_for_phone(
        phone=payload.phone,
        code=payload.code,
        db_path=db_path,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail or "Invalid or expired verification code.",
        )

    # Branch 1: Existing farmer login
    if farmer is not None:
        if not farmer.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farmer account has been deactivated. Please contact support.",
            )

        token = create_access_token(
            farmer_id=farmer["id"],
            farmer_uuid=farmer["uuid"],
            phone=farmer["phone"],
            token_version=farmer.get("token_version", 1),
        )
        _set_auth_cookie(response, token)

        profile = FarmerProfile(
            uuid=farmer["uuid"],
            name=farmer["name"],
            phone=farmer["phone"],
            preferred_language=farmer["preferred_language"],
            state=farmer.get("state"),
            district=farmer.get("district"),
            village=farmer.get("village"),
            created_at=farmer["created_at"],
            last_login_at=farmer.get("last_login_at"),
            is_active=bool(farmer["is_active"]),
        )

        return OTPVerifyResponse(
            is_registered=True,
            message="Authentication successful.",
            farmer=profile,
        )

    # Branch 2: New farmer needing profile registration
    return OTPVerifyResponse(
        is_registered=False,
        message="Phone number verified successfully. Please complete registration.",
        registration_token=reg_token,
    )


@router.post(
    "/register",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete Farmer Profile Registration",
)
def register_new_farmer(
    payload: FarmerRegisterRequest,
    response: Response,
    db_path: Path = Depends(get_db_path),
) -> OTPVerifyResponse:
    """
    Accepts valid short-lived registration token issued after successful OTP verification.
    Creates new farmer record in SQLite, establishes session, and returns profile.
    """
    success, error_detail, new_farmer = register_farmer(
        registration_token=payload.registration_token,
        name=payload.name,
        preferred_language=payload.preferred_language,
        state=payload.state,
        district=payload.district,
        village=payload.village,
        db_path=db_path,
    )

    if not success or new_farmer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail or "Unable to complete registration.",
        )

    token = create_access_token(
        farmer_id=new_farmer["id"],
        farmer_uuid=new_farmer["uuid"],
        phone=new_farmer["phone"],
        token_version=new_farmer.get("token_version", 1),
    )
    _set_auth_cookie(response, token)

    profile = FarmerProfile(
        uuid=new_farmer["uuid"],
        name=new_farmer["name"],
        phone=new_farmer["phone"],
        preferred_language=new_farmer["preferred_language"],
        state=new_farmer.get("state"),
        district=new_farmer.get("district"),
        village=new_farmer.get("village"),
        created_at=new_farmer["created_at"],
        last_login_at=new_farmer.get("last_login_at"),
        is_active=bool(new_farmer["is_active"]),
    )

    return OTPVerifyResponse(
        is_registered=True,
        message="Farmer account registered successfully.",
        farmer=profile,
    )


@router.get(
    "/me",
    response_model=AuthMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated Farmer Profile & Fields",
)
def get_authenticated_farmer_me(
    current_farmer: Dict[str, Any] = Depends(get_current_active_farmer),
    db_path: Path = Depends(get_db_path),
) -> AuthMeResponse:
    """
    Returns the authenticated farmer's profile, owned fields, and active sensor status.
    Never exposes fields or sensors belonging to another farmer.
    """
    try:
        summary = get_farmer_dashboard_summary(current_farmer["id"], db_path=db_path)
        return summary
    except Exception as exc:
        logger.error("Error retrieving dashboard summary for farmer %s: %s", current_farmer["id"], exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load farmer profile summary.",
        )


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and Invalidate Farmer Session",
)
def logout_farmer(
    response: Response,
    current_farmer: Dict[str, Any] = Depends(get_current_active_farmer),
    db_path: Path = Depends(get_db_path),
) -> AuthMessageResponse:
    """
    Invalidates session by incrementing token_version in SQLite and clearing session cookie.
    """
    invalidate_farmer_sessions(current_farmer["id"], db_path=db_path)
    _clear_auth_cookie(response)
    return AuthMessageResponse(
        status="success",
        message="Logged out successfully. All sessions revoked.",
    )
