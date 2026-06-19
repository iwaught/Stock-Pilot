"""
Abstract base class for all USDCLP trading strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class Signal:
    """Represents a single trading signal."""

    direction: str  # 'BUY' | 'SELL' | 'HOLD'
    confidence: str  # 'high' | 'medium' | 'low'
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: str
    strategy: str
    reasoning: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    indicators: Dict[str, Any] = field(default_factory=dict)
    hold_time: str = "4-24 hours"

    def confidence_pct(self) -> int:
        """Return confidence as an integer percentage."""
        return {"high": 85, "medium": 65, "low": 45}.get(self.confidence, 50)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "confidence": self.confidence,
            "confidencePct": self.confidence_pct(),
            "entryPrice": self.entry_price,
            "stopLoss": self.stop_loss,
            "takeProfit": self.take_profit,
            "riskReward": self.risk_reward,
            "strategy": self.strategy,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
            "holdTime": self.hold_time,
            "indicators": self.indicators,
        }

    def to_whatsapp_message(self) -> str:
        """Format signal as a WhatsApp message."""
        direction_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(
            self.direction, "⚪"
        )
        return (
            f"🎯 *USDCLP Trading Signal*\n"
            f"{'═' * 23}\n"
            f"Signal: {direction_emoji} *{self.direction}*\n"
            f"Entry Price: {self.entry_price:,.2f}\n"
            f"Stop Loss: {self.stop_loss:,.2f}\n"
            f"Take Profit: {self.take_profit:,.2f}\n"
            f"Risk/Reward: {self.risk_reward}\n"
            f"Strategy: {self.strategy}\n"
            f"Confidence: {self.confidence_pct()}%\n"
            f"Time: {self.timestamp[:19].replace('T', ' ')} UTC\n"
            f"\n"
            f"⏰ Hold time: {self.hold_time}\n"
            f"\n"
            f"📊 _{self.reasoning}_\n"
            f"\n"
            f"⚠️ _Not financial advice. Trade at your own risk._"
        )


class BaseStrategy(ABC):
    """Abstract base for all trading strategies."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """Generate a trading signal from market data."""

    @abstractmethod
    def backtest(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10000.0,
    ) -> Dict[str, Any]:
        """Run a backtest and return performance metrics."""
