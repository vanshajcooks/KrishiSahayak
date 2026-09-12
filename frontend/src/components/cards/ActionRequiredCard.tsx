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
}) => {
  const isUrgent = action.category === 'ACTION_REQUIRED';

  return (
    <div
      className={`rounded-2xl p-5 md:p-6 border shadow-sm transition ${
        isUrgent
          ? 'bg-amber-50/90 border-amber-300 ring-1 ring-amber-400/40'
          : 'bg-emerald-50/70 border-emerald-300 ring-1 ring-emerald-400/30'
      }`}
    >
      {/* Category Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isUrgent ? (
            <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full bg-amber-200 text-amber-900 border border-amber-300">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-800" />
              IMMEDIATE FARM ACTION
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-700" />
              FARM STATUS STABLE
            </span>
          )}
        </div>
      </div>

      {/* Title & Context */}
      <h3 className="text-lg md:text-xl font-black text-slate-900 leading-tight">
        {action.title}
      </h3>
      <p className="text-xs md:text-sm text-slate-700 mt-1.5 leading-relaxed font-medium">
        {action.subtitle}
      </p>

      {/* Primary Action Box */}
      <div className="mt-4 bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">
          What you should do now:
        </span>
        <p className="text-sm md:text-base font-bold text-slate-900 leading-snug">
          {action.primaryAction}
        </p>
        {action.secondaryAction && (
          <p className="text-xs text-slate-700 mt-2 pt-2 border-t border-slate-100 font-medium">
            <span className="font-bold text-slate-800">Next Step: </span>
            {action.secondaryAction}
          </p>
        )}
      </div>

      {/* View Full Advice Button */}
      <div className="mt-4 flex items-center justify-end">
        <button
          onClick={onViewAdvice}
          className={`flex items-center gap-2 text-xs md:text-sm font-bold px-4 py-2.5 rounded-xl transition active:scale-95 shadow-sm ${
            isUrgent
              ? 'bg-amber-700 hover:bg-amber-800 text-white'
              : 'bg-farm-700 hover:bg-farm-800 text-white'
          }`}
        >
          <span>View Full Advice</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
