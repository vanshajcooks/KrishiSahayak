'use client';

import React, { useState } from 'react';
import {
  Droplets,
  Thermometer,
  CloudRain,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
import { FarmState } from '@/types/farm';

interface IrrigationViewProps {
  state: FarmState;
  onBack: () => void;
}

export const IrrigationView: React.FC<IrrigationViewProps> = ({
  state,
  onBack,
}) => {
  const [isMarkedDone, setIsMarkedDone] = useState(false);

  const moisture = state.soilMoisture;
  const ambient = state.ambient;
  const weather = state.weather;

  return (
    <div className="space-y-4 pb-20 lg:pb-8 max-w-3xl mx-auto">
      {/* Header with back button */}
      <div className="flex items-center gap-2">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 active:scale-95 transition"
        >
          <ArrowLeft className="w-4 h-4 text-slate-700" />
        </button>
        <div>
          <h2 className="text-base font-bold text-slate-900">Irrigation Advice</h2>
          <p className="text-xs text-slate-500">Field 01 • Water Management</p>
        </div>
      </div>

      {/* Moisture Status Card */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Droplets className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-slate-600">Current Soil Moisture</span>
          </div>
          <span
            className={`text-xs font-black px-2.5 py-0.5 rounded-full border ${
              moisture.level === 'LOW'
                ? 'bg-rose-100 text-rose-800 border-rose-200'
                : moisture.level === 'HIGH'
                ? 'bg-blue-100 text-blue-800 border-blue-200'
                : 'bg-emerald-100 text-emerald-800 border-emerald-200'
            }`}
          >
            STATUS: {moisture.level}
          </span>
        </div>

        <div className="flex items-baseline justify-between mt-3">
          <span className="text-3xl font-black text-slate-900">
            {moisture.percentage}%
          </span>
          <span className="text-xs font-semibold text-slate-600">
            {moisture.interpretation}
          </span>
        </div>
      </div>

      {/* Field Conditions Grid */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
          Current Conditions
        </h3>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-100">
            <Thermometer className="w-4 h-4 text-amber-600 mx-auto mb-1" />
            <span className="text-[10px] text-slate-500 block">Temperature</span>
            <span className="text-sm font-extrabold text-slate-800">
              {ambient.temperature}°C
            </span>
          </div>

          <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-100">
            <Droplets className="w-4 h-4 text-blue-600 mx-auto mb-1" />
            <span className="text-[10px] text-slate-500 block">Humidity</span>
            <span className="text-sm font-extrabold text-slate-800">
              {ambient.humidity}%
            </span>
          </div>

          <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-100">
            <CloudRain className="w-4 h-4 text-sky-600 mx-auto mb-1" />
            <span className="text-[10px] text-slate-500 block">Rain Expected</span>
            <span className="text-sm font-extrabold text-slate-800">
              {weather.rainProbability < 20 ? 'Low' : 'Moderate'}
            </span>
          </div>
        </div>
      </div>

      {/* Recommendation & Reasons Card */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 w-fit">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Decision Recommendation</span>
        </div>

        <div>
          <h3 className="text-base font-bold text-slate-900">
            {state.recommendation.title}
          </h3>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
            "{state.recommendation.subtitle}"
          </p>
        </div>

        {/* Reasons Breakdown */}
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 space-y-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Why this is recommended:
          </span>
          {state.recommendation.reasons.map((reason, idx) => (
            <div key={idx} className="flex items-start gap-2 text-xs text-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-farm-600 mt-1.5 shrink-0" />
              <span>{reason}</span>
            </div>
          ))}
        </div>

        {/* Action Completion Button */}
        <div className="pt-2">
          {isMarkedDone ? (
            <div className="flex items-center justify-center gap-2 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Irrigation Marked as Completed</span>
            </div>
          ) : (
            <button
              onClick={() => setIsMarkedDone(true)}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs active:scale-95 transition shadow-sm"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Mark as Done</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
