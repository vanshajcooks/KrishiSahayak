/**
 * Shared Type Definitions for Farmer Smart Farming Assistant (SIH 26180)
 * Decoupled from UI components and backend transport layers.
 */

export type HealthState = 'HEALTHY' | 'GOOD' | 'NEEDS_ATTENTION' | 'CRITICAL';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type MoistureLevel = 'LOW' | 'OPTIMAL' | 'HIGH';
export type SeverityLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FarmProfile {
  farmName: string;
  crop: string;
  field: string;
}

export interface SoilMoistureData {
  percentage: number;
  level: MoistureLevel;
  interpretation: string; // e.g. "Your soil is dry."
}

export interface AmbientData {
  temperature: number; // °C
  humidity: number; // %
  lightHours?: number;
  tempTrend?: 'up' | 'down' | 'stable';
  moistureTrend?: 'up' | 'down' | 'stable';
}

export interface DailyForecast {
  day: string; // e.g. "Today", "Tomorrow", "Day 3"
  tempMax: number;
  tempMin: number;
  condition: string; // e.g. "Sunny", "Rain", "Cloudy"
  rainChance: number; // %
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  rainProbability: number;
  condition: string;
  interpretation: string; // e.g. "Hot and dry conditions expected."
  forecast: DailyForecast[];
}

export interface RiskItem {
  id: 'waterStress' | 'heatStress' | 'diseaseRisk';
  name: string;
  level: RiskLevel;
  explanation: string;
}

export interface RecommendedAction {
  category: 'ACTION_REQUIRED' | 'RECOMMENDED' | 'NORMAL';
  title: string;
  subtitle: string;
  primaryAction: string;
  secondaryAction?: string;
  reasons: string[];
}

export interface CropScanAnalysis {
  diseaseName: string;
  confidence: number; // e.g. 93%
  severity: 'Mild' | 'Moderate' | 'Severe' | 'None';
  findings: string;
  recommendedAction: string;
  safePractices: string[];
  crop?: string;
  condition?: string;
  bbox?: number[];
  isReal?: boolean;
  inferenceTimeMs?: number;
  // Multimodal Unified fields
  isUnified?: boolean;
  sensorAvailable?: boolean;
  sensorTelemetry?: BackendSensorTelemetry | null;
  decision?: BackendDecisionReport | null;
  weatherAvailable?: boolean;
  weather?: BackendWeatherData | null;
  insights?: string[];
}

export interface DiseasePrediction {
  crop: string;
  condition: string;
  confidence: number;
  bbox: number[];
}

export interface VisionPredictionResponse {
  status: string;
  model: string;
  predictions: DiseasePrediction[];
  count: number;
  inference_time_ms: number;
}

export interface BackendSensorTelemetry {
  sensor_id: string;
  soil_moisture: number;
  temperature: number;
  humidity: number;
  battery_voltage?: number | null;
  rain_level?: number | null;
  timestamp: string;
}

export interface BackendDecisionReport {
  sensor_id: string;
  timestamp: string;
  soil_moisture_status: 'LOW' | 'OPTIMAL' | 'HIGH';
  irrigation_action: 'IRRIGATE_SOON' | 'NO_IRRIGATION_NEEDED' | 'OVERWATERING_WARNING' | 'DELAY_IRRIGATION_RAIN_DETECTED';
  action_category: 'ACTION_REQUIRED' | 'RECOMMENDED' | 'NORMAL';
  action_title: string;
  action_subtitle: string;
  primary_action: string;
  water_stress_level: 'LOW' | 'MEDIUM' | 'HIGH';
  heat_stress_level: 'LOW' | 'MEDIUM' | 'HIGH';
  disease_risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  reasons: string[];
}

export interface BackendWeatherForecastItem {
  time: string;
  temp_max: number;
  temp_min: number;
  condition: string;
  rain_probability: number;
}

export interface BackendWeatherData {
  location: string;
  temperature: number;
  humidity: number;
  condition: string;
  rain_probability: number;
  wind_speed_kmh?: number | null;
  is_rain_forecasted: boolean;
  forecast: BackendWeatherForecastItem[];
  source: string;
  timestamp: string;
}

export interface UnifiedFarmAnalysisResponse {
  status: string;
  timestamp: string;
  vision: VisionPredictionResponse;
  sensor_available: boolean;
  sensor_telemetry?: BackendSensorTelemetry | null;
  decision?: BackendDecisionReport | null;
  weather_available: boolean;
  weather?: BackendWeatherData | null;
  insights: string[];
}

export interface FarmAlert {
  id: string;
  severity: SeverityLevel;
  category: string;
  title: string;
  message: string;
  action: string;
  timestamp: string;
  dismissed?: boolean;
}

export interface HistoricalMoisturePoint {
  day: string; // e.g. "Mon", "Tue"
  moisture: number; // %
  status: string;
}

export interface FarmState {
  profile: FarmProfile;
  cropHealth: {
    status: HealthState;
    diseaseRisk: RiskLevel;
    summary: string;
  };
  soilMoisture: SoilMoistureData;
  ambient: AmbientData;
  weather: WeatherData;
  risks: RiskItem[];
  recommendation: RecommendedAction;
  recentScan?: CropScanAnalysis;
  alerts: FarmAlert[];
  moistureHistory: HistoricalMoisturePoint[];
  lastUpdated: string;
  isRealData: boolean;
}

export interface DemoScenario {
  id: string;
  number: 1 | 2 | 3 | 4;
  name: string;
  shortDesc: string;
  state: FarmState;
}

export type ActiveTab = 'home' | 'scan' | 'field' | 'alerts' | 'settings' | 'irrigation';
export type AppLanguage = 'en' | 'hi';
export type AppMode = 'demo' | 'real';
export type ConnectivityState = 'CONNECTED_LIVE' | 'DEVICE_OFFLINE' | 'DEMO_MODE';
