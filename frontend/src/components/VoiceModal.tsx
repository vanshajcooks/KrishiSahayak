'use client';

import React, { useState } from 'react';
import { Mic, X, Sparkles, MessageSquare, Volume2, HelpCircle } from 'lucide-react';
import { FarmState } from '@/types/farm';

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentState: FarmState;
}

export const VoiceModal: React.FC<VoiceModalProps> = ({
  isOpen,
  onClose,
  currentState,
}) => {
  const [selectedPrompt, setSelectedPrompt] = useState<string>('Should I water my field?');

  if (!isOpen) return null;

  const getAssistantAnswer = (prompt: string): string => {
    const moisture = currentState.soilMoisture.percentage;
    const temp = currentState.ambient.temperature;
    const health = currentState.cropHealth.status;

    if (prompt.includes('water') || prompt.includes('irrigate')) {
      if (moisture < 30) {
        return `Your soil moisture is ${moisture}%, which is dry. Irrigation is recommended soon before temperatures rise.`;
      }
      return `Your soil moisture is ${moisture}%, which is in the optimal range. No watering is needed right now.`;
    }

    if (prompt.includes('healthy') || prompt.includes('disease')) {
      if (health === 'NEEDS_ATTENTION' || health === 'CRITICAL') {
        return `Warning: Foliage symptoms detected. Please inspect lower leaves and prune affected sections.`;
      }
      return `Your crop status is good. Leaves are healthy and no active disease risks are flagged.`;
    }

    if (prompt.includes('weather') || prompt.includes('temperature')) {
      return `Today's temperature is ${temp}°C with ${currentState.weather.humidity}% humidity. ${currentState.weather.interpretation}`;
    }

    return `All conditions for Field 01 are monitored. Soil is at ${moisture}% and temperature is ${temp}°C.`;
  };

  const sampleQuestions = [
    'Should I water my field?',
    'Is my crop healthy?',
    'What is today\'s weather forecast?',
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="bg-farm-700 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-farm-600 flex items-center justify-center">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold">Ask KhetSaathi</h2>
              <p className="text-xs text-farm-100">Smart Farming Assistant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-farm-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 space-y-4">
          {/* Audio Visualization Stub */}
          <div className="bg-farm-50 border border-farm-200 rounded-xl p-3 flex items-center justify-center gap-2">
            <Volume2 className="w-4 h-4 text-farm-700 animate-pulse" />
            <span className="text-xs font-semibold text-farm-800">
              Voice Assistant Ready (Touch to simulate questions)
            </span>
          </div>

          {/* Conversation Bubble Mockup */}
          <div className="space-y-3">
            {/* Farmer Question */}
            <div className="flex items-start justify-end gap-2">
              <div className="bg-farm-700 text-white rounded-2xl rounded-tr-none px-3.5 py-2 text-xs shadow-sm max-w-[85%]">
                <p className="font-medium">{selectedPrompt}</p>
                <span className="text-[9px] text-farm-200 block text-right mt-0.5">Farmer</span>
              </div>
            </div>

            {/* Assistant Response */}
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-farm-100 flex items-center justify-center text-farm-700 shrink-0 mt-1">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div className="bg-slate-100 text-slate-800 rounded-2xl rounded-tl-none px-3.5 py-2.5 text-xs shadow-sm max-w-[85%]">
                <p className="font-medium leading-relaxed">{getAssistantAnswer(selectedPrompt)}</p>
                <span className="text-[9px] text-slate-500 block mt-1">Assistant</span>
              </div>
            </div>
          </div>

          {/* Prompt Suggestions */}
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-2">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Tap a question to ask:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {sampleQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => setSelectedPrompt(q)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition active:scale-95 ${
                    selectedPrompt === q
                      ? 'bg-farm-100 border-farm-400 text-farm-900 font-semibold'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 font-normal'
                  }`}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="text-[10px] text-slate-400 text-center border-t border-slate-100 pt-2">
            Simulated interface. Live regional speech processing will connect on field deployment.
          </div>
        </div>

        {/* Footer Button */}
        <div className="bg-slate-50 px-4 py-2.5 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg hover:bg-slate-800 transition"
          >
            Close Dialogue
          </button>
        </div>
      </div>
    </div>
  );
};
