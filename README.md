# Smart Farming Assistant

> **Smart India Hackathon 2026 — Problem Statement 26180**  
> An intelligent, edge-capable precision agriculture system designed for smallholder farmers. Combines IoT soil/climate telemetry, heuristic decision intelligence, and on-device crop disease detection.

---

## 👥 The Team

| Name | Primary Roles & Focus | Key Responsibilities |
| :--- | :--- | :--- |
| **Siddharth** | Team Lead + Research + Documentation | Problem alignment, documentation, system architecture, presentation |
| **Vanshaj** | Web + Backend + AI/ML + Hardware/IoT | System integration, API pipelines, Pydantic schemas, hardware bridge |
| **Sneha** | Hardware / IoT | ESP32 sensor controller, wiring, calibration, telemetry payload framing |
| **Diya** | AI/ML Crop Health | Leaf disease dataset curation, YOLO11n model training, validation |
| **Aryan** | AI/ML + Frontend | Next.js dashboard UI, Recharts visualization, ONNX model inference bridge |
| **Arnav** | Climate / Risk Intelligence | Decision engine heuristics, weather API connectors, risk advisory logic |

---

## 🏗️ System Architecture

### 1. Development Architecture (Current)
During local development and prototyping:
- **ESP32 Sensor Controller**: Collects soil moisture, ambient temperature, and humidity.
- **FastAPI Backend (Local PC/Laptop)**: Validates incoming HTTP/JSON payloads, manages latest state, and prepares SQLite persistence.
- **Next.js Frontend (Local PC/Laptop)**: Connects to the local FastAPI server to display live sensor telemetry, gauges, and alerts.
- **AI/ML Development**: YOLO11n trained on leaf disease datasets and exported to ONNX format.

### 2. Field Deployment Architecture (Target)
In the actual farm environment:
- **ESP32 (Sensor Controller)**: Battery/solar-powered edge node placed in the field. Sends telemetry over local WiFi/HTTP to the gateway.
- **Raspberry Pi (Field Edge Gateway)**:
  - Runs the **FastAPI Backend** and local **SQLite Database**.
  - Hosts the **Decision Engine** (combining local sensor readings with fetched weather forecasts).
  - Hosts **ONNX Runtime Edge Inference** for crop disease detection via camera captures.
  - Serves as the local WiFi access point / hotspot or local network hub.
- **Mobile/Web Dashboard**: Farmer connects via smartphone browser to the Raspberry Pi's local web server to inspect field conditions and recommendations.

```
[Field Node: ESP32] (Sensors)
       │
       ▼  HTTP / JSON (Local WiFi)
[Field Gateway: Raspberry Pi]
       ├── FastAPI Backend (Python)
       ├── SQLite Database (Telemetry Storage)
       ├── Decision Engine (Irrigation & Climate Alerts)
       └── ONNX Edge AI (YOLO11n Leaf Disease Detection)
       │
       ▼  Local Web Interface / REST API
[Farmer Device] (Next.js Dashboard via Smartphone/Tablet)
```

---

## 📁 Repository Structure

```text
SIH/
├── .env.example              # Environment variable configuration template
├── .gitignore                # Git exclusions (Python, Node, C++, SQLite, Models)
├── README.md                 # Project overview and guide (this file)
├── ARCHITECTURE.md           # Deep-dive architectural specification
│
├── docs/                     # Technical specifications and team onboarding
│   ├── api_spec.md           # REST API endpoints & JSON schema contracts
│   └── team_responsibilities.md # Step-by-step role guides for each member
│
├── esp32/
│   └── sensor_node/          # Hardware/IoT node (Sneha & Vanshaj)
│       └── README.md         # Hardware wiring, sensor specs & telemetry format
│
├── backend/                  # Python FastAPI service (Vanshaj & Arnav)
│   ├── requirements.txt      # Minimal Python dependencies
│   ├── schemas.py            # Pydantic data validation models
│   └── main.py               # Application entrypoint (/health, /api/v1/sensors)
│
├── ai/                       # AI & Computer Vision (Diya & Aryan)
│   ├── disease_detection/    # YOLO11n dataset prep and training guide
│   └── inference/            # ONNX edge model deployment documentation
│
├── frontend/                 # Next.js web dashboard (Aryan & Vanshaj)
│   └── README.md             # UI setup guide (Tailwind, shadcn/ui, Recharts)
│
└── tests/                    # Verification suite
    ├── __init__.py
    └── test_backend.py       # API health check and schema validation tests
```

---

## 🚀 Quickstart & Milestone 1 Verification

### Backend Prerequisites
- Python 3.10+
- Recommended: Virtual environment (`venv`)

### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install minimal dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload --port 8000
```

### 2. Verify Health Check
Open your browser or run:
```bash
curl http://127.0.0.1:8000/health
# Expected output: {"status":"healthy","service":"smart-farming-backend","version":"0.1.0"}
```

### 3. Run Backend Verification Tests
```bash
pytest tests/ -v
```

---

## 🎯 Implementation Roadmap

1. [x] **Milestone 1**: Project architecture, documentation, data contracts, and basic backend health/validation scaffolding.
2. [ ] **Milestone 2**: ESP32 sensor integration and FastAPI telemetry ingestion endpoint.
3. [ ] **Milestone 3**: Decision engine heuristic rules (soil moisture thresholds + weather forecast integration).
4. [ ] **Milestone 4**: Next.js frontend dashboard (sensor cards, gauges, telemetry graphs with Recharts).
5. [ ] **Milestone 5**: YOLO11n leaf disease training, ONNX export, and edge inference integration.
6. [ ] **Milestone 6**: Field deployment optimization on Raspberry Pi.
