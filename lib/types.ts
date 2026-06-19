export interface ForexRate {
  pair: string; // "USD/CLP"
  rate: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  rsi: number;
  sma20: number;
  sma50: number;
  ema12: number;
  ema26: number;
  macd: { macd: number; signal: number; histogram: number };
  bollingerBands?: { upper: number; middle: number; lower: number };
  atr?: number;
  support: number;
  resistance: number;
  volatility: number;
  trend: 'bullish' | 'bearish' | 'neutral';
}

export interface TradeSignal {
  direction: 'BUY' | 'SELL' | 'HOLD';
  confidence: 'high' | 'medium' | 'low';
  reasoning: string;
}

export interface EnhancedTradeSignal extends TradeSignal {
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  riskReward: string;
  strategy: string;
  confidencePct: number;
  holdTime: string;
  timestamp: string;
  indicators: Partial<TechnicalIndicators>;
}

export interface BacktestTrade {
  date: string;
  direction: 'BUY' | 'SELL';
  entry: number;
  pnl: number;
}

export interface BacktestResult {
  strategy: string;
  days: number;
  initialBalance: number;
  finalBalance: number;
  totalReturn: number;
  totalTrades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  trades: BacktestTrade[];
}

export interface StrategyConfig {
  rsiOversold: number;
  rsiOverbought: number;
  bbPeriod: number;
  bbStdDev: number;
  atrPeriod: number;
  atrStopMultiplier: number;
  atrTargetMultiplier: number;
}

export interface Position {
  id: string;
  direction: 'buy' | 'sell';
  entryPrice: number;
  lotSize: number;
  openDate: string;
  status: 'open' | 'closed';
  closePrice?: number;
  closeDate?: string;
}

export interface HistoricalRate {
  date: string;
  rate: number;
}
