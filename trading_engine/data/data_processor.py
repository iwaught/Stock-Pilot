"""
Data processing utilities for the USDCLP trading engine.
Cleans and normalises raw market data for strategy consumption.
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove NaN rows, forward-fill missing values, and ensure required
    columns (Open, High, Low, Close, Volume) are present.
    """
    required = ["Open", "High", "Low", "Close"]
    for col in required:
        if col not in df.columns:
            df[col] = df.get("Close", pd.Series(dtype=float))

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[required + ["Volume"]].copy()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.ffill(inplace=True)
    df.dropna(inplace=True)
    return df


def to_historical_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert an OHLCV DataFrame to a list of dicts suitable for the
    Next.js frontend (matches the HistoricalRate interface).
    """
    records = []
    for dt, row in df.iterrows():
        records.append(
            {
                "date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt),
                "rate": round(float(row["Close"]), 2),
            }
        )
    return records


def calculate_returns(prices: pd.Series) -> pd.Series:
    """Compute simple period-over-period returns."""
    return prices.pct_change().dropna()


def resample_ohlcv(df: pd.DataFrame, freq: str = "4h") -> pd.DataFrame:
    """
    Resample tick/daily OHLCV data to a different frequency.

    Args:
        df: OHLCV DataFrame with a DatetimeIndex.
        freq: Pandas offset alias (e.g. '1h', '4h', '1D').
    """
    return df.resample(freq).agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
    ).dropna()
