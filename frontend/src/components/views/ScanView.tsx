'use client';

import React, { useState } from 'react';
import {
  Camera,
  UploadCloud,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  Lightbulb,
  ShieldAlert,
  FileCheck,
  Sparkles,
} from 'lucide-react';
import { CropScanAnalysis } from '@/types/farm';

interface ScanViewProps {
  onBackToHome: () => void;
  onViewAdvice: () => void;
  presetScan?: CropScanAnalysis;
}

export const ScanView: React.FC<ScanViewProps> = ({
  onBackToHome,
  onViewAdvice,
  presetScan,
}) => {
  type ScanStage = 'idle' | 'preview' | 'analyzing' | 'result';

  const [stage, setStage] = useState<ScanStage>('idle');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  // Realistic mock diagnostic result adhering to safe advisory guidelines
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
    }
  );

  const simulateCapture = () => {
    setSelectedImage('/sample-leaf.svg');
    setStage('preview');
  };

  const runAnalysis = () => {
    setStage('analyzing');
    setTimeout(() => {
      setStage('result');
    }, 1600);
  };

  const resetScan = () => {
    setSelectedImage(null);
    setStage('idle');
  };

  return (
    <div className="space-y-4 pb-20 lg:pb-8">
      {/* View Header */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-900">Scan Your Crop</h2>
          <p className="text-xs md:text-sm text-slate-600 mt-0.5">
            Take a clear leaf photo to check for possible disease symptoms.
          </p>
        </div>
        <span className="text-[11px] font-bold text-amber-800 bg-amber-100 px-2.5 py-1 rounded-full border border-amber-200 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-600" />
          <span>Simulated Data</span>
        </span>
      </div>

      {/* Main Responsive Container (1 col mobile/tablet, 2 cols desktop) */}
      <div className="lg:grid lg:grid-cols-12 lg:gap-6 space-y-4 lg:space-y-0">
        {/* Left Column: Camera / Image Preview (5 cols on desktop) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Camera Viewfinder
              </span>
              <span className="text-[10px] font-semibold text-slate-400">
                {stage === 'result' ? 'Scan Completed' : 'Ready'}
              </span>
            </div>

            {/* Viewfinder Display Box */}
            <div className="relative aspect-[4/3] rounded-xl bg-slate-900 border-2 border-dashed border-slate-600 flex flex-col items-center justify-center p-6 text-center overflow-hidden">
              {/* Corner Viewfinder Brackets */}
              <div className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-farm-400" />
              <div className="absolute top-3 right-3 w-6 h-6 border-t-2 border-r-2 border-farm-400" />
              <div className="absolute bottom-3 left-3 w-6 h-6 border-b-2 border-l-2 border-farm-400" />
              <div className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-farm-400" />

              {stage === 'idle' && (
                <>
                  <div className="w-14 h-14 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-farm-400 mb-2">
                    <Camera className="w-7 h-7" />
                  </div>
                  <p className="text-xs md:text-sm font-semibold text-slate-200">
                    Point camera at a single crop leaf
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Ensure proper natural lighting
                  </p>
                </>
              )}

              {(stage === 'preview' || stage === 'analyzing' || stage === 'result') && (
                <div className="flex flex-col items-center justify-center text-white">
                  <div className="w-16 h-16 rounded-2xl bg-farm-900/70 border border-farm-400 flex items-center justify-center mb-2 shadow-inner">
                    <FileCheck className="w-8 h-8 text-farm-300" />
                  </div>
                  <p className="text-sm font-bold">Leaf Sample Captured</p>
                  <p className="text-xs text-slate-300 mt-0.5">
                    {stage === 'result' ? 'Checked against crop health model (Simulated)' : 'Ready for analysis'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Tip beneath viewfinder */}
          <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2 text-amber-900">
            <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <span className="font-bold">Tip: </span>Keep the leaf clearly visible and avoid very dark images or blurry angles.
            </p>
          </div>
        </div>

        {/* Right Column: Interactive Controls & Analysis State (7 cols on desktop) */}
        <div className="lg:col-span-7">
          {/* STAGE 1: IDLE / ACTIONS */}
          {stage === 'idle' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Choose Capture Method</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Take a new leaf photo using your device camera or select an existing field image.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={simulateCapture}
                  className="flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm"
                >
                  <Camera className="w-4 h-4" />
                  <span>Take Photo</span>
                </button>

                <button
                  onClick={simulateCapture}
                  className="flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 font-bold text-xs md:text-sm active:scale-95 transition"
                >
                  <UploadCloud className="w-4 h-4 text-slate-600" />
                  <span>Upload Photo</span>
                </button>
              </div>

              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs text-slate-600 space-y-1">
                <span className="font-bold text-slate-800 block">How to get a better scan result:</span>
                <p>1. Center a single diseased leaf in the viewfinder.</p>
                <p>2. Keep camera steady to avoid motion blur.</p>
                <p>3. Capture both healthy green areas and discoloration spots.</p>
              </div>
            </div>
          )}

          {/* STAGE 2: PREVIEW STATE */}
          {stage === 'preview' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Review Leaf Photo</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Confirm the leaf spots are clearly visible before running diagnosis.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={runAnalysis}
                  className="py-3.5 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm"
                >
                  Analyze Leaf
                </button>
                <button
                  onClick={resetScan}
                  className="py-3.5 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs md:text-sm active:scale-95 transition"
                >
                  Retake Photo
                </button>
              </div>
            </div>
          )}

          {/* STAGE 3: ANALYZING STATE */}
          {stage === 'analyzing' && (
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center space-y-3">
              <div className="w-14 h-14 rounded-full border-4 border-farm-200 border-t-farm-700 animate-spin" />
              <h3 className="text-sm font-bold text-slate-900">Analyzing Leaf Health...</h3>
              <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                Examining leaf discoloration, spot patterns, and fungal symptoms against crop health models.
              </p>
            </div>
          )}

          {/* STAGE 4: RESULT STATE */}
          {stage === 'result' && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3.5">
              {/* Result Header Badge */}
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-200">
                  Possible Disease Detected (Simulated)
                </span>
                <span className="text-xs font-bold text-slate-500">
                  Confidence: <span className="text-slate-900">{analysisResult.confidence}% (Simulated)</span>
                </span>
              </div>

              {/* Disease Title & Severity */}
              <div>
                <h3 className="text-lg md:text-xl font-black text-slate-900">
                  {analysisResult.diseaseName}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-semibold text-slate-600">Severity:</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-900">
                    {analysisResult.severity}
                  </span>
                </div>
              </div>

              {/* What We Found */}
              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  What we found:
                </span>
                <p className="text-xs md:text-sm text-slate-800 leading-relaxed font-medium">
                  "{analysisResult.findings}"
                </p>
              </div>

              {/* Recommended Action */}
              <div className="bg-amber-50 rounded-xl p-3.5 border border-amber-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 block mb-1">
                  Recommended Action:
                </span>
                <p className="text-xs md:text-sm font-bold text-amber-950 leading-relaxed">
                  "{analysisResult.recommendedAction}"
                </p>
              </div>

              {/* Safe Agricultural Practices */}
              <div className="space-y-1.5 pt-1">
                <span className="text-xs font-bold text-slate-700 block">
                  Safe Management Guidelines:
                </span>
                <ul className="space-y-1.5 text-xs text-slate-600">
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
                  className="py-3 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs md:text-sm active:scale-95 transition text-center shadow-sm"
                >
                  View Advice
                </button>
                <button
                  onClick={resetScan}
                  className="flex items-center justify-center gap-1.5 py-3 px-4 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 font-bold text-xs md:text-sm active:scale-95 transition text-center"
                >
                  <RefreshCw className="w-3.5 h-3.5 text-slate-600" />
                  <span>Scan Another</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
