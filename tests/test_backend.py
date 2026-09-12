"""
Backend Scaffolding & Persistence Tests — Smart Farming Assistant (SIH 26180)
Tests FastAPI health check, sensor JSON validation, and SQLite persistence layer.
"""

import os
import sys
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db_path, get_recent_readings
from schemas import SensorReading


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """
    Ensures complete test isolation.
    Every test runs against a brand new temporary SQLite database.
    Production database (backend/data/smart_farming.db) is NEVER touched by tests.
    """
    test_db_file = tmp_path / "test_smart_farming.db"
    init_db(test_db_file)
    app.dependency_overrides[get_db_path] = lambda: test_db_file
    yield test_db_file
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provides FastAPI test client fixture."""
    return TestClient(app)


# ============================================================================
# Existing Tests (Preserved Exactly as Verified)
# ============================================================================

class TestHealthCheck:
    """Tests service availability endpoint."""

    def test_health_check_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "smart-farming-backend"
        assert data["version"] == "0.1.0"


class TestSensorValidationAndIngest:
    """Tests telemetry JSON schema validation and state management."""

    def test_latest_before_any_ingest_returns_404(self, client):
        response = client.get("/api/v1/sensors/latest")
        assert response.status_code == 404
        assert "No sensor readings available" in response.json()["detail"]

    def test_valid_sensor_telemetry_ingest_succeeds(self, client):
        payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 38.5,
            "temperature": 27.2,
            "humidity": 65.0,
            "battery_voltage": 4.05,
        }
        response = client.post("/api/v1/sensors/ingest", json=payload)
        assert response.status_code == 201

        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["sensor_id"] == "esp32_field_01"
        assert body["data"]["soil_moisture"] == 38.5
        assert body["data"]["temperature"] == 27.2
        assert body["data"]["humidity"] == 65.0
        assert body["data"]["battery_voltage"] == 4.05
        assert "timestamp" in body["data"]

    def test_get_latest_returns_most_recent_reading(self, client):
        payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 45.0,
            "temperature": 26.5,
            "humidity": 70.0,
            "battery_voltage": 3.92,
        }
        client.post("/api/v1/sensors/ingest", json=payload)

        response = client.get("/api/v1/sensors/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "esp32_field_01"
        assert data["soil_moisture"] == 45.0
        assert data["temperature"] == 26.5

    def test_rejects_soil_moisture_greater_than_100(self, client):
        invalid_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 105.0,  # Invalid: > 100.0%
            "temperature": 25.0,
            "humidity": 60.0,
        }
        response = client.post("/api/v1/sensors/ingest", json=invalid_payload)
        assert response.status_code == 422

    def test_rejects_negative_soil_moisture(self, client):
        invalid_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": -5.0,  # Invalid: < 0.0%
            "temperature": 25.0,
            "humidity": 60.0,
        }
        response = client.post("/api/v1/sensors/ingest", json=invalid_payload)
        assert response.status_code == 422

    def test_rejects_out_of_range_temperature(self, client):
        invalid_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 50.0,
            "temperature": 95.0,  # Invalid: > 65.0 C
            "humidity": 60.0,
        }
        response = client.post("/api/v1/sensors/ingest", json=invalid_payload)
        assert response.status_code == 422

    def test_rejects_missing_required_fields(self, client):
        incomplete_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 50.0,
            # Missing temperature and humidity
        }
        response = client.post("/api/v1/sensors/ingest", json=incomplete_payload)
        assert response.status_code == 422


# ============================================================================
# Milestone 4A: SQLite Persistence Tests
# ============================================================================

class TestSQLitePersistence:
    """Tests SQLite persistence, schema verification, and database query logic."""

    def test_db_initialization_creates_table_and_indexes(self, setup_test_db):
        """Verifies table schema and indexes exist in the SQLite database."""
        conn = sqlite3.connect(str(setup_test_db))
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_telemetry';")
        assert cursor.fetchone() is not None

        # Check table columns
        cursor.execute("PRAGMA table_info(sensor_telemetry);")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in columns
        assert "sensor_id" in columns
        assert "temperature" in columns
        assert "humidity" in columns
        assert "soil_moisture" in columns
        assert "rain_level" in columns
        assert "battery_voltage" in columns
        assert "timestamp" in columns

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sensor_telemetry';")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_telemetry_timestamp" in indexes
        assert "idx_telemetry_sensor_timestamp" in indexes
        conn.close()

    def test_ingest_persists_reading_to_sqlite(self, client, setup_test_db):
        """Verifies that an ingested payload actually writes a row to SQLite with matching values."""
        payload = {
            "sensor_id": "esp32_zone_1",
            "soil_moisture": 48.2,
            "temperature": 29.1,
            "humidity": 62.4,
            "battery_voltage": 3.98,
            "rain_level": 5.0,
        }
        resp = client.post("/api/v1/sensors/ingest", json=payload)
        assert resp.status_code == 201

        # Direct database inspection
        conn = sqlite3.connect(str(setup_test_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_telemetry WHERE sensor_id = 'esp32_zone_1';")
        row = cursor.fetchone()
        assert row is not None
        assert row["sensor_id"] == "esp32_zone_1"
        assert row["soil_moisture"] == 48.2
        assert row["temperature"] == 29.1
        assert row["humidity"] == 62.4
        assert row["battery_voltage"] == 3.98
        assert row["rain_level"] == 5.0
        assert row["timestamp"] is not None
        conn.close()

    def test_latest_retrieves_from_sqlite_across_multiple_readings(self, client):
        """Verifies that sending multiple readings returns the newest reading from SQLite."""
        reading_1 = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 30.0,
            "temperature": 25.0,
            "humidity": 50.0,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        }
        reading_2 = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 55.0,
            "temperature": 32.0,
            "humidity": 68.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        client.post("/api/v1/sensors/ingest", json=reading_1)
        client.post("/api/v1/sensors/ingest", json=reading_2)

        resp = client.get("/api/v1/sensors/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["soil_moisture"] == 55.0
        assert data["temperature"] == 32.0
        assert data["humidity"] == 68.0

    def test_filter_latest_by_sensor_id(self, client):
        """Verifies that the latest endpoint correctly filters by sensor_id."""
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "sensor_A", "soil_moisture": 35.0, "temperature": 24.0, "humidity": 55.0},
        )
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "sensor_B", "soil_moisture": 75.0, "temperature": 30.0, "humidity": 80.0},
        )

        resp_a = client.get("/api/v1/sensors/latest?sensor_id=sensor_A")
        assert resp_a.status_code == 200
        assert resp_a.json()["sensor_id"] == "sensor_A"
        assert resp_a.json()["soil_moisture"] == 35.0

        resp_b = client.get("/api/v1/sensors/latest?sensor_id=sensor_B")
        assert resp_b.status_code == 200
        assert resp_b.json()["sensor_id"] == "sensor_B"
        assert resp_b.json()["soil_moisture"] == 75.0

    def test_filter_latest_by_nonexistent_sensor_id_returns_404(self, client):
        """Verifies that querying a non-existent sensor_id returns HTTP 404."""
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "sensor_A", "soil_moisture": 40.0, "temperature": 25.0, "humidity": 60.0},
        )
        resp = client.get("/api/v1/sensors/latest?sensor_id=sensor_NONEXISTENT")
        assert resp.status_code == 404
        assert "No sensor reading found for sensor_id 'sensor_NONEXISTENT'" in resp.json()["detail"]

    def test_invalid_reading_not_persisted_in_db(self, client, setup_test_db):
        """Verifies that payload rejected with HTTP 422 does not write any row to SQLite."""
        invalid_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 150.0,  # Invalid
            "temperature": 25.0,
            "humidity": 60.0,
        }
        resp = client.post("/api/v1/sensors/ingest", json=invalid_payload)
        assert resp.status_code == 422

        conn = sqlite3.connect(str(setup_test_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sensor_telemetry;")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 0

    def test_database_records_ordered_by_timestamp(self, client, setup_test_db):
        """Verifies that get_recent_readings returns records in chronological order (oldest to newest)."""
        base_time = datetime.now(timezone.utc)
        for i in range(3):
            t = base_time + timedelta(minutes=i)
            client.post(
                "/api/v1/sensors/ingest",
                json={
                    "sensor_id": "esp32_field_01",
                    "soil_moisture": 40.0 + i,
                    "temperature": 25.0,
                    "humidity": 60.0,
                    "timestamp": t.isoformat(),
                },
            )

        recent = get_recent_readings(limit=10, db_path=setup_test_db)
        assert len(recent) == 3
        # Chronological order: first item should have lowest moisture (oldest)
        assert recent[0]["soil_moisture"] == 40.0
        assert recent[1]["soil_moisture"] == 41.0
        assert recent[2]["soil_moisture"] == 42.0

    def test_ingest_with_optional_rain_level(self, client, setup_test_db):
        """Verifies that rain_level is stored and returned when provided."""
        payload = {
            "sensor_id": "esp32_rain_test",
            "soil_moisture": 60.0,
            "temperature": 22.0,
            "humidity": 85.0,
            "rain_level": 78.5,
        }
        resp = client.post("/api/v1/sensors/ingest", json=payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["rain_level"] == 78.5

        latest_resp = client.get("/api/v1/sensors/latest?sensor_id=esp32_rain_test")
        assert latest_resp.status_code == 200
        assert latest_resp.json()["rain_level"] == 78.5

    def test_ingest_without_battery_voltage_persists_null(self, client, setup_test_db):
        """Verifies that omitted battery_voltage is stored as NULL in SQLite."""
        payload = {
            "sensor_id": "esp32_no_battery",
            "soil_moisture": 45.0,
            "temperature": 26.0,
            "humidity": 55.0,
        }
        resp = client.post("/api/v1/sensors/ingest", json=payload)
        assert resp.status_code == 201

        conn = sqlite3.connect(str(setup_test_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT battery_voltage FROM sensor_telemetry WHERE sensor_id = 'esp32_no_battery';")
        row = cursor.fetchone()
        assert row["battery_voltage"] is None
        conn.close()


# ============================================================================
# Milestone 4B: Decision Engine API Integration Tests
# ============================================================================

class TestDecisionEndpoint:
    """Integration tests for GET /api/v1/decision/recommendations."""

    def test_decision_endpoint_empty_db_returns_404(self, client):
        """Verifies that requesting decisions with an empty database returns 404."""
        response = client.get("/api/v1/decision/recommendations")
        assert response.status_code == 404
        assert "No sensor readings available" in response.json()["detail"]

    def test_decision_endpoint_evaluates_latest_ingested_reading(self, client):
        """Verifies that decision recommendations evaluate the latest stored sensor reading."""
        payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 22.0,
            "temperature": 28.0,
            "humidity": 82.0,
            "rain_level": 0.0,
        }
        client.post("/api/v1/sensors/ingest", json=payload)

        response = client.get("/api/v1/decision/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_id"] == "esp32_field_01"
        assert data["soil_moisture_status"] == "LOW"
        assert data["irrigation_action"] == "IRRIGATE_SOON"
        assert data["water_stress_level"] == "HIGH"
        assert data["heat_stress_level"] == "LOW"
        assert data["disease_risk_level"] == "HIGH"
        assert data["action_category"] == "ACTION_REQUIRED"
        assert any("favorable conditions for fungal disease" in r for r in data["reasons"])

    def test_decision_endpoint_heat_stress_integration(self, client):
        """Verifies that high ambient temperature triggers HIGH heat stress in API response."""
        payload = {
            "sensor_id": "esp32_field_heat",
            "soil_moisture": 50.0,
            "temperature": 36.5,
            "humidity": 45.0,
            "rain_level": 0.0,
        }
        client.post("/api/v1/sensors/ingest", json=payload)

        response = client.get("/api/v1/decision/recommendations?sensor_id=esp32_field_heat")
        assert response.status_code == 200
        data = response.json()
        assert data["heat_stress_level"] == "HIGH"
        assert any("above the 35.0°C threshold" in r for r in data["reasons"])

    def test_decision_endpoint_rain_override_integration(self, client):
        """Verifies rain detection (>=60%) overrides dry soil to delay irrigation in API response."""
        payload = {
            "sensor_id": "esp32_field_rain",
            "soil_moisture": 18.0,
            "temperature": 26.0,
            "humidity": 85.0,
            "rain_level": 75.0,
        }
        client.post("/api/v1/sensors/ingest", json=payload)

        response = client.get("/api/v1/decision/recommendations?sensor_id=esp32_field_rain")
        assert response.status_code == 200
        data = response.json()
        assert data["irrigation_action"] == "DELAY_IRRIGATION_RAIN_DETECTED"
        assert "Rain Detected — Delay Irrigation" in data["action_title"]

    def test_decision_endpoint_filters_by_sensor_id(self, client):
        """Verifies that the decision endpoint properly filters by sensor_id."""
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "node_dry", "soil_moisture": 20.0, "temperature": 25.0, "humidity": 50.0},
        )
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "node_optimal", "soil_moisture": 50.0, "temperature": 25.0, "humidity": 50.0},
        )

        resp_dry = client.get("/api/v1/decision/recommendations?sensor_id=node_dry")
        assert resp_dry.status_code == 200
        assert resp_dry.json()["soil_moisture_status"] == "LOW"
        assert resp_dry.json()["irrigation_action"] == "IRRIGATE_SOON"

        resp_opt = client.get("/api/v1/decision/recommendations?sensor_id=node_optimal")
        assert resp_opt.status_code == 200
        assert resp_opt.json()["soil_moisture_status"] == "OPTIMAL"
        assert resp_opt.json()["irrigation_action"] == "NO_IRRIGATION_NEEDED"

    def test_decision_endpoint_nonexistent_sensor_id_returns_404(self, client):
        """Verifies that requesting decision for a nonexistent sensor_id returns 404."""
        client.post(
            "/api/v1/sensors/ingest",
            json={"sensor_id": "node_existing", "soil_moisture": 45.0, "temperature": 25.0, "humidity": 50.0},
        )
        response = client.get("/api/v1/decision/recommendations?sensor_id=node_absent")
        assert response.status_code == 404
        assert "No sensor reading found for sensor_id 'node_absent'" in response.json()["detail"]


class TestPhase2DatabaseFoundation:
    """
    Validates Phase 2 relational database schema:
    Farmer -> Fields -> Sensors -> Telemetry
    Farmer -> Alerts -> Notifications
    """

    def test_phase2_tables_and_indexes_exist(self, setup_test_db):
        """Verifies all Phase 2 tables and required indexes exist upon init_db."""
        conn = sqlite3.connect(str(setup_test_db))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {"farmers", "fields", "sensors", "sensor_telemetry", "alerts", "notifications"}
        assert expected_tables.issubset(tables)

        cursor.execute("PRAGMA table_info(sensor_telemetry);")
        telemetry_cols = {row[1] for row in cursor.fetchall()}
        assert "field_id" in telemetry_cols

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = {row[0] for row in cursor.fetchall()}
        expected_indexes = {
            "idx_farmers_phone",
            "idx_fields_farmer_id",
            "idx_fields_uuid",
            "idx_sensors_field_id",
            "idx_telemetry_timestamp",
            "idx_telemetry_sensor_timestamp",
            "idx_telemetry_field_timestamp",
            "idx_alerts_farmer_status_created",
            "idx_alerts_field_status_created",
            "idx_notifications_alert_id",
            "idx_notifications_farmer_status",
        }
        assert expected_indexes.issubset(indexes)
        conn.close()

    def test_farmer_creation(self, setup_test_db):
        """Verifies creating a farmer record with valid fields."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO farmers (uuid, name, phone, preferred_language, state, district, village, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'));
            """,
            ("f-uuid-1", "Harpal Singh", "+919876543210", "pa", "Punjab", "Ludhiana", "Jagraon"),
        )
        conn.commit()
        farmer_id = cursor.lastrowid

        cursor.execute("SELECT * FROM farmers WHERE id = ?;", (farmer_id,))
        farmer = cursor.fetchone()
        assert farmer is not None
        assert farmer["name"] == "Harpal Singh"
        assert farmer["phone"] == "+919876543210"
        assert farmer["preferred_language"] == "pa"
        assert farmer["is_active"] == 1
        conn.close()

    def test_field_farmer_relationship(self, setup_test_db):
        """Verifies creating fields linked to a farmer and cascading deletion."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create farmer
        cursor.execute(
            """
            INSERT INTO farmers (uuid, name, phone, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'));
            """,
            ("f-uuid-2", "Sunita Devi", "+919876543211"),
        )
        farmer_id = cursor.lastrowid

        # Create field
        cursor.execute(
            """
            INSERT INTO fields (uuid, farmer_id, name, crop_type, sowing_date, soil_type, area_acres, latitude, longitude, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'));
            """,
            ("fld-uuid-1", farmer_id, "South Acre", "Wheat", "2026-10-01", "Loam", 4.0, 30.9, 75.85),
        )
        field_id = cursor.lastrowid

        cursor.execute("SELECT * FROM fields WHERE id = ?;", (field_id,))
        field = cursor.fetchone()
        assert field is not None
        assert field["farmer_id"] == farmer_id
        assert field["name"] == "South Acre"
        assert field["crop_type"] == "Wheat"

        # Cascade test: Deleting farmer deletes their fields
        cursor.execute("DELETE FROM farmers WHERE id = ?;", (farmer_id,))
        conn.commit()

        cursor.execute("SELECT * FROM fields WHERE id = ?;", (field_id,))
        assert cursor.fetchone() is None
        conn.close()

    def test_sensor_field_relationship(self, setup_test_db):
        """Verifies sensor registration and linking to a field."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Setup farmer & field
        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-3', 'A', '+919876543212', datetime('now'), datetime('now'));")
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at) VALUES ('fld-2', ?, 'East Field', 'Corn', datetime('now'), datetime('now'));", (farmer_id,))
        field_id = cursor.lastrowid

        # Register sensor
        cursor.execute(
            """
            INSERT INTO sensors (sensor_id, field_id, hardware_type, status, created_at, updated_at)
            VALUES (?, ?, 'ESP32_DHT22_CAPACITIVE', 'ACTIVE', datetime('now'), datetime('now'));
            """,
            ("esp32_east_01", field_id),
        )
        sensor_pk = cursor.lastrowid

        cursor.execute("SELECT * FROM sensors WHERE id = ?;", (sensor_pk,))
        sensor = cursor.fetchone()
        assert sensor is not None
        assert sensor["sensor_id"] == "esp32_east_01"
        assert sensor["field_id"] == field_id

        # Field deletion sets sensor.field_id to NULL (ON DELETE SET NULL)
        cursor.execute("DELETE FROM fields WHERE id = ?;", (field_id,))
        conn.commit()

        cursor.execute("SELECT * FROM sensors WHERE id = ?;", (sensor_pk,))
        sensor_after = cursor.fetchone()
        assert sensor_after is not None
        assert sensor_after["field_id"] is None
        conn.close()

    def test_telemetry_sensor_field_association_on_ingest(self, client, setup_test_db):
        """Verifies that when an ESP32 posts telemetry, backend auto-resolves sensor_id -> field_id."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # Provision farmer, field, sensor
        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-4', 'B', '+919876543213', datetime('now'), datetime('now'));")
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at) VALUES ('fld-3', ?, 'Tomato Zone', 'Tomato', datetime('now'), datetime('now'));", (farmer_id,))
        field_id = cursor.lastrowid
        cursor.execute("INSERT INTO sensors (sensor_id, field_id, created_at, updated_at) VALUES ('esp32_tomato_01', ?, datetime('now'), datetime('now'));", (field_id,))
        conn.commit()
        conn.close()

        # Ingest payload from ESP32 containing ONLY sensor_id
        payload = {
            "sensor_id": "esp32_tomato_01",
            "soil_moisture": 42.0,
            "temperature": 27.5,
            "humidity": 60.0,
        }
        res = client.post("/api/v1/sensors/ingest", json=payload)
        assert res.status_code == 201

        # Check telemetry row has field_id populated
        conn = sqlite3.connect(str(setup_test_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_telemetry WHERE sensor_id = 'esp32_tomato_01';")
        tel = cursor.fetchone()
        assert tel is not None
        assert tel["field_id"] == field_id

        # Check sensor's last_seen_at was updated
        cursor.execute("SELECT last_seen_at FROM sensors WHERE sensor_id = 'esp32_tomato_01';")
        sensor_row = cursor.fetchone()
        assert sensor_row["last_seen_at"] is not None
        conn.close()

    def test_historical_telemetry_preserved_when_field_deleted(self, setup_test_db):
        """Verifies that historical telemetry is NOT cascade-deleted when a field is deleted."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-5', 'C', '+919876543214', datetime('now'), datetime('now'));")
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at) VALUES ('fld-4', ?, 'Potato Field', 'Potato', datetime('now'), datetime('now'));", (farmer_id,))
        field_id = cursor.lastrowid

        # Insert telemetry referencing this field
        cursor.execute(
            """
            INSERT INTO sensor_telemetry (sensor_id, temperature, humidity, soil_moisture, timestamp, field_id)
            VALUES ('esp32_potato_01', 22.0, 70.0, 38.0, datetime('now'), ?);
            """,
            (field_id,),
        )
        tel_id = cursor.lastrowid
        conn.commit()

        # Delete the field
        cursor.execute("DELETE FROM fields WHERE id = ?;", (field_id,))
        conn.commit()

        # Telemetry record MUST still exist (historical preservation, field_id becomes NULL or stays intact without cascade)
        cursor.execute("SELECT * FROM sensor_telemetry WHERE id = ?;", (tel_id,))
        preserved_tel = cursor.fetchone()
        assert preserved_tel is not None
        assert preserved_tel["sensor_id"] == "esp32_potato_01"
        assert preserved_tel["field_id"] is None
        conn.close()

    def test_alert_farmer_field_relationship(self, setup_test_db):
        """Verifies creating alerts linked to farmer and field."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-6', 'D', '+919876543215', datetime('now'), datetime('now'));")
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at) VALUES ('fld-5', ?, 'Chilli Field', 'Chilli', datetime('now'), datetime('now'));", (farmer_id,))
        field_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO alerts (uuid, farmer_id, field_id, alert_type, severity, title, message, action_recommended, created_at)
            VALUES ('al-1', ?, ?, 'WATER_STRESS', 'HIGH', 'Severe Drought', 'Soil dry for 24h', 'Start drip irrigation', datetime('now'));
            """,
            (farmer_id, field_id),
        )
        alert_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM alerts WHERE id = ?;", (alert_id,))
        alert = cursor.fetchone()
        assert alert is not None
        assert alert["farmer_id"] == farmer_id
        assert alert["field_id"] == field_id
        assert alert["severity"] == "HIGH"
        assert alert["status"] == "ACTIVE"
        conn.close()

    def test_notification_alert_farmer_relationship(self, setup_test_db):
        """Verifies creating notifications linked to alert and farmer, with cascade delete on alert."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-7', 'E', '+919876543216', datetime('now'), datetime('now'));")
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO alerts (uuid, farmer_id, alert_type, severity, title, message, created_at) VALUES ('al-2', ?, 'HEAT_STRESS', 'MEDIUM', 'Heat Wave', '37C recorded', datetime('now'));", (farmer_id,))
        alert_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO notifications (alert_id, farmer_id, channel, status, recipient, sent_at)
            VALUES (?, ?, 'SMS', 'DELIVERED', '+919876543216', datetime('now'));
            """,
            (alert_id, farmer_id),
        )
        notif_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM notifications WHERE id = ?;", (notif_id,))
        notif = cursor.fetchone()
        assert notif is not None
        assert notif["alert_id"] == alert_id
        assert notif["farmer_id"] == farmer_id
        assert notif["channel"] == "SMS"
        assert notif["status"] == "DELIVERED"

        # Cascade test: Deleting alert cascades to notifications
        cursor.execute("DELETE FROM alerts WHERE id = ?;", (alert_id,))
        conn.commit()

        cursor.execute("SELECT * FROM notifications WHERE id = ?;", (notif_id,))
        assert cursor.fetchone() is None
        conn.close()

    def test_foreign_key_enforcement(self, setup_test_db):
        """Verifies that foreign key violations raise sqlite3.IntegrityError."""
        conn = sqlite3.connect(str(setup_test_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # Insert field with nonexistent farmer_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO fields (uuid, farmer_id, name, crop_type, created_at, updated_at)
                VALUES ('fld-err', 99999, 'Invalid', 'Crop', datetime('now'), datetime('now'));
                """
            )

        # Insert alert with nonexistent farmer_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO alerts (uuid, farmer_id, alert_type, severity, title, message, created_at)
                VALUES ('al-err', 99999, 'WATER_STRESS', 'LOW', 'Title', 'Msg', datetime('now'));
                """
            )
        conn.close()

    def test_duplicate_phone_rejected(self, setup_test_db):
        """Verifies UNIQUE constraint on farmers.phone."""
        conn = sqlite3.connect(str(setup_test_db))
        cursor = conn.cursor()

        cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-p1', 'P1', '+919000000001', datetime('now'), datetime('now'));")
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO farmers (uuid, name, phone, created_at, updated_at) VALUES ('f-p2', 'P2', '+919000000001', datetime('now'), datetime('now'));")
        conn.close()

    def test_duplicate_sensor_id_rejected(self, setup_test_db):
        """Verifies UNIQUE constraint on sensors.sensor_id."""
        conn = sqlite3.connect(str(setup_test_db))
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sensors (sensor_id, created_at, updated_at) VALUES ('esp32_dup_test', datetime('now'), datetime('now'));")
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO sensors (sensor_id, created_at, updated_at) VALUES ('esp32_dup_test', datetime('now'), datetime('now'));")
        conn.close()


