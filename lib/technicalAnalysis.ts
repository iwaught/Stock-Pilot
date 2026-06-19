import { TechnicalIndicators, TradeSignal, EnhancedTradeSignal } from './types';

// Default fallback rate when insufficient data is available
const DEFAULT_FALLBACK_RATE = 850;

/**
 * Calculate RSI (Relative Strength Index) - 14 period default
 */
export function calculateRSI(prices: number[], period: number = 14): number {
  if (prices.length < period + 1) return 50; // Not enough data, return neutral

  const changes: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }

  let avgGain = 0;
  let avgLoss = 0;

  // Calculate initial averages
  for (let i = 0; i < period; i++) {
    if (changes[i] > 0) {
      avgGain += changes[i];
    } else {
      avgLoss += Math.abs(changes[i]);
    }
  }
  avgGain /= period;
  avgLoss /= period;

  // Calculate smoothed averages
  for (let i = period; i < changes.length; i++) {
    if (changes[i] > 0) {
      avgGain = (avgGain * (period - 1) + changes[i]) / period;
      avgLoss = (avgLoss * (period - 1)) / period;
    } else {
      avgGain = (avgGain * (period - 1)) / period;
      avgLoss = (avgLoss * (period - 1) + Math.abs(changes[i])) / period;
    }
  }

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));

  return rsi;
}

/**
 * Calculate SMA (Simple Moving Average)
 */
export function calculateSMA(prices: number[], period: number): number {
  if (prices.length < period) return prices[prices.length - 1] || 0;

  const slice = prices.slice(-period);
  const sum = slice.reduce((acc, price) => acc + price, 0);
  return sum / period;
}

/**
 * Calculate EMA (Exponential Moving Average)
 */
export function calculateEMA(prices: number[], period: number): number {
  if (prices.length < period) return prices[prices.length - 1] || 0;

  const multiplier = 2 / (period + 1);
  let ema = calculateSMA(prices.slice(0, period), period);

  for (let i = period; i < prices.length; i++) {
    ema = (prices[i] - ema) * multiplier + ema;
  }

  return ema;
}

/**
 * Calculate MACD (12, 26, 9)
 */
export function calculateMACD(prices: number[]): { macd: number; signal: number; histogram: number } {
  if (prices.length < 26) {
    return { macd: 0, signal: 0, histogram: 0 };
  }

  const ema12 = calculateEMA(prices, 12);
  const ema26 = calculateEMA(prices, 26);
  const macd = ema12 - ema26;

  // Calculate signal line (9-period EMA of MACD)
  const macdValues: number[] = [];
  for (let i = 26; i <= prices.length; i++) {
    const slice = prices.slice(0, i);
    const e12 = calculateEMA(slice, 12);
    const e26 = calculateEMA(slice, 26);
    macdValues.push(e12 - e26);
  }

  const signal = calculateEMA(macdValues, 9);
  const histogram = macd - signal;

  return { macd, signal, histogram };
}

/**
 * Determine support and resistance levels from recent prices
 */
export function calculateSupportResistance(prices: number[]): { support: number; resistance: number } {
  if (prices.length < 20) {
    const currentPrice = prices[prices.length - 1] || DEFAULT_FALLBACK_RATE;
    return {
      support: currentPrice * 0.98,
      resistance: currentPrice * 1.02,
    };
  }

  // Use recent 30 days for support/resistance
  const recentPrices = prices.slice(-30);
  
  // Support: lowest price in recent period
  const support = Math.min(...recentPrices);
  
  // Resistance: highest price in recent period
  const resistance = Math.max(...recentPrices);

  return { support, resistance };
}

/**
 * Calculate standard deviation (volatility)
 */
export function calculateVolatility(prices: number[]): number {
  if (prices.length < 2) return 0;

  const returns: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
  }

  const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  const squaredDiffs = returns.map(r => Math.pow(r - mean, 2));
  const variance = squaredDiffs.reduce((sum, sd) => sum + sd, 0) / returns.length;
  const stdDev = Math.sqrt(variance);

  return stdDev * 100; // Return as percentage
}

/**
 * Determine trend based on moving averages and price action
 */
export function determineTrend(prices: number[], sma20: number, sma50: number): 'bullish' | 'bearish' | 'neutral' {
  if (prices.length === 0) return 'neutral';

  const currentPrice = prices[prices.length - 1];

  // Bullish: price above both SMAs and SMA20 > SMA50
  if (currentPrice > sma20 && currentPrice > sma50 && sma20 > sma50) {
    return 'bullish';
  }

  // Bearish: price below both SMAs and SMA20 < SMA50
  if (currentPrice < sma20 && currentPrice < sma50 && sma20 < sma50) {
    return 'bearish';
  }

  return 'neutral';
}

/**
 * Generate overall trade signal based on all indicators
 */
export function generateTradeSignal(indicators: TechnicalIndicators, currentPrice: number): TradeSignal {
  let bullishSignals = 0;
  let bearishSignals = 0;
  const reasons: string[] = [];

  // RSI Analysis
  if (indicators.rsi < 30) {
    bullishSignals += 2;
    reasons.push(`RSI at ${indicators.rsi.toFixed(1)} suggests oversold condition`);
  } else if (indicators.rsi > 70) {
    bearishSignals += 2;
    reasons.push(`RSI at ${indicators.rsi.toFixed(1)} indicates overbought condition`);
  } else if (indicators.rsi < 40) {
    bullishSignals += 1;
    reasons.push(`RSI at ${indicators.rsi.toFixed(1)} shows potential support`);
  } else if (indicators.rsi > 60) {
    bearishSignals += 1;
    reasons.push(`RSI at ${indicators.rsi.toFixed(1)} shows potential resistance`);
  }

  // Moving Average Analysis
  if (currentPrice > indicators.sma20 && currentPrice > indicators.sma50) {
    bullishSignals += 2;
    reasons.push('Price above both SMA20 and SMA50 (bullish trend)');
  } else if (currentPrice < indicators.sma20 && currentPrice < indicators.sma50) {
    bearishSignals += 2;
    reasons.push('Price below both SMA20 and SMA50 (bearish trend)');
  }

  if (indicators.sma20 > indicators.sma50) {
    bullishSignals += 1;
  } else {
    bearishSignals += 1;
  }

  // MACD Analysis
  if (indicators.macd.histogram > 0) {
    bullishSignals += 1;
    if (indicators.macd.histogram > 1) {
      reasons.push('MACD showing strong bullish momentum');
    }
  } else {
    bearishSignals += 1;
    if (indicators.macd.histogram < -1) {
      reasons.push('MACD showing strong bearish momentum');
    }
  }

  // Support/Resistance Analysis
  const priceToSupport = ((currentPrice - indicators.support) / currentPrice) * 100;
  const priceToResistance = ((indicators.resistance - currentPrice) / currentPrice) * 100;

  if (priceToSupport < 1) {
    bullishSignals += 2;
    reasons.push(`Price near support level at ${indicators.support.toFixed(2)}`);
  }

  if (priceToResistance < 1) {
    bearishSignals += 2;
    reasons.push(`Price near resistance level at ${indicators.resistance.toFixed(2)}`);
  }

  // Trend Analysis
  if (indicators.trend === 'bullish') {
    bullishSignals += 1;
  } else if (indicators.trend === 'bearish') {
    bearishSignals += 1;
  }

  // Determine signal
  const signalDiff = bullishSignals - bearishSignals;
  let direction: 'BUY' | 'SELL' | 'HOLD';
  let confidence: 'high' | 'medium' | 'low';

  if (signalDiff >= 3) {
    direction = 'BUY';
    confidence = signalDiff >= 5 ? 'high' : 'medium';
  } else if (signalDiff <= -3) {
    direction = 'SELL';
    confidence = signalDiff <= -5 ? 'high' : 'medium';
  } else {
    direction = 'HOLD';
    confidence = 'low';
  }

  const reasoning = reasons.length > 0 
    ? reasons.slice(0, 3).join('. ') + '.'
    : 'Indicators show mixed signals. Market conditions are unclear.';

  return {
    direction,
    confidence,
    reasoning,
  };
}

/**
 * Calculate Bollinger Bands (upper, middle, lower)
 */
export function calculateBollingerBands(
  prices: number[],
  period: number = 20,
  stdDev: number = 2.0,
): { upper: number; middle: number; lower: number } {
  if (prices.length < period) {
    const current = prices[prices.length - 1] || DEFAULT_FALLBACK_RATE;
    return { upper: current * 1.02, middle: current, lower: current * 0.98 };
  }

  const slice = prices.slice(-period);
  const mean = slice.reduce((s, p) => s + p, 0) / period;
  const variance = slice.reduce((s, p) => s + Math.pow(p - mean, 2), 0) / period;
  const std = Math.sqrt(variance);

  return {
    upper: parseFloat((mean + stdDev * std).toFixed(2)),
    middle: parseFloat(mean.toFixed(2)),
    lower: parseFloat((mean - stdDev * std).toFixed(2)),
  };
}

/**
 * Calculate ATR (Average True Range) from high, low, close arrays.
 * Falls back to average high-low range when close history is too short.
 */
export function calculateATR(
  highs: number[],
  lows: number[],
  closes: number[],
  period: number = 14,
): number {
  const len = Math.min(highs.length, lows.length, closes.length);
  if (len < 2) return 0;

  const trueRanges: number[] = [];
  for (let i = 1; i < len; i++) {
    const tr = Math.max(
      highs[i] - lows[i],
      Math.abs(highs[i] - closes[i - 1]),
      Math.abs(lows[i] - closes[i - 1]),
    );
    trueRanges.push(tr);
  }

  const slice = trueRanges.slice(-period);
  return parseFloat((slice.reduce((s, v) => s + v, 0) / slice.length).toFixed(2));
}

/**
 * Generate an enhanced trade signal with entry price, stop-loss, take-profit
 * and risk/reward ratio derived from Bollinger Bands and ATR.
 */
export function generateEnhancedSignal(
  indicators: TechnicalIndicators,
  currentPrice: number,
  atr: number,
  atrStopMultiplier: number = 1.5,
  atrTargetMultiplier: number = 3.0,
): EnhancedTradeSignal {
  const base = generateTradeSignal(indicators, currentPrice);

  let stopLoss = 0;
  let takeProfit = 0;
  let riskReward = 'N/A';

  if (atr > 0 && base.direction !== 'HOLD') {
    const stopDist = atr * atrStopMultiplier;
    const targetDist = atr * atrTargetMultiplier;

    if (base.direction === 'BUY') {
      stopLoss = parseFloat((currentPrice - stopDist).toFixed(2));
      takeProfit = parseFloat((currentPrice + targetDist).toFixed(2));
    } else {
      stopLoss = parseFloat((currentPrice + stopDist).toFixed(2));
      takeProfit = parseFloat((currentPrice - targetDist).toFixed(2));
    }

    const risk = Math.abs(currentPrice - stopLoss);
    const reward = Math.abs(currentPrice - takeProfit);
    const ratio = risk > 0 ? (reward / risk).toFixed(1) : '0';
    riskReward = `1:${ratio}`;
  }

  return {
    ...base,
    entryPrice: parseFloat(currentPrice.toFixed(2)),
    stopLoss,
    takeProfit,
    riskReward,
    strategy: 'Mean Reversion',
    confidencePct: base.confidence === 'high' ? 85 : base.confidence === 'medium' ? 65 : 45,
    holdTime: '4-24 hours',
    timestamp: new Date().toISOString(),
    indicators,
  };
}

/**
 * Calculate all technical indicators for a given price history
 */
export function calculateAllIndicators(prices: number[]): TechnicalIndicators {
  const rsi = calculateRSI(prices);
  const sma20 = calculateSMA(prices, 20);
  const sma50 = calculateSMA(prices, 50);
  const ema12 = calculateEMA(prices, 12);
  const ema26 = calculateEMA(prices, 26);
  const macd = calculateMACD(prices);
  const { support, resistance } = calculateSupportResistance(prices);
  const volatility = calculateVolatility(prices);
  const trend = determineTrend(prices, sma20, sma50);
  const bollingerBands = calculateBollingerBands(prices);
  // ATR approximation: without separate high/low arrays we pass close prices for
  // all three inputs, which yields TR = 0 for every bar (identical high/low/close).
  // The result is an ATR ≈ 0, which disables stop-loss/take-profit in the enhanced
  // signal. For more accurate risk levels, provide a proper OHLCV source.
  const atr = calculateATR(prices, prices, prices);

  return {
    rsi,
    sma20,
    sma50,
    ema12,
    ema26,
    macd,
    bollingerBands,
    atr,
    support,
    resistance,
    volatility,
    trend,
  };
}
