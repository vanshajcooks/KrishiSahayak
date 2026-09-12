'use client';

import React from 'react';
import { MapPin, Sprout, Clock } from 'lucide-react';
import { FarmProfile } from '@/types/farm';

interface FarmCardProps {
  profile: FarmProfile;
  lastUpdated: string;
  isRealData?: boolean;
}

export const FarmCard: React.FC<FarmCardProps> = ({
  profile,
  lastUpdated,
}) => {
  return (
    <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-farm-100 border border-farm-200 flex items-center justify-center text-farm-800 shrink-0">
            <Sprout className="w-7 h-7 text-farm-700" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                {profile.farmName}
              </span>
            </div>
            <h2 className="text-base md:text-lg font-black text-slate-900 leading-tight">
              Crop: <span className="text-farm-700">{profile.crop}</span>
            </h2>
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600 mt-0.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              <span>{profile.field}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 text-xs font-semibold text-slate-600 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{lastUpdated}</span>
        </div>
      </div>
    </div>
  );
};
