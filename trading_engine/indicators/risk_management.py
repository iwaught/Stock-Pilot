"""
Risk management utilities for USDCLP trading.
Handles position sizing, stop-loss, take-profit, and Sharpe ratio.
"""

import math
from typing import Tuple
import numpy as np
import pandas as pd


def calculate_position_size(
    account_balance: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
    pip_value: float = 1.0,
) -> float:
    """
    Calculate position size based on fixed-risk model.

    Args:
        account_balance: Total account balance in base currency.
        risk_pct: Percentage of account to risk (e.g. 1.0 for 1%).
        entry_price: Proposed entry price.
        stop_loss_price: Stop-loss price.
        pip_value: Value of 1 unit of price movement (default 1 CLP).

    Returns:
        Position size in units (notional CLP amount).
    """
    risk_amount = account_balance * (risk_pct / 100)
    price_risk = abs(entry_price - stop_loss_price)
    if price_risk == 0:
        return 0.0
    return round(risk_amount / price_risk * pip_value, 2)


def calculate_stop_loss(
    entry_price: float,
    atr: float,
    direction: str,
    multiplier: float = 1.5,
) -> float:
    """
    Calculate stop-loss price using ATR.

    Args:
        entry_price: Entry price.
        atr: Average True Range value.
        direction: 'BUY' or 'SELL'.
        multiplier: ATR multiplier for stop distance.
    """
    if direction.upper() == "BUY":
        return round(entry_price - atr * multiplier, 2)
    return round(entry_price + atr * multiplier, 2)


def calculate_take_profit(
    entry_price: float,
    stop_loss: float,
    risk_reward: float = 2.0,
) -> float:
    """
    Calculate take-profit price based on risk/reward ratio.

    Args:
        entry_price: Entry price.
        stop_loss: Stop-loss price.
        risk_reward: Desired risk/reward ratio (default 2.0 = 1:2).
    """
    risk = abs(entry_price - stop_loss)
    if entry_price > stop_loss:  # BUY
        return round(entry_price + risk * risk_reward, 2)
    return round(entry_price - risk * risk_reward, 2)


def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
) -> Tuple[float, str]:
    """
    Calculate actual risk/reward ratio.

    Returns:
        Tuple of (ratio_float, formatted_string e.g. "1:2.5").
    """
    risk = abs(entry_price - stop_loss)
    reward = abs(entry_price - take_profit)
    if risk == 0:
        return (0.0, "N/A")
    ratio = reward / risk
    return (round(ratio, 2), f"1:{ratio:.1f}")


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    periods_per_year: int = 252,
) -> float:
    """
    Calculate annualised Sharpe ratio from a series of period returns.

    Args:
        returns: Series of period returns (decimal, not percent).
        risk_free_rate: Annual risk-free rate (default 4%).
        periods_per_year: Trading periods in a year (252 for daily).
    """
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free_rate / periods_per_year
    std = returns.std()
    if std == 0:
        return 0.0
    return float(excess.mean() / std * math.sqrt(periods_per_year))


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown from an equity curve.

    Returns:
        Maximum drawdown as a negative percentage (e.g. -0.15 = -15%).
    """
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return float(drawdown.min())


def calculate_win_rate(trades: list) -> float:
    """
    Calculate win rate from a list of trade P&L values.

    Args:
        trades: List of P&L values (positive = win, negative = loss).

    Returns:
        Win rate as a percentage (0-100).
    """
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t > 0)
    return round(wins / len(trades) * 100, 1)
