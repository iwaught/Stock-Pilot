"""
Technical analysis indicators for USDCLP trading.
Implements RSI, SMA, EMA, MACD, Bollinger Bands, and ATR.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI (Relative Strength Index)."""
    if len(prices) < period + 1:
        return 50.0

    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0


def calculate_sma(prices: pd.Series, period: int) -> float:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    return float(prices.rolling(period).mean().iloc[-1])


def calculate_ema(prices: pd.Series, period: int) -> float:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    return float(prices.ewm(span=period, adjust=False).mean().iloc[-1])


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Dict[str, float]:
    """Calculate MACD, signal line, and histogram."""
    if len(prices) < slow:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> Dict[str, float]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    if len(prices) < period:
        current = float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        return {"upper": current * 1.02, "middle": current, "lower": current * 0.98}

    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std

    return {
        "upper": float(upper.iloc[-1]),
        "middle": float(sma.iloc[-1]),
        "lower": float(lower.iloc[-1]),
    }


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> float:
    """Calculate Average True Range."""
    if len(close) < period + 1:
        return float((high - low).mean()) if len(high) > 0 else 0.0

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(com=period - 1, min_periods=period).mean()
    return float(atr.iloc[-1])


def calculate_support_resistance(prices: pd.Series) -> Dict[str, float]:
    """Identify support and resistance levels from recent price history."""
    if len(prices) < 20:
        current = float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        return {"support": current * 0.98, "resistance": current * 1.02}

    recent = prices.iloc[-30:]
    return {
        "support": float(recent.min()),
        "resistance": float(recent.max()),
    }


def calculate_all_indicators(
    df: pd.DataFrame,
    rsi_period: int = 14,
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_period: int = 14,
) -> Dict[str, Any]:
    """
    Calculate all technical indicators from an OHLCV dataframe.
    Expects columns: Open, High, Low, Close, Volume (or at least Close).
    """
    close = df["Close"]
    high = df.get("High", close)
    low = df.get("Low", close)

    return {
        "rsi": calculate_rsi(close, rsi_period),
        "sma20": calculate_sma(close, 20),
        "sma50": calculate_sma(close, 50),
        "ema12": calculate_ema(close, 12),
        "ema26": calculate_ema(close, 26),
        "macd": calculate_macd(close),
        "bollinger_bands": calculate_bollinger_bands(close, bb_period, bb_std),
        "atr": calculate_atr(high, low, close, atr_period),
        "support_resistance": calculate_support_resistance(close),
        "current_price": float(close.iloc[-1]),
        "volatility": float(close.pct_change().std() * 100) if len(close) > 1 else 0.0,
    }
