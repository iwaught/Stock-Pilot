"""
USDCLP forex data fetching using yfinance.
Provides current rate and historical OHLCV data.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd
import requests


def fetch_historical_ohlcv(
    ticker: str = "USDCLP=X",
    days: int = 90,
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data for USDCLP via yfinance.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume,
    indexed by date (UTC).  Falls back to the free frankfurter API if
    yfinance is unavailable.
    """
    try:
        import yfinance as yf  # lazy import to avoid hard dependency at startup

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

        if df.empty:
            raise ValueError("yfinance returned empty dataframe")

        df.index = pd.to_datetime(df.index, utc=True)
        df.sort_index(inplace=True)
        return df

    except Exception as yf_error:
        print(f"yfinance failed ({yf_error}), falling back to Frankfurter API")
        return _fetch_from_frankfurter(days)


def fetch_current_rate(ticker: str = "USDCLP=X") -> Optional[float]:
    """
    Fetch the most recent USD/CLP exchange rate.
    Returns the rate as a float, or None on failure.
    """
    try:
        import yfinance as yf

        data = yf.Ticker(ticker)
        info = data.fast_info
        price = getattr(info, "last_price", None)
        if price:
            return float(price)
    except Exception:
        pass

    # Fallback: use frankfurter
    try:
        resp = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=CLP", timeout=10
        )
        resp.raise_for_status()
        return float(resp.json()["rates"]["CLP"])
    except Exception:
        pass

    # Last resort: last value from historical data
    try:
        df = _fetch_from_frankfurter(days=5)
        if not df.empty:
            return float(df["Close"].iloc[-1])
    except Exception:
        pass

    return None


def _fetch_from_frankfurter(days: int = 90) -> pd.DataFrame:
    """Fetch historical close prices from the free Frankfurter API."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)

    url = f"https://api.frankfurter.app/{start}..{end}?from=USD&to=CLP"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for date_str, rate_dict in data.get("rates", {}).items():
        clp = rate_dict.get("CLP")
        if clp:
            records.append({"date": date_str, "Close": float(clp)})

    if not records:
        raise ValueError("Frankfurter API returned no CLP rates")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    # Synthesise OHLC columns from Close (Frankfurter only provides close)
    df["Open"] = df["Close"].shift(1).fillna(df["Close"])
    df["High"] = df["Close"] * 1.005
    df["Low"] = df["Close"] * 0.995
    df["Volume"] = 0

    return df[["Open", "High", "Low", "Close", "Volume"]]
