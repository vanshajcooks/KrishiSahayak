'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  ActiveTab,
  AppLanguage,
  AppMode,
  ConnectivityState,
  FarmState,
} from '@/types/farm';
import { DEMO_SCENARIOS } from '@/data/demoScenarios';
import {
  checkBackendHealth,
  fetchLatestSensorReading,
  convertRealSensorToFarmState,
  API_BASE_URL,
} from '@/services/api';

import { Header } from '@/components/Header';
import { DemoModeBar } from '@/components/DemoModeBar';
import { BottomNav } from '@/components/BottomNav';
import { Sidebar } from '@/components/Sidebar';
import { VoiceModal } from '@/components/VoiceModal';

import { HomeView } from '@/components/views/HomeView';
import { ScanView } from '@/components/views/ScanView';
import { FieldView } from '@/components/views/FieldView';
import { AlertsView } from '@/components/views/AlertsView';
import { IrrigationView } from '@/components/views/IrrigationView';
import { SettingsView } from '@/components/views/SettingsView';

import { Mic, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';

export default function App() {
  // App navigation and settings state
  const [activeTab, setActiveTab] = useState<ActiveTab>('home');
  const [language, setLanguage] = useState<AppLanguage>('en');
  const [mode, setMode] = useState<AppMode>('demo');
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_2'); // Default to Water Stress for vivid demonstration

  // Real Mode state
  const [connectivity, setConnectivity] = useState<ConnectivityState>('DEMO_MODE');
  const [realFarmState, setRealFarmState] = useState<FarmState | null>(null);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // Voice Assistant dialogue modal state
  const [isVoiceOpen, setIsVoiceOpen] = useState<boolean>(false);

  // Derive current display state
  const currentScenario =
    DEMO_SCENARIOS.find((s) => s.id === selectedScenarioId) || DEMO_SCENARIOS[0];

  // Active state: In Demo Mode, always use chosen scenario. In Real Mode, use fetched real state.
  const activeState: FarmState =
    mode === 'demo'
      ? currentScenario.state
      : realFarmState || currentScenario.state;

  // Real Mode backend query
  const syncWithBackend = useCallback(async () => {
    setIsConnecting(true);
    setConnectionError(null);

    const health = await checkBackendHealth();

    if (!health.isOnline) {
      setConnectivity('DEVICE_OFFLINE');
      setRealFarmState(null);
      setConnectionError(
        `Unable to reach local field gateway at ${API_BASE_URL}. Ensure FastAPI backend is running.`
      );
      setIsConnecting(false);
      return;
    }

    // Backend is online, fetch latest telemetry
    const sensorRes = await fetchLatestSensorReading();

    if (sensorRes.success && sensorRes.data) {
      setConnectivity('CONNECTED_LIVE');
      setRealFarmState(convertRealSensorToFarmState(sensorRes.data));
    } else if (sensorRes.notFound) {
      setConnectivity('CONNECTED_LIVE');
      setConnectionError(
        'Connected to field gateway, but no sensor telemetry has been ingested yet.'
      );
      setRealFarmState(null);
    } else {
      setConnectivity('DEVICE_OFFLINE');
      setConnectionError(sensorRes.error || 'Failed to retrieve sensor data');
      setRealFarmState(null);
    }

    setIsConnecting(false);
  }, []);

  // When switching modes
  useEffect(() => {
    if (mode === 'real') {
      syncWithBackend();
    } else {
      setConnectivity('DEMO_MODE');
      setConnectionError(null);
    }
  }, [mode, syncWithBackend]);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col selection:bg-farm-200">
      {/* Sticky App Header spanning full width */}
      <Header
        language={language}
        onLanguageChange={setLanguage}
        mode={mode}
        connectivity={connectivity}
        alertCount={activeState.alerts.length}
        onAlertClick={() => setActiveTab('alerts')}
      />

      {/* Demo Mode Scenario Bar (Visible only when in Demo Mode) */}
      {mode === 'demo' && (
        <DemoModeBar
          currentScenarioId={selectedScenarioId}
          onSelectScenario={setSelectedScenarioId}
          onSwitchToReal={() => setMode('real')}
        />
      )}

      {/* Responsive Body Container:
          Mobile/Tablet (<1024px): Centered single/dual column with bottom navigation
          Desktop (>=1024px): Persistent Sidebar + Wide Main Content
      */}
      <div className="w-full max-w-7xl mx-auto flex-1 flex px-3.5 sm:px-6 lg:px-8 py-3.5 lg:py-6 gap-6">
        {/* Persistent Left Sidebar on Desktop (>= 1024px) */}
        <div className="hidden lg:block">
          <Sidebar
            activeTab={activeTab === 'irrigation' ? 'home' : activeTab}
            onTabChange={setActiveTab}
            language={language}
            alertCount={activeState.alerts.length}
            mode={mode}
            connectivity={connectivity}
            onOpenVoice={() => setIsVoiceOpen(true)}
          />
        </div>

        {/* Main View Area (intelligently takes remaining desktop width or full mobile width) */}
        <main className="flex-1 min-w-0">
          {/* REAL MODE OFFLINE / EMPTY ERROR STATE */}
          {mode === 'real' && !realFarmState && (
            <div className="bg-white rounded-2xl p-6 md:p-8 border border-slate-200 shadow-sm text-center my-6 max-w-xl mx-auto space-y-4">
              <div className="w-14 h-14 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
                <WifiOff className="w-7 h-7" />
              </div>

              <div>
                <h3 className="text-base md:text-lg font-bold text-slate-900">
                  DEVICE OFFLINE
                </h3>
                <p className="text-xs md:text-sm text-slate-600 mt-1 leading-relaxed max-w-md mx-auto">
                  Local Data Unavailable
                </p>
                {connectionError && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {connectionError}
                  </p>
                )}
              </div>

              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-left text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-bold text-slate-700">
                  <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
                  <span>Real Mode Requirements:</span>
                </div>
                <p className="text-[11px] md:text-xs text-slate-500">
                  • Target URL: <code className="text-slate-800">{API_BASE_URL}</code>
                </p>
                <p className="text-[11px] md:text-xs text-slate-500">
                  • Make sure FastAPI server is running with <code className="text-slate-800">uvicorn main:app</code>
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-2.5 pt-2">
                <button
                  onClick={syncWithBackend}
                  disabled={isConnecting}
                  className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs md:text-sm active:scale-95 transition shadow-sm disabled:opacity-60"
                >
                  <RefreshCw
                    className={`w-3.5 h-3.5 ${isConnecting ? 'animate-spin' : ''}`}
                  />
                  <span>{isConnecting ? 'Checking Connection...' : 'Retry Connection'}</span>
                </button>

                <button
                  onClick={() => setMode('demo')}
                  className="px-4 py-3 text-xs md:text-sm font-semibold text-amber-800 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 rounded-xl border border-amber-200 transition"
                >
                  Switch back to Demo Mode
                </button>
              </div>
            </div>
          )}

          {/* NORMAL VIEW RENDERING (Either Demo Mode or Live Data Present) */}
          {(mode === 'demo' || realFarmState) && (
            <>
              {activeTab === 'home' && (
                <HomeView
                  state={activeState}
                  onNavigateToScan={() => setActiveTab('scan')}
                  onNavigateToIrrigation={() => setActiveTab('irrigation')}
                  onNavigateToCropHealth={() => setActiveTab('scan')}
                />
              )}

              {activeTab === 'scan' && (
                <ScanView
                  onBackToHome={() => setActiveTab('home')}
                  onViewAdvice={() => setActiveTab('irrigation')}
                  presetScan={activeState.recentScan}
                />
              )}

              {activeTab === 'field' && <FieldView state={activeState} />}

              {activeTab === 'alerts' && (
                <AlertsView
                  initialAlerts={activeState.alerts}
                  onNavigateToIrrigation={() => setActiveTab('irrigation')}
                  onNavigateToScan={() => setActiveTab('scan')}
                  isRealData={activeState.isRealData}
                />
              )}

              {activeTab === 'irrigation' && (
                <IrrigationView
                  state={activeState}
                  onBack={() => setActiveTab('home')}
                />
              )}

              {activeTab === 'settings' && (
                <SettingsView
                  language={language}
                  onLanguageChange={setLanguage}
                  mode={mode}
                  onModeChange={setMode}
                  connectivity={connectivity}
                  onCheckConnection={syncWithBackend}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Floating Voice Assistant Action Button (Mobile & Tablet: < 1024px) */}
      <button
        onClick={() => setIsVoiceOpen(true)}
        className="lg:hidden fixed bottom-16 right-4 z-40 w-12 h-12 rounded-full bg-farm-700 hover:bg-farm-800 text-white shadow-lg shadow-farm-900/30 flex items-center justify-center active:scale-95 transition"
        aria-label="Ask Farm Assistant"
        title="Ask Farm Assistant"
      >
        <Mic className="w-5 h-5" />
      </button>

      {/* Voice Assistant Dialogue Modal (UI Placeholder) */}
      <VoiceModal
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
        currentState={activeState}
      />

      {/* Bottom Navigation (Hidden on Desktop >= 1024px) */}
      <div className="lg:hidden">
        <BottomNav
          activeTab={activeTab === 'irrigation' ? 'home' : activeTab}
          onTabChange={setActiveTab}
          language={language}
          alertCount={activeState.alerts.length}
        />
      </div>
    </div>
  );
}
