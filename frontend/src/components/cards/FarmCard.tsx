'use client';

import React from 'react';
import { MapPin, Sprout, Clock } from 'lucide-react';
import { FarmProfile } from '@/types/farm';

interface FarmCardProps {
  profile: FarmProfile;
  lastUpdated: string;
  isRealData: boolean;
}

export const FarmCard: React.FC<FarmCardProps> = ({
  profile,
  lastUpdated,
  isRealData,
}) => {
  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-farm-100 border border-farm-200 flex items-center justify-center text-farm-800">
            <Sprout className="w-6 h-6 text-farm-700" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                {profile.farmName}
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-900 leading-tight">
              Crop: <span className="text-farm-700">{profile.crop}</span>
            </h2>
            <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <span>{profile.field}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isRealData
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-amber-100 text-amber-800'
            }`}
          >
            {isRealData ? 'Live Sensor Data' : 'Simulated Data'}
          </span>
          <div className="flex items-center gap-1 text-[10px] text-slate-400 mt-1">
            <Clock className="w-3 h-3" />
            <span>{lastUpdated}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
