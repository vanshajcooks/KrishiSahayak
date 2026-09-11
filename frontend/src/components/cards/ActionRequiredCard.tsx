'use client';

import React from 'react';
import { AlertTriangle, CheckCircle, ArrowRight, Droplets, ShieldAlert } from 'lucide-react';
import { RecommendedAction } from '@/types/farm';

interface ActionRequiredCardProps {
  action: RecommendedAction;
  onViewAdvice: () => void;
  isRealData?: boolean;
}

export const ActionRequiredCard: React.FC<ActionRequiredCardProps> = ({
  action,
  onViewAdvice,
  isRealData = false,
}) => {
  const isUrgent = action.category === 'ACTION_REQUIRED';

  return (
    <div
      className={`rounded-2xl p-4 border shadow-sm transition ${
        isUrgent
          ? 'bg-amber-50/80 border-amber-300 ring-1 ring-amber-400/30'
          : 'bg-white border-slate-200'
      }`}
    >
      {/* Category Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          {isUrgent ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-200 text-amber-900">
              <AlertTriangle className="w-3 h-3 text-amber-700" />
              ACTION REQUIRED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              <CheckCircle className="w-3 h-3 text-emerald-600" />
              RECOMMENDED STATUS
            </span>
          )}
        </div>
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

      {/* Title & Context */}
      <h3 className="text-base font-bold text-slate-900 leading-snug">
        {action.title}
      </h3>
      <p className="text-xs text-slate-600 mt-1 leading-relaxed">
        {action.subtitle}
      </p>

      {/* Primary Action Box */}
      <div className="mt-3 bg-white/90 border border-slate-200/80 rounded-xl p-3">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
          What you should do:
        </span>
        <p className="text-xs font-semibold text-slate-900">
          {action.primaryAction}
        </p>
        {action.secondaryAction && (
          <p className="text-[11px] text-slate-600 mt-1 pt-1 border-t border-slate-100">
            <span className="font-semibold text-slate-700">Next: </span>
            {action.secondaryAction}
          </p>
        )}
      </div>

      {/* View Full Advice Button */}
      <div className="mt-3.5 flex items-center justify-end">
        <button
          onClick={onViewAdvice}
          className={`flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl transition active:scale-95 shadow-sm ${
            isUrgent
              ? 'bg-amber-600 hover:bg-amber-700 text-white'
              : 'bg-farm-700 hover:bg-farm-800 text-white'
          }`}
        >
          <span>View Full Advice</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
