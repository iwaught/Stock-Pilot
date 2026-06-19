'use client';

import { useState } from 'react';
import { StrategyConfig } from '@/lib/types';

interface StrategyConfigPanelProps {
  initialConfig: StrategyConfig;
  onSave?: (config: StrategyConfig) => void;
}

const FIELD_LABELS: Record<keyof StrategyConfig, { label: string; min: number; max: number; step: number }> = {
  rsiOversold:        { label: 'RSI Oversold',         min: 10, max: 45,  step: 1   },
  rsiOverbought:      { label: 'RSI Overbought',        min: 55, max: 90,  step: 1   },
  bbPeriod:           { label: 'BB Period',             min: 5,  max: 50,  step: 1   },
  bbStdDev:           { label: 'BB Std Dev',            min: 1,  max: 4,   step: 0.1 },
  atrPeriod:          { label: 'ATR Period',            min: 5,  max: 30,  step: 1   },
  atrStopMultiplier:  { label: 'ATR Stop Multiplier',   min: 0.5, max: 4,  step: 0.1 },
  atrTargetMultiplier:{ label: 'ATR Target Multiplier', min: 1,  max: 8,   step: 0.1 },
};

export default function StrategyConfigPanel({ initialConfig, onSave }: StrategyConfigPanelProps) {
  const [config, setConfig] = useState<StrategyConfig>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleChange = (key: keyof StrategyConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: parseFloat(value) }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (res.ok) {
        setSaved(true);
        onSave?.(config);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (err) {
      console.error('Failed to save config:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => setConfig(initialConfig);

  return (
    <div className="bg-[#1a1a1a] border border-[#262626] rounded-xl p-6">
      <h2 className="text-xl text-white font-semibold mb-1">Strategy Configuration</h2>
      <p className="text-zinc-500 text-sm mb-5">Tune the mean-reversion strategy parameters</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {(Object.keys(FIELD_LABELS) as Array<keyof StrategyConfig>).map((key) => {
          const meta = FIELD_LABELS[key];
          return (
            <div key={key} className="bg-[#0a0a0a] border border-[#262626] rounded-lg p-4">
              <label className="block text-zinc-400 text-xs uppercase mb-2">{meta.label}</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={meta.min}
                  max={meta.max}
                  step={meta.step}
                  value={config[key]}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="flex-1 accent-blue-500"
                />
                <span className="text-white text-sm font-mono w-12 text-right">
                  {config[key]}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Risk/Reward preview */}
      <div className="bg-[#0a0a0a] border border-[#262626] rounded-lg p-4 mb-5">
        <div className="text-zinc-500 text-xs uppercase mb-2">Implied Risk/Reward Ratio</div>
        <div className="text-white font-semibold text-lg">
          1:{(config.atrTargetMultiplier / config.atrStopMultiplier).toFixed(1)}
        </div>
        <div className="text-zinc-500 text-xs mt-1">
          Stop: {config.atrStopMultiplier}× ATR · Target: {config.atrTargetMultiplier}× ATR
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors"
        >
          {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Configuration'}
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2.5 rounded-lg border border-[#262626] text-zinc-400 hover:text-white hover:border-zinc-500 transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
