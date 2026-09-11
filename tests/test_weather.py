"""
Weather Integration Tests — Smart Farming Assistant (SIH 26180)
Tests modular weather service and its integration into the unified farm analysis endpoint.
All tests use mocked external API responses; zero live network calls are made.
"""

import io
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from PIL import Image

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from database import get_db_path, init_db
from fastapi.testclient import TestClient
from main import app
from schemas import WeatherData, WeatherForecastItem
from weather import (
    fetch_weather_async,
    fetch_weather_sync,
    get_weather_config,
    parse_weather_response,
)

SAMPLE_IMAGE_PATH = Path(__file__).resolve().parent.parent / "backend" / "models" / "sample_leaf.jpg"


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Ensures test database isolation."""
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


def sample_mock_weather_data(is_rain: bool = False) -> WeatherData:
    """Helper creating a valid WeatherData model for mocking."""
    return WeatherData(
        location="New Delhi, IN",
        temperature=29.5,
        humidity=78.0 if is_rain else 45.0,
        condition="Rain" if is_rain else "Clear",
        rain_probability=85.0 if is_rain else 15.0,
        wind_speed_kmh=12.5,
        is_rain_forecasted=is_rain,
        forecast=[
            WeatherForecastItem(
                time="2026-09-13",
                temp_max=31.0,
                temp_min=24.0,
                condition="Rain" if is_rain else "Clear",
                rain_probability=85.0 if is_rain else 15.0,
            )
        ],
        source="OpenWeatherMap",
        timestamp=datetime.now(timezone.utc),
    )


# ============================================================================
# Unit Tests: weather.py Parsing & Degradation
# ============================================================================

class TestWeatherServiceLogic:
    """Tests for weather service parser and fallback mechanisms."""

    def test_parse_weather_response_valid_json(self):
        """Verifies parsing of OpenWeatherMap JSON into WeatherData schema."""
        current_json = {
            "name": "Ludhiana",
            "main": {"temp": 32.4, "humidity": 65},
            "weather": [{"main": "Clouds", "description": "scattered clouds"}],
            "wind": {"speed": 4.5},
            "rain": {},
        }
        forecast_json = {
            "list": [
                {
                    "dt_txt": "2026-09-13 12:00:00",
                    "main": {"temp": 33.0, "temp_max": 34.5, "temp_min": 25.0},
                    "weather": [{"main": "Clear"}],
                    "pop": 0.2,
                }
            ]
        }

        data = parse_weather_response(
            current_data=current_json,
            forecast_data=forecast_json,
            location_name="Ludhiana Farm",
        )

        assert data.location == "Ludhiana Farm"
        assert data.temperature == 32.4
        assert data.humidity == 65.0
        assert data.condition == "Clouds"
        assert data.wind_speed_kmh == round(4.5 * 3.6, 1)
        assert len(data.forecast) == 1
        assert data.forecast[0].time == "2026-09-13"
        assert data.forecast[0].rain_probability == 20.0

    def test_fetch_weather_async_returns_none_when_no_api_key(self, monkeypatch):
        """Verifies that missing WEATHER_API_KEY skips weather fetch cleanly."""
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)
        import asyncio
        result = asyncio.run(fetch_weather_async())
        assert result is None

    def test_fetch_weather_sync_returns_none_when_no_api_key(self, monkeypatch):
        """Verifies that synchronous fetch also returns None when API key is unset."""
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)
        result = fetch_weather_sync()
        assert result is None

    @pytest.mark.anyio
    async def test_fetch_weather_async_handles_timeout_gracefully(self, monkeypatch):
        """Verifies that httpx timeouts return None without crashing."""
        monkeypatch.setenv("WEATHER_API_KEY", "mock_test_key_123")
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

        result = await fetch_weather_async(client=mock_client)
        assert result is None

    @pytest.mark.anyio
    async def test_fetch_weather_async_handles_api_error_status(self, monkeypatch):
        """Verifies that HTTP 401/500 responses return None gracefully."""
        monkeypatch.setenv("WEATHER_API_KEY", "invalid_key")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        result = await fetch_weather_async(client=mock_client)
        assert result is None


# ============================================================================
# Endpoint Tests: GET /api/v1/weather/current
# ============================================================================

class TestCurrentWeatherEndpoint:
    """Tests for GET /api/v1/weather/current."""

    def test_get_current_weather_unavailable_returns_503(self, client, monkeypatch):
        """Verifies 503 Service Unavailable when no weather API key is set."""
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)
        response = client.get("/api/v1/weather/current")
        assert response.status_code == 503
        assert "Weather service unavailable" in response.json()["detail"]

    def test_get_current_weather_returns_data_when_mocked(self, client):
        """Verifies 200 OK and structured WeatherData when weather is available."""
        mock_data = sample_mock_weather_data(is_rain=False)
        with patch("main.fetch_weather_async", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_data
            response = client.get("/api/v1/weather/current")

        assert response.status_code == 200
        res_json = response.json()
        assert res_json["location"] == "New Delhi, IN"
        assert res_json["temperature"] == 29.5
        assert res_json["humidity"] == 45.0
        assert res_json["condition"] == "Clear"
        assert len(res_json["forecast"]) == 1


# ============================================================================
# Multimodal Integration Tests: POST /api/v1/farm/analyze with Weather
# ============================================================================

class TestUnifiedFarmAnalyzeWithWeather:
    """Tests integrating weather into POST /api/v1/farm/analyze."""

    def test_analyze_with_vision_sensors_and_rain_weather(self, client):
        """
        Multimodal test:
        - Soil moisture is LOW (25%) -> Sensor engine requests IRRIGATE_SOON.
        - Weather forecasts RAIN (85% probability).
        - Verification: Cross-modal insight recommends delaying irrigation due to forecasted rain!
        """
        # Ingest dry soil reading
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "esp32_zone_01",
            "soil_moisture": 25.0,  # LOW -> IRRIGATE_SOON
            "temperature": 27.0,
            "humidity": 60.0,
        })

        mock_weather = sample_mock_weather_data(is_rain=True)
        image_bytes = create_synthetic_leaf_image_bytes()

        with patch("main.fetch_weather_async", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_weather
            response = client.post(
                "/api/v1/farm/analyze",
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Vision present
        assert data["vision"]["model"] == "yolo11n-crop-disease"

        # Sensor present
        assert data["sensor_available"] is True
        assert data["decision"]["irrigation_action"] == "IRRIGATE_SOON"

        # Weather present
        assert data["weather_available"] is True
        assert data["weather"]["condition"] == "Rain"
        assert data["weather"]["rain_probability"] == 85.0

        # Insights verify weather correlation
        insights_text = " ".join(data["insights"])
        assert "Weather Forecast (New Delhi, IN)" in insights_text
        assert "Delay planned irrigation" in insights_text

    def test_analyze_with_vision_sensors_and_dry_weather(self, client):
        """
        Multimodal test:
        - Soil moisture is LOW (25%) -> Sensor engine requests IRRIGATE_SOON.
        - Weather forecasts DRY (Clear, 15% rain probability).
        - Verification: Cross-modal insight confirms safe to proceed with irrigation.
        """
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "esp32_zone_01",
            "soil_moisture": 25.0,
            "temperature": 27.0,
            "humidity": 55.0,
        })

        mock_weather = sample_mock_weather_data(is_rain=False)
        image_bytes = create_synthetic_leaf_image_bytes()

        with patch("main.fetch_weather_async", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_weather
            response = client.post(
                "/api/v1/farm/analyze",
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["weather_available"] is True
        insights_text = " ".join(data["insights"])
        assert "Safe to proceed with scheduled irrigation" in insights_text

    def test_analyze_weather_unavailable_still_succeeds(self, client):
        """
        Verifies that when weather is unavailable (None),
        the analysis still completes 100% successfully using vision + sensors.
        """
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "esp32_zone_01",
            "soil_moisture": 45.0,
            "temperature": 26.0,
            "humidity": 65.0,
        })

        image_bytes = create_synthetic_leaf_image_bytes()

        with patch("main.fetch_weather_async", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            response = client.post(
                "/api/v1/farm/analyze",
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["weather_available"] is False
        assert data["weather"] is None
        assert data["sensor_available"] is True
        assert data["vision"]["count"] >= 0

    def test_analyze_weather_exception_does_not_break_endpoint(self, client):
        """
        Verifies that even if fetch_weather_async raises an unexpected exception,
        the analyze endpoint catches it and continues gracefully.
        """
        client.post("/api/v1/sensors/ingest", json={
            "sensor_id": "esp32_zone_01",
            "soil_moisture": 45.0,
            "temperature": 26.0,
            "humidity": 65.0,
        })

        image_bytes = create_synthetic_leaf_image_bytes()

        with patch("main.fetch_weather_async", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = RuntimeError("Simulated unexpected network failure")
            response = client.post(
                "/api/v1/farm/analyze",
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["weather_available"] is False
        assert data["weather"] is None
