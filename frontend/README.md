# Frontend — Smart Farming Assistant Web Dashboard

**Responsible Teammates**: Aryan (AI/ML + Frontend) & Vanshaj (Web + Backend)  
**Stack**: Next.js 14+ (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Recharts

---

## 1. Overview

The web dashboard provides the primary interface for farmers and agronomists. It visualizes real-time field telemetry, historical soil/climate trends, rule-based irrigation advisories, and crop health scan results.

---

## 2. Planned Page Layout & Key Components

```text
Dashboard Layout
├── Header (Status indicator: Edge Gateway Connected/Offline, Field Battery)
├── Section 1: Live Telemetry Cards
│   ├── Soil Moisture Gauge (0–100% with color coding: Red = Dry, Green = Optimal, Blue = Saturated)
│   ├── Ambient Temperature Card (°C)
│   └── Relative Humidity Card (%)
├── Section 2: Agricultural Advisory & Climate Risk (Decision Engine Output)
│   ├── Irrigation Action (e.g., "Irrigate 10mm" or "Hold - Rain in 4 hrs")
│   └── Fungal/Heat Stress Risk Banner
├── Section 3: Trend Visualizations (Recharts)
│   ├── Soil Moisture vs. Temperature (24-hour line chart)
│   └── Humidity vs. Dew Point Area Chart
└── Section 4: Crop Leaf Disease Scanner
    └── Drag-and-drop / mobile camera photo upload -> Instant ONNX diagnosis
```

---

## 3. Initial Setup Commands (When Frontend Implementation is Approved)

```bash
# Navigate to frontend directory
cd frontend

# Initialize Next.js with TypeScript and Tailwind CSS
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Install shadcn/ui CLI and core components
npx shadcn-ui@latest init
npx shadcn-ui@latest add card button badge alert

# Install Recharts and icons
npm install recharts lucide-react
```

---

## 4. API Consumption Configuration

Create `src/lib/api.ts` configured with base URL from environment:
- Local development: `http://127.0.0.1:8000`
- Field deployment: `http://192.168.4.1:8000` (Raspberry Pi gateway)
