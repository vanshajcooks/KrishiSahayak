'use client';

import React, { useState, useRef } from 'react';
import {
  Camera,
  UploadCloud,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  Lightbulb,
  Sparkles,
  WifiOff,
  Cpu,
  Clock,
  Scan,
  Droplets,
  CloudSun,
  CloudRain,
  Thermometer,
  Layers,
  AlertTriangle,
} from 'lucide-react';

import {
  CropScanAnalysis,
  DiseasePrediction,
  UnifiedFarmAnalysisResponse,
  BackendSensorTelemetry,
  BackendDecisionReport,
  BackendWeatherData,
  VisionReliabilityTier,
} from '@/types/farm';
import { analyzeUnifiedFarm } from '@/services/api';

interface ScanViewProps {
  onBackToHome: () => void;
  onViewAdvice: () => void;
  presetScan?: CropScanAnalysis;
  isRealData?: boolean;
}

type ScanStage = 'idle' | 'preview' | 'analyzing' | 'result' | 'error';

function formatCropName(crop: string): string {
  if (!crop || crop.toLowerCase() === 'unknown') return 'Crop';
  return crop.charAt(0).toUpperCase() + crop.slice(1).toLowerCase();
}

function formatConditionName(condition: string): string {
  if (!condition) return 'Healthy / Normal';
  return condition
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

function formatIrrigationStatus(
  action: string | undefined,
  decision?: BackendDecisionReport | null
): { text: string; colorClass: string; badgeClass: string } {
  if (decision?.primary_action) {
    const act = decision.primary_action.toLowerCase();
    if (act.includes('pause') || act.includes('rain')) {
      return {
        text: 'Paused (Rain Detected)',
        colorClass: 'text-blue-700 font-bold',
        badgeClass: 'bg-blue-100 text-blue-900 border-blue-200',
      };
    }
    if (act.includes('irrigate soon') || act.includes('low soil moisture')) {
      return {
        text: 'Irrigation Needed (Dry)',
        colorClass: 'text-rose-700 font-bold',
        badgeClass: 'bg-rose-100 text-rose-900 border-rose-200',
      };
    }
    if (act.includes('optimal') || act.includes('adequate') || act.includes('no irrigation')) {
      return {
        text: 'Adequate (Optimal)',
        colorClass: 'text-emerald-700 font-bold',
        badgeClass: 'bg-emerald-100 text-emerald-900 border-emerald-200',
      };
    }
    if (act.includes('overwater')) {
      return {
        text: 'Overwatering Warning',
        colorClass: 'text-amber-700 font-bold',
        badgeClass: 'bg-amber-100 text-amber-900 border-amber-200',
      };
    }
  }

  switch (action) {
    case 'IRRIGATE_SOON':
      return {
        text: 'Irrigation Needed (Dry)',
        colorClass: 'text-rose-700 font-bold',
        badgeClass: 'bg-rose-100 text-rose-900 border-rose-200',
      };
    case 'DELAY_IRRIGATION_RAIN_DETECTED':
      return {
        text: 'Paused (Rain Detected)',
        colorClass: 'text-blue-700 font-bold',
        badgeClass: 'bg-blue-100 text-blue-900 border-blue-200',
      };
    case 'OVERWATERING_WARNING':
      return {
        text: 'Overwatering Warning',
        colorClass: 'text-amber-700 font-bold',
        badgeClass: 'bg-amber-100 text-amber-900 border-amber-200',
      };
    case 'NO_IRRIGATION_NEEDED':
      return {
        text: 'Adequate (Optimal)',
        colorClass: 'text-emerald-700 font-bold',
        badgeClass: 'bg-emerald-100 text-emerald-900 border-emerald-200',
      };
    default:
      return {
        text: decision?.primary_action || 'Normal',
        colorClass: 'text-slate-800 font-semibold',
        badgeClass: 'bg-slate-100 text-slate-800 border-slate-200',
      };
  }
}

function buildAnalysisResultFromUnified(
  pred: DiseasePrediction,
  inferenceTimeMs?: number,
  sensorAvailable: boolean = false,
  sensorStale: boolean = false,
  sensorTelemetry?: BackendSensorTelemetry | null,
  decision?: BackendDecisionReport | null,
  weatherAvailable: boolean = false,
  weather?: BackendWeatherData | null,
  insights: string[] = [],
  reliabilityTier: VisionReliabilityTier = 'RELIABLE',
  isReliable: boolean = true
): CropScanAnalysis {
  const cropTitle = formatCropName(pred.crop);
  const conditionTitle = formatConditionName(pred.condition);
  const confPercent = Math.round(pred.confidence * 100);

  // Tier 2: Inconclusive (confidence < 0.50 or reliabilityTier === 'INCONCLUSIVE')
  if (reliabilityTier === 'INCONCLUSIVE' || !isReliable || pred.confidence < 0.50) {
    return {
      diseaseName: `Possible ${cropTitle} Pattern (${conditionTitle}) — Unclear`,
      confidence: confPercent,
      severity: 'None',
      findings: `The scan detected faint patterns weakly resembling ${conditionTitle} on ${cropTitle} at ${confPercent}% confidence. This is below the clear diagnostic threshold (50%) and may be caused by indistinct leaf features, shadows, or camera blur.`,
      recommendedAction: decision?.primary_action
        ? `${decision.primary_action} For foliar health: retake a clear, well-lit photograph centered on the leaf blade before taking any chemical or pruning action.`
        : 'Do not apply chemical sprays or quarantine crops based on this scan. Retake a sharp, well-lit photograph centered on the leaf blade.',
      safePractices: [
        'Ensure the camera is focused directly on a single leaf blade in natural lighting.',
        'Avoid including humans, fingers, complex backgrounds, or excessive shadows in the frame.',
        'Clean the camera lens and hold steady when capturing the photograph.',
        'If you suspect genuine crop distress in your field, consult your local agricultural extension officer.',
      ],
      crop: pred.crop,
      condition: pred.condition,
      bbox: pred.bbox,
      isReal: true,
      isUnified: true,
      inferenceTimeMs,
      sensorAvailable,
      sensorStale,
      sensorTelemetry,
      decision,
      weatherAvailable,
      weather,
      insights,
      reliabilityTier: 'INCONCLUSIVE',
      isReliable: false,
    };
  }

  if (pred.condition === 'healthy') {
    return {
      diseaseName: `${cropTitle} — Healthy Foliage`,
      confidence: confPercent,
      severity: 'None',
      findings: `Clear healthy leaf sample (${confPercent}% confidence). Green leaf color, surface, and vein structure look normal.`,
      recommendedAction:
        decision?.primary_action ||
        'Continue standard agronomic monitoring and scheduled irrigation.',
      safePractices: [
        'Maintain balanced watering and soil nutrient management.',
        'Inspect the lower canopy weekly for any early pest or foliar stress.',
        'Keep row spacing clear for adequate ventilation and sunlight.',
      ],
      crop: pred.crop,
      condition: pred.condition,
      bbox: pred.bbox,
      isReal: true,
      isUnified: true,
      inferenceTimeMs,
      sensorAvailable,
      sensorStale,
      sensorTelemetry,
      decision,
      weatherAvailable,
      weather,
      insights,
      reliabilityTier: 'RELIABLE',
      isReliable: true,
    };
  }

  // Disease condition detected
  const isBlight = pred.condition.includes('blight');
  const isSpot = pred.condition.includes('spot') || pred.condition.includes('scab');
  const isRust = pred.condition.includes('rust');

  let severity: 'Mild' | 'Moderate' | 'Severe' = 'Moderate';
  if (pred.confidence >= 0.85) severity = 'Moderate';
  else if (pred.confidence < 0.60) severity = 'Mild';

  let findings = `Foliar symptoms identified consistent with ${conditionTitle} on ${cropTitle} (${confPercent}% confidence).`;
  if (isBlight) {
    findings += ' Visible lesions and tissue discoloration observed on the leaf.';
  } else if (isSpot) {
    findings += ' Characteristic localized spots or chlorotic halos identified on the surface.';
  } else if (isRust) {
    findings += ' Pustule or rust-like discoloration detected on the leaf blade.';
  }

  const practices = [
    'Inspect adjacent plants and rows thoroughly to evaluate spread.',
    'Prune and safely dispose of visibly infected lower foliage away from the field.',
    'Avoid overhead watering to prevent splashing fungal spores onto upper canopy.',
    'Consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer for approved crop-management options.',
  ];

  let recommendedAction = `Inspect nearby ${cropTitle.toLowerCase()} plants and consult agricultural extension officer for approved disease management.`;
  if (decision?.primary_action) {
    recommendedAction = `${decision.primary_action} Meanwhile, quarantine affected ${cropTitle.toLowerCase()} foliage.`;
  }

  return {
    diseaseName: `${cropTitle}: ${conditionTitle}`,
    confidence: confPercent,
    severity,
    findings,
    recommendedAction,
    safePractices: practices,
    crop: pred.crop,
    condition: pred.condition,
    bbox: pred.bbox,
    isReal: true,
    isUnified: true,
    inferenceTimeMs,
    sensorAvailable,
    sensorStale,
    sensorTelemetry,
    decision,

    weatherAvailable,
    weather,
    insights,
    reliabilityTier: 'RELIABLE',
    isReliable: true,
  };
}

export const ScanView: React.FC<ScanViewProps> = ({
  onBackToHome,
  onViewAdvice,
  presetScan,
  isRealData = false,
}) => {
  const [stage, setStage] = useState<ScanStage>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isOfflineError, setIsOfflineError] = useState<boolean>(false);
  const [inferenceTime, setInferenceTime] = useState<number | null>(null);
  const [detectedPredictions, setDetectedPredictions] = useState<DiseasePrediction[]>([]);
  const [isLiveScan, setIsLiveScan] = useState<boolean>(presetScan?.isReal ?? false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  // Diagnostic result state
  const [analysisResult, setAnalysisResult] = useState<CropScanAnalysis>(
    presetScan || {
      diseaseName: 'Possible Early Blight (Alternaria solani)',
      confidence: 93,
      severity: 'Moderate',
      findings: 'Concentric ring spots and chlorotic yellow halos observed on lower foliage.',
      recommendedAction: 'Inspect nearby plants and begin appropriate disease management.',
      safePractices: [
        'Inspect affected plants and adjacent rows thoroughly.',
        'Prune and safely dispose of infected lower leaves.',
        'Avoid overhead watering to prevent water splashing spores onto upper leaves.',
        'Consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer for approved crop-management options.',
      ],
      isReal: false,
    }
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setErrorMessage(null);
    setIsOfflineError(false);
    setStage('preview');
  };

  const triggerCamera = () => {
    if (cameraInputRef.current) {
      cameraInputRef.current.value = '';
      cameraInputRef.current.click();
    }
  };

  const triggerUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const runAnalysis = async () => {
    if (!selectedFile) return;

    setStage('analyzing');
    setErrorMessage(null);
    setIsOfflineError(false);

    try {
      // Call the unified multimodal analysis endpoint
      const res = await analyzeUnifiedFarm(selectedFile, undefined, 0.25);

      if (!res.success) {
        setIsOfflineError(Boolean(res.isOffline));
        setErrorMessage(
          res.error || 'Failed to connect to the farm analysis service. Please check your backend connection.'
        );
        setStage('error');
        return;
      }

      if (res.data) {
        const unified = res.data;
        const preds = unified.vision?.predictions || [];
        setDetectedPredictions(preds);
        setInferenceTime(unified.vision?.inference_time_ms ?? null);
        setIsLiveScan(true);

        const sensorTel = unified.sensor_telemetry;
        const dec = unified.decision;
        const weatherTel = unified.weather;
        const insightsList = unified.insights || [];

        const relTier: VisionReliabilityTier =
          unified.vision?.reliability ||
          (preds.length === 0
            ? 'NO_DETECTION'
            : preds.some((p) => p.confidence >= 0.50)
            ? 'RELIABLE'
            : 'INCONCLUSIVE');
        const isRel =
          unified.vision?.is_reliable ?? (relTier === 'RELIABLE');

        if (preds.length > 0) {
          const top = [...preds].sort((a, b) => b.confidence - a.confidence)[0];
          const formatted = buildAnalysisResultFromUnified(
            top,
            unified.vision.inference_time_ms,
            unified.sensor_available,
            unified.sensor_stale || false,
            sensorTel,
            dec,
            unified.weather_available,
            weatherTel,
            insightsList,
            relTier,
            isRel
          );
          setAnalysisResult(formatted);
        } else {
          // Tier 3: Zero detections — do NOT claim healthy or hardcode 95%
          setAnalysisResult({
            diseaseName: 'No Reliable Foliar Symptoms Detected',
            confidence: 0,
            severity: 'None',
            findings:
              'The crop leaf scan detected no recognizable foliar disease patterns or damage lesions above threshold. If crop distress is suspected, please take a clear, well-lit close-up photograph of the affected leaf.',
            recommendedAction:
              dec?.primary_action ||
              'No obvious foliar disease symptoms identified. Continue regular field monitoring and scheduled irrigation.',
            safePractices: [
              'Ensure the leaf is well-lit and centered when capturing scans.',
              'Inspect the undersides of leaves during warm or humid periods.',
              'Maintain recommended drip irrigation and nutrient cycles.',
              'Consult local agricultural extension officers if unusual wilting appears.',
            ],
            isReal: true,
            isUnified: true,
            inferenceTimeMs: unified.vision.inference_time_ms,
            sensorAvailable: unified.sensor_available,
            sensorStale: unified.sensor_stale || false,
            sensorTelemetry: sensorTel,
            decision: dec,
            weatherAvailable: unified.weather_available,
            weather: weatherTel,
            insights: insightsList,
            reliabilityTier: 'NO_DETECTION',
            isReliable: false,
          });
        }

        setStage('result');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred';
      setIsOfflineError(true);
      setErrorMessage(msg);
      setStage('error');
    }
  };

  const resetScan = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMessage(null);
    setIsOfflineError(false);
    setDetectedPredictions([]);
    setInferenceTime(null);
    setStage('idle');
  };

  return (
    <div className="space-y-4 pb-20 lg:pb-8">
      {/* Hidden File Inputs for Camera and File Chooser */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileSelect}
        className="hidden"
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* View Header */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-900">Check Leaf Health</h2>
          <p className="text-xs md:text-sm text-slate-600 mt-0.5">
            Take a leaf photo to diagnose crop health alongside real-time soil moisture and weather.
          </p>
        </div>

        {isLiveScan ? (
          <span className="text-xs font-bold text-emerald-900 bg-emerald-100 px-3 py-1 rounded-full border border-emerald-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
            <span>Field Analysis Active</span>
          </span>
        ) : (
          <span className="text-xs font-bold text-amber-900 bg-amber-100 px-3 py-1 rounded-full border border-amber-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-700" />
            <span>Ready for Leaf Photo</span>
          </span>
        )}
      </div>

      {/* Main Responsive Container (1 col mobile/tablet, 2 cols desktop) */}
      <div className="lg:grid lg:grid-cols-12 lg:gap-6 space-y-4 lg:space-y-0">
        {/* Left Column: Camera / Image Preview (5 cols on desktop) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Camera Viewfinder
              </span>
              <span className="text-xs font-semibold text-slate-500">
                {stage === 'result'
                  ? 'Check Completed'
                  : stage === 'analyzing'
                  ? 'Checking Leaf...'
                  : stage === 'preview'
                  ? 'Photo Selected'
                  : stage === 'error'
                  ? 'Attention Needed'
                  : 'Ready'}
              </span>
            </div>

            {/* Viewfinder Display Box */}
            <div className="relative aspect-[4/3] rounded-xl bg-slate-900 border-2 border-dashed border-slate-600 flex flex-col items-center justify-center p-3 text-center overflow-hidden">
              {/* Corner Viewfinder Brackets */}
              <div className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-farm-400 z-10" />
              <div className="absolute top-3 right-3 w-6 h-6 border-t-2 border-r-2 border-farm-400 z-10" />
              <div className="absolute bottom-3 left-3 w-6 h-6 border-b-2 border-l-2 border-farm-400 z-10" />
              <div className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-farm-400 z-10" />

              {/* State A: Idle - Prompt to shoot/upload */}
              {stage === 'idle' && !previewUrl && (
                <div className="flex flex-col items-center justify-center p-4">
                  <div className="w-14 h-14 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-farm-400 mb-2 shadow-inner">
                    <Camera className="w-7 h-7" />
                  </div>
                  <p className="text-xs md:text-sm font-semibold text-slate-200">
                    Point camera at a single crop leaf
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Capture in daylight or choose a saved photo
                  </p>
                </div>
              )}

              {/* State B: Photo selected / analyzed */}
              {previewUrl && (
                <div className="relative w-full h-full flex items-center justify-center overflow-hidden rounded-lg">
                  <img
                    src={previewUrl}
                    alt="Selected leaf sample"
                    className="max-h-full max-w-full object-contain rounded-lg shadow-sm"
                  />

                  {/* Scanning active animation overlay */}
                  {stage === 'analyzing' && (
                    <div className="absolute inset-0 bg-slate-950/75 backdrop-blur-sm flex flex-col items-center justify-center p-4 text-white z-20">
                      <div className="w-12 h-12 rounded-full border-4 border-farm-300 border-t-farm-600 animate-spin mb-3" />
                      <div className="flex items-center gap-1.5 text-xs font-black tracking-wider text-farm-300 uppercase">
                        <Scan className="w-4 h-4 animate-pulse" />
                        <span>Checking Leaf Health...</span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 font-medium text-center">
                        Correlating symptoms with soil moisture & weather conditions...
                      </p>
                    </div>
                  )}

                  {/* Result completed badge overlay */}
                  {stage === 'result' && isLiveScan && (
                    <div className="absolute bottom-2 left-2 right-2 bg-slate-900/90 backdrop-blur-sm border border-slate-700 rounded-lg px-3 py-2 flex items-center justify-between text-xs text-white z-10">
                      <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                        <CheckCircle2 className="w-4 h-4" />
                        {analysisResult.condition ? formatConditionName(analysisResult.condition) : 'Analyzed'}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Quick Tip beneath viewfinder */}
          <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2 text-amber-900">
            <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <span className="font-bold">Tip: </span>Center a single leaf clearly in the viewfinder. Avoid shadows, excessive blur, or multiple leaves in one shot.
            </p>
          </div>
        </div>

        {/* Right Column: Interactive Controls & Analysis State (7 cols on desktop) */}
        <div className="lg:col-span-7">
          {/* STAGE 1: IDLE / CHOOSE CAPTURE METHOD */}
          {stage === 'idle' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Choose Capture Method</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Take a new leaf photo using your device camera or upload a field photograph for unified analysis.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={triggerCamera}
                  type="button"
                  className="flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm"
                >
                  <Camera className="w-4 h-4" />
                  <span>Take Photo</span>
                </button>

                <button
                  onClick={triggerUpload}
                  type="button"
                  className="flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 font-bold text-xs md:text-sm active:scale-95 transition"
                >
                  <UploadCloud className="w-4 h-4 text-slate-600" />
                  <span>Upload Photo</span>
                </button>
              </div>

              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs text-slate-600 space-y-1.5">
                <span className="font-bold text-slate-800 block">How leaf health check works:</span>
                <p className="leading-relaxed">1. Clear leaf photo is inspected for fungal, bacterial, or blight spots.</p>
                <p className="leading-relaxed">2. Soil moisture & rain readings from your field node are factored in.</p>
                <p className="leading-relaxed">3. Local weather forecasts help identify high-risk disease spread conditions.</p>
              </div>
            </div>
          )}

          {/* STAGE 2: PREVIEW STATE */}
          {stage === 'preview' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Review Leaf Photo</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Confirm the leaf spots and details are clearly visible before checking health.
                </p>
              </div>

              {selectedFile && (
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs flex items-center justify-between text-slate-600">
                  <span className="font-medium truncate max-w-[200px]">{selectedFile.name}</span>
                  <span className="text-slate-400 font-mono text-xs">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={runAnalysis}
                  type="button"
                  className="flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm"
                >
                  <Scan className="w-4 h-4" />
                  <span>Check Leaf Health</span>
                </button>

                <button
                  onClick={triggerUpload}
                  type="button"
                  className="py-3.5 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs md:text-sm active:scale-95 transition"
                >
                  Choose Different Photo
                </button>
              </div>
            </div>
          )}

          {/* STAGE 3: ANALYZING STATE */}
          {stage === 'analyzing' && (
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center space-y-3">
              <div className="w-14 h-14 rounded-full border-4 border-farm-200 border-t-farm-700 animate-spin" />
              <h3 className="text-base font-bold text-slate-900">Checking Leaf & Field Conditions...</h3>
              <p className="text-xs text-slate-600 max-w-sm leading-relaxed">
                Checking leaf patterns against common crop diseases, current soil moisture, and weather forecast.
              </p>
            </div>
          )}

          {/* STAGE ERROR: BACKEND OFFLINE OR INFERENCE ERROR */}
          {stage === 'error' && (
            <div className="bg-white rounded-2xl p-5 border border-rose-200 shadow-sm space-y-4">
              <div className="flex items-start gap-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    isOfflineError ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {isOfflineError ? <WifiOff className="w-5 h-5" /> : <AlertOctagon className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    {isOfflineError ? 'Field Gateway Offline' : 'Analysis Incomplete'}
                  </h3>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {isOfflineError
                      ? 'Could not reach your farm gateway service. Please check your network connection.'
                      : 'An error occurred while evaluating the leaf photo.'}
                  </p>
                </div>
              </div>

              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs space-y-1.5">
                <div className="text-slate-800 leading-relaxed font-medium">
                  {errorMessage || 'Unable to connect to field gateway.'}
                </div>
                {isOfflineError && (
                  <p className="text-xs text-amber-900 pt-1 leading-relaxed font-medium">
                    Ensure the farm server is powered on and connected to your local network.
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <button
                  onClick={runAnalysis}
                  type="button"
                  className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Analysis</span>
                </button>

                <button
                  onClick={resetScan}
                  type="button"
                  className="py-3 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs md:text-sm active:scale-95 transition"
                >
                  Choose Another Photo
                </button>
              </div>
            </div>
          )}

          {/* STAGE 4: RESULT STATE */}
          {stage === 'result' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              {/* Result Header Badge */}
              <div className="flex items-center justify-between">
                {analysisResult.reliabilityTier === 'INCONCLUSIVE' ? (
                  <span className="text-xs font-bold px-3 py-1 rounded-full border border-amber-300 bg-amber-100 text-amber-900 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                    <span>Unclear Photo / Inconclusive</span>
                  </span>
                ) : analysisResult.reliabilityTier === 'NO_DETECTION' ? (
                  <span className="text-xs font-bold px-3 py-1 rounded-full border border-slate-300 bg-slate-100 text-slate-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-slate-600" />
                    <span>No Disease Symptoms Detected</span>
                  </span>
                ) : (
                  <span
                    className={`text-xs font-bold px-3 py-1 rounded-full border flex items-center gap-1.5 ${
                      analysisResult.severity === 'None'
                        ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                        : 'bg-rose-100 text-rose-900 border-rose-300'
                    }`}
                  >
                    {analysisResult.severity === 'None' ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                        <span>Foliage Appears Healthy</span>
                      </>
                    ) : (
                      <>
                        <AlertOctagon className="w-3.5 h-3.5 text-rose-700" />
                        <span>Foliar Issue Identified</span>
                      </>
                    )}
                  </span>
                )}

                {analysisResult.reliabilityTier === 'NO_DETECTION' ? (
                  <span className="text-xs font-bold text-slate-500">
                    Confidence: <span className="text-slate-700 font-semibold">--</span>
                  </span>
                ) : analysisResult.reliabilityTier === 'INCONCLUSIVE' ? (
                  <span className="text-xs font-bold text-amber-800">
                    Confidence:{' '}
                    <span className="text-amber-900 font-black">
                      {analysisResult.confidence}% (Unreliable)
                    </span>
                  </span>
                ) : (
                  <span className="text-xs font-bold text-slate-600">
                    Confidence:{' '}
                    <span className="text-slate-900 font-black">
                      {analysisResult.confidence}%
                    </span>
                  </span>
                )}
              </div>

              {/* Disease Title & Severity */}
              <div>
                <h3 className="text-lg md:text-xl font-black text-slate-900">
                  {analysisResult.diseaseName}
                </h3>
                <div className="flex items-center gap-3 mt-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-slate-600">Severity:</span>
                    {analysisResult.reliabilityTier === 'INCONCLUSIVE' ? (
                      <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300">
                        Inconclusive
                      </span>
                    ) : (
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                          analysisResult.severity === 'None'
                            ? 'bg-emerald-100 text-emerald-900'
                            : analysisResult.severity === 'Severe'
                            ? 'bg-rose-100 text-rose-900'
                            : 'bg-amber-100 text-amber-900'
                        }`}
                      >
                        {analysisResult.severity}
                      </span>
                    )}
                  </div>

                  {isLiveScan && analysisResult.crop && analysisResult.reliabilityTier !== 'NO_DETECTION' && (
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <span>Crop:</span>
                      <span className="font-semibold text-slate-800">
                        {formatCropName(analysisResult.crop)}
                      </span>
                    </div>
                  )}

                  {isLiveScan && analysisResult.condition && analysisResult.reliabilityTier !== 'NO_DETECTION' && (
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <span>Condition:</span>
                      <span className="font-semibold text-slate-800">
                        {formatConditionName(analysisResult.condition)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Tier 2 & Tier 3 Callout Guidance Banners */}
              {analysisResult.reliabilityTier === 'INCONCLUSIVE' && (
                <div className="rounded-xl border border-amber-300 bg-amber-50/90 p-3.5 text-xs space-y-1.5 text-amber-950">
                  <div className="flex items-center gap-2 font-bold text-amber-900">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                    <span>Low Confidence / Inconclusive Detection</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-amber-800">
                    The detected pattern scored {analysisResult.confidence}% confidence, which is below the 50% diagnostic reliability threshold. This detection may be non-leaf background noise, shadows, or ambiguous foliage symptoms. <strong>Do not apply chemical sprays or quarantine crops based on this scan.</strong>
                  </p>
                  <p className="text-[11px] font-semibold text-amber-900 pt-0.5">
                    Guidance: Please retake a clear, well-lit photograph centered directly on a single leaf blade.
                  </p>
                </div>
              )}

              {analysisResult.reliabilityTier === 'NO_DETECTION' && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 space-y-1">
                  <p className="text-[11px] leading-relaxed">
                    No recognizable foliar symptoms or disease lesions were identified above threshold. If crop distress or discoloration is visible in your field, please capture a sharp close-up photograph of the affected leaf blade.
                  </p>
                </div>
              )}

              {/* MULTIMODAL TELEMETRY GRID: Field Sensors & Live Weather */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Panel 1: Field Sensor Telemetry */}
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 flex items-center gap-1.5">
                      <Droplets className="w-4 h-4 text-blue-600" />
                      <span>Field Sensors</span>
                    </span>
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                        analysisResult.sensorAvailable
                          ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                          : analysisResult.sensorStale
                          ? 'bg-amber-100 text-amber-900 border border-amber-300'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {analysisResult.sensorAvailable
                        ? 'Online'
                        : analysisResult.sensorStale
                        ? 'Gateway Disconnected'
                        : 'No Sensor Node'}
                    </span>
                  </div>

                  {analysisResult.sensorAvailable && analysisResult.sensorTelemetry ? (
                    <div className="space-y-1.5 text-slate-700 font-medium">
                      <div className="flex justify-between">
                        <span>Soil Moisture:</span>
                        <span className="font-bold text-slate-900">
                          {analysisResult.sensorTelemetry.soil_moisture.toFixed(1)}% (
                          {analysisResult.decision?.soil_moisture_status || 'OPTIMAL'})
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Temperature / Humidity:</span>
                        <span className="font-bold text-slate-900">
                          {analysisResult.sensorTelemetry.temperature.toFixed(1)}°C •{' '}
                          {analysisResult.sensorTelemetry.humidity.toFixed(0)}%
                        </span>
                      </div>
                      {analysisResult.sensorTelemetry.rain_level != null && (
                        <div className="flex justify-between text-xs">
                          <span>Rain Sensor:</span>
                          <span className="font-bold text-slate-900">
                            {analysisResult.sensorTelemetry.rain_level.toFixed(0)}%
                          </span>
                        </div>
                      )}
                      {analysisResult.decision ? (
                        <div className="pt-2 border-t border-slate-200 space-y-1">
                          <div className="flex justify-between items-center text-xs">
                            <span>Irrigation Status:</span>
                            <span
                              className={
                                formatIrrigationStatus(
                                  analysisResult.decision.irrigation_action,
                                  analysisResult.decision
                                ).colorClass
                              }
                            >
                              {
                                formatIrrigationStatus(
                                  analysisResult.decision.irrigation_action,
                                  analysisResult.decision
                                ).text
                              }
                            </span>
                          </div>
                          {analysisResult.decision.primary_action && (
                            <p className="text-xs text-slate-600 leading-snug">
                              {analysisResult.decision.primary_action}
                            </p>
                          )}
                        </div>
                      ) : (
                        <div className="flex justify-between items-center pt-2 border-t border-slate-200 text-xs">
                          <span>Irrigation Needed:</span>
                          <span className="text-slate-600 font-medium">Pending Data</span>
                        </div>
                      )}
                    </div>
                  ) : analysisResult.sensorStale ? (
                    <div className="space-y-1.5 text-slate-700 py-0.5">
                      <div className="flex items-center gap-1.5 text-amber-900 text-xs font-semibold bg-amber-50 p-2 rounded-lg border border-amber-200">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
                        <span>Sensor node offline (&gt;10s stale). Disconnected.</span>
                      </div>
                      {analysisResult.sensorTelemetry && (
                        <p className="text-xs text-slate-600 font-medium">
                          Last reading: {analysisResult.sensorTelemetry.soil_moisture.toFixed(1)}% moisture •{' '}
                          {analysisResult.sensorTelemetry.temperature.toFixed(1)}°C
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-600 italic">
                      No sensor telemetry ingested for this field. Diagnosis based on leaf pathology.
                    </p>
                  )}

                </div>

                {/* Panel 2: Live Weather Telemetry */}
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 flex items-center gap-1.5">
                      <CloudSun className="w-4 h-4 text-amber-600" />
                      <span>Local Weather</span>
                    </span>
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                        analysisResult.weatherAvailable
                          ? 'bg-blue-100 text-blue-900 border border-blue-200'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {analysisResult.weatherAvailable ? 'Live Telemetry' : 'Offline'}
                    </span>
                  </div>

                  {analysisResult.weatherAvailable && analysisResult.weather ? (
                    <div className="space-y-1.5 text-slate-700 font-medium">
                      <div className="flex justify-between">
                        <span className="truncate max-w-[130px]">{analysisResult.weather.location}:</span>
                        <span className="font-bold text-slate-900">
                          {analysisResult.weather.condition} • {analysisResult.weather.temperature.toFixed(1)}°C
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Precipitation Chance:</span>
                        <span className="font-bold text-slate-900">
                          {analysisResult.weather.rain_probability.toFixed(0)}%
                        </span>
                      </div>
                      {analysisResult.weather.is_rain_forecasted && (
                        <div className="pt-1.5 text-xs text-blue-900 font-bold flex items-center gap-1.5">
                          <CloudRain className="w-4 h-4 text-blue-600" />
                          <span>Rain forecasted in near term</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-600 italic">
                      Weather service not configured or unreachable. Analysis operates gracefully.
                    </p>
                  )}
                </div>
              </div>

              {/* FIELD & WEATHER ADVISORY */}
              {analysisResult.insights && analysisResult.insights.length > 0 && (
                <div className="bg-emerald-50/80 border border-emerald-300 rounded-xl p-4 space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-950 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-emerald-700" />
                    <span>Field & Weather Advisory:</span>
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-800 leading-relaxed font-medium">
                    {analysisResult.insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-emerald-700 font-bold mt-0.5">•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* What to do now */}
              <div className="bg-amber-50/90 rounded-xl p-4 border border-amber-300">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-900 block mb-1">
                  What to do now:
                </span>
                <p className="text-xs md:text-sm font-bold text-amber-950 leading-relaxed">
                  "{analysisResult.recommendedAction}"
                </p>
              </div>

              {/* Safe Agricultural Practices */}
              <div className="space-y-2 pt-1">
                <span className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
                  Safe Crop Care Guidelines:
                </span>
                <ul className="space-y-2 text-xs text-slate-700 font-medium">
                  {analysisResult.safePractices.map((practice, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-farm-600 shrink-0 mt-0.5" />
                      <span>{practice}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
                <button
                  onClick={onViewAdvice}
                  type="button"
                  className="py-3 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition text-center shadow-sm"
                >
                  View Irrigation Advice
                </button>
                <button
                  onClick={resetScan}
                  type="button"
                  className="flex items-center justify-center gap-1.5 py-3 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 font-bold text-xs md:text-sm active:scale-95 transition text-center"
                >
                  <RefreshCw className="w-3.5 h-3.5 text-slate-600" />
                  <span>Scan Another Leaf</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
