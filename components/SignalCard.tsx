import { EnhancedTradeSignal } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';

interface SignalCardProps {
  signal: EnhancedTradeSignal;
  title?: string;
}

export default function SignalCard({ signal, title = 'Trading Signal' }: SignalCardProps) {
  const isHold = signal.direction === 'HOLD';
  const isBuy = signal.direction === 'BUY';

  const colors = isBuy
    ? { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', badge: 'bg-green-500/20 text-green-300' }
    : isHold
    ? { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', badge: 'bg-yellow-500/20 text-yellow-300' }
    : { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', badge: 'bg-red-500/20 text-red-300' };

  const directionEmoji = isBuy ? '🟢' : isHold ? '🟡' : '🔴';
  const directionLabel = isBuy ? 'BUY USD' : isHold ? 'HOLD / WAIT' : 'SELL USD';

  const formattedTime = signal.timestamp
    ? new Date(signal.timestamp).toLocaleString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        month: 'short',
        day: 'numeric',
      })
    : '—';

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-xl p-6`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl text-white font-semibold">{title}</h2>
          <p className="text-zinc-500 text-xs mt-0.5">Strategy: {signal.strategy}</p>
        </div>
        <div className="text-right">
          <span className={`text-xs px-3 py-1 rounded-full uppercase font-semibold ${colors.badge}`}>
            {signal.confidence} — {signal.confidencePct}%
          </span>
          <p className="text-zinc-500 text-xs mt-1">{formattedTime}</p>
        </div>
      </div>

      {/* Direction */}
      <div className="flex items-center gap-3 mb-5">
        <span className="text-4xl">{directionEmoji}</span>
        <div className={`text-3xl font-bold ${colors.text}`}>{directionLabel}</div>
      </div>

      {/* Price levels — only shown for actionable signals */}
      {!isHold && signal.entryPrice > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="bg-[#0a0a0a] border border-[#262626] rounded-lg p-3 text-center">
            <div className="text-zinc-500 text-xs uppercase mb-1">Entry</div>
            <div className="text-white font-semibold text-sm">
              {formatNumber(signal.entryPrice, 2)}
            </div>
          </div>
          <div className="bg-[#0a0a0a] border border-red-900/40 rounded-lg p-3 text-center">
            <div className="text-zinc-500 text-xs uppercase mb-1">Stop Loss</div>
            <div className="text-red-400 font-semibold text-sm">
              {signal.stopLoss > 0 ? formatNumber(signal.stopLoss, 2) : '—'}
            </div>
          </div>
          <div className="bg-[#0a0a0a] border border-green-900/40 rounded-lg p-3 text-center">
            <div className="text-zinc-500 text-xs uppercase mb-1">Take Profit</div>
            <div className="text-green-400 font-semibold text-sm">
              {signal.takeProfit > 0 ? formatNumber(signal.takeProfit, 2) : '—'}
            </div>
          </div>
        </div>
      )}

      {/* Risk/Reward + Hold time */}
      {!isHold && signal.riskReward !== 'N/A' && (
        <div className="flex gap-3 mb-4">
          <div className="flex-1 bg-[#0a0a0a] border border-[#262626] rounded-lg p-3">
            <div className="text-zinc-500 text-xs uppercase mb-1">Risk / Reward</div>
            <div className="text-white font-semibold">{signal.riskReward}</div>
          </div>
          <div className="flex-1 bg-[#0a0a0a] border border-[#262626] rounded-lg p-3">
            <div className="text-zinc-500 text-xs uppercase mb-1">Hold Time</div>
            <div className="text-white font-semibold text-sm">{signal.holdTime}</div>
          </div>
        </div>
      )}

      {/* Reasoning */}
      <div className="bg-[#0a0a0a] border border-[#262626] rounded-lg p-4 mb-4">
        <div className="text-zinc-400 text-sm leading-relaxed">{signal.reasoning}</div>
      </div>

      {/* Bollinger Bands indicator bar */}
      {signal.indicators?.bollingerBands && signal.entryPrice > 0 && (
        <BollingerBar
          price={signal.entryPrice}
          bb={signal.indicators.bollingerBands as { upper: number; middle: number; lower: number }}
        />
      )}

      <div className="text-zinc-500 text-xs italic mt-3">
        ⚠️ Not financial advice. Use at your own risk.
      </div>
    </div>
  );
}

function BollingerBar({
  price,
  bb,
}: {
  price: number;
  bb: { upper: number; middle: number; lower: number };
}) {
  const range = bb.upper - bb.lower;
  if (range <= 0) return null;
  const pct = Math.max(0, Math.min(100, ((price - bb.lower) / range) * 100));

  return (
    <div className="mb-3">
      <div className="flex justify-between text-zinc-500 text-xs mb-1">
        <span>BB Lower {formatNumber(bb.lower, 0)}</span>
        <span>BB Upper {formatNumber(bb.upper, 0)}</span>
      </div>
      <div className="relative h-2 bg-[#1a1a1a] rounded-full overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-green-900/50 via-zinc-700/30 to-red-900/50 rounded-full" />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white shadow-lg"
          style={{ left: `${pct}%`, transform: 'translate(-50%, -50%)' }}
        />
      </div>
    </div>
  );
}
