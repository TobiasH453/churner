"""
Diagnostic: just navigate and describe what the agent sees.
No structured output — removes the 'done with data' bias.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from browser_use import Agent
from browser_use.llm import ChatAnthropic
from stealth_utils import create_stealth_profile

os.environ.setdefault('TIMEOUT_BrowserStartEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserLaunchEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserConnectedEvent', '90')

async def main():
    order = sys.argv[1] if len(sys.argv) > 1 else input("Order number: ").strip()
    url = f"https://www.amazon.com/gp/your-account/order-details?orderID={order}"

    llm = ChatAnthropic(
        model='claude-sonnet-4-5-20250929',
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        temperature=0.0,
        timeout=60,
        max_retries=10,
    )

    task = f"""
    Step 1: Navigate to {url}
    Step 2: Look at the page screenshot carefully. Describe EXACTLY what you see:
    - Is this a login/sign-in page?
    - Is this an order details page?
    - What text and elements are visible?
    Step 3: Report what you see as your final answer. Just describe the page contents.
    """

    profile = create_stealth_profile(user_data_dir="./data/browser-profile")

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=True,
        max_actions_per_step=3,
        browser_profile=profile,
        generate_gif='./logs/diagnose.gif',
        max_steps=5,
    )

    try:
        result = await agent.run()
        print("\n=== AGENT RESULT ===")
        print(result.final_result())
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
