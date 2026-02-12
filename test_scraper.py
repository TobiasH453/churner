"""
Test script: verify amazon_scraper.py works after Phase 1 fixes.
Usage: venv/bin/python3 test_scraper.py [ORDER_NUMBER]
Example: venv/bin/python3 test_scraper.py 123-4567890-1234567
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
    if len(sys.argv) > 1:
        order_number = sys.argv[1]
    else:
        order_number = input("Enter Amazon order number (e.g. 123-4567890-1234567): ").strip()

    if not order_number:
        print("Error: order number required")
        sys.exit(1)

    print(f"\nTesting AmazonScraper with order: {order_number}")
    print("Browser will open - watch for navigation to Amazon invoice page...")
    print("Press Ctrl+C to abort at any time.\n")

    scraper = AmazonScraper()

    try:
        result = await scraper.scrape_order_confirmation(order_number)
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
