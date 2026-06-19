"""
Flask REST API server for the USDCLP trading engine.

Endpoints:
  GET  /api/signals              — Current trading signals (both strategies)
  GET  /api/signals/run          — Force a fresh signal check (+ WhatsApp)
  POST /api/strategies/configure — Update strategy parameters at runtime
  GET  /api/backtest             — Run backtest (?strategy=mean_reversion&days=90)
  GET  /api/whatsapp/status      — WhatsApp configuration status
  GET  /health                   — Health check
"""

import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

import trading_engine.config as cfg
from trading_engine.data.forex_data import fetch_historical_ohlcv, fetch_current_rate
from trading_engine.data.data_processor import clean_ohlcv, to_historical_list
from trading_engine.strategies.usdclp_mean_reversion import USDCLPMeanReversionStrategy
from trading_engine.strategies.momentum_strategy import MomentumStrategy
from trading_engine.notifications.signal_manager import run_signal_check, get_last_signals
from trading_engine.notifications.whatsapp_notifier import check_whatsapp_configured

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=cfg.CORS_ORIGINS)

# Strategy instances (mutated by /api/strategies/configure)
_mean_reversion = USDCLPMeanReversionStrategy()
_momentum = MomentumStrategy()


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_market_data(days: int = None):
    """Fetch and clean market data; raise on failure."""
    df_raw = fetch_historical_ohlcv(ticker=cfg.DATA_TICKER, days=days or cfg.HISTORICAL_DAYS)
    return clean_ohlcv(df_raw)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.get("/api/signals")
def get_signals():
    """Return cached signals (or run a fresh check if cache is empty)."""
    cached = get_last_signals()
    if cached:
        return jsonify(cached)
    return get_signals_fresh()


@app.get("/api/signals/run")
def get_signals_fresh():
    """Force a fresh signal check and optionally send WhatsApp notification."""
    notify = request.args.get("notify", "false").lower() == "true"
    try:
        result = run_signal_check(notify=notify)
        return jsonify(result)
    except Exception:
        logger.exception("Signal generation failed")
        return jsonify({"error": "Signal generation failed. Check server logs."}), 500


@app.post("/api/strategies/configure")
def configure_strategy():
    """
    Update strategy parameters at runtime.

    Body (JSON, all fields optional):
    {
        "rsiOversold": 35,
        "rsiOverbought": 65,
        "bbPeriod": 20,
        "bbStdDev": 2.0,
        "atrPeriod": 14,
        "atrStopMultiplier": 1.5,
        "atrTargetMultiplier": 3.0
    }
    """
    # NOTE: strategy instances are module-level singletons. This is safe for a
    # single-worker development server. For multi-worker production deployments,
    # consider storing config in a database or using Flask application context.
    global _mean_reversion, _momentum
    body = request.get_json(silent=True) or {}

    _mean_reversion = USDCLPMeanReversionStrategy(
        rsi_oversold=body.get("rsiOversold"),
        rsi_overbought=body.get("rsiOverbought"),
        bb_period=body.get("bbPeriod"),
        bb_std=body.get("bbStdDev"),
        atr_period=body.get("atrPeriod"),
        atr_stop_mult=body.get("atrStopMultiplier"),
        atr_target_mult=body.get("atrTargetMultiplier"),
    )

    return jsonify({"status": "updated", "config": body})


@app.get("/api/backtest")
def run_backtest():
    """
    Run a strategy backtest.

    Query params:
      strategy: 'mean_reversion' (default) | 'momentum'
      days:     number of historical days (default 90)
    """
    strategy_name = request.args.get("strategy", "mean_reversion")
    days = int(request.args.get("days", cfg.HISTORICAL_DAYS))

    try:
        df = _get_market_data(days)
    except Exception:
        logger.exception("Failed to fetch market data for backtest")
        return jsonify({"error": "Failed to fetch market data. Check server logs."}), 500

    strategy = _mean_reversion if strategy_name == "mean_reversion" else _momentum
    result = strategy.backtest(df)
    result["strategy"] = strategy_name
    result["days"] = days
    return jsonify(result)


@app.get("/api/whatsapp/status")
def whatsapp_status():
    return jsonify(check_whatsapp_configured())


@app.get("/api/market")
def market_data():
    """Return current price and historical rates for the frontend."""
    try:
        df = _get_market_data()
        current = fetch_current_rate(cfg.DATA_TICKER)
        historical = to_historical_list(df)
        return jsonify({
            "currentPrice": current,
            "historical": historical,
        })
    except Exception:
        logger.exception("Failed to fetch market data")
        return jsonify({"error": "Failed to fetch market data. Check server logs."}), 500


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host=cfg.FLASK_HOST, port=cfg.FLASK_PORT, debug=False)
