"""
Smart Farming Assistant — Rule-Based Decision Engine (SIH 26180)
Provides deterministic, explainable agronomic decisions and risk evaluations
derived purely from local sensor telemetry (soil moisture, temperature, humidity, rain level).

Design principles:
- 100% pure evaluation: Zero database I/O or network dependencies.
- Explainable heuristics: Plain threshold-based evaluations without speculative claims.
- Rain override: Rain detection (>= 60.0%) overrides irrigation recommendations.
- Scientific framing: Microclimate evaluations indicate favorable conditions for fungal disease,
  never claiming confirmed leaf disease (which requires the vision model).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Union

from schemas import (
    ActionCategory,
    DecisionReport,
    IrrigationAction,
    MoistureStatus,
    RiskLevel,
    SensorReading,
)

# ============================================================================
# Agronomic Threshold Constants
# ============================================================================
MOISTURE_DRY_THRESHOLD: float = 30.0        # < 30% indicates water deficit
MOISTURE_WET_THRESHOLD: float = 70.0        # > 70% indicates potential waterlogging
RAIN_DETECTED_THRESHOLD: float = 60.0       # >= 60% calibrated rain sensor threshold
TEMP_HIGH_HEAT_THRESHOLD: float = 35.0      # > 35°C indicates high heat stress
TEMP_WARM_MIN: float = 24.0                 # Fungal germination lower temp boundary
TEMP_WARM_MAX: float = 32.0                 # Fungal germination upper temp boundary
HUMIDITY_HIGH_FUNGAL_THRESHOLD: float = 80.0  # >= 80% humidity creates high fungal risk microclimate
HUMIDITY_MODERATE_FUNGAL_THRESHOLD: float = 70.0  # >= 70% humidity creates moderate risk


def evaluate_reading(reading: Union[Dict[str, Any], SensorReading]) -> DecisionReport:
    """
    Pure evaluation function. Evaluates a single telemetry reading against
    agronomic rules and returns a structured DecisionReport.
    """
    # Extract values whether input is dict or Pydantic model
    if isinstance(reading, SensorReading):
        sensor_id = reading.sensor_id
        temperature = reading.temperature
        humidity = reading.humidity
        soil_moisture = reading.soil_moisture
        rain_level = reading.rain_level
        timestamp = reading.timestamp or datetime.now(timezone.utc)
    else:
        sensor_id = reading.get("sensor_id", "unknown_sensor")
        temperature = float(reading.get("temperature", 0.0))
        humidity = float(reading.get("humidity", 0.0))
        soil_moisture = float(reading.get("soil_moisture", 0.0))
        raw_rain = reading.get("rain_level")
        rain_level = float(raw_rain) if raw_rain is not None else None
        ts = reading.get("timestamp")
        if isinstance(ts, datetime):
            timestamp = ts
        elif isinstance(ts, str):
            timestamp = datetime.fromisoformat(ts)
        else:
            timestamp = datetime.now(timezone.utc)

    # ------------------------------------------------------------------------
    # 1. Rain Detection & Override Evaluation
    # ------------------------------------------------------------------------
    is_raining = rain_level is not None and rain_level >= RAIN_DETECTED_THRESHOLD

    # ------------------------------------------------------------------------
    # 2. Soil Moisture Classification
    # ------------------------------------------------------------------------
    if soil_moisture < MOISTURE_DRY_THRESHOLD:
        soil_moisture_status = MoistureStatus.LOW
        water_stress_level = RiskLevel.HIGH
        moisture_reason = (
            f"Soil moisture ({soil_moisture:.1f}%) is below the {MOISTURE_DRY_THRESHOLD:.1f}% threshold."
        )
    elif soil_moisture <= MOISTURE_WET_THRESHOLD:
        soil_moisture_status = MoistureStatus.OPTIMAL
        water_stress_level = RiskLevel.LOW
        moisture_reason = (
            f"Soil moisture ({soil_moisture:.1f}%) is in the optimal range "
            f"({MOISTURE_DRY_THRESHOLD:.1f}% to {MOISTURE_WET_THRESHOLD:.1f}%)."
        )
    else:
        soil_moisture_status = MoistureStatus.HIGH
        water_stress_level = RiskLevel.MEDIUM
        moisture_reason = (
            f"Soil moisture ({soil_moisture:.1f}%) exceeds the {MOISTURE_WET_THRESHOLD:.1f}% threshold."
        )

    # ------------------------------------------------------------------------
    # 3. Irrigation Recommendation & Rain Override
    # ------------------------------------------------------------------------
    if is_raining:
        irrigation_action = IrrigationAction.DELAY_IRRIGATION_RAIN_DETECTED
        action_title = "Rain Detected — Delay Irrigation"
        action_subtitle = "Active or recent rainfall detected by sensor."
        primary_action = "Delay planned irrigation to conserve water and prevent waterlogging."
        action_category = (
            ActionCategory.RECOMMENDED if soil_moisture_status == MoistureStatus.LOW else ActionCategory.NORMAL
        )
        assert rain_level is not None
        rain_reason = (
            f"Rain sensor ({rain_level:.1f}%) indicates active or recent rainfall "
            f"(>= {RAIN_DETECTED_THRESHOLD:.1f}% threshold)."
        )
    else:
        if soil_moisture_status == MoistureStatus.LOW:
            irrigation_action = IrrigationAction.IRRIGATE_SOON
            action_category = ActionCategory.ACTION_REQUIRED
            action_title = "Irrigation Needed"
            action_subtitle = "Soil moisture is below optimal threshold."
            primary_action = "Irrigate the field soon."
        elif soil_moisture_status == MoistureStatus.OPTIMAL:
            irrigation_action = IrrigationAction.NO_IRRIGATION_NEEDED
            action_category = ActionCategory.NORMAL
            action_title = "Soil Moisture is Optimal"
            action_subtitle = "Adequate water reserve present in soil."
            primary_action = "Maintain regular field monitoring."
        else:  # MoistureStatus.HIGH
            irrigation_action = IrrigationAction.OVERWATERING_WARNING
            action_category = ActionCategory.RECOMMENDED
            action_title = "High Soil Moisture Warning"
            action_subtitle = "Excess water detected in root zone."
            primary_action = "Check field drainage channels to prevent standing water."

        if rain_level is not None:
            rain_reason = (
                f"Rain sensor ({rain_level:.1f}%) indicates dry conditions "
                f"(< {RAIN_DETECTED_THRESHOLD:.1f}% threshold)."
            )
        else:
            rain_reason = "No rain sensor reading provided."

    # ------------------------------------------------------------------------
    # 4. Thermal Stress Evaluation
    # ------------------------------------------------------------------------
    if temperature > TEMP_HIGH_HEAT_THRESHOLD:
        heat_stress_level = RiskLevel.HIGH
        temp_reason = (
            f"Ambient temperature ({temperature:.1f}°C) is above the {TEMP_HIGH_HEAT_THRESHOLD:.1f}°C threshold."
        )
    elif temperature > 30.0:
        heat_stress_level = RiskLevel.MEDIUM
        temp_reason = (
            f"Ambient temperature ({temperature:.1f}°C) is elevated (between 30.0°C and {TEMP_HIGH_HEAT_THRESHOLD:.1f}°C)."
        )
    elif temperature >= 15.0:
        heat_stress_level = RiskLevel.LOW
        temp_reason = (
            f"Ambient temperature ({temperature:.1f}°C) is within normal range (15.0°C to 30.0°C)."
        )
    else:
        heat_stress_level = RiskLevel.MEDIUM
        temp_reason = (
            f"Ambient temperature ({temperature:.1f}°C) is below the 15.0°C threshold."
        )

    # ------------------------------------------------------------------------
    # 5. Fungal Microclimate Risk Evaluation
    # Note: Evaluates microclimate favorability, never claims leaf disease presence.
    # ------------------------------------------------------------------------
    if humidity >= HUMIDITY_HIGH_FUNGAL_THRESHOLD and (TEMP_WARM_MIN <= temperature <= TEMP_WARM_MAX):
        disease_risk_level = RiskLevel.HIGH
        disease_reason = (
            f"High humidity ({humidity:.1f}%) and warm temperature ({temperature:.1f}°C) "
            f"create favorable conditions for fungal disease."
        )
    elif humidity >= HUMIDITY_MODERATE_FUNGAL_THRESHOLD and (20.0 <= temperature <= 35.0):
        disease_risk_level = RiskLevel.MEDIUM
        disease_reason = (
            f"Elevated humidity ({humidity:.1f}%) creates moderately favorable conditions for fungal development."
        )
    else:
        disease_risk_level = RiskLevel.LOW
        disease_reason = "Microclimate conditions are not favorable for fungal disease development."

    # Synthesize factual reason list
    reasons: List[str] = [moisture_reason, rain_reason, temp_reason, disease_reason]

    return DecisionReport(
        sensor_id=sensor_id,
        timestamp=timestamp,
        soil_moisture_status=soil_moisture_status,
        irrigation_action=irrigation_action,
        action_category=action_category,
        action_title=action_title,
        action_subtitle=action_subtitle,
        primary_action=primary_action,
        water_stress_level=water_stress_level,
        heat_stress_level=heat_stress_level,
        disease_risk_level=disease_risk_level,
        reasons=reasons,
    )
