"""
Pydantic Schemas for Smart Farming Assistant (SIH 26180)
Defines strict data contracts for sensor telemetry, responses, and health checks.
"""

import sys

if __name__ == "backend.schemas":
    sys.modules.setdefault("schemas", sys.modules[__name__])
elif __name__ == "schemas":
    sys.modules.setdefault("backend.schemas", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "schemas", sys.modules[__name__])
    except ImportError:
        pass

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field



class HealthCheckResponse(BaseModel):
    """Schema for service health verification."""
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="smart-farming-backend", description="Microservice identifier")
    version: str = Field(default="0.1.0", description="API contract version")


class SensorReading(BaseModel):
    """
    Schema for incoming ESP32 sensor telemetry packet.
    Validates physical plausible ranges for agricultural sensors.
    """
    sensor_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the sensor node (e.g. 'esp32_zone_1')",
        examples=["esp32_field_01"]
    )
    soil_moisture: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Volumetric soil moisture percentage (0.0% to 100.0%)",
        examples=[42.5]
    )
    temperature: float = Field(
        ...,
        ge=-20.0,
        le=65.0,
        description="Ambient temperature in degrees Celsius (-20.0 to 65.0)",
        examples=[28.4]
    )
    humidity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Relative ambient humidity percentage (0.0% to 100.0%)",
        examples=[64.0]
    )
    battery_voltage: Optional[float] = Field(
        default=None,
        ge=2.0,
        le=6.0,
        description="Battery voltage of the field node in Volts (typically 3.0V - 4.2V)",
        examples=[3.95]
    )
    rain_level: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Normalized rain sensor level (0.0 to 100.0)",
        examples=[0.0]
    )
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the reading was taken or received"
    )


class SensorIngestResponse(BaseModel):
    """Schema for acknowledgement returned to ESP32 upon successful ingest."""
    status: str = Field(default="success", description="Status code string")
    message: str = Field(default="Telemetry received and validated", description="Human-readable acknowledgement")
    data: SensorReading


class LatestSensorResponse(BaseModel):
    """
    Schema returned to frontend dashboard representing the current state.
    Existing required response fields remain unchanged. rain_level is an optional additive field.
    """
    sensor_id: str
    soil_moisture: float
    temperature: float
    humidity: float
    battery_voltage: Optional[float] = None
    rain_level: Optional[float] = None
    timestamp: datetime


class MoistureStatus(str, Enum):
    LOW = "LOW"
    OPTIMAL = "OPTIMAL"
    HIGH = "HIGH"


class IrrigationAction(str, Enum):
    IRRIGATE_SOON = "IRRIGATE_SOON"
    NO_IRRIGATION_NEEDED = "NO_IRRIGATION_NEEDED"
    OVERWATERING_WARNING = "OVERWATERING_WARNING"
    DELAY_IRRIGATION_RAIN_DETECTED = "DELAY_IRRIGATION_RAIN_DETECTED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionCategory(str, Enum):
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    NORMAL = "NORMAL"


class DecisionReport(BaseModel):
    """
    Structured decision output from the rule-based decision engine.
    Derived from validated sensor telemetry (soil moisture, temperature, humidity, rain level).
    """
    sensor_id: str
    timestamp: datetime
    soil_moisture_status: MoistureStatus
    irrigation_action: IrrigationAction
    action_category: ActionCategory
    action_title: str
    action_subtitle: str
    primary_action: str
    water_stress_level: RiskLevel
    heat_stress_level: RiskLevel
    disease_risk_level: RiskLevel
    reasons: List[str]


class DiseasePrediction(BaseModel):
    """Individual crop disease or health detection."""
    crop: str = Field(..., description="Crop type (e.g. 'tomato', 'potato', 'corn', 'apple')")
    condition: str = Field(..., description="Condition or disease name (e.g. 'early_blight', 'late_blight', 'healthy')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="Bounding box [x1, y1, x2, y2]")


class VisionPredictionResponse(BaseModel):
    """Response returned by the crop disease vision inference endpoint."""
    status: str = Field(default="success", description="Status code string")
    model: str = Field(default="yolo11n-crop-disease", description="Model identifier")
    predictions: List[DiseasePrediction] = Field(default_factory=list, description="List of detected disease instances")
    count: int = Field(..., description="Number of detected instances")
    inference_time_ms: float = Field(..., description="Inference execution time in milliseconds")


class WeatherForecastItem(BaseModel):
    """Daily or upcoming period weather forecast item."""
    time: str = Field(..., description="Timestamp or day label (e.g. 'Today', 'Tomorrow', 'Day 3')")
    temp_max: float = Field(..., description="Maximum expected temperature in Celsius")
    temp_min: float = Field(..., description="Minimum expected temperature in Celsius")
    condition: str = Field(..., description="Short weather condition (e.g. 'Rain', 'Sunny', 'Cloudy')")
    rain_probability: float = Field(..., ge=0.0, le=100.0, description="Precipitation probability percentage (0 to 100)")


class WeatherData(BaseModel):
    """Structured weather information for the farm location."""
    location: str = Field(..., description="Farm or station geographic location description")
    temperature: float = Field(..., description="Current ambient temperature in Celsius")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Current relative humidity percentage")
    condition: str = Field(..., description="Current weather condition description (e.g. 'Clear', 'Rain', 'Cloudy')")
    rain_probability: float = Field(..., ge=0.0, le=100.0, description="Precipitation probability percentage (0 to 100)")
    wind_speed_kmh: Optional[float] = Field(default=None, description="Wind speed in km/h")
    is_rain_forecasted: bool = Field(default=False, description="Whether rainfall is expected in the upcoming forecast")
    forecast: List[WeatherForecastItem] = Field(default_factory=list, description="Upcoming weather forecast periods")
    source: str = Field(default="OpenWeatherMap", description="Weather data provider source")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Weather report timestamp")


class UnifiedAnalysisResponse(BaseModel):
    """
    Unified multimodal analysis response combining vision-based leaf disease detection
    with IoT sensor telemetry, agronomic rule-based decisions, and localized weather forecasts.
    """
    status: str = Field(default="success", description="Status code string")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the unified analysis"
    )
    vision: VisionPredictionResponse = Field(
        ...,
        description="Crop disease vision inference results from YOLO model"
    )
    sensor_available: bool = Field(
        ...,
        description="Indicates whether valid sensor telemetry was available for evaluation"
    )
    sensor_telemetry: Optional[LatestSensorResponse] = Field(
        default=None,
        description="Most recent sensor telemetry reading if available"
    )
    decision: Optional[DecisionReport] = Field(
        default=None,
        description="Agronomic decision report derived from sensor telemetry if available"
    )
    weather_available: bool = Field(
        default=False,
        description="Indicates whether live weather data was successfully retrieved"
    )
    weather: Optional[WeatherData] = Field(
        default=None,
        description="Current and forecast weather data if available"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Integrated agronomic insights synthesizing vision detections with field sensor conditions and weather forecasts"
    )

