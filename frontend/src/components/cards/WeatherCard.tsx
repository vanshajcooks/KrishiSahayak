'use client';

import React from 'react';
import { CloudSun, Droplets, Thermometer, CloudRain } from 'lucide-react';
import { WeatherData } from '@/types/farm';

interface WeatherCardProps {
  weather: WeatherData;
  isRealData?: boolean;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather, isRealData = false }) => {
  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
            <CloudSun className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 leading-tight">Weather</h3>
            <span className="text-[10px] font-bold text-slate-400 block mt-0.5">
              {isRealData ? 'Live Sensor Data' : 'Simulated Data'}
            </span>
          </div>
        </div>

        <span className="text-[11px] font-semibold text-slate-500">
          {weather.condition}
        </span>
      </div>

      {/* Primary Metrics Row */}
      <div className="grid grid-cols-3 gap-2 my-2 bg-slate-50 rounded-xl p-2.5 border border-slate-100">
        <div className="flex flex-col items-center text-center">
          <div className="flex items-center text-slate-400 mb-0.5">
            <Thermometer className="w-3.5 h-3.5 text-amber-600 mr-0.5" />
            <span className="text-[10px] uppercase font-bold">Temp</span>
          </div>
          <span className="text-base font-extrabold text-slate-800">
            {weather.temperature}°C
          </span>
        </div>

        <div className="flex flex-col items-center text-center border-x border-slate-200">
          <div className="flex items-center text-slate-400 mb-0.5">
            <Droplets className="w-3.5 h-3.5 text-blue-600 mr-0.5" />
            <span className="text-[10px] uppercase font-bold">Humidity</span>
          </div>
          <span className="text-base font-extrabold text-slate-800">
            {weather.humidity}%
          </span>
        </div>

        <div className="flex flex-col items-center text-center">
          <div className="flex items-center text-slate-400 mb-0.5">
            <CloudRain className="w-3.5 h-3.5 text-sky-600 mr-0.5" />
            <span className="text-[10px] uppercase font-bold">Rain</span>
          </div>
          <span className="text-base font-extrabold text-slate-800">
            {weather.rainProbability}%
          </span>
        </div>
      </div>

      {/* Short Interpretation */}
      <p className="text-xs text-slate-600 font-medium my-2">
        "{weather.interpretation}"
      </p>

      {/* Forecast Row (Today | Tomorrow | Day 3) */}
      <div className="grid grid-cols-3 gap-1.5 pt-2 border-t border-slate-100">
        {weather.forecast.map((fc, idx) => (
          <div
            key={idx}
            className="flex flex-col items-center bg-slate-50/70 rounded-lg py-1.5 px-1 text-center"
          >
            <span className="text-[10px] font-bold text-slate-600">{fc.day}</span>
            <span className="text-xs font-black text-slate-800 my-0.5">
              {fc.tempMax}° / {fc.tempMin}°
            </span>
            <span className="text-[9px] font-medium text-slate-500">
              Rain: {fc.rainChance}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
