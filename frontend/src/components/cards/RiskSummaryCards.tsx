'use client';

import React from 'react';
import { Droplets, Flame, AlertOctagon } from 'lucide-react';
import { RiskItem, RiskLevel } from '@/types/farm';

interface RiskSummaryCardsProps {
  risks: RiskItem[];
  isRealData?: boolean;
}

export const RiskSummaryCards: React.FC<RiskSummaryCardsProps> = ({ risks, isRealData = false }) => {
  const getBadgeStyle = (level: RiskLevel) => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'LOW':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    }
  };

  const getIcon = (id: string) => {
    switch (id) {
      case 'waterStress':
        return <Droplets className="w-4 h-4 text-blue-600" />;
      case 'heatStress':
        return <Flame className="w-4 h-4 text-amber-600" />;
      case 'diseaseRisk':
        return <AlertOctagon className="w-4 h-4 text-rose-600" />;
      default:
        return <AlertOctagon className="w-4 h-4 text-slate-600" />;
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2 px-1">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Field Stress & Risks
        </h3>
        <span
          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
            isRealData
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-amber-50 text-amber-800 border-amber-200'
          }`}
        >
          {isRealData ? 'Live Sensor Data' : 'Simulated Data'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {risks.map((risk) => (
          <div
            key={risk.id}
            className="bg-white rounded-2xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="w-7 h-7 rounded-lg bg-slate-50 flex items-center justify-center">
                  {getIcon(risk.id)}
                </div>
                <span
                  className={`text-[9px] font-black px-1.5 py-0.5 rounded-full border ${getBadgeStyle(
                    risk.level
                  )}`}
                >
                  {risk.level}
                </span>
              </div>
              <h4 className="text-xs font-bold text-slate-900 leading-tight">
                {risk.name}
              </h4>
            </div>

            <p className="text-[10px] text-slate-500 mt-2 line-clamp-3 leading-snug">
              {risk.explanation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
