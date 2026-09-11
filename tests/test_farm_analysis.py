"""
Unified Multimodal Farm Analysis Tests — Smart Farming Assistant (SIH 26180)
Tests the POST /api/v1/farm/analyze endpoint integrating YOLO vision inference
with localized SQLite sensor telemetry and rule-based agronomic decisions.
"""

import io
import os
import sys
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
