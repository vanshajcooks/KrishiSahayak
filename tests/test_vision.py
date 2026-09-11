"""
Vision AI Endpoint Tests — Smart Farming Assistant (SIH 26180)
Tests YOLO11 crop-disease detection endpoint (POST /api/v1/vision/predict).
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
from main import app

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent.parent / "backend" / "models" / "sample_leaf.jpg"


@pytest.fixture
def client():
    """Provides FastAPI test client."""
    return TestClient(app)


class TestVisionPredictEndpoint:
    """Tests for POST /api/v1/vision/predict."""

    def test_vision_predict_valid_leaf_image(self, client):
        """Verifies inference on a real leaf image returns valid structured detections."""
        if not SAMPLE_IMAGE_PATH.exists():
            pytest.skip(f"Sample leaf image not found at {SAMPLE_IMAGE_PATH}")

        with open(SAMPLE_IMAGE_PATH, "rb") as f:
            content = f.read()
            response = client.post(
                "/api/v1/vision/predict",
                files={"file": ("leaf.jpg", content, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["model"] == "yolo11n-crop-disease"
        assert isinstance(data["predictions"], list)
        assert data["count"] == len(data["predictions"])
        assert data["inference_time_ms"] > 0

        # Verify structure of detections
        if data["count"] > 0:
            pred = data["predictions"][0]
            assert "crop" in pred
            assert "condition" in pred
            assert "confidence" in pred
            assert 0.0 <= pred["confidence"] <= 1.0
            assert "bbox" in pred
            assert len(pred["bbox"]) == 4

    def test_vision_predict_synthetic_image_responds_correctly(self, client):
        """
        Verifies that a synthetic image upload responds correctly without assuming zero detections.
        """
        img = Image.new("RGB", (320, 320), color=(34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = client.post(
            "/api/v1/vision/predict",
            files={"file": ("synthetic.jpg", buf.getvalue(), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["predictions"], list)
        assert data["count"] == len(data["predictions"])
        assert "inference_time_ms" in data

    def test_vision_predict_confidence_filter(self, client):
        """Verifies that the conf query parameter filters predictions accordingly."""
        if not SAMPLE_IMAGE_PATH.exists():
            pytest.skip(f"Sample leaf image not found at {SAMPLE_IMAGE_PATH}")

        with open(SAMPLE_IMAGE_PATH, "rb") as f:
            content = f.read()
            response = client.post(
                "/api/v1/vision/predict?conf=0.999",
                files={"file": ("leaf.jpg", content, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        for pred in data["predictions"]:
            assert pred["confidence"] >= 0.999

    def test_vision_predict_empty_file_returns_400(self, client):
        """Verifies that an empty 0-byte file upload returns HTTP 400."""
        response = client.post(
            "/api/v1/vision/predict",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_vision_predict_corrupt_file_returns_400(self, client):
        """Verifies that a corrupted or non-image file returns HTTP 400."""
        corrupt_bytes = b"This is not a real JPEG image file content."
        response = client.post(
            "/api/v1/vision/predict",
            files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        assert "valid image" in response.json()["detail"].lower()

    def test_vision_predict_non_image_content_type_returns_400(self, client):
        """Verifies that non-image content-type returns HTTP 400."""
        response = client.post(
            "/api/v1/vision/predict",
            files={"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        assert response.status_code == 400
        assert "not an image" in response.json()["detail"].lower()
