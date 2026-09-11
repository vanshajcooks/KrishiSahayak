"""
Smart Farming Assistant — FastAPI Backend Service (SIH 26180)
Provides sensor telemetry ingestion, strict Pydantic validation, SQLite persistence, and state queries.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import get_db_path, get_latest_reading, init_db, insert_reading
from decision import evaluate_reading
from schemas import (
    DecisionReport,
    HealthCheckResponse,
    LatestSensorResponse,
    SensorIngestResponse,
    SensorReading,
)

logger = logging.getLogger("smart_farming.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes the SQLite database and tables upon startup.
    """
    init_db()
    yield


app = FastAPI(
    title="Smart Farming Assistant API",
    description="Backend API for SIH 26180: Sensor Ingest, Decision Engine & Farm Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Service Health Check",
)
def health_check() -> HealthCheckResponse:
    """Returns the operational health and version of the backend service."""
    return HealthCheckResponse(
        status="healthy",
        service="smart-farming-backend",
        version="0.1.0",
    )


@app.post(
    "/api/v1/sensors/ingest",
    response_model=SensorIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors"],
    summary="Ingest Sensor Telemetry",
)
def ingest_sensor_data(
    payload: SensorReading,
    db_path: Path = Depends(get_db_path),
) -> SensorIngestResponse:
    """
    Ingests, validates, and stores incoming telemetry from an ESP32 sensor controller into SQLite.
    Validates physical plausibility ranges for soil moisture, temp, humidity, and rain level.
    """
    try:
        insert_reading(payload, db_path=db_path)
    except Exception as e:
        logger.error("Failed to persist sensor reading to SQLite: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist sensor telemetry",
        )

    return SensorIngestResponse(
        status="success",
        message="Telemetry received and validated",
        data=payload,
    )


@app.get(
    "/api/v1/sensors/latest",
    response_model=LatestSensorResponse,
    status_code=status.HTTP_200_OK,
    tags=["Sensors"],
    summary="Get Latest Sensor Reading",
)
def get_latest_sensor_data(
    sensor_id: Optional[str] = None,
    db_path: Path = Depends(get_db_path),
) -> LatestSensorResponse:
    """
    Retrieves the most recent sensor reading from SQLite.
    Optionally filters by a specific sensor_id.
    """
    try:
        reading = get_latest_reading(sensor_id=sensor_id, db_path=db_path)
    except Exception as e:
        logger.error("Failed to query latest reading from SQLite: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest sensor telemetry",
        )

    if not reading:
        if sensor_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sensor reading found for sensor_id '{sensor_id}'",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sensor readings available yet",
            )

    return LatestSensorResponse(
        sensor_id=reading["sensor_id"],
        soil_moisture=reading["soil_moisture"],
        temperature=reading["temperature"],
        humidity=reading["humidity"],
        battery_voltage=reading["battery_voltage"],
        rain_level=reading.get("rain_level"),
        timestamp=reading["timestamp"],
    )


@app.get(
    "/api/v1/decision/recommendations",
    response_model=DecisionReport,
    status_code=status.HTTP_200_OK,
    tags=["Decision Engine"],
    summary="Get Decision Recommendations",
)
def get_decision_recommendations(
    sensor_id: Optional[str] = None,
    db_path: Path = Depends(get_db_path),
) -> DecisionReport:
    """
    Retrieves the latest sensor reading from SQLite and generates an
    explainable agricultural decision report and risk evaluation.
    Optionally filters by a specific sensor_id.
    """
    try:
        reading = get_latest_reading(sensor_id=sensor_id, db_path=db_path)
    except Exception as e:
        logger.error("Failed to retrieve reading for decision engine: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sensor telemetry for decision evaluation",
        )

    if not reading:
        if sensor_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sensor reading found for sensor_id '{sensor_id}' to evaluate decisions",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sensor readings available for decision evaluation",
            )

    return evaluate_reading(reading)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
