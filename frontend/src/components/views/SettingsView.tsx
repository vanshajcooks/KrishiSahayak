'use client';

import React from 'react';
import {
  Globe,
  Bell,
  Mic,
  Sprout,
  MapPin,
  Thermometer,
  Sparkles,
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
} from 'lucide-react';
import { AppLanguage, AppMode, ConnectivityState } from '@/types/farm';
import { API_BASE_URL } from '@/services/api';

interface SettingsViewProps {
  language: AppLanguage;
  onLanguageChange: (lang: AppLanguage) => void;
  mode: AppMode;
  onModeChange: (mode: AppMode) => void;
  connectivity: ConnectivityState;
  onCheckConnection: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  language,
  onLanguageChange,
  mode,
  onModeChange,
  connectivity,
  onCheckConnection,
}) => {
  const [notifications, setNotifications] = React.useState(true);
  const [voiceAssistance, setVoiceAssistance] = React.useState(true);
  const [unit, setUnit] = React.useState<'C' | 'F'>('C');

  return (
    <div className="space-y-4 pb-20 lg:pb-8">
      {/* View Header */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-900">Settings</h2>
          <p className="text-xs md:text-sm text-slate-500">Preferences and operational mode</p>
        </div>
        <span
          className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${
            mode === 'real'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-amber-50 text-amber-800 border-amber-200'
          }`}
        >
          {mode === 'real' ? 'Live Sensor Data' : 'Simulated Data'}
        </span>
      </div>

      {/* Responsive Grid: Left = Operational Mode, Right = Preferences */}
      <div className="lg:grid lg:grid-cols-2 lg:gap-6 space-y-4 lg:space-y-0">
        {/* Left Column: Mode Switcher */}
        <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm space-y-3 flex flex-col justify-between">
          <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Operational Mode</h3>
              <p className="text-xs text-slate-500">Choose between live field gateway and judge demo</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={() => onModeChange('demo')}
            className={`p-3 rounded-xl border text-left transition ${
              mode === 'demo'
                ? 'bg-amber-50 border-amber-400 ring-2 ring-amber-400/20 text-amber-950 font-bold'
                : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 font-medium'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs">Demo Mode</span>
              {mode === 'demo' && <span className="w-2 h-2 rounded-full bg-amber-600" />}
            </div>
            <p className="text-[10px] text-slate-500 font-normal leading-tight">
              4 SIH Judge Scenarios without live sensors
            </p>
          </button>

          <button
            onClick={() => onModeChange('real')}
            className={`p-3 rounded-xl border text-left transition ${
              mode === 'real'
                ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-400/20 text-emerald-950 font-bold'
                : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 font-medium'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs">Live Field Mode</span>
              {mode === 'real' && <span className="w-2 h-2 rounded-full bg-emerald-600" />}
            </div>
            <p className="text-[10px] text-slate-500 font-normal leading-tight">
              Queries local backend gateway
            </p>
          </button>
        </div>

        {/* Real Mode Gateway Connection Status & Retry */}
        {mode === 'real' && (
          <div className="mt-2 bg-slate-50 rounded-xl p-3 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500 font-semibold">Gateway URL:</span>
              <code className="text-[11px] bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800">
                {API_BASE_URL}
              </code>
            </div>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-1.5 text-xs font-bold">
                {connectivity === 'CONNECTED_LIVE' ? (
                  <>
                    <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-800">Connected to Local Gateway</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3.5 h-3.5 text-rose-600" />
                    <span className="text-rose-800">Gateway Offline / Unreachable</span>
                  </>
                )}
              </div>

              <button
                onClick={onCheckConnection}
                className="flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 active:scale-95 transition"
              >
                <RefreshCw className="w-3 h-3 text-slate-600" />
                <span>Test Connection</span>
              </button>
            </div>
          </div>
        )}
        </div>
      </div>

      {/* Settings Options List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100">
        {/* Language Selection */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Globe className="w-5 h-5 text-slate-500" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Language</h4>
              <p className="text-[11px] text-slate-500">English or हिंदी</p>
            </div>
          </div>
          <div className="flex gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => onLanguageChange('en')}
              className={`px-3 py-1 rounded text-xs font-bold transition ${
                language === 'en'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              English
            </button>
            <button
              onClick={() => onLanguageChange('hi')}
              className={`px-3 py-1 rounded text-xs font-bold transition ${
                language === 'hi'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              हिंदी
            </button>
          </div>
        </div>

        {/* Notifications Toggle */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Bell className="w-5 h-5 text-slate-500" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Notifications</h4>
              <p className="text-[11px] text-slate-500">Urgent irrigation & disease alerts</p>
            </div>
          </div>
          <button
            onClick={() => setNotifications(!notifications)}
            className={`w-12 h-6 rounded-full transition p-0.5 relative ${
              notifications ? 'bg-farm-700' : 'bg-slate-300'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                notifications ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Voice Assistance Toggle */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Mic className="w-5 h-5 text-slate-500" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Voice Assistance</h4>
              <p className="text-[11px] text-slate-500">Enable voice dialogue prompts</p>
            </div>
          </div>
          <button
            onClick={() => setVoiceAssistance(!voiceAssistance)}
            className={`w-12 h-6 rounded-full transition p-0.5 relative ${
              voiceAssistance ? 'bg-farm-700' : 'bg-slate-300'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                voiceAssistance ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Units Toggle */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Thermometer className="w-5 h-5 text-slate-500" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Temperature Units</h4>
              <p className="text-[11px] text-slate-500">Celsius (°C) or Fahrenheit (°F)</p>
            </div>
          </div>
          <div className="flex gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setUnit('C')}
              className={`px-3 py-1 rounded text-xs font-bold transition ${
                unit === 'C'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              °C
            </button>
            <button
              onClick={() => setUnit('F')}
              className={`px-3 py-1 rounded text-xs font-bold transition ${
                unit === 'F'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              °F
            </button>
          </div>
        </div>

        {/* Crop Profile Info */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Sprout className="w-5 h-5 text-farm-700" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Crop</h4>
              <p className="text-[11px] text-slate-500">Currently monitored</p>
            </div>
          </div>
          <span className="text-xs font-bold text-slate-900 bg-slate-100 px-3 py-1 rounded-lg">
            Tomato
          </span>
        </div>

        {/* Field Profile Info */}
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <MapPin className="w-5 h-5 text-slate-500" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Field</h4>
              <p className="text-[11px] text-slate-500">Designated farm plot</p>
            </div>
          </div>
          <span className="text-xs font-bold text-slate-900 bg-slate-100 px-3 py-1 rounded-lg">
            Field 01
          </span>
        </div>
      </div>
    </div>
  </div>
);
};
