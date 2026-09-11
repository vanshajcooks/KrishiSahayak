"""
Smart Farming Assistant — FastAPI Backend Service (SIH 26180)
Provides sensor telemetry ingestion, strict Pydantic validation, SQLite persistence, and state queries.
"""

import sys

if __name__ == "backend.main":
    sys.modules.setdefault("main", sys.modules[__name__])
elif __name__ == "main":
    sys.modules.setdefault("backend.main", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "main", sys.modules[__name__])
    except ImportError:
        pass

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware


try:
    from backend.analysis import build_unified_analysis
    from backend.database import get_db_path, get_latest_reading, init_db, insert_reading
    from backend.decision import evaluate_reading
    from backend.schemas import (
        DecisionReport,
        HealthCheckResponse,
        LatestSensorResponse,
        SensorIngestResponse,
        SensorReading,
        UnifiedAnalysisResponse,
        VisionPredictionResponse,
        WeatherData,
    )
    from backend.vision import load_model, predict_image
    from backend.weather import fetch_weather_async
except ImportError:
    from analysis import build_unified_analysis
    from database import get_db_path, get_latest_reading, init_db, insert_reading
    from decision import evaluate_reading
    from schemas import (
        DecisionReport,
        HealthCheckResponse,
        LatestSensorResponse,
        SensorIngestResponse,
        SensorReading,
        UnifiedAnalysisResponse,
        VisionPredictionResponse,
        WeatherData,
    )
    from vision import load_model, predict_image
    from weather import fetch_weather_async


logger = logging.getLogger("smart_farming.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes the SQLite database, tables, and pre-warms the YOLO vision model upon startup.
    """
    init_db()
    try:
        load_model()
    except Exception as exc:
        logger.warning("YOLO vision model could not be pre-loaded at startup: %s", exc)
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


@app.post(
    "/api/v1/vision/predict",
    response_model=VisionPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Vision AI"],
    summary="Predict Crop Disease from Leaf Image",
)
async def predict_crop_disease(
    file: UploadFile = File(..., description="Uploaded crop leaf image (JPEG, PNG)"),
    conf: float = Query(default=0.25, ge=0.05, le=1.0, description="Minimum confidence threshold"),
) -> VisionPredictionResponse:
    """
    Runs YOLO11 crop-disease detection on an uploaded leaf photograph.
    Returns detected crops, conditions (disease or healthy), confidence, bounding boxes,
    count, and inference execution time in milliseconds.
    """
    # 1. Validate content-type if provided
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file content-type '{file.content_type}' is not an image",
        )

    # 2. Read file bytes
    try:
        image_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded image file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded image file",
        )

    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty",
        )

    # 3. Execute YOLO vision inference
    try:
        predictions, inference_time_ms = predict_image(image_bytes=image_bytes, conf=conf)
    except FileNotFoundError as exc:
        logger.error("Vision model weights missing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOLO vision model weights not found",
        )
    except ValueError as exc:
        logger.warning("Invalid image file uploaded: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error during vision inference: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing image inference",
        )

    return VisionPredictionResponse(
        status="success",
        model="yolo11n-crop-disease",
        predictions=predictions,
        count=len(predictions),
        inference_time_ms=inference_time_ms,
    )


@app.post(
    "/api/v1/farm/analyze",
    response_model=UnifiedAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Integrated Farm Analysis"],
    summary="Unified Multimodal Farm Analysis (Leaf Vision + Sensor Decisions)",
)
async def analyze_farm(
    file: UploadFile = File(..., description="Uploaded crop leaf image (JPEG, PNG)"),
    sensor_id: Optional[str] = Query(default=None, description="Optional sensor ID to filter telemetry"),
    form_sensor_id: Optional[str] = Form(default=None, alias="sensor_id", description="Optional sensor ID passed via form-data"),
    conf: float = Query(default=0.25, ge=0.05, le=1.0, description="Minimum confidence threshold for vision model"),
    form_conf: Optional[float] = Form(default=None, alias="conf", description="Confidence threshold passed via form-data"),
    db_path: Path = Depends(get_db_path),
) -> UnifiedAnalysisResponse:
    """
    Unified multimodal analysis endpoint.
    1. Runs YOLO crop-disease detection on the uploaded leaf image.
    2. Queries the latest sensor telemetry from SQLite (optionally filtered by sensor_id).
    3. Evaluates sensor telemetry against the deterministic agronomic decision engine.
    4. Synthesizes cross-modal insights correlating leaf pathology with field microclimate.
    Gracefully handles missing or unavailable sensor telemetry without failing the request.
    """
    effective_sensor_id = form_sensor_id if form_sensor_id is not None else sensor_id
    effective_conf = form_conf if form_conf is not None else conf

    # 1. Validate file content-type if provided
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file content-type '{file.content_type}' is not an image",
        )

    # 2. Read file bytes
    try:
        image_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded image file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded image file",
        )

    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty",
        )

    # 3. Execute YOLO vision inference
    try:
        predictions, inference_time_ms = predict_image(image_bytes=image_bytes, conf=effective_conf)
    except FileNotFoundError as exc:
        logger.error("Vision model weights missing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOLO vision model weights not found",
        )
    except ValueError as exc:
        logger.warning("Invalid image file uploaded: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error during vision inference: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing image inference",
        )

    vision_response = VisionPredictionResponse(
        status="success",
        model="yolo11n-crop-disease",
        predictions=predictions,
        count=len(predictions),
        inference_time_ms=inference_time_ms,
    )

    # 4. Retrieve latest sensor telemetry from SQLite
    sensor_reading = None
    try:
        sensor_reading = get_latest_reading(sensor_id=effective_sensor_id, db_path=db_path)
    except Exception as exc:
        logger.warning("Failed to query sensor reading from SQLite during unified analysis: %s", exc)
        # Continue gracefully with sensor_reading = None

    # 5. Evaluate sensor decision if telemetry is available
    decision_report = None
    if sensor_reading is not None:
        try:
            decision_report = evaluate_reading(sensor_reading)
        except Exception as exc:
            logger.warning("Failed to evaluate decision on sensor reading: %s", exc)

    # 6. Fetch live/forecast weather telemetry (optional third modality)
    weather_telemetry = None
    try:
        weather_telemetry = await fetch_weather_async()
    except Exception as exc:
        logger.warning("Failed to fetch weather telemetry during unified analysis: %s", exc)

    # 7. Synthesize multimodal response
    return build_unified_analysis(
        vision=vision_response,
        sensor_reading=sensor_reading,
        decision=decision_report,
        weather=weather_telemetry,
    )


@app.get(
    "/api/v1/weather/current",
    response_model=WeatherData,
    status_code=status.HTTP_200_OK,
    tags=["Weather"],
    summary="Get Current Weather & Forecast for Farm Location",
)
async def get_current_weather() -> WeatherData:
    """
    Retrieves real-time weather and forecast data for the configured farm location.
    Returns HTTP 503 if WEATHER_API_KEY is not configured or external service is unreachable.
    """
    weather = await fetch_weather_async()
    if weather is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service unavailable. Check WEATHER_API_KEY and network connectivity.",
        )
    return weather


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

