"""
Interactive menu mode for the trading bot.
Provides a loop-based menu with prompts — nicer than remembering CLI flags.
"""

import sys
import logging

from bot.orders import execute_order
from bot.history import display_history, clear_history
from bot.validators import SUPPORTED_SYMBOLS, VALID_SIDES, VALID_ORDER_TYPES

logger = logging.getLogger("trading_bot.interactive")


def _prompt_choice(prompt, options, allow_custom=False):
    """
    Show numbered options and let user pick one.
    Returns the selected value.
    """
    print(f"\n  {prompt}")
    print("  " + "─" * 35)
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")

    if allow_custom:
        print(f"    {len(options) + 1}. [Enter custom value]")

    while True:
        try:
            choice = input("\n  → Your choice: ").strip()

            # let user type the value directly too
            if choice.upper() in [o.upper() for o in options]:
                return choice.upper()

            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
            elif allow_custom and idx == len(options) + 1:
                custom = input("  → Enter value: ").strip()
                return custom.upper()
            else:
                print("  ❌ Invalid choice, try again")
        except ValueError:
            if allow_custom and choice:
                # maybe they typed a custom value directly
                return choice.upper()
            print("  ❌ Please enter a number or valid option")
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            return None


def _prompt_input(prompt, required=True, default=None):
    """Get text input from user with optional default."""
    suffix = f" [{default}]" if default else ""
    suffix += " (required)" if required and not default else ""

    try:
        value = input(f"  → {prompt}{suffix}: ").strip()

        if not value and default:
            return str(default)
        if not value and required:
            print("  ❌ This field is required")
            return _prompt_input(prompt, required, default)

        return value if value else None
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return None


def _confirm_order(params):
    """Show order details and ask for confirmation before placing."""
    print("\n  " + "═" * 40)
    print("  📋 ORDER CONFIRMATION")
    print("  " + "═" * 40)
    print(f"    Symbol    : {params.get('symbol', 'N/A')}")
    print(f"    Side      : {params.get('side', 'N/A')}")
    print(f"    Type      : {params.get('type', 'N/A')}")
    print(f"    Quantity  : {params.get('quantity', 'N/A')}")

    if params.get('price'):
        print(f"    Price     : {params.get('price')}")
    if params.get('stop_price'):
        print(f"    Stop Price: {params.get('stop_price')}")

    print("  " + "─" * 40)

    try:
        confirm = input("\n  Place this order? (y/n): ").strip().lower()
        return confirm in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _place_order_flow():
    """Walk user through placing an order step by step."""
    print("\n  📝 NEW ORDER")
    print("  " + "=" * 35)

    # pick symbol — show popular ones but allow custom
    popular = SUPPORTED_SYMBOLS[:8]  # don't show all of them
    symbol = _prompt_choice("Select trading pair:", popular, allow_custom=True)
    if not symbol:
        return

    # pick side
    side = _prompt_choice("Order side:", VALID_SIDES)
    if not side:
        return

    # pick type
    order_type = _prompt_choice("Order type:", VALID_ORDER_TYPES)
    if not order_type:
        return

    # get quantity
    quantity = _prompt_input("Quantity (e.g., 0.01)")
    if not quantity:
        return

    # get price if needed
    price = None
    stop_price = None

    if order_type in ("LIMIT", "STOP_LIMIT"):
        price = _prompt_input("Limit price")
        if not price:
            return

    if order_type == "STOP_LIMIT":
        stop_price = _prompt_input("Stop/trigger price")
        if not stop_price:
            return

    # confirm before executing
    order_params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }

    if not _confirm_order(order_params):
        print("  ❌ Order cancelled.\n")
        return

    # go!
    print("\n  ⏳ Placing order...")
    execute_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )


def run_interactive():
    """Main interactive menu loop."""
    print("\n  🎛️  Interactive Mode")
    print("  Type a number to select an option, or 'q' to quit.\n")

    while True:
        print("  ┌──────────────────────────────────┐")
        print("  │      MAIN MENU                   │")
        print("  ├──────────────────────────────────┤")
        print("  │  1. 📝 Place New Order            │")
        print("  │  2. 📜 View Trade History          │")
        print("  │  3. 🗑️  Clear History              │")
        print("  │  4. ❌ Exit                        │")
        print("  └──────────────────────────────────┘")

        try:
            choice = input("\n  → Select option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 Goodbye!\n")
            break

        if choice == "1":
            _place_order_flow()
        elif choice == "2":
            display_history()
        elif choice == "3":
            try:
                confirm = input("  Are you sure? (y/n): ").strip().lower()
                if confirm in ("y", "yes"):
                    clear_history()
            except (EOFError, KeyboardInterrupt):
                pass
        elif choice in ("4", "q", "Q", "quit", "exit"):
            print("\n  👋 Goodbye!\n")
            break
        else:
            print("  ❌ Invalid option, pick 1-4\n")
