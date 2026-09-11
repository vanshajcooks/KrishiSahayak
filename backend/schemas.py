"""
Pydantic Schemas for Smart Farming Assistant (SIH 26180)
Defines strict data contracts for sensor telemetry, responses, and health checks.
"""

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


