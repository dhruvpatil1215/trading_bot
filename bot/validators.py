"""
Input validation for trade parameters.
Tries to catch common mistakes before hitting the API.
"""

import logging

logger = logging.getLogger("trading_bot.validators")

# symbols we support — can expand this later
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT",
]

VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP_LIMIT"]


def validate_symbol(symbol):
    """Check if trading pair is supported."""
    symbol = symbol.upper().strip()
    if symbol not in SUPPORTED_SYMBOLS:
        logger.warning(f"Symbol '{symbol}' not in supported list")
        print(f"\n⚠️  Warning: '{symbol}' might not be a valid trading pair.")
        print(f"   Supported pairs: {', '.join(SUPPORTED_SYMBOLS[:5])}...")
        # still allow it — maybe user knows what they're doing
        return symbol
    return symbol


def validate_side(side):
    """Validate order side (BUY/SELL)."""
    side = side.upper().strip()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be BUY or SELL.\n"
            f"  Example: --side BUY"
        )
    return side


def validate_order_type(order_type):
    """Validate order type."""
    # normalize different input formats
    order_type = order_type.upper().strip().replace("-", "_")
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be MARKET, LIMIT, or STOP_LIMIT.\n"
            f"  Example: --type LIMIT\n"
            f"  For stop-limit: --type STOP_LIMIT"
        )
    return order_type


def validate_quantity(quantity):
    """Make sure quantity makes sense."""
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(
            f"Quantity must be a number, got '{quantity}'.\n"
            f"  Example: --quantity 0.01"
        )

    if qty <= 0:
        raise ValueError(
            f"Quantity must be positive, got {qty}.\n"
            f"  Hint: Use a small value like 0.001 for testing"
        )

    # warn if quantity seems unusually large
    if qty > 1000:
        logger.warning(f"Large quantity detected: {qty}")
        print(f"\n⚠️  Heads up: quantity {qty} seems pretty large. Double check?")

    return qty


def validate_price(price, order_type):
    """Validate price — required for LIMIT and STOP_LIMIT orders."""
    if order_type in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise ValueError(
                f"Price is required for {order_type} orders!\n"
                f"  Example: --price 42000.50"
            )
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValueError(
                f"Price must be a number, got '{price}'.\n"
                f"  Example: --price 42000.50"
            )
        if p <= 0:
            raise ValueError(f"Price must be positive, got {p}")
        return p

    # for MARKET orders, price is ignored
    if price is not None:
        logger.info("Price provided for MARKET order — will be ignored")
        print("ℹ️  Note: price is ignored for MARKET orders")
    return None


def validate_stop_price(stop_price, order_type):
    """Validate stop price — only needed for STOP_LIMIT orders."""
    if order_type == "STOP_LIMIT":
        if stop_price is None:
            raise ValueError(
                "Stop price is required for STOP_LIMIT orders!\n"
                "  This is the trigger price that activates your limit order.\n"
                "  Example: --stop-price 41000"
            )
        try:
            sp = float(stop_price)
        except (ValueError, TypeError):
            raise ValueError(
                f"Stop price must be a number, got '{stop_price}'.\n"
                f"  Example: --stop-price 41000"
            )
        if sp <= 0:
            raise ValueError(f"Stop price must be positive, got {sp}")
        return sp

    # not a stop-limit order, ignore stop price
    if stop_price is not None:
        logger.info(f"Stop price ignored for {order_type} orders")
        print(f"ℹ️  Note: stop price is only used for STOP_LIMIT orders")
    return None


def validate_all(symbol, side, order_type, quantity, price, stop_price=None):
    """
    Run all validations at once.
    Returns cleaned values or raises ValueError.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)
    clean_stop = validate_stop_price(stop_price, clean_type)

    logger.info(f"Validation passed: {clean_symbol} {clean_side} {clean_type} qty={clean_qty}")

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "type": clean_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stop_price": clean_stop,
    }
