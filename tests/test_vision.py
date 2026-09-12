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


class TestVisionModelWarmup:
    """Tests for model pre-warming logic and graceful startup handling."""

    def test_warmup_model_executes_successfully(self):
        """Verifies that warmup_model runs a dummy forward pass and returns True."""
        from vision import warmup_model
        result = warmup_model(imgsz=320)
        assert result is True

    def test_lifespan_warmup_failure_handled_gracefully(self):
        """Verifies that if warmup fails during lifespan startup, the app still starts without raising an error."""
        import asyncio
        from unittest.mock import patch
        from main import lifespan

        with patch("main.warmup_model", side_effect=RuntimeError("Simulated warmup crash")):
            async def run_lifespan():
                async with lifespan(app):
                    pass

            asyncio.run(run_lifespan())


class TestVisionReliabilityAndConfidenceThreshold:
    """
    Tests for the Three-Tier YOLO Reliability Gate in the vision pipeline:
    - Tier 1: RELIABLE (confidence >= 0.50)
    - Tier 2: INCONCLUSIVE (0.25 <= confidence < 0.50)
    - Tier 3: NO_DETECTION (zero candidate detections)
    """

    def test_sample_leaf_is_tier1_reliable(self, client):
        """
        Confirms that the sample leaf image (73.3% confidence) is classified as
        Tier 1: RELIABLE with is_reliable=True and top_confidence >= 0.50.
        """
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
        assert data["reliability"] == "RELIABLE"
        assert data["is_reliable"] is True
        assert data["top_confidence"] is not None
        assert data["top_confidence"] >= 0.50
        assert data["count"] > 0

    def test_synthetic_image_is_tier3_no_detection(self, client):
        """
        Confirms that an image with zero candidate detections is classified as
        Tier 3: NO_DETECTION with is_reliable=False.
        """
        img = Image.new("RGB", (320, 320), color=(34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        response = client.post(
            "/api/v1/vision/predict",
            files={"file": ("synthetic.jpg", buf.getvalue(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["reliability"] == "NO_DETECTION"
        assert data["is_reliable"] is False
        assert data["top_confidence"] is None

    def test_evaluate_vision_reliability_all_three_tiers(self):
        """
        Validates evaluate_vision_reliability() across all boundary conditions:
        - conf >= 0.50 -> RELIABLE (Tier 1)
        - 0.25 <= conf < 0.50 -> INCONCLUSIVE (Tier 2)
        - empty list -> NO_DETECTION (Tier 3)
        """
        from analysis import evaluate_vision_reliability
        from schemas import DiseasePrediction, VisionReliabilityTier

        # Tier 1: Reliable (0.733)
        preds_tier1 = [
            DiseasePrediction(crop="potato", condition="late_blight", confidence=0.733, bbox=[0, 0, 10, 10])
        ]
        tier, is_rel, top_conf = evaluate_vision_reliability(preds_tier1)
        assert tier == VisionReliabilityTier.RELIABLE
        assert is_rel is True
        assert top_conf == 0.733

        # Tier 1 boundary: exactly 0.50
        preds_boundary = [
            DiseasePrediction(crop="tomato", condition="early_blight", confidence=0.50, bbox=[0, 0, 10, 10])
        ]
        tier, is_rel, top_conf = evaluate_vision_reliability(preds_boundary)
        assert tier == VisionReliabilityTier.RELIABLE
        assert is_rel is True
        assert top_conf == 0.50

        # Tier 2: Inconclusive (0.38 false positive)
        preds_tier2 = [
            DiseasePrediction(crop="corn", condition="leaf_blight", confidence=0.38, bbox=[0, 0, 10, 10])
        ]
        tier, is_rel, top_conf = evaluate_vision_reliability(preds_tier2)
        assert tier == VisionReliabilityTier.INCONCLUSIVE
        assert is_rel is False
        assert top_conf == 0.38

        # Tier 2: Low boundary (0.25)
        preds_tier2_low = [
            DiseasePrediction(crop="corn", condition="rust", confidence=0.25, bbox=[0, 0, 10, 10])
        ]
        tier, is_rel, top_conf = evaluate_vision_reliability(preds_tier2_low)
        assert tier == VisionReliabilityTier.INCONCLUSIVE
        assert is_rel is False
        assert top_conf == 0.25

        # Tier 3: Zero detections
        tier, is_rel, top_conf = evaluate_vision_reliability([])
        assert tier == VisionReliabilityTier.NO_DETECTION
        assert is_rel is False
        assert top_conf is None

        # Multiple proposals: highest confidence determines tier
        preds_multi = [
            DiseasePrediction(crop="corn", condition="leaf_blight", confidence=0.35, bbox=[0, 0, 10, 10]),
            DiseasePrediction(crop="tomato", condition="early_blight", confidence=0.62, bbox=[10, 10, 20, 20]),
        ]
        tier, is_rel, top_conf = evaluate_vision_reliability(preds_multi)
        assert tier == VisionReliabilityTier.RELIABLE
        assert is_rel is True
        assert top_conf == 0.62


