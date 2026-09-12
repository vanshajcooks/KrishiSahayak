'use client';

import React from 'react';
import { ShieldCheck, ShieldAlert, ArrowRight } from 'lucide-react';
import { HealthState, RiskLevel } from '@/types/farm';

interface CropHealthCardProps {
  status: HealthState;
  diseaseRisk: RiskLevel;
  summary: string;
  onViewDetails: () => void;
  isRealData?: boolean;
}

export const CropHealthCard: React.FC<CropHealthCardProps> = ({
  status,
  diseaseRisk,
  summary,
  onViewDetails,
}) => {
  let badgeStyle = 'bg-emerald-100 text-emerald-900 border-emerald-300';
  let Icon = ShieldCheck;

  if (status === 'NEEDS_ATTENTION') {
    badgeStyle = 'bg-amber-100 text-amber-900 border-amber-300';
    Icon = ShieldAlert;
  } else if (status === 'CRITICAL') {
    badgeStyle = 'bg-rose-100 text-rose-900 border-rose-300';
    Icon = ShieldAlert;
  }

  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-farm-100 text-farm-700 flex items-center justify-center shrink-0">
              <Icon className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">Crop Health</h3>
          </div>

          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeStyle}`}>
            {status === 'NEEDS_ATTENTION' ? 'Needs Attention' : status === 'CRITICAL' ? 'Critical' : 'Healthy'}
          </span>
        </div>

        {/* Disease Risk Pill */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs font-semibold text-slate-600">Disease Risk:</span>
          <span
            className={`text-xs font-black px-2.5 py-0.5 rounded-full ${
              diseaseRisk === 'HIGH'
                ? 'bg-rose-100 text-rose-900'
                : diseaseRisk === 'MEDIUM'
                ? 'bg-amber-100 text-amber-900'
                : 'bg-emerald-100 text-emerald-900'
            }`}
          >
            {diseaseRisk}
          </span>
        </div>

        {/* Summary Message */}
        <p className="text-xs text-slate-700 mt-2.5 leading-relaxed font-medium">
          "{summary}"
        </p>
      </div>

      {/* View Details Button */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 flex justify-end">
        <button
          onClick={onViewDetails}
          className="flex items-center gap-1 text-xs font-bold text-farm-700 hover:text-farm-800 active:scale-95 transition"
        >
          <span>View Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
