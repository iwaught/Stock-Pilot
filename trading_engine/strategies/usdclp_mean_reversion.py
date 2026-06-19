"""
USDCLP Mean-Reversion Strategy.

Logic:
- Generate BUY when price touches/crosses below the lower Bollinger Band
  AND RSI is oversold (< RSI_OVERSOLD threshold).
- Generate SELL when price touches/crosses above the upper Bollinger Band
  AND RSI is overbought (> RSI_OVERBOUGHT threshold).
- Stop-loss is placed 1.5 × ATR from entry; take-profit at 3 × ATR.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from trading_engine.strategies.base_strategy import BaseStrategy, Signal
from trading_engine.indicators.technical_analysis import (
    calculate_all_indicators,
    calculate_bollinger_bands,
    calculate_rsi,
    calculate_atr,
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


class USDCLPMeanReversionStrategy(BaseStrategy):
    """Mean-reversion strategy for the USD/CLP pair."""

    def __init__(
        self,
        rsi_oversold: int = None,
        rsi_overbought: int = None,
        bb_period: int = None,
        bb_std: float = None,
        atr_period: int = None,
        atr_stop_mult: float = None,
        atr_target_mult: float = None,
    ):
        super().__init__("USDCLP Mean Reversion")
        self.rsi_oversold = rsi_oversold or cfg.RSI_OVERSOLD
        self.rsi_overbought = rsi_overbought or cfg.RSI_OVERBOUGHT
        self.bb_period = bb_period or cfg.BB_PERIOD
        self.bb_std = bb_std or cfg.BB_STD_DEV
        self.atr_period = atr_period or cfg.ATR_PERIOD
        self.atr_stop_mult = atr_stop_mult or cfg.ATR_STOP_MULTIPLIER
        self.atr_target_mult = atr_target_mult or cfg.ATR_TARGET_MULTIPLIER

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """Generate a BUY / SELL / HOLD signal from OHLCV data."""
        # Minimum bars needed: largest window among BB period, ATR period, and MACD slow EMA
        MIN_INDICATOR_BARS = max(self.bb_period, self.atr_period, cfg.MOMENTUM_SLOW_PERIOD)
        if df.empty or len(df) < MIN_INDICATOR_BARS:
            return self._hold_signal(0.0, "Insufficient data for analysis")

        indicators = calculate_all_indicators(
            df,
            rsi_period=14,
            bb_period=self.bb_period,
            bb_std=self.bb_std,
            atr_period=self.atr_period,
        )

        close = df["Close"]
        current_price = indicators["current_price"]
        rsi = indicators["rsi"]
        bb = indicators["bollinger_bands"]
        atr = indicators["atr"]

        # ── Signal scoring ────────────────────────────────────────────────
        buy_score = 0
        sell_score = 0
        reasons: List[str] = []

        # Bollinger Band touches
        bb_pct = (current_price - bb["lower"]) / max(bb["upper"] - bb["lower"], 1e-9)

        if current_price <= bb["lower"]:
            buy_score += 3
            reasons.append(f"Price at/below lower Bollinger Band ({bb['lower']:,.2f})")
        elif bb_pct < 0.15:
            buy_score += 2
            reasons.append("Price near lower Bollinger Band")

        if current_price >= bb["upper"]:
            sell_score += 3
            reasons.append(f"Price at/above upper Bollinger Band ({bb['upper']:,.2f})")
        elif bb_pct > 0.85:
            sell_score += 2
            reasons.append("Price near upper Bollinger Band")

        # RSI confirmation
        if rsi < self.rsi_oversold:
            buy_score += 2
            reasons.append(f"RSI oversold at {rsi:.1f}")
        elif rsi < 40:
            buy_score += 1

        if rsi > self.rsi_overbought:
            sell_score += 2
            reasons.append(f"RSI overbought at {rsi:.1f}")
        elif rsi > 60:
            sell_score += 1

        # MACD momentum alignment
        macd = indicators["macd"]
        if macd["histogram"] > 0:
            buy_score += 1
        else:
            sell_score += 1

        # Moving average trend filter
        sma20 = indicators["sma20"]
        sma50 = indicators["sma50"]
        if sma20 > sma50:
            buy_score += 1
        elif sma20 < sma50:
            sell_score += 1

        # ── Determine direction ───────────────────────────────────────────
        diff = buy_score - sell_score

        if diff >= 4:
            direction = "BUY"
            confidence = "high" if diff >= 6 else "medium"
        elif diff <= -4:
            direction = "SELL"
            confidence = "high" if diff <= -6 else "medium"
        else:
            return self._hold_signal(
                current_price,
                "Mixed signals — waiting for clearer setup",
                indicators,
            )

        # ── Risk levels ───────────────────────────────────────────────────
        stop_loss = calculate_stop_loss(
            current_price, atr, direction, self.atr_stop_mult
        )
        take_profit = calculate_take_profit(
            current_price, stop_loss, self.atr_target_mult / self.atr_stop_mult
        )
        _, rr_str = calculate_risk_reward_ratio(current_price, stop_loss, take_profit)

        reasoning = ". ".join(reasons[:3]) + "."

        return Signal(
            direction=direction,
            confidence=confidence,
            entry_price=round(current_price, 2),
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=rr_str,
            strategy=self.name,
            reasoning=reasoning,
            indicators={
                "rsi": round(rsi, 2),
                "sma20": round(sma20, 2),
                "sma50": round(sma50, 2),
                "macd": {k: round(v, 4) for k, v in macd.items()},
                "bollingerBands": {k: round(v, 2) for k, v in bb.items()},
                "atr": round(atr, 2),
            },
        )

    # ── Backtesting ────────────────────────────────────────────────────────

    def backtest(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10_000.0,
    ) -> Dict[str, Any]:
        """
        Simple event-driven backtest on OHLCV data.
        Each trade risks 1% of the running balance.
        """
        if len(df) < self.bb_period + 30:
            return {"error": "Insufficient data for backtest"}

        balance = initial_balance
        trade_pnls: List[float] = []
        equity: List[float] = [balance]
        trades_log: List[Dict[str, Any]] = []

        window = max(self.bb_period, self.atr_period, 26)

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
            if price_risk == 0:
                equity.append(balance)
                continue

            units = risk_amount / price_risk

            # Simulate outcome using next candle's OHLC
            if i + 1 >= len(df):
                equity.append(balance)
                continue

            next = df.iloc[i + 1]
            if signal.direction == "BUY":
                if next["Low"] <= sl:
                    pnl = -risk_amount
                elif next["High"] >= tp:
                    pnl = units * (tp - entry)
                else:
                    pnl = units * (float(next["Close"]) - entry)
            else:  # SELL
                if next["High"] >= sl:
                    pnl = -risk_amount
                elif next["Low"] <= tp:
                    pnl = units * (entry - tp)
                else:
                    pnl = units * (entry - float(next["Close"]))

            balance += pnl
            trade_pnls.append(pnl)
            equity.append(balance)
            trades_log.append(
                {
                    "date": str(df.index[i]),
                    "direction": signal.direction,
                    "entry": round(entry, 2),
                    "pnl": round(pnl, 2),
                }
            )

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
            "trades": trades_log[-20:],  # last 20 trades for display
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
