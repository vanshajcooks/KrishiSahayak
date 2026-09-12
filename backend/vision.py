"""
Smart Farming Assistant — Vision Inference Subsystem (SIH 26180)
Provides YOLO11-based crop disease and health detection from leaf photographs.

Design principles:
- Isolated vision module: Model loading and inference logic decoupled from API routing.
- Path priority: YOLO_MODEL_PATH environment variable → backend/models/best.pt.
- Memory caching: Model is loaded and cached once in memory rather than per request.
- Robust validation: Verifies image format with Pillow and handles errors gracefully.
"""

import sys

if __name__ == "backend.vision":
    sys.modules.setdefault("vision", sys.modules[__name__])
elif __name__ == "vision":
    sys.modules.setdefault("backend.vision", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "vision", sys.modules[__name__])
    except ImportError:
        pass

import io
import os
import time
import logging
from pathlib import Path
from typing import Any, List, Optional, Tuple


from PIL import Image

try:
    from backend.schemas import DiseasePrediction
except ImportError:
    from schemas import DiseasePrediction


logger = logging.getLogger("smart_farming.vision")

# Default model location: backend/models/best.pt
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "best.pt"

# Global in-memory model cache
_cached_model: Optional[Any] = None

# Mapping from trained YOLO class labels to standardized (crop, condition) tuples
CLASS_MAPPING = {
    "Tomato Early blight": ("tomato", "early_blight"),
    "Tomato Septoria leaf spot": ("tomato", "septoria_leaf_spot"),
    "Tomato leaf": ("tomato", "healthy"),
    "Tomato bacterial spot": ("tomato", "bacterial_spot"),
    "Tomato leaf late blight": ("tomato", "late_blight"),
    "Potato leaf early blight": ("potato", "early_blight"),
    "Potato leaf late blight": ("potato", "late_blight"),
    "Corn leaf blight": ("corn", "leaf_blight"),
    "Corn rust leaf": ("corn", "rust"),
    "Apple Scab Leaf": ("apple", "scab"),
}


def get_model_path() -> Path:
    """
    Resolves the model weights path.
    Priority:
      1. YOLO_MODEL_PATH environment variable
      2. backend/models/best.pt
    """
    env_path = os.environ.get("YOLO_MODEL_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_MODEL_PATH


def load_model() -> Any:
    """
    Loads and caches the YOLO vision model in memory.
    Thread-safe and cached across requests.
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    model_path = get_model_path()
    if not model_path.exists():
        logger.error("YOLO vision model weights not found at: %s", model_path)
        raise FileNotFoundError(f"YOLO vision model not found at path: {model_path}")

    logger.info("Loading YOLO vision model from: %s", model_path)
    from ultralytics import YOLO

    _cached_model = YOLO(str(model_path))
    return _cached_model


def warmup_model(imgsz: int = 640) -> bool:
    """
    Performs one dummy YOLO inference on a blank synthetic image to initialize
    PyTorch CPU execution kernels and the Ultralytics predictor pipeline.
    Ensures that subsequent user-facing inference requests execute with warm latency.
    """
    model = load_model()
    dummy_img = Image.new("RGB", (imgsz, imgsz), color=(128, 128, 128))
    model.predict(
        source=dummy_img,
        imgsz=imgsz,
        save=False,
        verbose=False,
    )
    logger.info("YOLO vision model warmed up successfully.")
    return True


def predict_image(
    image_bytes: bytes,
    conf: float = 0.25,
    imgsz: int = 640,
) -> Tuple[List[DiseasePrediction], float]:
    """
    Executes YOLO inference on an uploaded image.
    Validates image bytes, parses bounding boxes, maps classes to (crop, condition),
    and measures inference execution time in milliseconds.
    """
    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Image data is empty")

    # Validate that bytes represent a valid readable image format
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        # Re-open after verify() to reset file pointer for inference
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:
        raise ValueError(f"Uploaded file could not be parsed as a valid image: {exc}")

    model = load_model()
    start_time = time.perf_counter()

    # Run inference in-memory without saving images to disk
    results = model.predict(
        source=image,
        imgsz=imgsz,
        conf=conf,
        save=False,
        verbose=False,
    )

    inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    predictions: List[DiseasePrediction] = []

    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            if class_name in CLASS_MAPPING:
                crop, condition = CLASS_MAPPING[class_name]
            else:
                crop, condition = "unknown", class_name.lower().replace(" ", "_")

            predictions.append(
                DiseasePrediction(
                    crop=crop,
                    condition=condition,
                    confidence=round(confidence, 3),
                    bbox=[round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                )
            )

    return predictions, inference_time_ms
