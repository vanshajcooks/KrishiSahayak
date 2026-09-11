# Team Roles & Milestone Responsibilities

**Smart India Hackathon 2026 — Smart Farming Assistant (PS 26180)**

This document details ownership, primary folders, and beginner-friendly next steps for each team member.

---

## 1. Siddharth — Team Lead + Research + Documentation
* **Primary Workspace**: `docs/`, `ARCHITECTURE.md`, `README.md`
* **Responsibilities**:
  * Ensure the solution strictly addresses SIH Problem Statement 26180.
  * Maintain system architecture docs, pitch decks, and hackathon presentation material.
  * Conduct agricultural research on crop-specific moisture thresholds (e.g., wheat, rice, cotton, tomato).
  * Coordinate milestone reviews across hardware, software, and AI teams.

---

## 2. Vanshaj — Full-Stack & Integration (Web + Backend + IoT + AI)
* **Primary Workspace**: `backend/`, root integration pipelines
* **Responsibilities**:
  * Maintain the FastAPI backend application structure and Pydantic validation schemas.
  * Set up SQLite persistence in Milestone 2.
  * Coordinate with Sneha to ensure ESP32 HTTP requests land cleanly on `/api/v1/sensors/ingest`.
  * Coordinate with Aryan on Next.js API consumption and CORS configuration.
  * Assist in packaging the backend and decision engine for field deployment on the Raspberry Pi.

---

## 3. Sneha — Hardware & IoT Subsystem
* **Primary Workspace**: `esp32/sensor_node/`
* **Responsibilities**:
  * Maintain and calibrate the ESP32 sensor node hardware.
  * Wire capacitive soil moisture sensor (analog pin) and DHT22 temperature/humidity sensor (digital GPIO).
  * Calibrate raw capacitive sensor ADC values to true 0–100% volumetric moisture percentages.
  * Frame the outgoing JSON payload matching the contract in [api_spec.md](file:///c:/Projects/SIH/docs/api_spec.md).
  * (Note: Existing working sensor node code is preserved; final HTTP transmission will be tested in Milestone 2).

---

## 4. Diya — AI / ML Crop Health
* **Primary Workspace**: `ai/disease_detection/`
* **Responsibilities**:
  * Curate and clean leaf disease image datasets (e.g., PlantVillage, regional Indian crop disease sets).
  * Split dataset into `train/`, `val/`, `test/` partitions in standard YOLO format.
  * Train the YOLO11n (nano) model using Ultralytics PyTorch framework.
  * Evaluate precision, recall, and mAP50 metrics.
  * Hand off trained `.pt` model weights to Aryan for ONNX conversion.

---

## 5. Aryan — AI / ML + Frontend
* **Primary Workspace**: `frontend/`, `ai/inference/`
* **Responsibilities**:
  * Build the Next.js responsive web dashboard using Tailwind CSS and shadcn/ui.
  * Build telemetry visualizations using Recharts (soil moisture gauge, historical humidity/temperature curves).
  * Convert Diya's trained PyTorch `.pt` model to `.onnx` format.
  * Implement lightweight ONNX Runtime inference script in `ai/inference/` for deployment on the Raspberry Pi gateway.

---

## 6. Arnav — Climate & Risk Intelligence
* **Primary Workspace**: `backend/decision_engine/` (Milestone 3)
* **Responsibilities**:
  * Design simple, explainable heuristic rules for agricultural irrigation triggers.
  * Integrate free weather forecasting API (such as Open-Meteo) to anticipate upcoming rainfall.
  * Calculate crop health risk indicators (Vapor Pressure Deficit, heat stress, fungal disease risk conditions).
  * Generate clear, human-readable advice for the farmer dashboard (e.g., *"Rain expected in 6 hours; hold irrigation"*).
