'use client';

import React from 'react';
import { Sprout, Bell, Globe, Wifi, WifiOff, Sparkles } from 'lucide-react';
import { AppLanguage, AppMode, ConnectivityState } from '@/types/farm';
import { translations } from '@/data/translations';

interface HeaderProps {
  language: AppLanguage;
  onLanguageChange: (lang: AppLanguage) => void;
  mode: AppMode;
  connectivity: ConnectivityState;
  alertCount: number;
  onAlertClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  onLanguageChange,
  mode,
  connectivity,
  alertCount,
  onAlertClick,
}) => {
  const t = translations[language];

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
        {/* Brand & Assistant Title */}
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-farm-700 flex items-center justify-center text-white shadow-sm shadow-farm-800/20">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">
              {t.appTitle}
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              {mode === 'demo' ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
                  <Sparkles className="w-3 h-3" />
                  <span>DEMO MODE</span>
                  <span className="text-amber-600 font-normal">• Simulated Data</span>
                </span>
              ) : connectivity === 'CONNECTED_LIVE' ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  <Wifi className="w-3 h-3" />
                  <span>LIVE FIELD</span>
                  <span className="text-emerald-600 font-normal">• Live Sensor Data</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-rose-800 bg-rose-100 px-2 py-0.5 rounded-full">
                  <WifiOff className="w-3 h-3" />
                  <span>DEVICE OFFLINE</span>
                  <span className="text-rose-600 font-normal">• Local Data Unavailable</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Controls: Language & Alerts */}
        <div className="flex items-center gap-2">
          {/* Language Switcher */}
          <button
            onClick={() => onLanguageChange(language === 'en' ? 'hi' : 'en')}
            className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 active:scale-95 transition"
            title="Switch Language"
          >
            <Globe className="w-3.5 h-3.5 text-farm-700" />
            <span>{language === 'en' ? 'हिंदी' : 'English'}</span>
          </button>

          {/* Notifications Bell */}
          <button
            onClick={onAlertClick}
            className="relative p-2 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 active:scale-95 transition"
            aria-label="View Alerts"
          >
            <Bell className="w-5 h-5 text-slate-700" />
            {alertCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                {alertCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
