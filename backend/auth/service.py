"""
Authentication Business Logic Service (SIH 26180)
Coordinates phone validation, Twilio Verify, database persistence, and session lifecycle.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jwt

try:
    from backend.database import get_connection, get_db_path
    from backend.auth.schemas import (
        FarmerProfile,
        FieldSummary,
        AuthMeResponse,
    )
    from backend.auth.security import (
        create_access_token,
        create_registration_token,
        decode_token,
        otp_send_limiter,
        otp_verify_limiter,
    )
    from backend.auth.twilio_verify import get_twilio_client
except ImportError:
    from database import get_connection, get_db_path
    from auth.schemas import (
        FarmerProfile,
        FieldSummary,
        AuthMeResponse,
    )
    from auth.security import (
        create_access_token,
        create_registration_token,
        decode_token,
        otp_send_limiter,
        otp_verify_limiter,
    )
    from auth.twilio_verify import get_twilio_client

logger = logging.getLogger("smart_farming.auth.service")


# Rate limit configuration
OTP_SEND_MAX_REQUESTS = 3
OTP_SEND_WINDOW_SECONDS = 600  # 10 minutes

OTP_VERIFY_MAX_REQUESTS = 5
OTP_VERIFY_WINDOW_SECONDS = 900  # 15 minutes


def send_otp_for_phone(phone: str, twilio_client=None) -> Tuple[bool, str, int]:
    """
    Sends an SMS OTP to normalized phone using Twilio Verify.
    Applies rate limiting. Does not disclose whether user exists.
    Returns: (success: bool, message: str, retry_after: int)
    """
    allowed, retry_after = otp_send_limiter.is_allowed(
        phone, OTP_SEND_MAX_REQUESTS, OTP_SEND_WINDOW_SECONDS
    )
    if not allowed:
        return (
            False,
            f"Too many OTP requests. Please try again in {retry_after} seconds.",
            retry_after,
        )

    client = twilio_client or get_twilio_client()
    try:
        sent = client.send_verification(phone)
        if sent:
            return True, "Verification code sent if phone number is eligible.", 0
        else:
            return False, "Failed to dispatch verification code. Please check configuration.", 0
    except Exception as exc:
        logger.error("Failed to send OTP to %s: %s", phone[:6] + "****", exc)
        return False, "Unable to send verification code at this time. Please try again later.", 0


def verify_otp_for_phone(
    phone: str,
    code: str,
    db_path: Optional[Path] = None,
    twilio_client=None,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Verifies the user-submitted code against Twilio Verify.
    Returns: (is_valid: bool, error_detail: Optional[str], farmer_dict: Optional[dict], reg_token: Optional[str])
    """
    allowed, retry_after = otp_verify_limiter.is_allowed(
        phone, OTP_VERIFY_MAX_REQUESTS, OTP_VERIFY_WINDOW_SECONDS
    )
    if not allowed:
        return (
            False,
            f"Too many failed verification attempts. Please wait {retry_after} seconds before trying again.",
            None,
            None,
        )

    client = twilio_client or get_twilio_client()
    verified = client.check_verification(phone, code)

    if not verified:
        # Increment failed attempts on farmer if account exists
        _record_failed_attempt(phone, db_path=db_path)
        return False, "Invalid or expired verification code.", None, None

    # Verification successful -> reset rate limiter
    otp_verify_limiter.reset(phone)

    # Check database for existing farmer
    farmer = get_farmer_by_phone(phone, db_path=db_path)
    if farmer is not None:
        # Existing farmer: record login & reset failed count
        _record_successful_login(farmer["id"], db_path=db_path)
        # Fetch fresh record
        farmer = get_farmer_by_id(farmer["id"], db_path=db_path)
        return True, None, farmer, None
    else:
        # New farmer: issue short-lived single-purpose registration token
        reg_token = create_registration_token(phone)
        return True, None, None, reg_token


def register_farmer(
    registration_token: str,
    name: str,
    preferred_language: str = "en",
    state: Optional[str] = None,
    district: Optional[str] = None,
    village: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Creates a new farmer profile using a verified registration token.
    Returns: (success: bool, error_message: Optional[str], new_farmer: Optional[dict])
    """
    try:
        payload = decode_token(registration_token)
    except jwt.ExpiredSignatureError:
        return False, "Registration token has expired. Please verify your phone again.", None
    except jwt.PyJWTError:
        return False, "Invalid registration token.", None

    if payload.get("type") != "registration_token":
        return False, "Supplied token is not valid for registration.", None

    phone = payload.get("sub")
    if not phone:
        return False, "Invalid registration payload.", None

    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # Double check if farmer with this phone already exists
        cursor.execute("SELECT id FROM farmers WHERE phone = ? LIMIT 1;", (phone,))
        existing = cursor.fetchone()
        if existing:
            return False, "A farmer with this phone number is already registered.", None

        now = datetime.now(timezone.utc).isoformat()
        farmer_uuid = str(uuid.uuid4())

        cursor.execute(
            """
            INSERT INTO farmers (
                uuid, name, phone, preferred_language,
                state, district, village, created_at, updated_at,
                is_active, last_login_at, token_version, failed_login_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 1, 0);
            """,
            (
                farmer_uuid,
                name.strip(),
                phone,
                preferred_language.strip() if preferred_language else "en",
                state.strip() if state else None,
                district.strip() if district else None,
                village.strip() if village else None,
                now,
                now,
                now,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

    new_farmer = get_farmer_by_id(new_id, db_path=resolved_path)
    return True, None, new_farmer


def get_farmer_by_phone(phone: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Looks up a farmer record by normalized phone number."""
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, uuid, name, phone, preferred_language, state, district, village,
                   created_at, updated_at, is_active, last_login_at, token_version,
                   failed_login_count, locked_until, deactivated_at
            FROM farmers WHERE phone = ? LIMIT 1;
            """,
            (phone,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_farmer_by_id(farmer_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Looks up a farmer record by internal integer ID."""
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, uuid, name, phone, preferred_language, state, district, village,
                   created_at, updated_at, is_active, last_login_at, token_version,
                   failed_login_count, locked_until, deactivated_at
            FROM farmers WHERE id = ? LIMIT 1;
            """,
            (farmer_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def invalidate_farmer_sessions(farmer_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Increments token_version for the given farmer, revoking all existing session tokens.
    """
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE farmers
            SET token_version = token_version + 1,
                updated_at = ?
            WHERE id = ?;
            """,
            (datetime.now(timezone.utc).isoformat(), farmer_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_farmer_dashboard_summary(farmer_id: int, db_path: Optional[Path] = None) -> AuthMeResponse:
    """
    Constructs the authenticated /auth/me payload containing farmer profile,
    their registered fields, and active sensor count.
    Never exposes fields or sensors belonging to another farmer.
    """
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # 1. Fetch Farmer
        cursor.execute(
            """
            SELECT id, uuid, name, phone, preferred_language, state, district, village,
                   created_at, last_login_at, is_active
            FROM farmers WHERE id = ? LIMIT 1;
            """,
            (farmer_id,),
        )
        farmer_row = cursor.fetchone()
        if not farmer_row:
            raise ValueError(f"Farmer {farmer_id} not found")

        farmer_profile = FarmerProfile(
            uuid=farmer_row["uuid"],
            name=farmer_row["name"],
            phone=farmer_row["phone"],
            preferred_language=farmer_row["preferred_language"],
            state=farmer_row["state"],
            district=farmer_row["district"],
            village=farmer_row["village"],
            created_at=farmer_row["created_at"],
            last_login_at=farmer_row["last_login_at"],
            is_active=bool(farmer_row["is_active"]),
        )

        # 2. Fetch Farmer's Fields and Sensor Counts
        cursor.execute(
            """
            SELECT f.id, f.uuid, f.name, f.crop_type, f.soil_type, f.area_acres,
                   COUNT(s.id) as sensor_count
            FROM fields f
            LEFT JOIN sensors s ON s.field_id = f.id
            WHERE f.farmer_id = ? AND f.is_active = 1
            GROUP BY f.id
            ORDER BY f.id ASC;
            """,
            (farmer_id,),
        )
        field_rows = cursor.fetchall()
        fields_list: List[FieldSummary] = []
        total_active_sensors = 0

        for r in field_rows:
            cnt = r["sensor_count"] or 0
            total_active_sensors += cnt
            fields_list.append(
                FieldSummary(
                    uuid=r["uuid"],
                    name=r["name"],
                    crop_type=r["crop_type"],
                    soil_type=r["soil_type"],
                    area_acres=r["area_acres"],
                    sensor_count=cnt,
                )
            )

        return AuthMeResponse(
            farmer=farmer_profile,
            fields=fields_list,
            active_sensor_count=total_active_sensors,
        )


def _record_failed_attempt(phone: str, db_path: Optional[Path] = None) -> None:
    """Increments failed_login_count on the farmer row if found."""
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE farmers
            SET failed_login_count = failed_login_count + 1,
                updated_at = ?
            WHERE phone = ?;
            """,
            (datetime.now(timezone.utc).isoformat(), phone),
        )
        conn.commit()


def _record_successful_login(farmer_id: int, db_path: Optional[Path] = None) -> None:
    """Updates last_login_at and resets failed_login_count."""
    resolved_path = db_path or get_db_path()
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE farmers
            SET last_login_at = ?,
                failed_login_count = 0,
                updated_at = ?
            WHERE id = ?;
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                farmer_id,
            ),
        )
        conn.commit()
