'use client';

import React from 'react';
import { Camera, ArrowRight } from 'lucide-react';
import { FarmState } from '@/types/farm';
import { FarmCard } from '../cards/FarmCard';
import { ActionRequiredCard } from '../cards/ActionRequiredCard';
import { WaterStatusCard } from '../cards/WaterStatusCard';
import { CropHealthCard } from '../cards/CropHealthCard';
import { WeatherCard } from '../cards/WeatherCard';
import { RiskSummaryCards } from '../cards/RiskSummaryCards';

interface HomeViewProps {
  state: FarmState;
  onNavigateToScan: () => void;
  onNavigateToIrrigation: () => void;
  onNavigateToCropHealth: () => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  state,
  onNavigateToScan,
  onNavigateToIrrigation,
  onNavigateToCropHealth,
}) => {
  return (
    <div className="space-y-4 md:space-y-5 pb-20 lg:pb-8">
      {/* 1. HERO: Immediate Farm Advice / Action Required Banner */}
      <ActionRequiredCard
        action={state.recommendation}
        onViewAdvice={onNavigateToIrrigation}
      />

      {/* 2. QUICK ACTIONS BAR: Check Leaf Health & Irrigation Details */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          onClick={onNavigateToScan}
          className="flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-farm-700 to-farm-800 text-white shadow-sm hover:from-farm-800 hover:to-farm-900 active:scale-[0.98] transition group text-left"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center text-white shrink-0">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <span className="text-sm md:text-base font-bold block leading-tight">
                Check Leaf Health
              </span>
              <span className="text-xs text-farm-100 mt-0.5 block font-medium">
                Scan leaf photo for disease symptoms
              </span>
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-white/80 group-hover:translate-x-0.5 transition-transform shrink-0" />
        </button>

        <button
          onClick={onNavigateToIrrigation}
          className="flex items-center justify-between p-4 rounded-2xl bg-white border border-slate-200 text-slate-900 shadow-sm hover:bg-slate-50 active:scale-[0.98] transition group text-left"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
              <Camera className="hidden" />
              <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
            </div>
            <div>
              <span className="text-sm md:text-base font-bold block leading-tight">
                Irrigation & Moisture
              </span>
              <span className="text-xs text-slate-500 mt-0.5 block font-medium">
                View soil water levels & weather forecast
              </span>
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
        </button>
      </div>

      {/* 3. FARM PROFILE: Farm Name, Crop Type, Field & Last Refresh */}
      <FarmCard
        profile={state.profile}
        lastUpdated={state.lastUpdated}
      />

      {/* 4. THREE-PANEL FIELD TRIAGE: Crop Health, Soil Moisture, Weather */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 md:gap-4">
        <CropHealthCard
          status={state.cropHealth.status}
          diseaseRisk={state.cropHealth.diseaseRisk}
          summary={state.cropHealth.summary}
          onViewDetails={onNavigateToCropHealth}
        />

        <WaterStatusCard
          moisture={state.soilMoisture}
          onViewAdvice={onNavigateToIrrigation}
        />

        <WeatherCard
          weather={state.weather}
        />
      </div>

      {/* 5. DETAILED FIELD RISKS: Water Stress, Heat Stress, Disease Spread */}
      <RiskSummaryCards
        risks={state.risks}
      />
    </div>
  );
};
