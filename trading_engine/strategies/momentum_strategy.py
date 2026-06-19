"""
USDCLP Momentum Strategy.

Logic:
- Generate BUY when MACD crosses above signal AND price is above SMA50.
- Generate SELL when MACD crosses below signal AND price is below SMA50.
- Uses ATR for stop-loss and 2:1 risk/reward for take-profit.
"""

from typing import Dict, Any, List
import pandas as pd

from trading_engine.strategies.base_strategy import BaseStrategy, Signal
from trading_engine.indicators.technical_analysis import (
    calculate_all_indicators,
    calculate_macd,
    calculate_sma,
    calculate_atr,
    calculate_rsi,
)
from trading_engine.indicators.risk_management import (
    calculate_stop_loss,
    calculate_take_profit,
    calculate_risk_reward_ratio,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
)
import trading_engine.config as cfg


class MomentumStrategy(BaseStrategy):
    """MACD-driven momentum strategy for the USD/CLP pair."""

    def __init__(
        self,
        fast: int = None,
        slow: int = None,
        signal: int = None,
        atr_period: int = None,
        atr_stop_mult: float = None,
        risk_reward: float = 2.0,
    ):
        super().__init__("USDCLP Momentum")
        self.fast = fast or cfg.MOMENTUM_FAST_PERIOD
        self.slow = slow or cfg.MOMENTUM_SLOW_PERIOD
        self.signal_period = signal or cfg.MOMENTUM_SIGNAL_PERIOD
        self.atr_period = atr_period or cfg.ATR_PERIOD
        self.atr_stop_mult = atr_stop_mult or cfg.ATR_STOP_MULTIPLIER
        self.risk_reward = risk_reward

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """Generate a signal based on MACD crossovers."""
        if df.empty or len(df) < self.slow + self.signal_period + 5:
            return self._hold_signal(0.0, "Insufficient data for analysis")

        close = df["Close"]
        high = df.get("High", close)
        low = df.get("Low", close)

        current_price = float(close.iloc[-1])

        # Current and previous MACD values
        macd_now = calculate_macd(close, self.fast, self.slow, self.signal_period)
        macd_prev = calculate_macd(close.iloc[:-1], self.fast, self.slow, self.signal_period)

        hist_now = macd_now["histogram"]
        hist_prev = macd_prev["histogram"]

        sma50 = calculate_sma(close, 50)
        sma20 = calculate_sma(close, 20)
        rsi = calculate_rsi(close)
        atr = calculate_atr(high, low, close, self.atr_period)

        reasons: List[str] = []
        buy_score = 0
        sell_score = 0

        # MACD crossover
        if hist_prev < 0 and hist_now > 0:
            buy_score += 4
            reasons.append("MACD bullish crossover")
        elif hist_now > 0:
            buy_score += 2
            reasons.append("MACD positive momentum")

        if hist_prev > 0 and hist_now < 0:
            sell_score += 4
            reasons.append("MACD bearish crossover")
        elif hist_now < 0:
            sell_score += 2
            reasons.append("MACD negative momentum")

        # Trend filter
        if current_price > sma50:
            buy_score += 1
            reasons.append("Price above SMA50 (uptrend)")
        else:
            sell_score += 1
            reasons.append("Price below SMA50 (downtrend)")

        if sma20 > sma50:
            buy_score += 1
        else:
            sell_score += 1

        # RSI filter (avoid extremes for momentum)
        if 40 < rsi < 70:
            buy_score += 1
        if 30 < rsi < 60:
            sell_score += 1

        diff = buy_score - sell_score

        if diff >= 4:
            direction = "BUY"
            confidence = "high" if diff >= 6 else "medium"
        elif diff <= -4:
            direction = "SELL"
            confidence = "high" if diff <= -6 else "medium"
        else:
            return self._hold_signal(current_price, "No clear momentum signal", {
                "rsi": round(rsi, 2),
                "sma20": round(sma20, 2),
                "sma50": round(sma50, 2),
                "macd": {k: round(v, 4) for k, v in macd_now.items()},
            })

        stop_loss = calculate_stop_loss(current_price, atr, direction, self.atr_stop_mult)
        take_profit = calculate_take_profit(current_price, stop_loss, self.risk_reward)
        _, rr_str = calculate_risk_reward_ratio(current_price, stop_loss, take_profit)

        return Signal(
            direction=direction,
            confidence=confidence,
            entry_price=round(current_price, 2),
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=rr_str,
            strategy=self.name,
            reasoning=". ".join(reasons[:3]) + ".",
            indicators={
                "rsi": round(rsi, 2),
                "sma20": round(sma20, 2),
                "sma50": round(sma50, 2),
                "macd": {k: round(v, 4) for k, v in macd_now.items()},
                "atr": round(atr, 2),
            },
        )

    def backtest(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10_000.0,
    ) -> Dict[str, Any]:
        if len(df) < self.slow + self.signal_period + 30:
            return {"error": "Insufficient data for backtest"}

        balance = initial_balance
        trade_pnls: List[float] = []
        equity: List[float] = [balance]
        trades_log: List[Dict[str, Any]] = []

        window = self.slow + self.signal_period + 10

        for i in range(window, len(df)):
            slice_df = df.iloc[: i + 1].copy()
            signal = self.generate_signal(slice_df)

            if signal.direction == "HOLD":
                equity.append(balance)
                continue

            entry = signal.entry_price
            sl = signal.stop_loss
            tp = signal.take_profit
            risk_amount = balance * (cfg.RISK_PER_TRADE_PCT / 100)
            price_risk = abs(entry - sl)

            if price_risk == 0 or i + 1 >= len(df):
                equity.append(balance)
                continue

            units = risk_amount / price_risk
            next_candle = df.iloc[i + 1]

            if signal.direction == "BUY":
                if next_candle["Low"] <= sl:
                    pnl = -risk_amount
                elif next_candle["High"] >= tp:
                    pnl = units * (tp - entry)
                else:
                    pnl = units * (float(next_candle["Close"]) - entry)
            else:
                if next_candle["High"] >= sl:
                    pnl = -risk_amount
                elif next_candle["Low"] <= tp:
                    pnl = units * (entry - tp)
                else:
                    pnl = units * (entry - float(next_candle["Close"]))

            balance += pnl
            trade_pnls.append(pnl)
            equity.append(balance)
            trades_log.append({
                "date": str(df.index[i]),
                "direction": signal.direction,
                "entry": round(entry, 2),
                "pnl": round(pnl, 2),
            })

        equity_series = pd.Series(equity)
        returns = equity_series.pct_change().dropna()

        return {
            "initialBalance": initial_balance,
            "finalBalance": round(balance, 2),
            "totalReturn": round((balance - initial_balance) / initial_balance * 100, 2),
            "totalTrades": len(trade_pnls),
            "winRate": calculate_win_rate(trade_pnls),
            "sharpeRatio": round(calculate_sharpe_ratio(returns), 3),
            "maxDrawdown": round(calculate_max_drawdown(equity_series) * 100, 2),
            "trades": trades_log[-20:],
        }

    def _hold_signal(
        self,
        price: float,
        reason: str,
        indicators: Dict[str, Any] = None,
    ) -> Signal:
        return Signal(
            direction="HOLD",
            confidence="low",
            entry_price=price,
            stop_loss=0.0,
            take_profit=0.0,
            risk_reward="N/A",
            strategy=self.name,
            reasoning=reason,
            indicators=indicators or {},
        )
