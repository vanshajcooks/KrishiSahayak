'use client';

import React from 'react';
import { Home, Camera, Gauge, Bell, Settings } from 'lucide-react';
import { ActiveTab, AppLanguage } from '@/types/farm';
import { translations } from '@/data/translations';

interface BottomNavProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  language: AppLanguage;
  alertCount: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  onTabChange,
  language,
  alertCount,
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
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-lg px-2 py-1.5 pb-safe">
      <div className="max-w-md mx-auto grid grid-cols-5 gap-1">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`relative flex flex-col items-center justify-center py-1 rounded-xl transition min-h-[50px] ${
                isActive
                  ? 'text-farm-700 font-bold bg-farm-50/70'
                  : 'text-slate-500 hover:text-slate-800 font-medium'
              }`}
            >
              <div className="relative">
                <Icon className={`w-5 h-5 transition-transform ${isActive ? 'scale-110 text-farm-700' : ''}`} />
                {Boolean(item.badge && item.badge > 0) && (
                  <span className="absolute -top-1 -right-2 w-4 h-4 bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[11px] mt-1 leading-none">{item.label}</span>
              {isActive && (
                <span className="w-1.5 h-1.5 bg-farm-700 rounded-full mt-1" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
