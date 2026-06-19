"""
Signal manager — orchestrates strategy execution, signal generation,
and WhatsApp notification dispatch.

Designed to be run:
  - Once (python -m trading_engine.notifications.signal_manager)
  - On a schedule (via the built-in scheduler or cron)
  - As a persistent background service
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import schedule

from trading_engine.data.forex_data import fetch_historical_ohlcv, fetch_current_rate
from trading_engine.data.data_processor import clean_ohlcv
from trading_engine.strategies.usdclp_mean_reversion import USDCLPMeanReversionStrategy
from trading_engine.strategies.momentum_strategy import MomentumStrategy
from trading_engine.notifications.whatsapp_notifier import (
    send_whatsapp_message,
    check_whatsapp_configured,
)
import trading_engine.config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level cache for the most recent signals
_last_signals: Dict[str, Any] = {}


def run_signal_check(notify: bool = True) -> Dict[str, Any]:
    """
    Fetch latest market data, run both strategies, and optionally
    send the most actionable signal via WhatsApp.

    Returns a dict with both strategy signals for the API.
    """
    global _last_signals

    logger.info("Running signal check at %s UTC", datetime.now(timezone.utc).isoformat())

    try:
        df_raw = fetch_historical_ohlcv(ticker=cfg.DATA_TICKER, days=cfg.HISTORICAL_DAYS)
        df = clean_ohlcv(df_raw)
    except Exception as exc:
        logger.error("Failed to fetch market data: %s", exc)
        return {"error": str(exc)}

    mean_rev = USDCLPMeanReversionStrategy()
    momentum = MomentumStrategy()

    mr_signal = mean_rev.generate_signal(df)
    mom_signal = momentum.generate_signal(df)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "currentPrice": mr_signal.entry_price or mom_signal.entry_price,
        "meanReversion": mr_signal.to_dict(),
        "momentum": mom_signal.to_dict(),
    }

    _last_signals = result

    if notify:
        _dispatch_notification(mr_signal, mom_signal)

    return result


def _dispatch_notification(mr_signal, mom_signal) -> None:
    """Choose the stronger signal and send a WhatsApp notification."""
    whatsapp_status = check_whatsapp_configured()
    if not whatsapp_status["configured"]:
        logger.warning("WhatsApp not configured — skipping notification")
        return

    # Prefer the signal with higher confidence; prefer non-HOLD signals
    priority = {"high": 3, "medium": 2, "low": 1}
    active_signals = [s for s in [mr_signal, mom_signal] if s.direction != "HOLD"]

    if not active_signals:
        logger.info("Both strategies return HOLD — no notification sent")
        return

    best = max(active_signals, key=lambda s: priority.get(s.confidence, 0))
    message = best.to_whatsapp_message()
    sent = send_whatsapp_message(message)
    if sent:
        logger.info("Signal sent via WhatsApp: %s (%s)", best.direction, best.strategy)
    else:
        logger.error("WhatsApp notification failed")


def get_last_signals() -> Dict[str, Any]:
    """Return the cached result of the most recent signal check."""
    return _last_signals


def start_scheduler(interval_minutes: int = None) -> None:
    """
    Start a blocking scheduler that runs signal checks on a fixed interval.
    Runs an initial check immediately, then on the schedule.
    """
    interval = interval_minutes or cfg.SIGNAL_CHECK_INTERVAL_MINUTES
    logger.info("Starting signal scheduler (every %d minutes)", interval)

    # Run once immediately
    run_signal_check()

    schedule.every(interval).minutes.do(run_signal_check)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    start_scheduler()
