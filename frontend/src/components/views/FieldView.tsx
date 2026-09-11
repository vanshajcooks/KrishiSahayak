'use client';

import React from 'react';
import {
  Droplets,
  Thermometer,
  CloudSun,
  Sun,
  TrendingDown,
  TrendingUp,
  Minus,
  Calendar,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { FarmState } from '@/types/farm';

interface FieldViewProps {
  state: FarmState;
}

export const FieldView: React.FC<FieldViewProps> = ({ state }) => {
  const moisture = state.soilMoisture;
  const ambient = state.ambient;

  // Simple timeline entries
  const timelineEvents = [
    { time: 'Today', event: 'Soil moisture low', type: 'warning' },
    { time: 'Today', event: 'Field sensors connected', type: 'info' },
    { time: 'Yesterday', event: 'Crop condition normal', type: 'normal' },
    { time: '2 days ago', event: 'Soil moisture in optimal range', type: 'normal' },
  ];

  return (
    <div className="space-y-4 pb-20 lg:pb-8">
      {/* View Header */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-900">
            {state.isRealData ? 'Field conditions — Live' : 'Field conditions — Simulated'}
          </h2>
          <p className="text-xs md:text-sm text-slate-600 mt-0.5">
            {state.profile.crop} • {state.profile.field}
          </p>
        </div>
        <span
          className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${
            state.isRealData
              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
              : 'bg-amber-100 text-amber-800 border-amber-300'
          }`}
        >
          {state.isRealData ? 'Live Sensor Data' : 'Simulated Data'}
        </span>
      </div>

      {/* Sensor Tiles Grid (2 cols mobile, 4 cols desktop) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
        {/* Soil Moisture */}
        <div className="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <Droplets className="w-4 h-4" />
              </div>
              <div className="flex items-center gap-0.5 text-xs font-bold text-rose-600">
                <TrendingDown className="w-3.5 h-3.5" />
                <span>Trend ↓</span>
              </div>
            </div>
            <span className="text-xs font-bold text-slate-500 block mt-2">Soil Moisture</span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {moisture.percentage}%
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100">
            <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded">
              {moisture.level}
            </span>
            <p className="text-[11px] text-slate-600 font-medium mt-1">
              {moisture.interpretation}
            </p>
          </div>
        </div>

        {/* Temperature */}
        <div className="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <Thermometer className="w-4 h-4" />
              </div>
              <div className="flex items-center gap-0.5 text-xs font-bold text-amber-600">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Trend ↑</span>
              </div>
            </div>
            <span className="text-xs font-bold text-slate-500 block mt-2">Temperature</span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {ambient.temperature}°C
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100">
            <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded">
              {ambient.temperature >= 35 ? 'Warm Heat' : 'Moderate'}
            </span>
            <p className="text-[11px] text-slate-600 font-medium mt-1">
              {ambient.temperature >= 35 ? 'High afternoon heat.' : 'Comfortable for crop.'}
            </p>
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                <CloudSun className="w-4 h-4" />
              </div>
              <div className="flex items-center gap-0.5 text-xs font-bold text-slate-400">
                <Minus className="w-3.5 h-3.5" />
                <span>Stable</span>
              </div>
            </div>
            <span className="text-xs font-bold text-slate-500 block mt-2">Air Humidity</span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {ambient.humidity}%
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100">
            <span className="text-[10px] font-bold text-sky-800 bg-sky-50 px-1.5 py-0.5 rounded">
              Relative
            </span>
            <p className="text-[11px] text-slate-600 font-medium mt-1">
              {ambient.humidity > 75 ? 'Humid air increases fungal risk.' : 'Normal air moisture.'}
            </p>
          </div>
        </div>

        {/* Sunlight Hours */}
        <div className="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center">
                <Sun className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-semibold text-slate-400">Daylight</span>
            </div>
            <span className="text-xs font-bold text-slate-500 block mt-2">Sun Exposure</span>
            {ambient.lightHours !== undefined && ambient.lightHours !== null && !state.isRealData ? (
              <span className="text-2xl font-black text-slate-900 block mt-0.5">
                {ambient.lightHours} hrs
              </span>
            ) : (
              <span className="text-sm md:text-base font-bold text-slate-500 block mt-1">
                Not available
              </span>
            )}
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100">
            {ambient.lightHours !== undefined && ambient.lightHours !== null && !state.isRealData ? (
              <>
                <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded">
                  Simulated
                </span>
                <p className="text-[11px] text-slate-600 font-medium mt-1">
                  Estimated daylight hours for scenario.
                </p>
              </>
            ) : (
              <>
                <span className="text-[10px] font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                  Sensor not connected
                </span>
                <p className="text-[11px] text-slate-500 font-medium mt-1">
                  Light sensor not installed on field node.
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 7-Day Soil Moisture Trend Graph (Recharts) */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm md:text-base font-bold text-slate-900">7-Day Soil Moisture</h3>
            <p className="text-[11px] md:text-xs text-slate-500">Volumetric moisture percentage (%)</p>
          </div>
          <span className="text-[10px] md:text-xs font-bold text-farm-700 bg-farm-50 px-2.5 py-1 rounded-full border border-farm-200">
            Safe zone: 35-65%
          </span>
        </div>

        <div className="h-52 lg:h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={state.moistureHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#cbd5e1" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} stroke="#cbd5e1" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.75rem',
                  fontSize: '11px',
                }}
              />
              <Line
                type="monotone"
                dataKey="moisture"
                name="Moisture %"
                stroke="#15803d"
                strokeWidth={2.5}
                dot={{ r: 3.5, fill: '#15803d' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Simple Farm History Timeline */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-1.5 mb-3">
          <Calendar className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm md:text-base font-bold text-slate-900">Farm History</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {timelineEvents.map((item, index) => (
            <div key={index} className="flex items-start gap-3 bg-slate-50 rounded-xl p-3 border border-slate-100">
              <div
                className={`w-3.5 h-3.5 rounded-full border-2 border-white shrink-0 mt-0.5 ${
                  item.type === 'warning'
                    ? 'bg-amber-500 ring-2 ring-amber-100'
                    : 'bg-farm-600 ring-2 ring-farm-100'
                }`}
              />
              <div className="flex-1 min-w-0">
                <span className="text-[10px] md:text-[11px] font-bold text-slate-400 block">{item.time}</span>
                <p className="text-xs md:text-sm font-semibold text-slate-800 mt-0.5">{item.event}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
