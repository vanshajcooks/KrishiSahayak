"""
Backend Authentication Tests (SIH 26180 — Phase 3B)
Comprehensive unit and integration test suite for KhetSaathi Phone OTP Authentication.
Fully mocks Twilio Verify API to ensure reliable, zero-cost, hermetic testing.
"""

import os
import sys
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db_path, get_connection
from auth.schemas import normalize_phone_number
from auth.security import (
    create_access_token,
    create_registration_token,
    decode_token,
    otp_send_limiter,
    otp_verify_limiter,
    AUTH_COOKIE_NAME,
)
from auth.service import (
    send_otp_for_phone,
    verify_otp_for_phone,
    register_farmer,
    invalidate_farmer_sessions,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """
    Ensures complete test isolation.
    Every test runs against a brand new temporary SQLite database.
    Rate limiters are reset between tests.
    """
    test_db_file = tmp_path / "test_auth_smart_farming.db"
    init_db(test_db_file)
    app.dependency_overrides[get_db_path] = lambda: test_db_file

    # Reset in-memory rate limiters
    otp_send_limiter._history.clear()
    otp_verify_limiter._history.clear()

    yield test_db_file

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provides FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_twilio():
    """Provides a mock TwilioVerifyClient."""
    mock = MagicMock()
    mock.is_configured = True
    mock.send_verification.return_value = True
    mock.check_verification.return_value = True
    return mock


# ============================================================================
# 1 & 2: Phone Normalization & Validation Tests
# ============================================================================

class TestPhoneNormalization:
    def test_valid_10_digit_indian_number(self):
        assert normalize_phone_number("9876543210") == "+919876543210"
        assert normalize_phone_number("8123456789") == "+918123456789"
        assert normalize_phone_number("7000000000") == "+917000000000"
        assert normalize_phone_number("6999999999") == "+916999999999"

    def test_valid_number_with_leading_zero(self):
        assert normalize_phone_number("09876543210") == "+919876543210"

    def test_valid_number_with_91_prefix(self):
        assert normalize_phone_number("919876543210") == "+919876543210"
        assert normalize_phone_number("+919876543210") == "+919876543210"

    def test_valid_number_with_formatting(self):
        assert normalize_phone_number("+91 98765-43210") == "+919876543210"
        assert normalize_phone_number("09876 543 210") == "+919876543210"
        assert normalize_phone_number("(98765) 43210") == "+919876543210"

    def test_invalid_phone_numbers_rejected(self):
        invalid_numbers = [
            "",
            "12345",
            "abcdefghij",
            "1234567890",      # Indian mobile numbers do not start with 1
            "5555555555",      # Does not start with 6-9
            "+1234",           # Too short E.164
            "+911234567890",   # +91 with invalid first digit
            "98765432101234",  # Too long
        ]
        for num in invalid_numbers:
            with pytest.raises(ValueError):
                normalize_phone_number(num)


# ============================================================================
# 3 & 4: OTP Send & Rate Limiting Tests
# ============================================================================

class TestOTPSend:
    def test_otp_send_success(self, client):
        with patch("backend.routers.auth.send_otp_for_phone") as mock_send:
            mock_send.return_value = (True, "Verification code sent.", 0)
            response = client.post("/api/v1/auth/otp/send", json={"phone": "9876543210"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"

    def test_otp_send_invalid_phone(self, client):
        response = client.post("/api/v1/auth/otp/send", json={"phone": "00000"})
        assert response.status_code == 422

    def test_otp_send_rate_limiting(self, client):
        with patch("backend.auth.service.get_twilio_client") as mock_get_client:
            mock_twilio = MagicMock()
            mock_twilio.send_verification.return_value = True
            mock_get_client.return_value = mock_twilio

            phone = "9876543210"
            # Limit is 3 requests per 10 mins
            for i in range(3):
                res = client.post("/api/v1/auth/otp/send", json={"phone": phone})
                assert res.status_code == 200, f"Request {i+1} failed"

            # 4th request must trigger rate limit HTTP 429
            res_blocked = client.post("/api/v1/auth/otp/send", json={"phone": phone})
            assert res_blocked.status_code == 429
            assert "Too many OTP requests" in res_blocked.json()["detail"]


# ============================================================================
# 5 & 6: OTP Verification & Invalid OTP Tests
# ============================================================================

class TestOTPVerify:
    def test_invalid_otp_rejected(self, client):
        with patch("backend.auth.service.get_twilio_client") as mock_get_client:
            mock_twilio = MagicMock()
            mock_twilio.check_verification.return_value = False
            mock_get_client.return_value = mock_twilio

            response = client.post(
                "/api/v1/auth/otp/verify",
                json={"phone": "9876543210", "code": "000000"},
            )
            assert response.status_code == 400
            assert "Invalid or expired verification code" in response.json()["detail"]

    def test_otp_verify_rate_limiting_after_repeated_failures(self, client):
        with patch("backend.auth.service.get_twilio_client") as mock_get_client:
            mock_twilio = MagicMock()
            mock_twilio.check_verification.return_value = False
            mock_get_client.return_value = mock_twilio

            phone = "9777777777"
            # Max 5 attempts
            for _ in range(5):
                res = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": "111111"})
                assert res.status_code == 400

            # 6th attempt triggers 400 with rate limit detail
            res_blocked = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": "111111"})
            assert res_blocked.status_code == 400
            assert "Too many failed verification attempts" in res_blocked.json()["detail"]


# ============================================================================
# 7: Existing Farmer Login Flow
# ============================================================================

class TestExistingFarmerLogin:
    def test_existing_farmer_login_sets_cookie_and_updates_last_login(self, client, setup_test_db):
        db_path = setup_test_db
        # Seed an existing active farmer
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO farmers (
                    uuid, name, phone, preferred_language, state, district, village,
                    created_at, updated_at, is_active, token_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1);
                """,
                (
                    "existing-uuid-1234",
                    "Ramesh Patel",
                    "+919876543210",
                    "hi",
                    "Gujarat",
                    "Anand",
                    "Vasna",
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        with patch("backend.auth.service.get_twilio_client") as mock_get_client:
            mock_twilio = MagicMock()
            mock_twilio.check_verification.return_value = True
            mock_get_client.return_value = mock_twilio

            response = client.post(
                "/api/v1/auth/otp/verify",
                json={"phone": "9876543210", "code": "123456"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_registered"] is True
            assert data["farmer"]["name"] == "Ramesh Patel"
            assert data["farmer"]["phone"] == "+919876543210"

            # Check that HttpOnly cookie was set
            cookie = response.cookies.get(AUTH_COOKIE_NAME)
            assert cookie is not None

            # Verify last_login_at updated in database
            with get_connection(db_path) as conn:
                row = conn.execute("SELECT last_login_at, failed_login_count FROM farmers WHERE phone = '+919876543210';").fetchone()
                assert row["last_login_at"] is not None
                assert row["failed_login_count"] == 0


# ============================================================================
# 8, 9, 10: New Farmer Registration Flow & Registration Token Validation
# ============================================================================

class TestNewFarmerRegistration:
    def test_new_farmer_verification_returns_registration_token(self, client):
        with patch("backend.auth.service.get_twilio_client") as mock_get_client:
            mock_twilio = MagicMock()
            mock_twilio.check_verification.return_value = True
            mock_get_client.return_value = mock_twilio

            response = client.post(
                "/api/v1/auth/otp/verify",
                json={"phone": "9998887776", "code": "654321"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_registered"] is False
            assert data["registration_token"] is not None
            assert data["farmer"] is None

    def test_registration_with_valid_token_creates_farmer_and_session(self, client, setup_test_db):
        reg_token = create_registration_token("+919998887776")

        response = client.post(
            "/api/v1/auth/register",
            json={
                "registration_token": reg_token,
                "name": "Kiran Rao",
                "preferred_language": "en",
                "state": "Karnataka",
                "district": "Mandya",
                "village": "Shivalli",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_registered"] is True
        assert data["farmer"]["name"] == "Kiran Rao"
        assert data["farmer"]["phone"] == "+919998887776"
        assert data["farmer"]["state"] == "Karnataka"

        # Cookie must be set
        cookie = response.cookies.get(AUTH_COOKIE_NAME)
        assert cookie is not None

        # Verify farmer exists in SQLite
        with get_connection(setup_test_db) as conn:
            row = conn.execute("SELECT name, phone FROM farmers WHERE phone = '+919998887776';").fetchone()
            assert row is not None
            assert row["name"] == "Kiran Rao"

    def test_expired_registration_token_rejected(self, client):
        # Create expired token
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "+919998887776",
            "type": "registration_token",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        }
        import jwt
        from auth.security import AUTH_SECRET_KEY, JWT_ALGORITHM
        expired_token = jwt.encode(payload, AUTH_SECRET_KEY, algorithm=JWT_ALGORITHM)

        response = client.post(
            "/api/v1/auth/register",
            json={"registration_token": expired_token, "name": "Kiran Rao"},
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_access_token_cannot_be_used_as_registration_token(self, client):
        access_token = create_access_token(
            farmer_id=1,
            farmer_uuid="uuid-1",
            phone="+919998887776",
            token_version=1,
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"registration_token": access_token, "name": "Kiran Rao"},
        )
        assert response.status_code == 400
        assert "not valid for registration" in response.json()["detail"].lower()


# ============================================================================
# 11, 12, 13, 14, 15: Authenticated /me, Inactive Rejection, Expiry, Logout, Farmer Isolation
# ============================================================================

class TestAuthenticationGuardsAndMe:
    def test_unauthenticated_me_rejected(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_authenticated_me_returns_farmer_and_fields(self, client, setup_test_db):
        db_path = setup_test_db
        # Insert Farmer & Field
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO farmers (uuid, name, phone, preferred_language, created_at, updated_at, is_active, token_version)
                VALUES ('farmer-uuid-a', 'Farmer A', '+919111111111', 'en', ?, ?, 1, 1);
                """,
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )
            farmer_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO fields (uuid, farmer_id, name, crop_type, area_acres, created_at, updated_at, is_active)
                VALUES ('field-uuid-a', ?, 'North Plot', 'Tomato', 2.5, ?, ?, 1);
                """,
                (farmer_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )
            field_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO sensors (sensor_id, field_id, created_at, updated_at)
                VALUES ('sensor_01', ?, ?, ?);
                """,
                (field_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

        token = create_access_token(
            farmer_id=farmer_id,
            farmer_uuid="farmer-uuid-a",
            phone="+919111111111",
            token_version=1,
        )

        # Send via Cookie
        client.cookies.set(AUTH_COOKIE_NAME, token)
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["farmer"]["name"] == "Farmer A"
        assert len(data["fields"]) == 1
        assert data["fields"][0]["name"] == "North Plot"
        assert data["fields"][0]["sensor_count"] == 1
        assert data["active_sensor_count"] == 1

        # Also works via Authorization: Bearer
        client.cookies.clear()
        res_bearer = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_bearer.status_code == 200
        assert res_bearer.json()["farmer"]["name"] == "Farmer A"

    def test_inactive_farmer_rejected_with_403(self, client, setup_test_db):
        with get_connection(setup_test_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO farmers (uuid, name, phone, preferred_language, created_at, updated_at, is_active, token_version)
                VALUES ('deactivated-uuid', 'Deactivated Farmer', '+919222222222', 'en', ?, ?, 0, 1);
                """,
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )
            farmer_id = cursor.lastrowid
            conn.commit()

        token = create_access_token(
            farmer_id=farmer_id,
            farmer_uuid="deactivated-uuid",
            phone="+919222222222",
            token_version=1,
        )
        client.cookies.set(AUTH_COOKIE_NAME, token)
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 403
        assert "inactive or suspended" in res.json()["detail"].lower()

    def test_expired_token_rejected_with_401(self, client):
        token = create_access_token(
            farmer_id=1,
            farmer_uuid="uuid-1",
            phone="+919111111111",
            token_version=1,
            expires_delta=timedelta(seconds=-10),
        )
        client.cookies.set(AUTH_COOKIE_NAME, token)
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401
        assert "expired" in res.json()["detail"].lower()

    def test_logout_invalidates_token_version(self, client, setup_test_db):
        db_path = setup_test_db
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO farmers (uuid, name, phone, preferred_language, created_at, updated_at, is_active, token_version)
                VALUES ('logout-uuid', 'Logout Farmer', '+919333333333', 'en', ?, ?, 1, 1);
                """,
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )
            farmer_id = cursor.lastrowid
            conn.commit()

        token = create_access_token(
            farmer_id=farmer_id,
            farmer_uuid="logout-uuid",
            phone="+919333333333",
            token_version=1,
        )
        client.cookies.set(AUTH_COOKIE_NAME, token)

        # Call logout
        res_logout = client.post("/api/v1/auth/logout")
        assert res_logout.status_code == 200

        # Previous token with token_version=1 must now be rejected
        res_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_after.status_code == 401
        assert "revoked" in res_after.json()["detail"].lower()

    def test_farmer_a_cannot_access_farmer_b_fields(self, client, setup_test_db):
        db_path = setup_test_db
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            # Farmer A
            cursor.execute(
                "INSERT INTO farmers (uuid, name, phone, preferred_language, created_at, updated_at, is_active, token_version) VALUES ('uuid-a', 'Farmer A', '+919111111111', 'en', 'now', 'now', 1, 1);"
            )
            farmer_a_id = cursor.lastrowid
            # Farmer B
            cursor.execute(
                "INSERT INTO farmers (uuid, name, phone, preferred_language, created_at, updated_at, is_active, token_version) VALUES ('uuid-b', 'Farmer B', '+919222222222', 'en', 'now', 'now', 1, 1);"
            )
            farmer_b_id = cursor.lastrowid

            # Field for Farmer B only
            cursor.execute(
                "INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at, is_active) VALUES ('field-b', ?, 'Farmer B Orchard', 'Apple', 'now', 'now', 1);",
                (farmer_b_id,),
            )
            conn.commit()

        token_a = create_access_token(
            farmer_id=farmer_a_id,
            farmer_uuid="uuid-a",
            phone="+919111111111",
            token_version=1,
        )
        client.cookies.set(AUTH_COOKIE_NAME, token_a)
        res_a = client.get("/api/v1/auth/me")
        assert res_a.status_code == 200
        # Farmer A has 0 fields
        assert len(res_a.json()["fields"]) == 0


# ============================================================================
# 16, 17, 18, 19: CORS & Existing Subsystem Regression Tests
# ============================================================================

class TestCorsAndSubsystemsRegression:
    def test_cors_does_not_use_wildcard_origins_with_credentials(self):
        # Inspect main app middleware
        cors_middlewares = [m for m in app.user_middleware if "CORSMiddleware" in str(m)]
        assert len(cors_middlewares) > 0
        kwargs = cors_middlewares[0].kwargs
        assert kwargs["allow_credentials"] is True
        # Explicit origins must NOT contain '*'
        assert "*" not in kwargs["allow_origins"]

    def test_esp32_ingestion_remains_functional(self, client):
        payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 32.5,
            "temperature": 27.2,
            "humidity": 65.0,
            "rain_level": 0.0,
            "battery_voltage": 3.95,
        }
        res = client.post("/api/v1/sensors/ingest", json=payload)
        assert res.status_code == 201
        assert res.json()["status"] == "success"

    def test_decision_recommendations_endpoint_still_works(self, client):
        # Ingest reading first
        client.post(
            "/api/v1/sensors/ingest",
            json={
                "sensor_id": "esp32_field_01",
                "soil_moisture": 18.0,
                "temperature": 36.5,
                "humidity": 45.0,
            },
        )
        res = client.get("/api/v1/decision/recommendations?sensor_id=esp32_field_01")
        assert res.status_code == 200
        data = res.json()
        assert "soil_moisture_status" in data
        assert "irrigation_action" in data
        assert "primary_action" in data
        assert data["soil_moisture_status"] == "LOW"

    def test_health_endpoint_remains_public(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
