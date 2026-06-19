# USDCLP-Pilot Integration Guide

## Overview

This guide explains how to set up and run the complete USDCLP trading system, which combines:

1. **Python trading engine** (`trading_engine/`) — signal generation, backtesting, WhatsApp notifications
2. **Flask REST API** (`trading_engine/api_server.py`) — bridges Python engine with the Next.js frontend
3. **Next.js frontend** (`app/`) — real-time dashboard with signals, charts, and configuration UI

---

## Prerequisites

- **Node.js** ≥ 18 (for the Next.js frontend)
- **Python** ≥ 3.10 (for the trading engine)
- A **Twilio account** with WhatsApp Sandbox enabled (for notifications)

---

## 1. Clone & Install

```bash
git clone https://github.com/iwaught/USDCLP-Pilot.git
cd USDCLP-Pilot
```

### Next.js frontend

```bash
npm install
```

### Python trading engine

```bash
cd trading_engine
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

---

## 2. Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Key variables to configure:

| Variable | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | Twilio account SID (from console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sandbox number (e.g. `whatsapp:+14155238886`) |
| `WHATSAPP_TO` | Your WhatsApp number (e.g. `whatsapp:+56912345678`) |
| `FLASK_API_URL` | URL of the Flask server (default `http://localhost:5001`) |

---

## 3. Run the Application

### Option A — Full stack (Python + Next.js)

**Terminal 1 — Python Flask API:**

```bash
cd trading_engine
source venv/bin/activate
python api_server.py
```

The Flask server starts at `http://localhost:5001`.

**Terminal 2 — Signal scheduler (optional, sends WhatsApp alerts):**

```bash
cd trading_engine
source venv/bin/activate
python -m trading_engine.notifications.signal_manager
```

This runs an immediate check and then repeats every 60 minutes (configurable via `SIGNAL_CHECK_INTERVAL_MINUTES`).

**Terminal 3 — Next.js frontend:**

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Option B — Frontend only (no Python)

The Next.js app works standalone. It generates signals in-process using the Frankfurter API for historical data. Simply run:

```bash
npm run dev
```

WhatsApp notifications are not available in this mode.

---

## 4. API Endpoints

### Flask server (`http://localhost:5001`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/signals` | Cached trading signals (both strategies) |
| GET | `/api/signals/run` | Force fresh signal check (`?notify=true` to send WhatsApp) |
| POST | `/api/strategies/configure` | Update strategy parameters |
| GET | `/api/backtest` | Run backtest (`?strategy=mean_reversion&days=90`) |
| GET | `/api/whatsapp/status` | WhatsApp configuration status |
| GET | `/api/market` | Current price + historical rates |

### Next.js API routes (`http://localhost:3000`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/forex` | Current rate + 90-day history |
| GET | `/api/signals` | Trading signals (proxies to Flask, falls back to in-process) |
| GET | `/api/backtest` | Backtest results (proxies to Flask, falls back to in-process) |
| GET | `/api/config` | Strategy configuration |
| POST | `/api/config` | Update strategy parameters |

---

## 5. Twilio WhatsApp Setup

1. Create a free Twilio account at [twilio.com](https://www.twilio.com/try-twilio)
2. Navigate to **Messaging → Try it out → Send a WhatsApp message**
3. Follow the sandbox instructions: send `join <your-sandbox-keyword>` to the Twilio number from your WhatsApp
4. Set the environment variables in your `.env` file

### Test a notification

```bash
cd trading_engine
source venv/bin/activate
python -c "
from notifications.whatsapp_notifier import send_whatsapp_message
send_whatsapp_message('🎯 USDCLP-Pilot test message — system is working!')
"
```

---

## 6. Project Structure

```
USDCLP-Pilot/
├── app/                          # Next.js 15 frontend
│   ├── api/
│   │   ├── forex/route.ts        # Current + historical rates
│   │   ├── signals/route.ts      # Trading signals
│   │   ├── backtest/route.ts     # Backtest endpoint
│   │   └── config/route.ts       # Strategy configuration
│   ├── components/
│   │   ├── SignalCard.tsx         # Enhanced signal with SL/TP
│   │   ├── StrategyConfig.tsx     # Strategy parameter UI
│   │   ├── BacktestResults.tsx    # Backtest visualisation
│   │   └── ...                   # Existing components
│   └── page.tsx                  # Dashboard with tabs
├── trading_engine/               # Python backend
│   ├── strategies/
│   │   ├── base_strategy.py      # Abstract base + Signal dataclass
│   │   ├── usdclp_mean_reversion.py
│   │   └── momentum_strategy.py
│   ├── indicators/
│   │   ├── technical_analysis.py # RSI, SMA, MACD, BB, ATR
│   │   └── risk_management.py    # Position sizing, Sharpe, drawdown
│   ├── data/
│   │   ├── forex_data.py         # yfinance + Frankfurter fallback
│   │   └── data_processor.py     # OHLCV cleaning & utilities
│   ├── notifications/
│   │   ├── whatsapp_notifier.py  # Twilio WhatsApp
│   │   └── signal_manager.py     # Scheduler & orchestration
│   ├── api_server.py             # Flask REST API
│   ├── config.py                 # Env-based configuration
│   └── requirements.txt
├── docs/
│   ├── INTEGRATION_GUIDE.md      # This file
│   └── TRADING_STRATEGY.md       # Strategy documentation
└── .env.example
```
