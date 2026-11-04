# KhetSaathi (खेतसाथी) — Smart Farming Assistant

> **Edge-Capable Precision Agriculture & Crop Intelligence Platform**  
> An edge-first smart farming platform designed for smallholder farmers. Combines real-time IoT soil and microclimate telemetry, a 3-tier reliable YOLO vision pipeline for crop disease detection, deterministic agronomic heuristics, and phone-based OTP authentication with bilingual support (English & हिन्दी).

[![Tests](https://img.shields.io/badge/tests-116%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)]()
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg?logo=next.js&logoColor=white)]()
[![YOLO11](https://img.shields.io/badge/YOLO-11n-blue.svg?logo=ultralytics&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

---

## 🌟 Key Features

### 1. 📡 Physical Edge IoT Telemetry Pipeline
- Direct HTTP/JSON ingestion from battery/solar-powered **ESP32 microcontroller nodes**.
- Real-time sensors: **Capacitive Soil Moisture**, **DHT22** (ambient temperature and relative humidity), and rain detection.
- **Freshness Gate**: Automatically marks data stale/offline if the node fails to ping within a 10-second window, preventing misleading agronomic advice.

### 2. 🔬 3-Tier YOLO Vision Reliability Gate
- Edge-optimized **YOLO11n** model (`yolo11n-crop-disease`) for plant leaf disease detection.
- **Strict Reliability Classification** to prevent AI hallucinations:
  - **Tier 1 — Reliable ($\ge 0.50$ confidence):** Confirmed disease detection; triggers cross-modal risk correlations and treatment actions.
  - **Tier 2 — Inconclusive ($0.25 \le \text{confidence} < 0.50$):** Suppresses chemical/disease recommendations and instructs the farmer to take a clearer, well-lit photograph.
  - **Tier 3 — No Detection ($< 0.25$):** Does not falsely report "Healthy" with hardcoded high confidence; clearly advises that no reliable symptoms were found.

### 3. 🧠 Multimodal Agronomic Decision Engine
- Deterministic, explainable rule engine that cross-correlates **leaf pathology + real-time soil moisture + microclimate + weather forecasts**.
- E.g., if early blight is detected on leaves while ambient humidity is $>80\%$ and soil moisture is elevated, it flags fungal spore multiplication risk.
- Delays irrigation recommendations automatically if rain is imminent in the weather forecast.

### 4. 🌾 Farmer-Centric Bilingual Dashboard (English & हिन्दी)
- Built with **Next.js 14**, **Tailwind CSS**, and **Lucide Icons**.
- Professional, farmer-first terminology: clear primary action cards (*"Irrigation Recommended"*, *"Check Leaf Health"*, *"Field Climate Normal"*).
- **Interactive Simulation Mode**: Includes 4 realistic farm scenarios (Optimal, Water Stress, Heat Stress, Disease Outbreak) for live demonstrations and testing without active hardware.

### 5. 🔐 Secure Phone-First Authentication (Twilio Verify v2)
- Mobile-first login & registration using verified SMS OTPs.
- Zero local OTP storage — fully delegated to Twilio Verify v2 API with sliding-window rate limiting.
- **Stateless JWT Sessions via HttpOnly Secure Cookies** with instant revocation support via SQLite `token_version`.

### 6. 🗄️ Relational Database Foundation
- Normalized SQLite relational architecture with enforced foreign key cascades:
  $$\text{Farmer} \xrightarrow{\text{1:N}} \text{Fields} \xrightarrow{\text{1:N}} \text{Sensors} \xrightarrow{\text{1:N}} \text{Sensor Telemetry}$$
  $$\text{Farmer} \xrightarrow{\text{1:N}} \text{Alerts} \xrightarrow{\text{1:N}} \text{Notifications}$$
- Automated dynamic provisioning script (`backend/dev_provision.py`) for reproducible edge deployment and field node onboarding.

---

## 🏗️ System Architecture

```
[Field Node: ESP32 + DHT22 + Moisture Sensor]
                    │
                    ▼  HTTP POST /api/v1/sensors/ingest
[Gateway / Cloud Backend: FastAPI]
    ├── SQLite Database (Relational Farmer, Field, Sensor, Telemetry Models)
    ├── YOLO11n Crop-Disease Vision Engine (3-Tier Reliability Gate)
    ├── Deterministic Agronomic Decision Engine (Crop Moisture & Heat Stress)
    ├── Twilio Verify v2 Authentication Service (JWT + HttpOnly Cookies)
    └── OpenWeather / Live Forecast Integration
                    │
                    ▼  REST API + HttpOnly Session
[Farmer Client: Next.js 14 App Router]
    ├── Bilingual Dashboard (EN / HI)
    ├── Leaf Health Scanner (Camera Upload + Bounding Boxes)
    ├── Real-Time Gauge Visualizations & Action Required Cards
    └── Interactive Demo Mode (Offline Judge Scenarios)
```

---

## 📁 Repository Structure

```text
SIH/
├── backend/                  # FastAPI Python backend service
│   ├── auth/                 # Modular authentication package
│   │   ├── dependencies.py   # FastAPI get_current_active_farmer security guards
│   │   ├── schemas.py        # Pydantic schemas & E.164 phone normalization
│   │   ├── security.py       # JWT session generation & sliding-window rate limiters
│   │   ├── service.py        # Auth business logic & SQLite interactions
│   │   └── twilio_verify.py  # Twilio Verify v2 API adapter
│   ├── data/                 # SQLite database storage (smart_farming.db)
│   ├── models/               # Pre-trained YOLO11 crop disease weights (best.pt)
│   ├── routers/              # API Sub-routers (auth.py, etc.)
│   ├── analysis.py           # Unified multimodal synthesis & freshness engine
│   ├── database.py           # SQLite schema migrations & CRUD operations
│   ├── decision.py           # Agronomic heuristic rules & stress evaluations
│   ├── dev_provision.py      # Idempotent development node provisioning CLI
│   ├── main.py               # Application entrypoint & CORS configuration
│   ├── requirements.txt      # Python dependencies
│   ├── schemas.py            # Pydantic models for IoT telemetry, vision, & decisions
│   ├── vision.py             # YOLO11 inference wrapper & model warm-up
│   └── weather.py            # Async weather forecast connector
│
├── frontend/                 # Next.js 14 frontend dashboard
│   ├── src/
│   │   ├── app/              # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   │   ├── components/       # UI Components (Header, Sidebar, BottomNav, DemoModeBar)
│   │   │   ├── cards/        # ActionRequired, CropHealth, WaterStatus, WeatherCard
│   │   │   └── views/        # HomeView, ScanView, FieldView, AlertsView, SettingsView
│   │   ├── data/             # Translations (EN/HI) and demo scenarios
│   │   ├── services/         # API Client for backend gateway communication
│   │   └── types/            # TypeScript data contracts & state interfaces
│   ├── package.json          # Node dependencies & build scripts
│   └── tsconfig.json         # TypeScript configuration
│
├── esp32/
│   └── sensor_node/          # ESP32 C++/Arduino firmware for sensor telemetry
│
├── tests/                    # Comprehensive automated test suite (116 tests)
│   ├── test_auth.py          # Phone normalization, OTP, rate limits, JWT, session tests
│   ├── test_backend.py       # API health check, ingestion, persistence, & provisioning
│   ├── test_decision.py      # Agronomic decision rules & edge boundaries
│   ├── test_farm_analysis.py # Multimodal cross-modal synthesis tests
│   ├── test_vision.py        # YOLO reliability tier validation tests
│   └── test_weather.py       # Weather parsing & fallback integration tests
│
├── .env.example              # Environment variables template
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.10+ (recommended: Python 3.12 or 3.13 via `uv` or `venv`)
- **Node.js**: 18.17+ and `npm`

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/KhetSaathi.git
cd KhetSaathi

# Create and activate Python virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your preferred secret keys & configuration
```

#### Provision a Development Node (Farmer $\to$ Field $\to$ Sensor)
```bash
# Set a development phone number and provision local node
$env:DEV_FARMER_PHONE = "+919876543210"
python -m backend.dev_provision
```

#### Run the Backend Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The API documentation is accessible at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

### 3. Running Automated Tests

The repository includes a comprehensive, hermetic test suite covering all services, mocks, and edge cases:

```bash
uv run pytest tests/
# or: pytest tests/ -v
```

```text
======================= 116 passed in 20.35s =======================
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health status check | Public |
| `POST` | `/api/v1/sensors/ingest` | ESP32 hardware telemetry ingestion | Device / Public |
| `GET` | `/api/v1/sensors/latest` | Most recent sensor reading with freshness status | Optional / Farmer |
| `GET` | `/api/v1/decision/recommendations` | Agronomic stress analysis and advice | Optional / Farmer |
| `POST` | `/api/v1/vision/predict` | YOLO11 leaf disease detection with reliability tier | Public |
| `POST` | `/api/v1/farm/analyze` | Multimodal analysis (Vision + Telemetry + Weather) | Public |
| `GET` | `/api/v1/weather/current` | Real-time weather and forecast for farm location | Public |
| `POST` | `/api/v1/auth/otp/send` | Dispatches verification OTP via SMS | Public (Rate-Limited) |
| `POST` | `/api/v1/auth/otp/verify` | Validates code, sets session cookie or issues registration token | Public (Rate-Limited) |
| `POST` | `/api/v1/auth/register` | Completes farmer registration with verified token | Token-Gated |
| `GET` | `/api/v1/auth/me` | Returns current farmer profile, fields, and active sensors | Cookie / Bearer |
| `POST` | `/api/v1/auth/logout` | Revokes current session and clears cookies | Cookie / Bearer |

---

## 🛡️ Security & Reliability Principles

1. **Anti-Hallucination Vision Gate**: Strict confidence thresholding ensures farmers never receive false disease remedies or unverified chemical guidance.
2. **Session Security**: Uses `HttpOnly`, `SameSite=Lax`, and `Secure` cookies to protect farmer sessions against XSS and token-theft attacks.
3. **Instant Session Invalidation**: Single-click logout invalidates the server-side `token_version`, instantly revoking all active sessions.
4. **Resilient Offline Operation**: If internet connectivity is interrupted, the edge gateway continues processing sensor telemetry and running local decision heuristics.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
