import { NextResponse } from 'next/server';
import { HistoricalRate } from '@/lib/types';
import {
  calculateAllIndicators,
  generateEnhancedSignal,
  calculateATR,
} from '@/lib/technicalAnalysis';

const FLASK_API = process.env.FLASK_API_URL || 'http://localhost:5001';

/**
 * GET /api/signals
 *
 * Attempts to fetch a live signal from the Python Flask backend.
 * Falls back to generating a signal in-process from the Frankfurter API.
 */
export async function GET() {
  // 1. Try the Python trading engine first
  try {
    const res = await fetch(`${FLASK_API}/api/signals`, { next: { revalidate: 300 } });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json({ source: 'python_engine', ...data });
    }
  } catch {
    // Python engine not running — fall back to in-process generation
  }

  // 2. Fallback: generate signal in-process using the same Frankfurter data
  try {
    const forexRes = await fetch(`${process.env.NEXTAUTH_URL || ''}/api/forex`, {
      next: { revalidate: 300 },
    });

    let historical: HistoricalRate[] = [];
    let currentPrice = 0;

    if (forexRes.ok) {
      const forexData = await forexRes.json();
      historical = forexData.historical ?? [];
      currentPrice = forexData.current?.rate ?? 0;
    }

    if (!historical.length || !currentPrice) {
      return NextResponse.json({ error: 'Unable to fetch market data' }, { status: 503 });
    }

    const prices = historical.map((h) => h.rate);
    const indicators = calculateAllIndicators(prices);
    const atr = indicators.atr ?? calculateATR(prices, prices, prices);
    const signal = generateEnhancedSignal(indicators, currentPrice, atr);

    return NextResponse.json({
      source: 'in_process',
      timestamp: new Date().toISOString(),
      currentPrice,
      meanReversion: signal,
    });
  } catch (err) {
    console.error('Signal generation error:', err);
    return NextResponse.json({ error: 'Signal generation failed' }, { status: 500 });
  }
}
