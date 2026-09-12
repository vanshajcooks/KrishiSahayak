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
}) => {
  const percentage = Math.max(0, Math.min(100, moisture.percentage));

  // Determine color and status styling
  let badgeClass = 'bg-emerald-100 text-emerald-900 border-emerald-300';
  let barColor = 'bg-emerald-600';

  if (moisture.level === 'LOW') {
    badgeClass = 'bg-rose-100 text-rose-900 border-rose-300';
    barColor = 'bg-rose-600';
  } else if (moisture.level === 'HIGH') {
    badgeClass = 'bg-blue-100 text-blue-900 border-blue-300';
    barColor = 'bg-blue-600';
  }

  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
              <Droplets className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">Water Status</h3>
          </div>

          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeClass}`}>
            {moisture.level === 'LOW' ? 'Needs Water (Low)' : moisture.level === 'HIGH' ? 'Overwatered' : 'Optimal'}
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
      <div className="flex justify-between text-xs font-semibold text-slate-500 mt-2 px-0.5">
        <span>0% (Dry)</span>
        <span>Optimal (35-65%)</span>
        <span>100% (Wet)</span>
      </div>
      </div>

      {/* Action Button */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 flex justify-end">
        <button
          onClick={onViewAdvice}
          className="flex items-center gap-1.5 text-xs font-bold text-blue-700 hover:text-blue-800 active:scale-95 transition"
        >
          <span>Irrigation Advice</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
