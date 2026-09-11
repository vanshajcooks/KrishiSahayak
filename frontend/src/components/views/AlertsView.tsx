'use client';

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Flame,
  Droplets,
  AlertOctagon,
  CheckCircle,
  X,
  Bell,
  ArrowRight,
} from 'lucide-react';
import { FarmAlert, SeverityLevel } from '@/types/farm';

interface AlertsViewProps {
  initialAlerts: FarmAlert[];
  isRealData?: boolean;
  onNavigateToIrrigation: () => void;
  onNavigateToScan: () => void;
}

export const AlertsView: React.FC<AlertsViewProps> = ({
  initialAlerts,
  isRealData = false,
  onNavigateToIrrigation,
  onNavigateToScan,
}) => {
  const [alerts, setAlerts] = useState<FarmAlert[]>(initialAlerts);

  // Synchronize alerts immediately when the demo scenario or real state changes
  useEffect(() => {
    setAlerts(initialAlerts);
  }, [initialAlerts]);

  // Dismiss an alert
  const dismissAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  // Severity rank comparator for sorting: HIGH > MEDIUM > LOW
  const severityRank: Record<SeverityLevel, number> = {
    HIGH: 3,
    MEDIUM: 2,
    LOW: 1,
  };

  const sortedAlerts = [...alerts].sort(
    (a, b) => severityRank[b.severity] - severityRank[a.severity]
  );

  const getAlertIcon = (category: string) => {
    if (category.toLowerCase().includes('water')) {
      return <Droplets className="w-4 h-4 text-blue-600" />;
    }
    if (category.toLowerCase().includes('heat')) {
      return <Flame className="w-4 h-4 text-amber-600" />;
    }
    return <AlertOctagon className="w-4 h-4 text-rose-600" />;
  };

  return (
    <div className="space-y-4 pb-20 lg:pb-8">
      {/* Header */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-900">
            {isRealData ? 'Farm Alerts — Live' : 'Farm Alerts — Simulated'}
          </h2>
          <p className="text-xs md:text-sm text-slate-500">Sorted by urgency and severity</p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span
            className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${
              isRealData
                ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                : 'bg-amber-100 text-amber-800 border-amber-300'
            }`}
          >
            {isRealData ? 'Live Sensor Data' : 'Simulated Data'}
          </span>
          <span className="text-xs md:text-sm font-bold px-3 py-1 rounded-full bg-slate-100 text-slate-700">
            {alerts.length} Active
          </span>
        </div>
      </div>

      {/* Empty State */}
      {sortedAlerts.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
            <CheckCircle className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">No Active Alerts</h3>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            All field conditions are currently within normal thresholds.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedAlerts.map((alert) => {
            const isHigh = alert.severity === 'HIGH';

            return (
              <div
                key={alert.id}
                className={`bg-white rounded-2xl p-4 border shadow-sm transition relative overflow-hidden ${
                  isHigh
                    ? 'border-rose-300 ring-1 ring-rose-400/20'
                    : 'border-amber-200'
                }`}
              >
                {/* Severity indicator line */}
                <div
                  className={`absolute top-0 left-0 bottom-0 w-1.5 ${
                    isHigh ? 'bg-rose-500' : 'bg-amber-500'
                  }`}
                />

                <div className="pl-1">
                  {/* Top Bar: Category & Dismiss */}
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <div className="w-6 h-6 rounded-md bg-slate-100 flex items-center justify-center">
                        {getAlertIcon(alert.category)}
                      </div>
                      <span
                        className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
                          isHigh
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {alert.severity} — {alert.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-400">
                        {alert.timestamp}
                      </span>
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
                        title="Dismiss alert"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Alert Title & Message */}
                  <h3 className="text-sm font-bold text-slate-900 mt-1">
                    {alert.title}
                  </h3>
                  <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                    "{alert.message}"
                  </p>

                  {/* Recommended Action */}
                  <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Action
                      </span>
                      <p className="text-xs font-bold text-slate-800">
                        {alert.action}
                      </p>
                    </div>

                    {alert.category.toLowerCase().includes('water') && (
                      <button
                        onClick={onNavigateToIrrigation}
                        className="text-xs font-bold text-blue-700 hover:text-blue-800 flex items-center gap-1 active:scale-95 transition"
                      >
                        <span>Irrigate</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}

                    {alert.category.toLowerCase().includes('disease') && (
                      <button
                        onClick={onNavigateToScan}
                        className="text-xs font-bold text-farm-700 hover:text-farm-800 flex items-center gap-1 active:scale-95 transition"
                      >
                        <span>Scan</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
