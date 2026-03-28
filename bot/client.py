"""
Binance client wrapper.
Tries to connect to the Futures testnet API.
Falls back to simulation if anything goes wrong (network, KYC, etc).
"""

import logging
import time
import random
import string

logger = logging.getLogger("trading_bot.client")

# testnet keys — these are public testnet credentials
# in a real project you'd use env vars or a config file
TESTNET_API_KEY = "your_testnet_api_key_here"
TESTNET_API_SECRET = "your_testnet_api_secret_here"
TESTNET_URL = "https://testnet.binancefuture.com"


def _generate_order_id():
    """Generate a fake order ID that looks realistic."""
    return "SIM_" + "".join(random.choices(string.digits, k=12))


def _simulated_response(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Create a fake order response that mimics Binance API structure.
    Used when the real API is unavailable.
    """
    # simulate a tiny delay so it feels more realistic
    time.sleep(random.uniform(0.2, 0.6))

    # generate realistic-looking prices
    base_prices = {
        "BTCUSDT": 67500.0, "ETHUSDT": 3450.0, "BNBUSDT": 580.0,
        "SOLUSDT": 142.0, "XRPUSDT": 0.62, "DOGEUSDT": 0.145,
        "ADAUSDT": 0.48, "AVAXUSDT": 35.5, "DOTUSDT": 7.2,
    }

    if order_type == "MARKET":
        # for market orders, simulate a fill price with some slippage
        base = base_prices.get(symbol, 100.0)
        fill_price = round(base * random.uniform(0.998, 1.002), 2)
    else:
        fill_price = price

    response = {
        "orderId": _generate_order_id(),
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": str(quantity),
        "price": str(fill_price),
        "status": "FILLED" if order_type == "MARKET" else "NEW",
        "executedQty": str(quantity),
        "avgPrice": str(fill_price),
        "timestamp": int(time.time() * 1000),
        "simulated": True,  # flag so we know it's not real
    }

    # include stop price for stop-limit orders
    if order_type == "STOP_LIMIT" and stop_price is not None:
        response["stopPrice"] = str(stop_price)
        # stop-limit orders sit pending until trigger price is hit
        response["status"] = "NEW"

    logger.info(f"Generated simulated response for {symbol}")
    return response


def get_binance_client():
    """
    Try to create a Binance Futures client.
    Returns None if it fails — caller should handle that.
    """
    try:
        from binance.client import Client

        client = Client(
            TESTNET_API_KEY,
            TESTNET_API_SECRET,
            testnet=True
        )
        # quick connectivity check
        client.futures_ping()
        logger.info("Connected to Binance Futures testnet")
        return client

    except ImportError:
        logger.error("python-binance not installed! Run: pip install python-binance")
        return None
    except Exception as e:
        # could be network issue, bad keys, KYC, whatever
        logger.error(f"Failed to connect to Binance: {e}")
        return None


def place_order(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Place an order on Binance Futures testnet.
    If the API call fails for any reason, returns a simulated response instead.
    """
    client = get_binance_client()

    if client is not None:
        try:
            logger.info(f"Attempting real order: {side} {quantity} {symbol}")

            if order_type == "MARKET":
                result = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="MARKET",
                    quantity=quantity,
                )
            elif order_type == "STOP_LIMIT":
                # stop-limit uses STOP type on binance futures
                result = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="STOP",
                    quantity=quantity,
                    price=str(price),
                    stopPrice=str(stop_price),
                    timeInForce="GTC",
                )
            else:
                # regular LIMIT order
                result = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="LIMIT",
                    quantity=quantity,
                    price=str(price),
                    timeInForce="GTC",  # good till cancelled
                )

            result["simulated"] = False
            logger.info(f"Real order placed! ID: {result.get('orderId')}")
            return result

        except Exception as e:
            # fallback if API fails
            logger.error(f"Real order failed: {e}")
            logger.info("Falling back to simulated order...")
            print(f"\n⚠️  API error: {e}")
            print("   Using simulated response instead.\n")

    else:
        logger.info("No API connection — using simulation mode")
        print("\nℹ️  Running in simulation mode (API unavailable)\n")

    # fallback to simulation
    return _simulated_response(symbol, side, order_type, quantity, price, stop_price)
