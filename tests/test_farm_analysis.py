"""
Unified Multimodal Farm Analysis Tests — Smart Farming Assistant (SIH 26180)
Tests the POST /api/v1/farm/analyze endpoint integrating YOLO vision inference
with localized SQLite sensor telemetry and rule-based agronomic decisions.
"""

import io
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from PIL import Image


# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from database import init_db, get_db_path, insert_reading
from main import app
from schemas import SensorReading, VisionPredictionResponse, DiseasePrediction
from analysis import synthesize_farm_insights, build_unified_analysis

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent.parent / "backend" / "models" / "sample_leaf.jpg"


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """
    Ensures test isolation by running against a temporary SQLite database.
    Production database is never touched.
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


def create_synthetic_leaf_image_bytes() -> bytes:
    """Creates an in-memory synthetic green leaf JPEG."""
    img = Image.new("RGB", (320, 320), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ============================================================================
# Endpoint Tests: POST /api/v1/farm/analyze
# ============================================================================

class TestUnifiedFarmAnalyzeEndpoint:
    """Tests for POST /api/v1/farm/analyze."""

    def test_analyze_with_both_leaf_and_sensor_data(self, client, setup_test_db):
        """
        Verifies that when both an image and sensor telemetry are present,
        the unified response contains vision results, sensor telemetry,
        decision evaluations, and integrated cross-modal insights.
        """
        # Ingest sensor reading
        ingest_payload = {
            "sensor_id": "esp32_field_01",
            "soil_moisture": 25.0,  # LOW -> IRRIGATE_SOON
            "temperature": 28.5,
            "humidity": 82.0,      # High fungal microclimate risk
            "rain_level": 0.0,
        }
        ingest_res = client.post("/api/v1/sensors/ingest", json=ingest_payload)
        assert ingest_res.status_code == 201

        image_bytes = (
            SAMPLE_IMAGE_PATH.read_bytes()
            if SAMPLE_IMAGE_PATH.exists()
            else create_synthetic_leaf_image_bytes()
        )

        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timestamp" in data

        # Vision verification
        assert data["vision"]["model"] == "yolo11n-crop-disease"
        assert isinstance(data["vision"]["predictions"], list)
        assert data["vision"]["inference_time_ms"] > 0

        # Sensor & Decision verification
        assert data["sensor_available"] is True
        assert data["sensor_telemetry"] is not None
        assert data["sensor_telemetry"]["sensor_id"] == "esp32_field_01"
        assert data["sensor_telemetry"]["soil_moisture"] == 25.0

        assert data["decision"] is not None
        assert data["decision"]["soil_moisture_status"] == "LOW"
        assert data["decision"]["irrigation_action"] == "IRRIGATE_SOON"
        assert data["decision"]["disease_risk_level"] == "HIGH"

        # Insights verification
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) >= 2
        insights_text = " ".join(data["insights"])
        assert "Soil moisture is 25.0%" in insights_text

    def test_analyze_graceful_when_no_sensor_data_exists(self, client):
        """
        Verifies that when database is empty (no sensor readings),
        the endpoint still succeeds, runs vision inference, and gracefully
        reports sensor_available=False without throwing 404/500 errors.
        """
        image_bytes = (
            SAMPLE_IMAGE_PATH.read_bytes()
            if SAMPLE_IMAGE_PATH.exists()
            else create_synthetic_leaf_image_bytes()
        )

        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["vision"]["model"] == "yolo11n-crop-disease"
        assert data["sensor_available"] is False
        assert data["sensor_telemetry"] is None
        assert data["decision"] is None

        # Insights should explain missing telemetry
        insights_text = " ".join(data["insights"])
        assert "Sensor telemetry unavailable" in insights_text

    def test_analyze_filters_by_sensor_id_query_param(self, client):
        """Verifies filtering telemetry by sensor_id query parameter."""
        # Ingest for node A (dry) and node B (optimal)
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "node_alpha",
            "soil_moisture": 22.0,
            "temperature": 25.0,
            "humidity": 60.0,
        })
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "node_beta",
            "soil_moisture": 50.0,
            "temperature": 25.0,
            "humidity": 60.0,
        })

        image_bytes = create_synthetic_leaf_image_bytes()

        response = client.post(
            "/api/v1/farm/analyze?sensor_id=node_alpha",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sensor_available"] is True
        assert data["sensor_telemetry"]["sensor_id"] == "node_alpha"
        assert data["sensor_telemetry"]["soil_moisture"] == 22.0
        assert data["decision"]["soil_moisture_status"] == "LOW"

    def test_analyze_filters_by_sensor_id_form_param(self, client):
        """Verifies filtering telemetry by sensor_id passed in form-data body."""
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "node_gamma",
            "soil_moisture": 45.0,
            "temperature": 26.0,
            "humidity": 65.0,
        })

        image_bytes = create_synthetic_leaf_image_bytes()

        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            data={"sensor_id": "node_gamma"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sensor_available"] is True
        assert data["sensor_telemetry"]["sensor_id"] == "node_gamma"
        assert data["sensor_telemetry"]["soil_moisture"] == 45.0
        assert data["decision"]["soil_moisture_status"] == "OPTIMAL"

    def test_analyze_nonexistent_sensor_id_handles_gracefully(self, client):
        """
        Verifies that querying a nonexistent sensor_id returns vision results
        and sets sensor_available=False without failing the request.
        """
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "node_alpha",
            "soil_moisture": 40.0,
            "temperature": 25.0,
            "humidity": 60.0,
        })

        image_bytes = create_synthetic_leaf_image_bytes()

        response = client.post(
            "/api/v1/farm/analyze?sensor_id=node_nonexistent",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["sensor_available"] is False
        assert data["sensor_telemetry"] is None
        assert data["decision"] is None

    def test_analyze_confidence_threshold_filtering(self, client):
        """Verifies that confidence threshold query parameter filters predictions."""
        image_bytes = (
            SAMPLE_IMAGE_PATH.read_bytes()
            if SAMPLE_IMAGE_PATH.exists()
            else create_synthetic_leaf_image_bytes()
        )

        response = client.post(
            "/api/v1/farm/analyze?conf=0.999",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        for pred in data["vision"]["predictions"]:
            assert pred["confidence"] >= 0.999

    def test_analyze_empty_file_returns_400(self, client):
        """Verifies that an empty file upload returns HTTP 400."""
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_analyze_non_image_content_type_returns_400(self, client):
        """Verifies that non-image MIME types return HTTP 400."""
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("document.txt", b"plain text", "text/plain")},
        )
        assert response.status_code == 400
        assert "not an image" in response.json()["detail"].lower()

    def test_analyze_corrupt_image_returns_400(self, client):
        """Verifies that corrupt bytes labelled as JPEG return HTTP 400."""
        corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_RANDOM_GARBAGE"
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        assert "valid image" in response.json()["detail"].lower()


# ============================================================================
# Modular Unit Tests: analysis.py
# ============================================================================

class TestModularAnalysisLogic:
    """Direct unit tests for synthesis logic in analysis.py."""

    def test_synthesize_insights_disease_and_high_humidity(self):
        """Cross-modal correlation: disease detected + favorable fungal microclimate."""
        vision = VisionPredictionResponse(
            status="success",
            model="yolo11n-crop-disease",
            predictions=[
                DiseasePrediction(
                    crop="tomato",
                    condition="early_blight",
                    confidence=0.88,
                    bbox=[10.0, 10.0, 100.0, 100.0],
                )
            ],
            count=1,
            inference_time_ms=50.0,
        )

        reading = {
            "sensor_id": "test_s1",
            "soil_moisture": 25.0,
            "temperature": 27.0,
            "humidity": 85.0,
            "rain_level": 0.0,
            "timestamp": "2026-09-12T01:00:00Z",
        }
        from decision import evaluate_reading
        decision = evaluate_reading(reading)

        unified = build_unified_analysis(vision=vision, sensor_reading=reading, decision=decision)

        assert unified.sensor_available is True
        assert unified.sensor_telemetry is not None
        assert unified.decision is not None

        insights_text = " ".join(unified.insights)
        assert "Early Blight" in insights_text
        assert "Tomato" in insights_text
        assert "fungal proliferation" in insights_text
        assert "drip irrigation" in insights_text

    def test_synthesize_insights_healthy_and_rain_override(self):
        """Cross-modal correlation: healthy foliage + active rain pausing irrigation."""
        vision = VisionPredictionResponse(
            status="success",
            model="yolo11n-crop-disease",
            predictions=[
                DiseasePrediction(
                    crop="potato",
                    condition="healthy",
                    confidence=0.92,
                    bbox=[5.0, 5.0, 50.0, 50.0],
                )
            ],
            count=1,
            inference_time_ms=45.0,
        )

        reading = {
            "sensor_id": "test_s2",
            "soil_moisture": 25.0,
            "temperature": 22.0,
            "humidity": 65.0,
            "rain_level": 75.0,  # Rain override active
            "timestamp": "2026-09-12T01:00:00Z",
        }
        from decision import evaluate_reading
        decision = evaluate_reading(reading)

        unified = build_unified_analysis(vision=vision, sensor_reading=reading, decision=decision)

        insights_text = " ".join(unified.insights)
        assert "healthy Potato foliage" in insights_text
        assert "rain is detected" in insights_text


class TestTelemetryFreshnessAndStaleHandling:
    """Tests for 10-second telemetry freshness threshold and stale sensor degradation."""

    def test_is_telemetry_fresh_boundary_evaluations(self):
        """Validates exact threshold boundaries for is_telemetry_fresh()."""
        from analysis import is_telemetry_fresh
        ref_time = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)

        # 2 seconds old -> Fresh
        ts_fresh = datetime(2026, 9, 12, 11, 59, 58, tzinfo=timezone.utc)
        assert is_telemetry_fresh(ts_fresh, reference_time=ref_time) is True

        # Exactly 10.0 seconds old -> Fresh
        ts_exact = datetime(2026, 9, 12, 11, 59, 50, tzinfo=timezone.utc)
        assert is_telemetry_fresh(ts_exact, reference_time=ref_time) is True

        # 10.1 seconds old -> Stale
        ts_stale = datetime(2026, 9, 12, 11, 59, 49, 900000, tzinfo=timezone.utc)
        assert is_telemetry_fresh(ts_stale, reference_time=ref_time) is False

        # 60 seconds old -> Stale
        ts_old = datetime(2026, 9, 12, 11, 59, 0, tzinfo=timezone.utc)
        assert is_telemetry_fresh(ts_old, reference_time=ref_time) is False

        # ISO format strings
        assert is_telemetry_fresh("2026-09-12T11:59:55Z", reference_time=ref_time) is True
        assert is_telemetry_fresh("2026-09-12T11:59:45Z", reference_time=ref_time) is False

        # Invalid/None
        assert is_telemetry_fresh(None) is False
        assert is_telemetry_fresh("invalid-date") is False

    def test_analyze_with_stale_telemetry_marks_sensor_unavailable_and_stale(self, client):
        """
        When database has telemetry older than 10 seconds (e.g. ESP32 disconnected),
        the endpoint marks sensor_available=False, sensor_stale=True, decision=None,
        excludes stale sensor data from live context, and provides stale insight.
        """
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=25)
        client.post(
            "/api/v1/sensors/ingest",
            json={
                "sensor_id": "esp32_disconnected",
                "soil_moisture": 15.0,  # Dry
                "temperature": 32.0,
                "humidity": 45.0,
                "timestamp": stale_time.isoformat(),
            },
        )

        image_bytes = create_synthetic_leaf_image_bytes()
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Sensor must NOT be presented as live/available
        assert data["sensor_available"] is False
        assert data["sensor_stale"] is True
        assert data["decision"] is None

        # Telemetry should be attached with is_fresh=False
        assert data["sensor_telemetry"] is not None
        assert data["sensor_telemetry"]["is_fresh"] is False
        assert data["sensor_telemetry"]["sensor_id"] == "esp32_disconnected"

        # Insights must indicate stale telemetry and omit live sensor context
        insights_text = " ".join(data["insights"]).lower()
        assert "stale" in insights_text
        assert "soil moisture is" not in insights_text

    def test_analyze_with_fresh_telemetry_maintains_live_decision_and_availability(self, client):
        """
        When telemetry was received within 10 seconds (e.g. active ESP32 pinging every 2s),
        sensor_available=True, sensor_stale=False, decision is evaluated, and live context is included.
        """
        fresh_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        client.post(
            "/api/v1/sensors/ingest",
            json={
                "sensor_id": "esp32_active",
                "soil_moisture": 25.0,  # Dry -> IRRIGATE_SOON
                "temperature": 28.0,
                "humidity": 50.0,
                "timestamp": fresh_time.isoformat(),
            },
        )

        image_bytes = create_synthetic_leaf_image_bytes()
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sensor_available"] is True
        assert data["sensor_stale"] is False
        assert data["decision"] is not None
        assert data["decision"]["irrigation_action"] == "IRRIGATE_SOON"
        assert data["sensor_telemetry"]["is_fresh"] is True

        insights_text = " ".join(data["insights"])
        assert "Soil moisture is 25.0%" in insights_text

    def test_latest_sensors_endpoint_reports_freshness_flag(self, client):
        """Verifies GET /api/v1/sensors/latest sets is_fresh accordingly."""
        # 1. Stale reading
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        client.post(
            "/api/v1/sensors/ingest",
            json={
                "sensor_id": "node_stale",
                "soil_moisture": 40.0,
                "temperature": 25.0,
                "humidity": 60.0,
                "timestamp": stale_time.isoformat(),
            },
        )
        res_stale = client.get("/api/v1/sensors/latest?sensor_id=node_stale")
        assert res_stale.status_code == 200
        assert res_stale.json()["is_fresh"] is False

        # 2. Fresh reading
        fresh_time = datetime.now(timezone.utc)
        client.post(
            "/api/v1/sensors/ingest",
            json={
                "sensor_id": "node_fresh",
                "soil_moisture": 45.0,
                "temperature": 26.0,
                "humidity": 62.0,
                "timestamp": fresh_time.isoformat(),
            },
        )
        res_fresh = client.get("/api/v1/sensors/latest?sensor_id=node_fresh")
        assert res_fresh.status_code == 200
        assert res_fresh.json()["is_fresh"] is True


class TestFarmAnalysisReliabilityGate:
    """
    Tests verifying the Three-Tier YOLO Reliability Gate within Unified Farm Analysis:
    - Tier 1: >=0.50 Reliable (genuine disease & cross-modal recommendations)
    - Tier 2: 0.25-<0.50 Inconclusive (bypasses disease quarantine/treatment advisories; prompts retake)
    - Tier 3: Zero detections (honest report without false 95% healthy claim)
    """

    def test_unified_analysis_with_sample_leaf_is_tier1_reliable(self, client):
        """Confirms that sample_leaf.jpg produces Tier 1: RELIABLE with full cross-modal insights."""
        if not SAMPLE_IMAGE_PATH.exists():
            pytest.skip(f"Sample leaf image not found at {SAMPLE_IMAGE_PATH}")

        with open(SAMPLE_IMAGE_PATH, "rb") as f:
            content = f.read()

        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", content, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vision"]["reliability"] == "RELIABLE"
        assert data["vision"]["is_reliable"] is True
        assert data["vision"]["top_confidence"] >= 0.50
        assert data["vision"]["count"] > 0

        insights_text = " ".join(data["insights"])
        assert "Late Blight" in insights_text
        assert "Potato" in insights_text

    def test_unified_analysis_with_synthetic_image_is_tier3_no_detection(self, client):
        """Confirms that an image with 0 detections produces Tier 3: NO_DETECTION without false 95% healthy claim."""
        image_bytes = create_synthetic_leaf_image_bytes()
        response = client.post(
            "/api/v1/farm/analyze",
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vision"]["reliability"] == "NO_DETECTION"
        assert data["vision"]["is_reliable"] is False
        assert data["vision"]["count"] == 0

        insights_text = " ".join(data["insights"])
        assert "No reliable foliar disease symptoms detected" in insights_text
        assert "95%" not in insights_text

    def test_unified_analysis_inconclusive_does_not_trigger_disease_advisories(self):
        """
        Confirms that a 38% detection (Tier 2: INCONCLUSIVE):
        1. Is marked as INCONCLUSIVE and is_reliable=False.
        2. Prompts user for a clear retake.
        3. Does NOT trigger fungal proliferation or quarantine advisories despite high humidity.
        4. Preserves live sensor context and general irrigation advice.
        """
        from decision import evaluate_reading
        from schemas import DiseasePrediction, VisionPredictionResponse, VisionReliabilityTier

        # 38% Corn leaf blight false positive
        vision = VisionPredictionResponse(
            status="success",
            model="yolo11n-crop-disease",
            predictions=[
                DiseasePrediction(
                    crop="corn",
                    condition="leaf_blight",
                    confidence=0.38,
                    bbox=[10.0, 10.0, 100.0, 100.0],
                )
            ],
            count=1,
            inference_time_ms=40.0,
        )

        reading = {
            "sensor_id": "test_inconclusive_sensor",
            "soil_moisture": 20.0,  # Dry -> IRRIGATE_SOON
            "temperature": 27.0,
            "humidity": 85.0,       # High humidity -> normally triggers fungal alert
            "rain_level": 0.0,
            "timestamp": "2026-09-12T01:00:00Z",
        }
        decision = evaluate_reading(reading)

        unified = build_unified_analysis(vision=vision, sensor_reading=reading, decision=decision)

        # 1. Verify reliability tier
        assert unified.vision.reliability == VisionReliabilityTier.INCONCLUSIVE
        assert unified.vision.is_reliable is False
        assert unified.vision.top_confidence == 0.38

        insights_text = " ".join(unified.insights)

        # 2. Verify inconclusive warning & retake guidance
        assert "Inconclusive detection (38% confidence)" in insights_text
        assert "Please retake a clear, well-lit photo" in insights_text

        # 3. Verify disease-specific advisories are NOT triggered
        assert "fungal proliferation" not in insights_text
        assert "quarantine affected" not in insights_text
        assert "drip irrigation to hydrate roots without splashing" not in insights_text

        # 4. Verify sensor context and basic irrigation advice are preserved
        assert "Soil moisture is 20.0%" in insights_text
        assert "Soil moisture is low. Proceed with scheduled irrigation." in insights_text

    def test_unified_analysis_reliable_maintains_cross_modal_disease_actions(self):
        """
        Confirms that a high-confidence detection (e.g. 85% early blight, Tier 1: RELIABLE):
        1. Is marked as RELIABLE and is_reliable=True.
        2. Preserves disease diagnosis.
        3. Preserves cross-modal fungal and irrigation advisories under high humidity.
        """
        from decision import evaluate_reading
        from schemas import DiseasePrediction, VisionPredictionResponse, VisionReliabilityTier

        vision = VisionPredictionResponse(
            status="success",
            model="yolo11n-crop-disease",
            predictions=[
                DiseasePrediction(
                    crop="tomato",
                    condition="early_blight",
                    confidence=0.85,
                    bbox=[10.0, 10.0, 100.0, 100.0],
                )
            ],
            count=1,
            inference_time_ms=45.0,
        )

        reading = {
            "sensor_id": "test_reliable_sensor",
            "soil_moisture": 20.0,
            "temperature": 27.0,
            "humidity": 85.0,
            "rain_level": 0.0,
            "timestamp": "2026-09-12T01:00:00Z",
        }
        decision = evaluate_reading(reading)

        unified = build_unified_analysis(vision=vision, sensor_reading=reading, decision=decision)

        assert unified.vision.reliability == VisionReliabilityTier.RELIABLE
        assert unified.vision.is_reliable is True
        insights_text = " ".join(unified.insights)
        assert "Detected possible Early Blight on Tomato (85% confidence)" in insights_text
        assert "fungal proliferation" in insights_text
        assert "drip irrigation to hydrate roots without splashing water onto infected foliage" in insights_text

    def test_unified_analysis_inconclusive_preserves_independent_sensor_and_weather_insights(self):
        """
        Confirms that Tier 2 (INCONCLUSIVE) preserves independent fresh sensor and weather insights:
        1. Sensor telemetry and irrigation recommendations are produced.
        2. Weather forecast context and weather-irrigation correlations are produced.
        3. Only disease-specific pathogen/quarantine/fungal correlations are suppressed.
        """
        from decision import evaluate_reading
        from schemas import (
            DiseasePrediction,
            VisionPredictionResponse,
            VisionReliabilityTier,
            WeatherData,
            WeatherForecastItem,
        )

        vision = VisionPredictionResponse(
            status="success",
            model="yolo11n-crop-disease",
            predictions=[
                DiseasePrediction(
                    crop="corn",
                    condition="leaf_blight",
                    confidence=0.38,
                    bbox=[10.0, 10.0, 100.0, 100.0],
                )
            ],
            count=1,
            inference_time_ms=35.0,
        )

        reading = {
            "sensor_id": "sensor_tier2_test",
            "soil_moisture": 22.0,
            "temperature": 28.0,
            "humidity": 80.0,
            "rain_level": 0.0,
            "timestamp": "2026-09-12T01:00:00Z",
        }
        decision = evaluate_reading(reading)

        weather = WeatherData(
            location="Derabassi Farm",
            temperature=36.0,
            humidity=80.0,
            condition="Partly Cloudy",
            rain_probability=20.0,
            is_rain_forecasted=False,
            forecast=[
                WeatherForecastItem(
                    time="Today",
                    temp_max=36.0,
                    temp_min=24.0,
                    condition="Partly Cloudy",
                    rain_probability=20.0,
                )
            ],
            source="OpenWeatherMap",
        )

        unified = build_unified_analysis(
            vision=vision,
            sensor_reading=reading,
            decision=decision,
            weather=weather,
        )

        assert unified.vision.reliability == VisionReliabilityTier.INCONCLUSIVE
        assert unified.vision.is_reliable is False
        assert unified.sensor_available is True
        assert unified.weather_available is True

        insights_text = " ".join(unified.insights)

        # Inconclusive prompt
        assert "Inconclusive detection (38% confidence)" in insights_text
        assert "Please retake a clear, well-lit photo" in insights_text

        # Independent sensor insights
        assert "Soil moisture is 22.0%" in insights_text
        assert "Soil moisture is low. Proceed with scheduled irrigation." in insights_text

        # Independent weather insights
        assert "Weather Forecast (Derabassi Farm): Partly Cloudy" in insights_text
        assert "Weather confirmation: Dry forecast" in insights_text
        assert "Weather thermal alert: Elevated temperatures (36.0°C) expected." in insights_text

        # Disease-specific correlations are suppressed
        assert "fungal proliferation" not in insights_text
        assert "spore dispersal" not in insights_text
        assert "quarantine affected" not in insights_text



