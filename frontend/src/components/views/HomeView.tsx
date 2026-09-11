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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 md:gap-4 pb-20 lg:pb-8">
      {/* Row 1: Farm Card (Full width across all screen sizes) */}
      <div className="md:col-span-2 lg:col-span-3 order-1">
        <FarmCard
          profile={state.profile}
          lastUpdated={state.lastUpdated}
          isRealData={state.isRealData}
        />
      </div>

      {/* Recommended Action:
          Mobile: order-2 (immediately prominent below Farm Card)
          Tablet: order-2 (spans 2 cols)
          Desktop: order-3 (Row 3, spanning the entire 3-column width)
      */}
      <div className="md:col-span-2 lg:col-span-3 order-2 lg:order-3">
        <ActionRequiredCard
          action={state.recommendation}
          onViewAdvice={onNavigateToIrrigation}
          isRealData={state.isRealData}
        />
      </div>

      {/* Row 2 on Desktop: 3-column triage of crop indicators */}
      {/* Crop Health Card */}
      <div className="md:col-span-1 lg:col-span-1 order-5 md:order-4 lg:order-2 flex flex-col">
        <CropHealthCard
          status={state.cropHealth.status}
          diseaseRisk={state.cropHealth.diseaseRisk}
          summary={state.cropHealth.summary}
          onViewDetails={onNavigateToCropHealth}
          isRealData={state.isRealData}
        />
      </div>

      {/* Water Status Card */}
      <div className="md:col-span-1 lg:col-span-1 order-4 md:order-3 lg:order-2 flex flex-col">
        <WaterStatusCard
          moisture={state.soilMoisture}
          onViewAdvice={onNavigateToIrrigation}
          isRealData={state.isRealData}
        />
      </div>

      {/* Weather Card */}
      <div className="md:col-span-1 lg:col-span-1 order-6 md:order-5 lg:order-2 flex flex-col">
        <WeatherCard
          weather={state.weather}
          isRealData={state.isRealData}
        />
      </div>

      {/* Row 4 on Desktop: Field Risks (Water Stress | Heat Stress | Disease Risk) */}
      <div className="md:col-span-2 lg:col-span-3 order-7 lg:order-4">
        <RiskSummaryCards
          risks={state.risks}
          isRealData={state.isRealData}
        />
      </div>

      {/* Row 5 on Desktop: Quick Crop Scan Banner Card */}
      <div className="md:col-span-1 lg:col-span-3 order-3 md:order-6 lg:order-5">
        <div className="bg-gradient-to-r from-farm-700 to-farm-800 rounded-2xl p-4 md:p-5 text-white shadow-md shadow-farm-900/10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 h-full">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center text-white shrink-0">
              <Camera className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm md:text-base font-bold leading-tight">Scan Your Crop</h3>
              <p className="text-xs md:text-sm text-farm-100 mt-0.5">
                Take a clear leaf photo to check for possible disease symptoms.
              </p>
            </div>
          </div>

          <button
            onClick={onNavigateToScan}
            className="flex items-center justify-center gap-1.5 text-xs md:text-sm font-bold px-4 py-2.5 rounded-xl bg-white text-farm-800 hover:bg-farm-50 active:scale-95 transition shadow-sm shrink-0 self-start sm:self-auto"
          >
            <span>Scan Crop</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
