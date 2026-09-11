'use client';

import React from 'react';
import { Droplets, ArrowRight } from 'lucide-react';
import { SoilMoistureData } from '@/types/farm';

interface WaterStatusCardProps {
  moisture: SoilMoistureData;
  onViewAdvice: () => void;
  isRealData?: boolean;
}

export const WaterStatusCard: React.FC<WaterStatusCardProps> = ({
  moisture,
  onViewAdvice,
  isRealData = false,
}) => {
  const percentage = Math.max(0, Math.min(100, moisture.percentage));

  // Determine color and status styling
  let badgeClass = 'bg-emerald-100 text-emerald-800 border-emerald-200';
  let barColor = 'bg-emerald-500';

  if (moisture.level === 'LOW') {
    badgeClass = 'bg-rose-100 text-rose-800 border-rose-200';
    barColor = 'bg-rose-500';
  } else if (moisture.level === 'HIGH') {
    badgeClass = 'bg-blue-100 text-blue-800 border-blue-200';
    barColor = 'bg-blue-500';
  }

  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Droplets className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">Water Status</h3>
            <span className="text-[10px] font-bold text-slate-400 block mt-0.5">
              {isRealData ? 'Live Sensor Data' : 'Simulated Data'}
            </span>
          </div>
        </div>

        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${badgeClass}`}>
          STATUS: {moisture.level}
        </span>
      </div>

      {/* Moisture Display */}
      <div className="flex items-baseline justify-between mt-2">
        <div>
          <span className="text-2xl font-black text-slate-900 tracking-tight">
            {percentage}%
          </span>
          <span className="text-xs text-slate-500 ml-1.5 font-medium">Soil Moisture</span>
        </div>
        <p className="text-xs font-semibold text-slate-700">
          {moisture.interpretation}
        </p>
      </div>

      {/* Visual Progress Bar */}
      <div className="mt-3 w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Threshold Labels */}
      <div className="flex justify-between text-[10px] font-semibold text-slate-400 mt-1.5 px-0.5">
        <span>0% (Dry)</span>
        <span>Optimal (35-65%)</span>
        <span>100% (Wet)</span>
      </div>

      {/* Action Button */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 flex justify-end">
        <button
          onClick={onViewAdvice}
          className="flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-800 active:scale-95 transition"
        >
          <span>Irrigation Advice</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
