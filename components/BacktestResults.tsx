'use client';

import { useState } from 'react';
import { BacktestResult } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';

interface BacktestResultsProps {
  initialResult?: BacktestResult | null;
}

export default function BacktestResults({ initialResult = null }: BacktestResultsProps) {
  const [result, setResult] = useState<BacktestResult | null>(initialResult);
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState<'mean_reversion' | 'momentum'>('mean_reversion');
  const [days, setDays] = useState(90);

  const runBacktest = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/backtest?strategy=${strategy}&days=${days}`);
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Backtest error:', err);
    } finally {
      setLoading(false);
    }
  };

  const isPositive = result ? result.totalReturn >= 0 : undefined;

  return (
    <div className="bg-[#1a1a1a] border border-[#262626] rounded-xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl text-white font-semibold">Backtesting</h2>
          <p className="text-zinc-500 text-sm">Historical strategy simulation</p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as 'mean_reversion' | 'momentum')}
            className="bg-[#0a0a0a] border border-[#262626] text-zinc-300 text-sm rounded-lg px-3 py-2"
          >
            <option value="mean_reversion">Mean Reversion</option>
            <option value="momentum">Momentum</option>
          </select>

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-[#0a0a0a] border border-[#262626] text-zinc-300 text-sm rounded-lg px-3 py-2"
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>

          <button
            onClick={runBacktest}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors"
          >
            {loading ? 'Running…' : 'Run Backtest'}
          </button>
        </div>
      </div>

      {!result && !loading && (
        <div className="text-center py-10 text-zinc-500">
          Select a strategy and click <span className="text-zinc-300">Run Backtest</span> to see results.
        </div>
      )}

      {loading && (
        <div className="text-center py-10 text-zinc-400">Running backtest…</div>
      )}

      {result && !loading && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <MetricCard
              label="Total Return"
              value={`${result.totalReturn >= 0 ? '+' : ''}${result.totalReturn}%`}
              positive={isPositive}
            />
            <MetricCard label="Total Trades" value={String(result.totalTrades)} />
            <MetricCard label="Win Rate" value={`${result.winRate}%`} positive={result.winRate >= 50} />
            <MetricCard
              label="Max Drawdown"
              value={`${result.maxDrawdown}%`}
              positive={false}
            />
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <MetricCard
              label="Final Balance"
              value={`$${formatNumber(result.finalBalance, 2)}`}
            />
            <MetricCard
              label="Sharpe Ratio"
              value={result.sharpeRatio !== 0 ? String(result.sharpeRatio) : 'N/A'}
              positive={result.sharpeRatio > 1}
            />
          </div>

          {/* Recent trades */}
          {result.trades.length > 0 && (
            <div>
              <h3 className="text-zinc-400 text-xs uppercase mb-3">Recent Trades</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-zinc-500 text-xs uppercase border-b border-[#262626]">
                      <th className="text-left pb-2 pr-4">Date</th>
                      <th className="text-left pb-2 pr-4">Direction</th>
                      <th className="text-right pb-2 pr-4">Entry</th>
                      <th className="text-right pb-2">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} className="border-b border-[#1a1a1a] hover:bg-white/5">
                        <td className="py-2 pr-4 text-zinc-400">{t.date.slice(0, 10)}</td>
                        <td className="py-2 pr-4">
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${
                              t.direction === 'BUY'
                                ? 'bg-green-500/15 text-green-400'
                                : 'bg-red-500/15 text-red-400'
                            }`}
                          >
                            {t.direction}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-right text-zinc-300">
                          {formatNumber(t.entry, 2)}
                        </td>
                        <td
                          className={`py-2 text-right font-medium ${
                            t.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {t.pnl >= 0 ? '+' : ''}
                          {formatNumber(t.pnl, 2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive?: boolean;
}) {
  const textColor =
    positive === undefined
      ? 'text-white'
      : positive
      ? 'text-green-400'
      : 'text-red-400';

  return (
    <div className="bg-[#0a0a0a] border border-[#262626] rounded-lg p-3">
      <div className="text-zinc-500 text-xs uppercase mb-1">{label}</div>
      <div className={`font-semibold text-lg ${textColor}`}>{value}</div>
    </div>
  );
}
