"""Manual scraper check for Amazon order or shipping extraction.

Usage:
  python3 scripts/debug/manual_scraper_check.py order 123-4567890-1234567
  python3 scripts/debug/manual_scraper_check.py shipping 123-4567890-1234567
  python3 scripts/debug/manual_scraper_check.py shipping 123-4567890-1234567 amz_business
"""

import asyncio
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

load_dotenv(override=True)

from amazon_scraper import AmazonScraper


async def main() -> None:
    args = sys.argv[1:]
    debug = False
    account_type = "amz_personal"

    if "--debug" in args:
        debug = True
        args = [arg for arg in args if arg != "--debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")
        logging.getLogger("Agent").setLevel(logging.DEBUG)
        logging.getLogger("browser_use").setLevel(logging.DEBUG)
        print("DEBUG logging enabled for Agent/browser_use.")

    if len(args) >= 3:
        mode = args[0]
        order_number = args[1]
        account_type = args[2]
    elif len(args) >= 2:
        mode = args[0]
        order_number = args[1]
    elif len(args) == 1:
        mode = "shipping"
        order_number = args[0]
    else:
        mode = input("Test type (order/shipping) [shipping]: ").strip() or "shipping"
        order_number = input("Enter Amazon order number (e.g. 123-4567890-1234567): ").strip()
        account_type = input("Account type (amz_personal/amz_business) [amz_personal]: ").strip() or "amz_personal"

    if not order_number:
        print("Error: order number required")
        raise SystemExit(1)

    if mode not in ("order", "shipping"):
        print(f"Error: mode must be 'order' or 'shipping', got '{mode}'")
        raise SystemExit(1)
    if account_type not in ("amz_personal", "amz_business"):
        print(f"Error: account_type must be 'amz_personal' or 'amz_business', got '{account_type}'")
        raise SystemExit(1)

    scraper = AmazonScraper(account_type=account_type)

    if mode == "order":
        print(f"\nTesting scrape_order_confirmation with order: {order_number} (account={account_type})")
        print("Browser will open - watch for navigation to Amazon invoice page...")
        func = scraper.scrape_order_confirmation
    else:
        print(f"\nTesting scrape_shipping_confirmation with order: {order_number} (account={account_type})")
        print("Browser will open - watch for navigation to Amazon order details page...")
        func = scraper.scrape_shipping_confirmation

    print("Press Ctrl+C to abort at any time.\n")

    try:
        result = await func(order_number)
        print("\n=== SUCCESS: Agent returned structured data ===")
        print(result.model_dump_json(indent=2))
    except RuntimeError as exc:
        print("\n=== AGENT ERROR (no structured output) ===")
        print(str(exc))
        print("\nCheck debug artifacts:")
        print("  GIF: ./logs/agent.gif")
        print("  Conversation dir: ./logs/agent_conversations/")
    except Exception as exc:
        print("\n=== UNEXPECTED ERROR ===")
        print(f"{type(exc).__name__}: {exc}")
        raise

    print("\nDebug artifacts saved to:")
    print("  GIF recording: ./logs/agent.gif (if created)")
    print("  LLM conversation dir: ./logs/agent_conversations/ (if created)")


if __name__ == "__main__":
    asyncio.run(main())
