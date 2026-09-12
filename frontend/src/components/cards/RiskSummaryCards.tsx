'use client';

import React from 'react';
import { Droplets, Flame, AlertOctagon } from 'lucide-react';
import { RiskItem, RiskLevel } from '@/types/farm';

interface RiskSummaryCardsProps {
  risks: RiskItem[];
  isRealData?: boolean;
}

export const RiskSummaryCards: React.FC<RiskSummaryCardsProps> = ({ risks }) => {
  const getBadgeStyle = (level: RiskLevel) => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-100 text-rose-900 border-rose-300';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'LOW':
        return 'bg-emerald-100 text-emerald-900 border-emerald-300';
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
      <div className="flex items-center justify-between mb-2.5 px-1">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Field Stress & Disease Risk Breakdown
        </h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {risks.map((risk) => (
          <div
            key={risk.id}
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center border border-slate-100">
                  {getIcon(risk.id)}
                </div>
                <span
                  className={`text-xs font-black px-2 py-0.5 rounded-full border ${getBadgeStyle(
                    risk.level
                  )}`}
                >
                  {risk.level}
                </span>
              </div>
              <h4 className="text-sm font-bold text-slate-900 leading-tight">
                {risk.name}
              </h4>
            </div>

            <p className="text-xs text-slate-600 mt-2.5 leading-relaxed font-medium">
              {risk.explanation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
