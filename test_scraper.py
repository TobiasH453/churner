"""
Test script: verify amazon_scraper.py works after Phase 1 fixes.
Usage:
  venv/bin/python3 test_scraper.py order 123-4567890-1234567
  venv/bin/python3 test_scraper.py shipping 123-4567890-1234567
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from amazon_scraper import AmazonScraper

async def main():
    # Parse arguments: test_scraper.py [order|shipping] ORDER_NUMBER
    args = sys.argv[1:]

    if len(args) >= 2:
        mode = args[0]
        order_number = args[1]
    elif len(args) == 1:
        mode = "shipping"
        order_number = args[0]
    else:
        mode = input("Test type (order/shipping) [shipping]: ").strip() or "shipping"
        order_number = input("Enter Amazon order number (e.g. 123-4567890-1234567): ").strip()

    if not order_number:
        print("Error: order number required")
        sys.exit(1)

    if mode not in ("order", "shipping"):
        print(f"Error: mode must be 'order' or 'shipping', got '{mode}'")
        sys.exit(1)

    scraper = AmazonScraper()

    if mode == "order":
        print(f"\nTesting scrape_order_confirmation with order: {order_number}")
        print("Browser will open - watch for navigation to Amazon invoice page...")
        func = scraper.scrape_order_confirmation
    else:
        print(f"\nTesting scrape_shipping_confirmation with order: {order_number}")
        print("Browser will open - watch for navigation to Amazon order details page...")
        func = scraper.scrape_shipping_confirmation

    print("Press Ctrl+C to abort at any time.\n")

    try:
        result = await func(order_number)
        print("\n=== SUCCESS: Agent returned structured data ===")
        print(result.model_dump_json(indent=2))
    except RuntimeError as e:
        print(f"\n=== AGENT ERROR (no structured output) ===")
        print(str(e))
        print("\nCheck debug artifacts:")
        print("  GIF: ./logs/agent.gif")
        print("  Conversation: ./logs/agent_conversation.json")
    except Exception as e:
        print(f"\n=== UNEXPECTED ERROR ===")
        print(f"{type(e).__name__}: {e}")
        raise

    print("\nDebug artifacts saved to:")
    print("  GIF recording: ./logs/agent.gif (if created)")
    print("  LLM conversation: ./logs/agent_conversation.json (if created)")

if __name__ == "__main__":
    asyncio.run(main())
