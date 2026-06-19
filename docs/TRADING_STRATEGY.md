# USDCLP Trading Strategy Documentation

## Overview

The USDCLP-Pilot implements two complementary trading strategies for the USD/CLP currency pair:

1. **Mean Reversion** — exploits overbought/oversold conditions using Bollinger Bands and RSI
2. **Momentum** — follows directional price moves confirmed by MACD crossovers

---

## Strategy 1: USDCLP Mean Reversion

### Rationale

The USD/CLP exchange rate tends to exhibit mean-reversion behaviour over short to medium timeframes due to:
- Central Bank of Chile (BCCH) intervention tendencies
- Copper price correlations creating cyclical pressures
- Strong liquidity support near historically significant levels

### Entry Conditions

**BUY signal (USD strength expected)**
- Price touches or crosses below the lower Bollinger Band (20-period, 2σ)
- RSI < 35 (oversold)
- Combined score ≥ 4 across all conditions

**SELL signal (USD weakness expected)**
- Price touches or crosses above the upper Bollinger Band (20-period, 2σ)
- RSI > 65 (overbought)
- Combined score ≥ 4 across all conditions

### Exit Levels

| Level | Calculation |
|---|---|
| Stop-Loss | Entry ± ATR(14) × 1.5 |
| Take-Profit | Entry ± ATR(14) × 3.0 |
| Risk/Reward | 1:2.0 (default) |

### Confidence Scoring

| Score Difference | Confidence | WhatsApp notification |
|---|---|---|
| ≥ 6 | High (85%) | Always |
| 4–5 | Medium (65%) | Always |
| < 4 | HOLD | Never |

---

## Strategy 2: USDCLP Momentum

### Rationale

Significant macro events (copper price shocks, Chilean political events, US Fed decisions) create extended directional moves that can be captured with momentum strategies.

### Entry Conditions

**BUY signal**
- MACD histogram crosses from negative to positive
- Price is above SMA50

**SELL signal**
- MACD histogram crosses from positive to negative
- Price is below SMA50

### Exit Levels

| Level | Calculation |
|---|---|
| Stop-Loss | Entry ± ATR(14) × 1.5 |
| Take-Profit | Entry ± ATR(14) × 3.0 |
| Risk/Reward | 1:2.0 |

---

## Technical Indicators

### Bollinger Bands (20, 2.0)
- **Upper Band**: SMA20 + 2×σ — overbought zone
- **Middle Band**: SMA20 — fair value
- **Lower Band**: SMA20 − 2×σ — oversold zone

### RSI (14)
| Value | Interpretation |
|---|---|
| < 30 | Strongly oversold |
| 30–35 | Oversold |
| 35–65 | Neutral |
| 65–70 | Overbought |
| > 70 | Strongly overbought |

### ATR (14)
Average True Range measures volatility. Used for:
- Dynamic stop-loss placement (1.5× ATR)
- Take-profit targets (3.0× ATR)
- Position sizing (risk/ATR × account risk)

### MACD (12, 26, 9)
- **MACD Line**: EMA(12) − EMA(26)
- **Signal Line**: EMA(9) of MACD
- **Histogram**: MACD − Signal (key for crossover detection)

### SMA 20 / SMA 50
- Short-term and medium-term trend direction
- Golden cross (SMA20 > SMA50) → bullish bias
- Death cross (SMA20 < SMA50) → bearish bias

---

## Risk Management

### Position Sizing

```
Risk Amount = Account Balance × Risk% (default 1%)
Position Size = Risk Amount / (Entry − Stop Loss)
```

**Example:**
- Account: $10,000
- Risk: 1% = $100
- Entry: 900.00, Stop: 896.50 (3.50 CLP distance)
- Position: $100 / 3.50 = ~28.6 USD notional

### Kelly Criterion (informational)

The full Kelly fraction is not used operationally but is tracked in backtests as a reference:

```
f* = (bp - q) / b
where b = odds, p = win rate, q = 1 - p
```

### Maximum Risk Limits

| Parameter | Default | Description |
|---|---|---|
| Risk per trade | 1% | Maximum loss per signal |
| Max position | 100,000 CLP | Notional cap |
| Hold time | 4–24 hours | Expected holding period |

---

## WhatsApp Signal Format

```
🎯 USDCLP Trading Signal
═══════════════════════
Signal: 🟢 BUY
Entry Price: 900.50
Stop Loss: 896.25
Take Profit: 909.50
Risk/Reward: 1:2.0
Strategy: USDCLP Mean Reversion
Confidence: 85%
Time: 2025-06-15 14:30 UTC

⏰ Hold time: 4-24 hours

📊 Price at/below lower Bollinger Band (896.10). RSI oversold at 32.4. MACD positive momentum.

⚠️ Not financial advice. Trade at your own risk.
```

---

## Backtesting Methodology

The in-built backtester uses:

1. **Event-driven simulation** — processes each historical bar sequentially
2. **No lookahead bias** — signal generated using only data up to bar `i`
3. **Next-bar execution** — trade filled at bar `i+1` open/close
4. **Fixed risk** — 1% of running balance per trade
5. **Stop/target detection** — checks if next bar's high/low triggers exit

### Metrics

| Metric | Description |
|---|---|
| Total Return | (Final − Initial) / Initial × 100% |
| Win Rate | Winning trades / Total trades |
| Sharpe Ratio | Annualised excess return / σ (daily, 252 periods) |
| Max Drawdown | Maximum peak-to-trough decline |

---

## Disclaimer

This system is for **educational and informational purposes only**. It does not constitute financial advice. Currency trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results.
