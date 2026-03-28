"""
Trade history — saves orders to a JSON file so you can review them later.
Nothing fancy, just append and read.
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("trading_bot.history")

# store history in project root
HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "trade_history.json"
)


def _load_history():
    """Load existing history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                # file got corrupted somehow, start fresh
                logger.warning("History file was not a list, resetting")
                return []
    except json.JSONDecodeError:
        logger.error("History file is corrupted, starting fresh")
        return []
    except Exception as e:
        logger.error(f"Error reading history: {e}")
        return []


def save_trade(order_result):
    """Save a trade to the history file."""
    history = _load_history()

    # add some extra metadata
    entry = {
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order": order_result,
    }

    history.append(entry)

    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        logger.info(f"Trade saved to history (total: {len(history)} trades)")
    except Exception as e:
        # don't crash if we can't save history
        logger.error(f"Failed to save trade history: {e}")
        print(f"⚠️  Couldn't save to history file: {e}")


def get_history():
    """Get all trade history."""
    return _load_history()


def display_history():
    """Print trade history in a readable format."""
    history = _load_history()

    if not history:
        print("\n📭 No trade history found.")
        print("   Place some orders first!\n")
        return

    print(f"\n{'=' * 60}")
    print(f"  📜 TRADE HISTORY ({len(history)} trades)")
    print(f"{'=' * 60}\n")

    for i, entry in enumerate(history, 1):
        order = entry.get("order", {})
        recorded = entry.get("recorded_at", "Unknown")
        symbol = order.get("symbol", "N/A")
        side = order.get("side", "N/A")
        qty = order.get("executedQty", order.get("quantity", "N/A"))
        price = order.get("avgPrice", order.get("price", "N/A"))
        is_sim = order.get("simulated", False)
        status = order.get("status", "N/A")

        mode_tag = "[SIM]" if is_sim else "[LIVE]"
        side_icon = "🟢" if side == "BUY" else "🔴"

        # try to calc total
        try:
            total = f"${float(qty) * float(price):,.2f}"
        except (ValueError, TypeError):
            total = "N/A"

        print(f"  #{i} {mode_tag} {recorded}")
        print(f"     {side_icon} {side} {qty} {symbol} @ {price} = {total}")
        print(f"     Status: {status}")
        print()

    print(f"{'=' * 60}\n")


def clear_history():
    """Clear all trade history. Mostly for testing."""
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            logger.info("Trade history cleared")
            print("🗑️  Trade history cleared.")
        else:
            print("ℹ️  No history file to clear.")
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        print(f"❌ Couldn't clear history: {e}")
