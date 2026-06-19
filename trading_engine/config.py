"""
Configuration module for the USDCLP Trading Engine.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Twilio WhatsApp configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
WHATSAPP_TO = os.getenv("WHATSAPP_TO", "")  # Your WhatsApp number: whatsapp:+56912345678

# Flask server
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# OANDA API (optional alternative data source)
OANDA_API_KEY = os.getenv("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID", "")

# Strategy parameters - Mean Reversion
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "35"))
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "65"))
BB_PERIOD = int(os.getenv("BB_PERIOD", "20"))
BB_STD_DEV = float(os.getenv("BB_STD_DEV", "2.0"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_STOP_MULTIPLIER = float(os.getenv("ATR_STOP_MULTIPLIER", "1.5"))
ATR_TARGET_MULTIPLIER = float(os.getenv("ATR_TARGET_MULTIPLIER", "3.0"))

# Strategy parameters - Momentum
MOMENTUM_FAST_PERIOD = int(os.getenv("MOMENTUM_FAST_PERIOD", "12"))
MOMENTUM_SLOW_PERIOD = int(os.getenv("MOMENTUM_SLOW_PERIOD", "26"))
MOMENTUM_SIGNAL_PERIOD = int(os.getenv("MOMENTUM_SIGNAL_PERIOD", "9"))

# Risk management
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))  # 1% risk per trade
ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000.0"))
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "100000"))  # Max notional in CLP

# Signal scheduler
SIGNAL_CHECK_INTERVAL_MINUTES = int(os.getenv("SIGNAL_CHECK_INTERVAL_MINUTES", "60"))
TRADING_DAYS_ONLY = os.getenv("TRADING_DAYS_ONLY", "true").lower() == "true"

# Data
HISTORICAL_DAYS = int(os.getenv("HISTORICAL_DAYS", "90"))
DATA_TICKER = os.getenv("DATA_TICKER", "USDCLP=X")
