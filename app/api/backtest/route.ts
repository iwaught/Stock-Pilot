import { NextRequest, NextResponse } from 'next/server';
import { HistoricalRate, BacktestResult } from '@/lib/types';
import { calculateAllIndicators, generateTradeSignal, calculateBollingerBands } from '@/lib/technicalAnalysis';

const FLASK_API = process.env.FLASK_API_URL || 'http://localhost:5001';

/**
 * GET /api/backtest?strategy=mean_reversion&days=90
 *
 * Proxies to the Python engine when available; otherwise runs a
 * lightweight in-process simulation.
 */
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const strategy = searchParams.get('strategy') ?? 'mean_reversion';
  const days = Number(searchParams.get('days') ?? 90);

  // Try Python engine
  try {
    const res = await fetch(
      `${FLASK_API}/api/backtest?strategy=${strategy}&days=${days}`,
      { next: { revalidate: 0 } },
    );
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Fall through to in-process backtest
  }

  // In-process lightweight backtest
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    const url = `https://api.frankfurter.app/${startDate.toISOString().split('T')[0]}..${endDate.toISOString().split('T')[0]}?from=USD&to=CLP`;

    const fxRes = await fetch(url, { next: { revalidate: 3600 } });
    if (!fxRes.ok) throw new Error('Frankfurter fetch failed');

    const fxData = await fxRes.json();
    const historical: HistoricalRate[] = Object.entries(fxData.rates ?? {})
      .map(([date, rateObj]) => ({
        date,
        rate: (rateObj as { CLP?: number }).CLP ?? 0,
      }))
      .filter((r) => r.rate > 0)
      .sort((a, b) => a.date.localeCompare(b.date));

    if (historical.length < 30) {
      return NextResponse.json({ error: 'Insufficient historical data' }, { status: 422 });
    }

    const prices = historical.map((h) => h.rate);
    const trades: BacktestResult['trades'] = [];
    const WINDOW = 20;
    const RISK_PCT = 0.01;
    let balance = 10_000;
    const equity: number[] = [balance];
    let wins = 0;

    for (let i = WINDOW; i < prices.length - 1; i++) {
      const slice = prices.slice(0, i + 1);
      const indicators = calculateAllIndicators(slice);
      const bb = calculateBollingerBands(slice);
      const signal = generateTradeSignal(indicators, slice[i]);

      if (signal.direction === 'HOLD') {
        equity.push(balance);
        continue;
      }

      const entry = slice[i];
      // ATR proxy: BB width / 4 ≈ one standard deviation of the band, used as a
      // rough stop-distance estimate. Note: this differs from the Python engine's
      // true ATR (which uses high/low/close ranges) and will produce different
      // backtest results. This in-process fallback is for indicative use only.
      const atr = (bb.upper - bb.lower) / 4;
      const stopDist = atr * 1.5;
      const riskAmount = balance * RISK_PCT;
      const priceRisk = stopDist;
      if (priceRisk === 0) { equity.push(balance); continue; }

      const units = riskAmount / priceRisk;
      const next = prices[i + 1];
      let pnl: number;

      if (signal.direction === 'BUY') {
        pnl = units * (next - entry);
      } else {
        pnl = units * (entry - next);
      }

      balance += pnl;
      equity.push(balance);
      if (pnl > 0) wins++;
      trades.push({ date: historical[i].date, direction: signal.direction, entry: parseFloat(entry.toFixed(2)), pnl: parseFloat(pnl.toFixed(2)) });
    }

    const totalTrades = trades.length;
    const winRate = totalTrades > 0 ? parseFloat(((wins / totalTrades) * 100).toFixed(1)) : 0;
    const totalReturn = parseFloat(((balance - 10_000) / 10_000 * 100).toFixed(2));

    const result: BacktestResult = {
      strategy,
      days,
      initialBalance: 10_000,
      finalBalance: parseFloat(balance.toFixed(2)),
      totalReturn,
      totalTrades,
      winRate,
      sharpeRatio: 0,
      maxDrawdown: 0,
      trades: trades.slice(-20),
    };

    return NextResponse.json(result);
  } catch (err) {
    console.error('Backtest error:', err);
    return NextResponse.json({ error: 'Backtest failed' }, { status: 500 });
  }
}
