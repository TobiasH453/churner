"""
Debug test: run with full DEBUG logging to trace the 'items' error.
"""
import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

# Enable DEBUG logging BEFORE importing browser_use
logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s %(message)s')

from browser_use import Agent
from browser_use.llm import ChatAnthropic
from stealth_utils import create_stealth_profile

os.environ.setdefault('TIMEOUT_BrowserStartEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserLaunchEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserConnectedEvent', '90')

async def main():
    order = sys.argv[1] if len(sys.argv) > 1 else "114-7189993-5200247"
    url = f"https://www.amazon.com/gp/your-account/order-details?orderID={order}"

    llm = ChatAnthropic(
        model='claude-sonnet-4-5-20250929',
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        temperature=0.0,
        timeout=60,
        max_retries=10,
    )

    task = f"""
    Navigate to {url} and describe what you see on the page.
    """

    profile = create_stealth_profile(user_data_dir="./data/browser-profile")

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=True,
        max_actions_per_step=3,
        browser_profile=profile,
        max_failures=2,
        max_steps=3,
    )

    try:
        result = await agent.run()
        print("\n=== RESULT ===")
        print(result.final_result())
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"{type(e).__name__}: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
