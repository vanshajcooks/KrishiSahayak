"""
Smart Farming Assistant — Multimodal Farm Analysis Subsystem (SIH 26180)
Fuses vision AI crop disease detections with localized IoT sensor telemetry
and agronomic rule-based decisions into integrated, actionable farm intelligence.

Design principles:
- Modularity: Synthesis logic is decoupled from FastAPI routing and transport layers.
- Graceful degradation: Functions seamlessly whether sensor readings are available or missing.
- Scientific accuracy: Correlates detected leaf pathology with microclimate moisture and humidity.
"""

import sys

if __name__ == "backend.analysis":
    sys.modules.setdefault("analysis", sys.modules[__name__])
elif __name__ == "analysis":
    sys.modules.setdefault("backend.analysis", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "analysis", sys.modules[__name__])
    except ImportError:
        pass

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


try:
    from backend.schemas import (
        DecisionReport,
        LatestSensorResponse,
        UnifiedAnalysisResponse,
        VisionPredictionResponse,
        WeatherData,
    )
except ImportError:
    from schemas import (
        DecisionReport,
        LatestSensorResponse,
        UnifiedAnalysisResponse,
        VisionPredictionResponse,
        WeatherData,
    )



def synthesize_farm_insights(
    vision: VisionPredictionResponse,
    decision: Optional[DecisionReport],
    sensor_telemetry: Optional[LatestSensorResponse],
    weather: Optional[WeatherData] = None,
) -> List[str]:
    """
    Synthesizes integrated, cross-modal insights combining leaf vision detections,
    localized environmental and soil sensor data, and regional weather forecasts.
    """
    insights: List[str] = []

    # ------------------------------------------------------------------------
    # 1. Vision AI Analysis Summary
    # ------------------------------------------------------------------------
    has_disease = False
    condition_name = "Healthy"
    if vision.count == 0:
        insights.append(
            "Vision AI: No foliar disease symptoms detected on the leaf sample above confidence threshold."
        )
    else:
        top_pred = max(vision.predictions, key=lambda p: p.confidence)
        crop_name = top_pred.crop.capitalize()
        condition_name = top_pred.condition.replace("_", " ").title()
        conf_pct = int(round(top_pred.confidence * 100))

        if top_pred.condition == "healthy":
            insights.append(
                f"Vision AI: Leaf identified as healthy {crop_name} foliage ({conf_pct}% confidence)."
            )
        else:
            has_disease = True
            insights.append(
                f"Vision AI: Detected possible {condition_name} on {crop_name} ({conf_pct}% confidence)."
            )

    # ------------------------------------------------------------------------
    # 2. Localized Sensor Telemetry & Agronomic Decision Integration
    # ------------------------------------------------------------------------
    if sensor_telemetry is None or decision is None:
        insights.append(
            "Sensor telemetry unavailable: Field sensor telemetry was not found or has not been ingested yet."
        )
    else:
        insights.append(
            f"Sensor Context: Soil moisture is {sensor_telemetry.soil_moisture:.1f}% ({decision.soil_moisture_status.value}), "
            f"ambient temp {sensor_telemetry.temperature:.1f}°C, and humidity {sensor_telemetry.humidity:.1f}%."
        )

        if has_disease:
            if decision.disease_risk_level.value in ("HIGH", "MEDIUM"):
                insights.append(
                    "Cross-modal alert: Foliar symptoms detected alongside high ambient humidity. "
                    "Current microclimate favors fungal proliferation; avoid overhead irrigation and improve canopy aeration."
                )
            if decision.irrigation_action.value == "IRRIGATE_SOON":
                insights.append(
                    "Irrigation note: Soil moisture is low, but foliar disease symptoms are present. "
                    "Use ground or drip irrigation to hydrate roots without splashing water onto infected foliage."
                )
            elif decision.irrigation_action.value == "DELAY_IRRIGATION_RAIN_DETECTED":
                insights.append(
                    "Rain advisory: Active rain detected by sensor while foliar disease is present. "
                    "Ensure proper field drainage to prevent waterlogging and fungal spore dispersal."
                )
        else:
            if decision.irrigation_action.value == "IRRIGATE_SOON":
                insights.append(
                    "Crop foliage appears healthy, but soil moisture is low. Proceed with scheduled irrigation."
                )
            elif decision.irrigation_action.value == "DELAY_IRRIGATION_RAIN_DETECTED":
                insights.append(
                    "Foliage appears healthy and sensor rain is detected. Irrigation is paused to conserve water."
                )
            elif decision.irrigation_action.value == "OVERWATERING_WARNING":
                insights.append(
                    "Soil moisture is excessively high. Monitor field drainage to prevent root rot."
                )

    # ------------------------------------------------------------------------
    # 3. Weather Forecast Integration (Optional Third Modality)
    # ------------------------------------------------------------------------
    if weather is not None:
        # General Weather Context
        insights.append(
            f"Weather Forecast ({weather.location}): {weather.condition}, {weather.temperature:.1f}°C, "
            f"{weather.humidity:.0f}% humidity, {weather.rain_probability:.0f}% rain chance."
        )

        # Weather + Irrigation Correlation
        is_rain_likely = weather.is_rain_forecasted or weather.rain_probability >= 50.0 or "rain" in weather.condition.lower()

        if decision is not None and decision.irrigation_action.value == "IRRIGATE_SOON":
            if is_rain_likely:
                insights.append(
                    f"Weather advisory: Rain forecasted ({weather.rain_probability:.0f}% chance). "
                    f"Delay planned irrigation to conserve water and prevent nutrient leaching."
                )
            else:
                insights.append(
                    f"Weather confirmation: Dry forecast ({weather.condition}, {weather.rain_probability:.0f}% rain chance). "
                    f"Safe to proceed with scheduled irrigation."
                )

        # Weather + Disease Proliferation Alert
        if has_disease and (is_rain_likely or weather.humidity >= 75.0):
            insights.append(
                f"Weather & Pathology alert: Incoming high humidity/rain ({weather.humidity:.0f}% RH) will accelerate "
                f"spore dispersal for {condition_name}. Apply approved protective measures before rainfall begins."
            )

        # Weather Thermal Stress Alert
        if weather.temperature >= 35.0:
            insights.append(
                f"Weather thermal alert: Elevated temperatures ({weather.temperature:.1f}°C) expected. "
                f"Increased evapotranspiration will dry soil faster; monitor root zone moisture."
            )

    return insights


def build_unified_analysis(
    vision: VisionPredictionResponse,
    sensor_reading: Optional[Dict[str, Any]],
    decision: Optional[DecisionReport],
    weather: Optional[WeatherData] = None,
) -> UnifiedAnalysisResponse:
    """
    Constructs a UnifiedAnalysisResponse from vision, sensor, and optional weather subsystems.
    Gracefully handles presence or absence of sensor reading and weather telemetry.
    """
    sensor_telemetry: Optional[LatestSensorResponse] = None
    if sensor_reading is not None:
        sensor_telemetry = LatestSensorResponse(
            sensor_id=sensor_reading["sensor_id"],
            soil_moisture=sensor_reading["soil_moisture"],
            temperature=sensor_reading["temperature"],
            humidity=sensor_reading["humidity"],
            battery_voltage=sensor_reading.get("battery_voltage"),
            rain_level=sensor_reading.get("rain_level"),
            timestamp=sensor_reading["timestamp"],
        )

    insights = synthesize_farm_insights(
        vision=vision,
        decision=decision,
        sensor_telemetry=sensor_telemetry,
        weather=weather,
    )

    return UnifiedAnalysisResponse(
        status="success",
        timestamp=datetime.now(timezone.utc),
        vision=vision,
        sensor_available=sensor_telemetry is not None,
        sensor_telemetry=sensor_telemetry,
        decision=decision,
        weather_available=weather is not None,
        weather=weather,
        insights=insights,
    )

