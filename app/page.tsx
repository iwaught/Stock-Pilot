'use client';

import { useState, useEffect, useMemo } from 'react';
import RateCard from '@/components/RateCard';
import Converter from '@/components/Converter';
import TechnicalPanel from '@/components/TechnicalPanel';
import TradeSignal from '@/components/TradeSignal';
import PriceChart from '@/components/PriceChart';
import PositionTracker from '@/components/PositionTracker';
import SignalCard from '@/components/SignalCard';
import BacktestResults from '@/components/BacktestResults';
import StrategyConfigPanel from '@/components/StrategyConfig';
import {
  ForexRate,
  HistoricalRate,
  TechnicalIndicators,
  TradeSignal as TradeSignalType,
  StrategyConfig,
} from '@/lib/types';
import {
  calculateAllIndicators,
  generateTradeSignal,
  generateEnhancedSignal,
  calculateSMA,
} from '@/lib/technicalAnalysis';

const DEFAULT_CONFIG: StrategyConfig = {
  rsiOversold: 35,
  rsiOverbought: 65,
  bbPeriod: 20,
  bbStdDev: 2.0,
  atrPeriod: 14,
  atrStopMultiplier: 1.5,
  atrTargetMultiplier: 3.0,
};

export default function Home() {
  const [currentRate, setCurrentRate] = useState<ForexRate | null>(null);
  const [historicalRates, setHistoricalRates] = useState<HistoricalRate[]>([]);
  const [indicators, setIndicators] = useState<TechnicalIndicators | null>(null);
  const [tradeSignal, setTradeSignal] = useState<TradeSignalType | null>(null);
  const [strategyConfig, setStrategyConfig] = useState<StrategyConfig>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'backtest' | 'config'>('dashboard');

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('/api/forex');
        if (!response.ok) throw new Error('Failed to fetch forex data');

        const data = await response.json();
        setCurrentRate(data.current);
        setHistoricalRates(data.historical);

        // Calculate technical indicators
        const prices = data.historical.map((h: HistoricalRate) => h.rate);
        const calculatedIndicators = calculateAllIndicators(prices);
        setIndicators(calculatedIndicators);

        // Generate basic trade signal
        const signal = generateTradeSignal(calculatedIndicators, data.current.rate);
        setTradeSignal(signal);

        setLoading(false);
      } catch (err) {
        console.error('Error fetching forex data:', err);
        setError('Failed to load forex data. Please refresh the page.');
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Enhanced signal is derived from indicators + currentRate + strategyConfig.
  // Recomputes automatically whenever any of these change (e.g. config tab save).
  const enhancedSignalMemo = useMemo(() => {
    if (!indicators || !currentRate) return null;
    const atr = indicators.atr ?? 0;
    return generateEnhancedSignal(
      indicators,
      currentRate.rate,
      atr,
      strategyConfig.atrStopMultiplier,
      strategyConfig.atrTargetMultiplier,
    );
  }, [indicators, currentRate, strategyConfig]);

  // Memoized SMA arrays for chart - calculated incrementally
  const { sma20Data, sma50Data } = useMemo(() => {
    const sma20: number[] = [];
    const sma50: number[] = [];

    if (historicalRates.length > 0) {
      const prices = historicalRates.map((h) => h.rate);

      for (let i = 0; i < prices.length; i++) {
        const slice = prices.slice(0, i + 1);
        sma20.push(calculateSMA(slice, 20));
        sma50.push(calculateSMA(slice, 50));
      }
    }

    return { sma20Data: sma20, sma50Data: sma50 };
  }, [historicalRates]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-white text-xl">Loading USD/CLP data...</div>
      </div>
    );
  }

  if (error || !currentRate || !indicators || !tradeSignal) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-8">
        <div className="bg-red-900/20 border border-red-800 text-red-400 px-6 py-4 rounded-lg max-w-md">
          <p className="font-medium">Error loading data</p>
          <p className="text-sm mt-1">{error || 'Unable to load forex data'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
            USDCLP-Pilot 🇨🇱
          </h1>
          <p className="text-zinc-400 text-lg">
            Personal USD/CLP Forex Trading Assistant
          </p>
          <p className="text-zinc-500 text-sm mt-1">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-1 mb-6 border-b border-[#262626]">
          {(['dashboard', 'backtest', 'config'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2.5 text-sm font-medium capitalize transition-colors -mb-px border-b-2 ${
                activeTab === tab
                  ? 'border-white text-white'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {tab === 'config' ? 'Strategy Config' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* ── Dashboard tab ───────────────────────────────────────────── */}
        {activeTab === 'dashboard' && (
          <>
            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="lg:col-span-2">
                <RateCard rate={currentRate} />
              </div>
              <div>
                <Converter rate={currentRate.rate} />
              </div>
            </div>

            {/* Enhanced Signal Card (primary) */}
            {enhancedSignalMemo && (
              <div className="mb-6">
                <SignalCard signal={enhancedSignalMemo} title="🎯 Trading Signal" />
              </div>
            )}

            {/* Legacy signal (compact) */}
            <div className="mb-6">
              <TradeSignal signal={tradeSignal} />
            </div>

            {/* Technical Analysis Panel */}
            <div className="mb-6">
              <TechnicalPanel indicators={indicators} currentPrice={currentRate.rate} />
            </div>

            {/* Historical Chart */}
            <div className="mb-6">
              <PriceChart data={historicalRates} sma20Data={sma20Data} sma50Data={sma50Data} />
            </div>

            {/* Position Tracker */}
            <div>
              <PositionTracker currentRate={currentRate.rate} />
            </div>
          </>
        )}

        {/* ── Backtest tab ─────────────────────────────────────────────── */}
        {activeTab === 'backtest' && (
          <BacktestResults />
        )}

        {/* ── Config tab ───────────────────────────────────────────────── */}
        {activeTab === 'config' && (
          <StrategyConfigPanel
            initialConfig={strategyConfig}
            onSave={(cfg) => setStrategyConfig(cfg)}
          />
        )}
      </div>
    </div>
  );
}

