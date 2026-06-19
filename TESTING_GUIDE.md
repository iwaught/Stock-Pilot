# 🧪 USDCLP-Pilot Trading Engine - Testing Guide

Complete guide to test the integrated ForexSmartBot trading engine with WhatsApp notifications.

## Table of Contents
1. [Quick Start Testing](#quick-start-testing)
2. [Development Setup](#development-setup)
3. [Test Scenarios](#test-scenarios)
4. [WhatsApp Setup](#whatsapp-setup)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start Testing

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/iwaught/USDCLP-Pilot.git
cd USDCLP-Pilot

# Install frontend dependencies
npm install

# Install Python trading engine dependencies
cd trading_engine
pip install -r requirements.txt
cd ..
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
# For basic testing, you can skip Twilio credentials initially
nano .env
```

### 3. Start the System

**Terminal 1 - Python Trading Engine:**
```bash
cd trading_engine
python api_server.py
# Should see: "Flask server running on http://0.0.0.0:5001"
```

**Terminal 2 - Next.js Frontend:**
```bash
npm run dev
# Should see: "▲ Next.js 15.0.0"
# Open: http://localhost:3000
```

---

## Development Setup

### Full Environment Configuration

Create `.env` file in the root directory:

```dotenv
# ── Twilio WhatsApp (Optional for basic testing) ──
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+56912345678

# ── Flask API Server ──
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000

# ── Strategy Parameters ──
RSI_OVERSOLD=35
RSI_OVERBOUGHT=65
BB_PERIOD=20
BB_STD_DEV=2.0
ATR_PERIOD=14
ATR_STOP_MULTIPLIER=1.5
ATR_TARGET_MULTIPLIER=3.0
RISK_PER_TRADE_PCT=1.0
ACCOUNT_BALANCE=10000

# ── Data Source ──
DATA_TICKER=USDCLP=X
HISTORICAL_DAYS=90
SIGNAL_CHECK_INTERVAL_MINUTES=60
```

---

## Test Scenarios

### Test 1: Run Live Signals (No Twilio)

**Goal:** Test signal generation without WhatsApp

```bash
cd trading_engine
python api_server.py
```

In another terminal:
```bash
curl http://localhost:5001/api/signals
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "signal": "BUY",
    "entry_price": 900.50,
    "stop_loss": 896.25,
    "take_profit": 909.50,
    "risk_reward": 2.0,
    "confidence": 85,
    "strategy": "USDCLP Mean Reversion",
    "timestamp": "2026-06-19T10:30:00Z"
  }
}
```

✅ **Success Criteria:**
- Returns valid JSON
- Contains BUY/SELL/HOLD signal
- Has entry price, stop loss, take profit
- Risk/reward ratio is positive

---

### Test 2: Backtest Historical Data

**Goal:** Test backtesting with 90 days of historical data

```bash
curl "http://localhost:5001/api/backtest?strategy=mean_reversion&days=90"
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "strategy": "mean_reversion",
    "period_days": 90,
    "total_trades": 12,
    "winning_trades": 8,
    "losing_trades": 4,
    "win_rate": 67.0,
    "total_return": 5.2,
    "sharpe_ratio": 1.45,
    "max_drawdown": -3.2,
    "trades": [
      {
        "entry_price": 900.5,
        "exit_price": 905.2,
        "return_pct": 0.52,
        "holding_hours": 6
      }
    ]
  }
}
```

✅ **Success Criteria:**
- Returns historical backtest results
- Shows win rate > 50%
- Includes Sharpe ratio
- Lists individual trades

---

### Test 3: Frontend Dashboard

**Goal:** Verify UI integration with backend

1. Open http://localhost:3000
2. You should see three tabs:
   - **Dashboard** - Real-time signal display
   - **Backtest** - Run and visualize backtest results
   - **Strategy Config** - Adjust parameters

**Test each tab:**

**Dashboard Tab:**
- ✅ Displays current signal (BUY/SELL/HOLD)
- ✅ Shows entry price, stop loss, take profit
- ✅ Displays confidence score
- ✅ Shows Bollinger Band position
- ✅ Has risk/reward ratio

**Backtest Tab:**
- ✅ Has strategy selector dropdown
- ✅ Has period selector (30/60/90 days)
- ✅ "Run Backtest" button works
- ✅ Shows trade table with results
- ✅ Displays performance metrics

**Strategy Config Tab:**
- ✅ Has sliders for all parameters
- ✅ Sliders update signal in real-time
- ✅ Shows current parameter values
- ✅ Parameters persist in session

---

### Test 4: WhatsApp Integration (Optional)

**Prerequisites:**
1. Create Twilio account: https://www.twilio.com/try-twilio
2. Enable WhatsApp Sandbox: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
3. Get your account credentials

**Setup:**

```bash
# Update .env with Twilio credentials
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+56912345678  # Your WhatsApp number
```

**Test Signal Delivery:**

```bash
cd trading_engine

# Run immediate signal check
python notifications/signal_manager.py
```

**Expected:**
- ✅ Message sent to your WhatsApp
- ✅ Format includes entry, stop loss, take profit
- ✅ Shows strategy and confidence
- ✅ Contains timestamp

**Sample WhatsApp Message:**
```
🎯 USDCLP Trading Signal
═══════════════════════
Signal: 🟢 BUY
Entry Price: 900.50 / Stop Loss: 896.25 / Take Profit: 909.50
Risk/Reward: 1:2.0 | Strategy: USDCLP Mean Reversion | Confidence: 85%
⏰ 2026-06-19 10:30 UTC
```

---

### Test 5: Automated Signal Scheduler (Optional)

**Goal:** Run signals every hour (configurable)

```bash
cd trading_engine

# Set interval to 1 minute for testing
# Edit config.py or .env:
# SIGNAL_CHECK_INTERVAL_MINUTES=1

python notifications/signal_manager.py
```

**Expected:**
- ✅ First signal sent immediately
- ✅ Next signal checks in 1 minute
- ✅ Continues running indefinitely
- ✅ Logs each check to console

**Stop with:** `Ctrl+C`

---

### Test 6: Strategy Configuration

**Goal:** Test parameter updates and signal changes

```bash
# Update parameters via API
curl -X POST http://localhost:5001/api/strategies/configure \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "mean_reversion",
    "params": {
      "rsi_oversold": 40,
      "rsi_overbought": 60,
      "bb_period": 15,
      "risk_per_trade_pct": 2.0
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Strategy configured",
  "params": {
    "rsi_oversold": 40,
    "rsi_overbought": 60,
    "bb_period": 15,
    "risk_per_trade_pct": 2.0
  }
}
```

✅ **Success Criteria:**
- ✅ Parameters updated successfully
- ✅ New signals reflect new parameters
- ✅ Frontend sliders show new values

---

## WhatsApp Setup

### Step 1: Create Twilio Account

1. Go to https://www.twilio.com/try-twilio
2. Sign up with your email
3. Verify phone number
4. Get credentials:
   - **Account SID**: Find on dashboard
   - **Auth Token**: Click "View full API credentials"

### Step 2: Enable WhatsApp Sandbox

1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Click "Send a WhatsApp message"
3. Sandbox will give you:
   - **From Number**: `whatsapp:+14155238886`
   - **Join Code**: Something like `join cream-pilot`
4. Send the join code to sandbox from your WhatsApp to activate it

### Step 3: Add to Environment

```bash
# .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+56912345678  # Your number with country code
```

### Step 4: Test

```bash
cd trading_engine
python -c "
from notifications.signal_manager import send_signal_whatsapp
send_signal_whatsapp({
    'signal': 'BUY',
    'entry_price': 900.50,
    'stop_loss': 896.25,
    'take_profit': 909.50,
    'risk_reward': 2.0,
    'confidence': 85,
    'strategy': 'USDCLP Mean Reversion'
})
"
```

---

## Troubleshooting

### Issue: Flask Server Won't Start

```
Error: Address already in use
```

**Solution:**
```bash
# Find process using port 5001
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or change port in .env
FLASK_PORT=5002
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
cd trading_engine
pip install -r requirements.txt
```

### Issue: CORS Error in Frontend

```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:**
1. Check `.env` has correct `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=http://localhost:3000
   ```
2. Restart Flask server
3. Check frontend is on correct URL (http://localhost:3000, not 127.0.0.1:3000)

### Issue: WhatsApp Message Not Received

**Checklist:**
- ✅ Twilio credentials correct in `.env`
- ✅ WhatsApp number has country code (e.g., +56 for Chile)
- ✅ Number is verified in Twilio sandbox
- ✅ Sandbox not expired (expires after 72 hours of inactivity)
- ✅ Check Twilio logs: https://console.twilio.com/us1/develop/sms/logs

**Renew Sandbox:**
```bash
# Send join code again to sandbox number
# "join cream-pilot" (or your code)
```

### Issue: Backtest Returns No Data

```
"total_trades": 0
```

**Solution:**
1. Check data source is working:
   ```bash
   python -c "import yfinance as yf; print(yf.download('USDCLP=X', period='90d'))"
   ```
2. Increase `HISTORICAL_DAYS` in `.env`
3. Check market is open (USDCLP trades M-F)

---

## API Reference

### GET /api/signals
Get current trading signal

```bash
curl http://localhost:5001/api/signals
```

### GET /api/backtest
Run historical backtest

```bash
curl "http://localhost:5001/api/backtest?strategy=mean_reversion&days=90"
```

**Parameters:**
- `strategy`: `mean_reversion` or `momentum` (default: `mean_reversion`)
- `days`: 7-365 (default: 90)

### POST /api/strategies/configure
Update strategy parameters

```bash
curl -X POST http://localhost:5001/api/strategies/configure \
  -H "Content-Type: application/json" \
  -d '{"strategy":"mean_reversion","params":{"rsi_oversold":40}}'
```

### GET /api/whatsapp/status
Check WhatsApp notification status

```bash
curl http://localhost:5001/api/whatsapp/status
```

---

## Performance Testing

### Load Test Signals

```bash
# Test 100 signal requests
for i in {1..100}; do
  curl -s http://localhost:5001/api/signals > /dev/null
done
echo "Completed 100 requests"
```

### Monitor Resource Usage

```bash
# Terminal 1: Monitor Python process
watch -n 1 'ps aux | grep python'

# Terminal 2: Monitor Flask requests
tail -f trading_engine/api_server.log
```

---

## Next Steps

After testing passes:

1. ✅ Deploy Flask to production (Heroku, AWS, etc.)
2. ✅ Set up permanent WhatsApp number (not sandbox)
3. ✅ Configure production database
4. ✅ Add portfolio tracking
5. ✅ Enable live trading (with broker API integration)

---

## Support

For issues, check:
- Flask server logs: `trading_engine/api_server.log`
- Browser console: `F12` → Console tab
- GitHub Issues: https://github.com/iwaught/USDCLP-Pilot/issues

Good luck testing! 🚀
