"""
Order logic — validates inputs and places the trade.
This is the main entry point for executing orders.
"""

import logging
from bot.validators import validate_all
from bot.client import place_order
from bot.history import save_trade

logger = logging.getLogger("trading_bot.orders")


def execute_order(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Validate inputs, place the order, and save to history.
    Returns the order result dict.
    """
    # step 1: validate everything first
    try:
        params = validate_all(symbol, side, order_type, quantity, price, stop_price)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n❌ Validation Error:\n   {e}")
        return None

    # step 2: place the order
    logger.info(f"Executing order: {params}")
    result = place_order(
        symbol=params["symbol"],
        side=params["side"],
        order_type=params["type"],
        quantity=params["quantity"],
        price=params["price"],
        stop_price=params.get("stop_price"),
    )

    if result is None:
        # shouldn't really happen since we have simulation fallback
        # but just in case
        logger.error("Order returned None — something went really wrong")
        print("\n❌ Failed to place order. Check logs for details.")
        return None

    # step 3: save to trade history
    save_trade(result)

    # step 4: print a nice summary
    _print_order_summary(result)

    return result


def _print_order_summary(order):
    """Print a formatted order summary to console."""
    is_sim = order.get("simulated", False)
    mode = "SIMULATED" if is_sim else "LIVE"

    symbol = order.get("symbol", "N/A")
    side = order.get("side", "N/A")
    otype = order.get("type", "N/A")
    qty = order.get("executedQty", order.get("quantity", "N/A"))
    price = order.get("avgPrice", order.get("price", "N/A"))
    order_id = order.get("orderId", "N/A")
    status = order.get("status", "N/A")
    stop_price = order.get("stopPrice", None)

    # calculate total value if possible
    try:
        total = float(qty) * float(price)
        total_str = f"${total:,.2f}"
    except (ValueError, TypeError):
        total_str = "N/A"

    # build the summary box
    width = 50
    print("\n" + "═" * width)
    print(f"  📋 ORDER SUMMARY [{mode}]")
    print("═" * width)
    print(f"  Order ID  : {order_id}")
    print(f"  Symbol    : {symbol}")
    print(f"  Side      : {'🟢 ' + side if side == 'BUY' else '🔴 ' + side}")
    print(f"  Type      : {otype}")
    print(f"  Quantity  : {qty}")
    print(f"  Price     : {price}")
    if stop_price:
        print(f"  Stop Price: {stop_price}")
    print(f"  Total     : {total_str}")
    print(f"  Status    : {status}")
    print("─" * width)

    if is_sim:
        print("  ⚠️  This was a simulated order")
        print("     (API was unavailable)")
    else:
        print("  ✅ Live order executed on Binance Testnet")

    print("═" * width + "\n")
