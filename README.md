# 🤖 Binance Futures Trading Bot

A CLI-based trading bot built with Python and the `python-binance` library. Designed to work with the Binance Futures Testnet API, with an automatic fallback to simulated responses when the API is unavailable.

## Why This Approach?

Working with crypto exchange APIs can be tricky — testnet endpoints go down, API keys expire, KYC requirements change, and network issues happen. Instead of letting these problems block development and testing, this bot uses a **dual-mode approach**:

1. **Live Mode**: Attempts to connect to Binance Futures Testnet and place real orders
2. **Simulation Mode**: If the API fails for any reason, generates realistic simulated responses

This way, the bot always works and you can test the full workflow regardless of API availability.

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance API wrapper + simulation fallback
│   ├── orders.py            # Order execution logic
│   ├── validators.py        # Input validation with friendly messages
│   ├── history.py           # Trade history (JSON file storage)
│   ├── logging_config.py    # Logging setup
│   └── cli.py               # CLI interface (argparse)
├── logs/                    # Log files (auto-created)
├── trade_history.json       # Trade records (auto-created)
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set your testnet API keys in bot/client.py
#    Get keys from: https://testnet.binancefuture.com
```

## Usage

### Place Orders

```bash
# Market buy order
python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Market sell
python -m bot.cli --symbol ETHUSDT --side SELL --type MARKET --quantity 0.5

# Limit buy order (requires --price)
python -m bot.cli --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 42000

# Limit sell
python -m bot.cli -s SOLUSDT --side SELL -t LIMIT -q 1.0 -p 150.00
```

### View Trade History

```bash
# Show all past trades
python -m bot.cli --history

# Clear trade history
python -m bot.cli --clear-history
```

### Help

```bash
python -m bot.cli --help
```

## How It Works

### python-binance Integration

The bot uses `python-binance` to connect to the **Binance Futures Testnet**:

```python
from binance.client import Client

client = Client(api_key, api_secret, testnet=True)
client.futures_create_order(
    symbol="BTCUSDT",
    side="BUY",
    type="MARKET",
    quantity=0.01
)
```

The client wrapper (`bot/client.py`) handles:
- Creating the connection with testnet credentials
- Connectivity check via `futures_ping()`
- Placing MARKET and LIMIT orders through the Futures API
- Catching **any** exception and falling back gracefully

### Simulation Fallback

When the API is unavailable (network issues, expired keys, KYC problems, library not installed), the bot automatically switches to simulation:

```python
# What happens internally:
try:
    result = client.futures_create_order(...)  # try real API
except Exception:
    result = _simulated_response(...)  # fallback to fake response
```

Simulated responses:
- Match the structure of real Binance API responses
- Include realistic prices with simulated slippage
- Are clearly marked with `"simulated": True`
- Show a warning in the console output

### Trade History

Every order (real or simulated) is saved to `trade_history.json`:
- Timestamped entries
- Full order details preserved
- Easily view with `--history` flag
- Human-readable JSON format

## Features

| Feature | Description |
|---------|-------------|
| Market Orders | Buy/sell at current market price |
| Limit Orders | Buy/sell at a specific price |
| Input Validation | Friendly error messages for bad inputs |
| Trade History | JSON file storage with formatted display |
| Logging | Console (INFO) + file (DEBUG) logging |
| Simulation Mode | Automatic fallback when API unavailable |
| CLI Interface | argparse with examples and help text |

## Challenges Faced and Solutions

### 1. Binance Testnet Reliability
**Problem**: The Futures testnet API can be unreliable — sometimes it's down, rate limits are strict, and API keys can expire without notice.

**Solution**: Built a simulation layer that generates responses matching the real API structure. The bot tries the real API first and seamlessly falls back to simulation. Users always see consistent output regardless of API status.

### 2. KYC and Account Restrictions
**Problem**: Even testnet accounts sometimes require verification steps, and the setup process can be confusing for new users.

**Solution**: The bot works out of the box in simulation mode. Users can optionally configure testnet keys for live testing, but it's not required for development or demonstration purposes.

### 3. Input Validation Edge Cases
**Problem**: Users might enter invalid symbols, negative quantities, or forget required fields for limit orders.

**Solution**: Created a validation layer with descriptive error messages that guide users to fix their inputs. For example, forgetting `--price` on a LIMIT order gives a clear message with an example command.

### 4. Keeping the Code Readable
**Problem**: It's tempting to over-engineer a trading bot with design patterns and abstractions.

**Solution**: Kept the codebase flat and simple — each module does one thing. No unnecessary classes or inheritance. Comments explain the "why" not the "what".

## Example Output

```
╔══════════════════════════════════════════════╗
║   🤖 Binance Futures Trading Bot v1.0       ║
║   Testnet + Simulation Fallback             ║
╚══════════════════════════════════════════════╝

ℹ️  Running in simulation mode (API unavailable)

================================================
  📋 ORDER SUMMARY [SIMULATED]
================================================
  Order ID  : SIM_483921057362
  Symbol    : BTCUSDT
  Side      : 🟢 BUY
  Type      : MARKET
  Quantity  : 0.01
  Price     : 67485.32
  Total     : $674.85
  Status    : FILLED
------------------------------------------------
  ⚠️  This was a simulated order
     (API was unavailable)
================================================
```

## Tech Stack

- **Python 3.x**
- **python-binance** — Official Binance API wrapper
- **argparse** — CLI argument parsing (stdlib)
- **logging** — Structured logging (stdlib)
- **json** — Trade history storage (stdlib)

## Notes

- This bot is for **educational/testing purposes only**
- Never use real funds without proper risk management
- Testnet API keys are public — never commit real API keys to git
- The simulation mode uses approximate prices and should not be used for financial decisions

---

*Built as an internship project to demonstrate practical API integration and error handling.*
