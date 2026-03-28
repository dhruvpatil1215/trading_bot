"""
CLI interface for the trading bot.
Uses argparse to handle command-line arguments.
"""

import argparse
import sys
import logging

from bot.logging_config import setup_logging
from bot.orders import execute_order
from bot.history import display_history, clear_history


def create_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="🤖 Binance Futures Trading Bot (Testnet + Simulation Fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # order arguments
    parser.add_argument("--symbol", "-s", type=str, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument("--side", type=str, choices=["BUY", "SELL"], help="BUY or SELL")
    parser.add_argument("--type", "-t", type=str, choices=["MARKET", "LIMIT"], help="Order type")
    parser.add_argument("--quantity", "-q", type=float, help="Order quantity")
    parser.add_argument("--price", "-p", type=float, default=None, help="Price for LIMIT orders")

    # history flags
    parser.add_argument("--history", action="store_true", help="View trade history")
    parser.add_argument("--clear-history", action="store_true", help="Clear trade history")

    return parser


def print_banner():
    """Show banner."""
    banner = """
╔══════════════════════════════════════════════╗
║   🤖 Binance Futures Trading Bot v1.0       ║
║   Testnet + Simulation Fallback             ║
║                                              ║
║   Use --help for available commands          ║
╚══════════════════════════════════════════════╝
"""
    print(banner)


def main():
    logger = setup_logging()
    parser = create_parser()
    args = parser.parse_args()

    print_banner()

    # history mode
    if args.history:
        display_history()
        return

    if args.clear_history:
        clear_history()
        return

    # check required args
    missing = []
    if not args.symbol:
        missing.append("--symbol")
    if not args.side:
        missing.append("--side")
    if not args.type:
        missing.append("--type")
    if not args.quantity:
        missing.append("--quantity")

    if missing:
        print(f"\n❌ Missing required arguments: {', '.join(missing)}")
        sys.exit(1)

    # logging
    logger.info("=" * 40)
    logger.info("New order request received")

    # ✅ ORDER REQUEST SUMMARY (IMPORTANT FIX)
    print("\n===============================")
    print("        ORDER REQUEST")
    print("===============================")
    print(f"Symbol:     {args.symbol}")
    print(f"Side:       {args.side}")
    print(f"Type:       {args.type}")
    print(f"Quantity:   {args.quantity}")
    print(f"Price:      {args.price if args.price else 'MARKET PRICE'}")
    print("===============================\n")

    try:
        result = execute_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
        )

        if result:
            logger.info("Order completed successfully")
            print("\n✅ Order placed successfully\n")
        else:
            logger.error("Order failed")
            print("\n❌ Order failed\n")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n❌ ERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()