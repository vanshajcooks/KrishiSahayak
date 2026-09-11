'use client';

import React from 'react';
import { Sparkles, CheckCircle2, Droplets, AlertOctagon, Flame } from 'lucide-react';
import { DEMO_SCENARIOS } from '@/data/demoScenarios';

interface DemoModeBarProps {
  currentScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
  onSwitchToReal: () => void;
}

export const DemoModeBar: React.FC<DemoModeBarProps> = ({
  currentScenarioId,
  onSelectScenario,
  onSwitchToReal,
}) => {
  return (
    <div className="bg-amber-50 border-b border-amber-200 text-xs">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 mb-2 sm:mb-0">
          <div className="flex items-center gap-2 font-semibold text-amber-900">
            <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="font-bold">Judge Demo Scenarios (SIH 26180)</span>
            <span className="hidden md:inline text-[11px] text-amber-700 bg-amber-200/60 px-2 py-0.5 rounded-full font-medium">
              Simulated Data Only
            </span>
          </div>

          <button
            onClick={onSwitchToReal}
            className="text-[11px] font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 px-2.5 py-1 rounded-lg transition self-start sm:self-auto border border-emerald-300 active:scale-95"
          >
            Switch to Live Field Mode
          </button>
        </div>

        {/* 4 Scenario Buttons (Responsive: 4 cols on mobile, horizontal flex on tablet/desktop) */}
        <div className="grid grid-cols-4 sm:flex sm:flex-wrap gap-1.5 mt-2 sm:mt-1.5">
          {DEMO_SCENARIOS.map((sc) => {
            const isActive = sc.id === currentScenarioId;
            let Icon = CheckCircle2;
            if (sc.number === 2) Icon = Droplets;
            if (sc.number === 3) Icon = AlertOctagon;
            if (sc.number === 4) Icon = Flame;

            return (
              <button
                key={sc.id}
                onClick={() => onSelectScenario(sc.id)}
                className={`flex items-center justify-center gap-1.5 p-1.5 sm:px-3 sm:py-1.5 rounded-lg border text-center transition active:scale-95 ${
                  isActive
                    ? 'bg-amber-600 border-amber-700 text-white font-bold shadow-sm'
                    : 'bg-white border-amber-200 text-amber-900 hover:bg-amber-100/70 font-medium'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-white' : 'text-amber-700'}`} />
                <span className="text-[10px] sm:text-xs leading-tight truncate">
                  <span className="font-bold">S{sc.number}:</span>{' '}
                  <span className="hidden sm:inline">{sc.name}</span>
                  <span className="sm:hidden">{sc.name.split(' ')[0]}</span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
