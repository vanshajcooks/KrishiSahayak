# API Specification — Smart Farming Assistant

**Version**: 0.1.0  
**Base URL**: `http://<server-ip>:8000`  
**Protocol**: HTTP/1.1  
**Data Format**: JSON (`application/json`)

---

## 1. System Endpoints

### 1.1 Health Check
Verifies backend service availability and version.

* **Endpoint**: `GET /health`
* **Headers**: None required
* **Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "service": "smart-farming-backend",
    "version": "0.1.0"
  }
  ```

---

## 2. Sensor Telemetry Endpoints

### 2.1 Ingest Sensor Telemetry
Called periodically by the ESP32 sensor controller node to submit telemetry.

* **Endpoint**: `POST /api/v1/sensors/ingest`
* **Headers**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "sensor_id": "esp32_zone_1",
    "soil_moisture": 34.2,
    "temperature": 28.5,
    "humidity": 62.0,
    "battery_voltage": 3.95
  }
  ```
* **Validation Rules**:
  * `sensor_id`: string, 1 to 50 characters, required.
  * `soil_moisture`: float, range `0.0` to `100.0` (percentage), required.
  * `temperature`: float, range `-20.0` to `65.0` (°C), required.
  * `humidity`: float, range `0.0` to `100.0` (percentage), required.
  * `battery_voltage`: float, range `2.0` to `6.0` (Volts), optional (persists as NULL if omitted).
  * `rain_level`: float, range `0.0` to `100.0` (percentage), optional additive field for rain sensor.
* **Storage**:
  * Persisted locally in SQLite: `backend/data/smart_farming.db` (table `sensor_telemetry`).
  * Designed for offline-first Raspberry Pi field deployment; SQLite files are excluded from Git.
* **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Telemetry received and validated",
    "data": {
      "sensor_id": "esp32_zone_1",
      "soil_moisture": 34.2,
      "temperature": 28.5,
      "humidity": 62.0,
      "battery_voltage": 3.95,
      "received_at": "2026-09-08T03:30:00.000Z"
    }
  }
  ```
* **Error Response (422 Unprocessable Entity)**:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "soil_moisture"],
        "msg": "Input should be less than or equal to 100",
        "type": "less_than_equal"
      }
    ]
  }
  ```

---

### 2.2 Get Latest Sensor Reading
Polled or fetched by the Next.js frontend to render current live dashboard metrics.

* **Endpoint**: `GET /api/v1/sensors/latest`
* **Query Parameters**:
  * `sensor_id` (optional): Filter by specific sensor node ID. Defaults to latest overall.
* **Response (200 OK)**:
  Existing required response fields remain unchanged. `rain_level` is an optional additive field.
  ```json
  {
    "sensor_id": "esp32_zone_1",
    "soil_moisture": 34.2,
    "temperature": 28.5,
    "humidity": 62.0,
    "battery_voltage": 3.95,
    "rain_level": 0.0,
    "timestamp": "2026-09-08T03:30:00.000Z"
  }
  ```
* **Response (404 Not Found)** — If no readings have been ingested yet:
  ```json
  {
    "detail": "No sensor readings available yet"
  }
  ```

---

## 3. Future Planned Endpoints (Milestone 3 & Beyond)

### 3.1 Decision Recommendations
* **Endpoint**: `GET /api/v1/decision/recommendations`
* **Purpose**: Returns current agricultural advisories (irrigation recommendation, weather warnings, fungal disease risk).
* **Expected Response Schema**:
  ```json
  {
    "timestamp": "2026-09-08T03:30:00Z",
    "irrigation_status": "IRRIGATION_NEEDED",
    "message": "Soil moisture is 22%. Irrigate with 15mm of water before noon.",
    "risk_level": "moderate",
    "weather_summary": "Clear skies, rain expected in 36 hours"
  }
  ```

### 3.2 AI Disease Detection
* **Endpoint**: `POST /api/v1/ai/predict`
* **Format**: `multipart/form-data` with an image file
* **Purpose**: Runs YOLO11n ONNX inference on an uploaded leaf photograph and returns bounding boxes, detected disease class, and confidence score.
