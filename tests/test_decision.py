"""
Unit Tests for Rule-Based Decision Engine — Smart Farming Assistant (SIH 26180)
Tests pure agronomic evaluation logic and all critical boundary thresholds.
"""

import os
import sys
from datetime import datetime, timezone
import pytest

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from decision import evaluate_reading
from schemas import (
    ActionCategory,
    IrrigationAction,
    MoistureStatus,
    RiskLevel,
    SensorReading,
)


class TestSoilMoistureAndRainOverrideRules:
    """Tests soil moisture boundaries (30.0%, 70.0%) and rain override (60.0%)."""

    def test_dry_soil_triggers_irrigate_soon(self):
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 29.9,
            "temperature": 25.0,
            "humidity": 60.0,
            "rain_level": 0.0,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.LOW
        assert report.irrigation_action == IrrigationAction.IRRIGATE_SOON
        assert report.water_stress_level == RiskLevel.HIGH
        assert report.action_category == ActionCategory.ACTION_REQUIRED
        assert "below the 30.0% threshold" in report.reasons[0]

    def test_moisture_lower_boundary_optimal(self):
        # Exactly 30.0% is the lower bound of OPTIMAL
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 30.0,
            "temperature": 25.0,
            "humidity": 60.0,
            "rain_level": 0.0,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.OPTIMAL
        assert report.irrigation_action == IrrigationAction.NO_IRRIGATION_NEEDED
        assert report.water_stress_level == RiskLevel.LOW
        assert report.action_category == ActionCategory.NORMAL

    def test_moisture_upper_boundary_optimal(self):
        # Exactly 70.0% is the upper bound of OPTIMAL
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 70.0,
            "temperature": 25.0,
            "humidity": 60.0,
            "rain_level": 0.0,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.OPTIMAL
        assert report.irrigation_action == IrrigationAction.NO_IRRIGATION_NEEDED
        assert report.water_stress_level == RiskLevel.LOW

    def test_moisture_overwatering_boundary(self):
        # 70.1% exceeds the optimal boundary
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 70.1,
            "temperature": 25.0,
            "humidity": 60.0,
            "rain_level": 0.0,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.HIGH
        assert report.irrigation_action == IrrigationAction.OVERWATERING_WARNING
        assert report.water_stress_level == RiskLevel.MEDIUM
        assert report.action_category == ActionCategory.RECOMMENDED

    def test_rain_override_at_boundary_with_dry_soil(self):
        # Even with critically low soil moisture (15%), rain_level exactly 60.0% MUST override
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 15.0,
            "temperature": 24.0,
            "humidity": 80.0,
            "rain_level": 60.0,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.LOW
        assert report.irrigation_action == IrrigationAction.DELAY_IRRIGATION_RAIN_DETECTED
        assert "Rain Detected — Delay Irrigation" in report.action_title
        assert "indicates active or recent rainfall" in report.reasons[1]

    def test_rain_below_boundary_does_not_override(self):
        # Rain at 59.9% is below calibrated threshold; dry soil proceeds to IRRIGATE_SOON
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 20.0,
            "temperature": 26.0,
            "humidity": 55.0,
            "rain_level": 59.9,
        }
        report = evaluate_reading(reading)
        assert report.soil_moisture_status == MoistureStatus.LOW
        assert report.irrigation_action == IrrigationAction.IRRIGATE_SOON
        assert report.action_category == ActionCategory.ACTION_REQUIRED


class TestThermalStressRules:
    """Tests temperature boundaries (15.0°C, 30.0°C, 35.0°C)."""

    def test_high_heat_stress_above_35(self):
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 35.1,
            "humidity": 50.0,
        }
        report = evaluate_reading(reading)
        assert report.heat_stress_level == RiskLevel.HIGH
        assert "above the 35.0°C threshold" in report.reasons[2]

    def test_moderate_heat_stress_at_35_boundary(self):
        # Exactly 35.0°C is MEDIUM heat stress (not yet exceeding 35)
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 35.0,
            "humidity": 50.0,
        }
        report = evaluate_reading(reading)
        assert report.heat_stress_level == RiskLevel.MEDIUM

    def test_normal_temperature_range(self):
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 25.0,
            "humidity": 50.0,
        }
        report = evaluate_reading(reading)
        assert report.heat_stress_level == RiskLevel.LOW

    def test_cool_temperature_boundary(self):
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 14.9,
            "humidity": 50.0,
        }
        report = evaluate_reading(reading)
        assert report.heat_stress_level == RiskLevel.MEDIUM
        assert "below the 15.0°C threshold" in report.reasons[2]


class TestFungalMicroclimateRiskRules:
    """Tests fungal microclimate conditions and scientific framing."""

    def test_high_fungal_conditions_at_lower_temp_boundary(self):
        # Exactly 80.0% humidity and 24.0°C temp -> HIGH fungal microclimate
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 24.0,
            "humidity": 80.0,
        }
        report = evaluate_reading(reading)
        assert report.disease_risk_level == RiskLevel.HIGH
        assert "favorable conditions for fungal disease" in report.reasons[3]

    def test_high_fungal_conditions_at_upper_temp_boundary(self):
        # Exactly 80.0% humidity and 32.0°C temp -> HIGH fungal microclimate
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 32.0,
            "humidity": 80.0,
        }
        report = evaluate_reading(reading)
        assert report.disease_risk_level == RiskLevel.HIGH

    def test_fungal_conditions_below_humidity_boundary(self):
        # 79.9% humidity at 25.0°C -> MEDIUM (not HIGH)
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 25.0,
            "humidity": 79.9,
        }
        report = evaluate_reading(reading)
        assert report.disease_risk_level == RiskLevel.MEDIUM
        assert "moderately favorable conditions" in report.reasons[3]

    def test_dry_climate_has_low_fungal_risk(self):
        reading = {
            "sensor_id": "esp32_01",
            "soil_moisture": 50.0,
            "temperature": 26.0,
            "humidity": 45.0,
        }
        report = evaluate_reading(reading)
        assert report.disease_risk_level == RiskLevel.LOW
        assert "not favorable for fungal disease" in report.reasons[3]


class TestInputTypeCompatibility:
    """Verifies that evaluate_reading accepts both dictionaries and Pydantic models."""

    def test_evaluates_pydantic_sensor_reading_instance(self):
        reading = SensorReading(
            sensor_id="esp32_zone_2",
            soil_moisture=45.0,
            temperature=27.0,
            humidity=65.0,
            battery_voltage=3.95,
            rain_level=0.0,
            timestamp=datetime.now(timezone.utc),
        )
        report = evaluate_reading(reading)
        assert report.sensor_id == "esp32_zone_2"
        assert report.soil_moisture_status == MoistureStatus.OPTIMAL
        assert report.irrigation_action == IrrigationAction.NO_IRRIGATION_NEEDED
        assert report.water_stress_level == RiskLevel.LOW
        assert report.heat_stress_level == RiskLevel.LOW
        assert report.disease_risk_level == RiskLevel.LOW
