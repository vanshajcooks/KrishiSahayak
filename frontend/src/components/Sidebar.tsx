'use client';

import React from 'react';
import { Home, Camera, Gauge, Bell, Settings, Mic, Sprout, Sparkles, Wifi, WifiOff } from 'lucide-react';
import { ActiveTab, AppLanguage, AppMode, ConnectivityState } from '@/types/farm';
import { translations } from '@/data/translations';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  language: AppLanguage;
  alertCount: number;
  mode: AppMode;
  connectivity: ConnectivityState;
  onOpenVoice: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  language,
  alertCount,
  mode,
  connectivity,
  onOpenVoice,
}) => {
  const t = translations[language];

  const navItems = [
    { id: 'home' as ActiveTab, label: t.home, icon: Home },
    { id: 'scan' as ActiveTab, label: t.scan, icon: Camera },
    { id: 'field' as ActiveTab, label: t.fieldNav, icon: Gauge },
    { id: 'alerts' as ActiveTab, label: t.alerts, icon: Bell, badge: alertCount },
    { id: 'settings' as ActiveTab, label: t.settings, icon: Settings },
  ];

  return (
    <aside className="w-60 xl:w-64 bg-white border border-slate-200/80 rounded-2xl shadow-sm p-4 flex flex-col justify-between shrink-0 h-[calc(100vh-140px)] sticky top-24">
      {/* Top Nav Section */}
      <div className="space-y-6">
        {/* Navigation List */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 block mb-2">
            Navigation
          </span>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-semibold transition group ${
                    isActive
                      ? 'bg-farm-50 text-farm-800 font-bold border border-farm-200/80 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-5 h-5 transition-colors ${
                        isActive ? 'text-farm-700' : 'text-slate-400 group-hover:text-slate-600'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>

                  {Boolean(item.badge && item.badge > 0) && (
                    <span className="w-5 h-5 bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Operational Status Pill */}
        <div className="px-3 pt-2 border-t border-slate-100">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
            System Mode
          </span>
          {mode === 'demo' ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-2.5 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-bold">
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                <span>DEMO MODE</span>
              </div>
              <p className="text-[10px] text-amber-700 mt-1">Simulated Data</p>
            </div>
          ) : connectivity === 'CONNECTED_LIVE' ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-2.5 text-xs text-emerald-900">
              <div className="flex items-center gap-1.5 font-bold">
                <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                <span>LIVE FIELD</span>
              </div>
              <p className="text-[10px] text-emerald-700 mt-1">Live Sensor Data</p>
            </div>
          ) : (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-2.5 text-xs text-rose-900">
              <div className="flex items-center gap-1.5 font-bold">
                <WifiOff className="w-3.5 h-3.5 text-rose-600" />
                <span>DEVICE OFFLINE</span>
              </div>
              <p className="text-[10px] text-rose-700 mt-1">Local Data Unavailable</p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Action: Ask Farm Assistant */}
      <div className="pt-4 border-t border-slate-100">
        <button
          onClick={onOpenVoice}
          className="w-full flex items-center justify-center gap-2.5 py-3 px-4 rounded-xl bg-farm-700 hover:bg-farm-800 text-white font-bold text-xs active:scale-95 transition shadow-sm"
        >
          <Mic className="w-4 h-4 text-white" />
          <span>{t.askAssistant}</span>
        </button>
      </div>
    </aside>
  );
};
