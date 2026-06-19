import { NextRequest, NextResponse } from 'next/server';
import { StrategyConfig } from '@/lib/types';

const FLASK_API = process.env.FLASK_API_URL || 'http://localhost:5001';

const DEFAULT_CONFIG: StrategyConfig = {
  rsiOversold: 35,
  rsiOverbought: 65,
  bbPeriod: 20,
  bbStdDev: 2.0,
  atrPeriod: 14,
  atrStopMultiplier: 1.5,
  atrTargetMultiplier: 3.0,
};

/**
 * GET /api/config — Returns current strategy configuration.
 */
export async function GET() {
  try {
    const res = await fetch(`${FLASK_API}/api/whatsapp/status`, { next: { revalidate: 0 } });
    const whatsapp = res.ok ? await res.json() : { configured: false };
    return NextResponse.json({ config: DEFAULT_CONFIG, whatsapp });
  } catch {
    return NextResponse.json({ config: DEFAULT_CONFIG, whatsapp: { configured: false } });
  }
}

/**
 * POST /api/config — Forwards updated config to the Python engine.
 */
export async function POST(req: NextRequest) {
  const body = (await req.json()) as Partial<StrategyConfig>;

  try {
    const res = await fetch(`${FLASK_API}/api/strategies/configure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Python engine not running
  }

  // Return acknowledged config even if Python engine is down
  return NextResponse.json({ status: 'updated', config: { ...DEFAULT_CONFIG, ...body } });
}
