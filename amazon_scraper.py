import asyncio
import os
from browser_use import Agent
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr
from models import OrderDetails, ShippingDetails
from utils import logger, get_env
from typing import Union
from stealth_utils import create_stealth_profile
from runtime_checks import ensure_browser_runtime_compatibility

os.makedirs("./logs", exist_ok=True)

# Increase browser-use watchdog timeouts (default 30s is too short for initial profile load)
os.environ.setdefault('TIMEOUT_BrowserStartEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserLaunchEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserConnectedEvent', '90')

# Path to persistent browser profile directory
USER_DATA_DIR = "./data/browser-profile"

class AnthropicWrapper:
    """Wrapper to add provider attribute for browser-use compatibility"""
    def __init__(self, llm):
        self._llm = llm
        self.provider = 'anthropic'

    def __getattr__(self, name):
        # Map model_name to model for browser-use compatibility
        if name == 'model_name':
            return getattr(self._llm, 'model', None)
        return getattr(self._llm, name)

class AmazonScraper:
    def __init__(self):
        ensure_browser_runtime_compatibility()
        # Create ChatAnthropic with wrapper for browser-use compatibility
        base_llm = ChatAnthropic(
            model_name='claude-sonnet-4-5-20250929',
            api_key=SecretStr(get_env('ANTHROPIC_API_KEY')),
            temperature=0.0,
            timeout=60,
            stop=None
        )
        self.llm = AnthropicWrapper(base_llm)
        self.amazon_email = get_env('AMAZON_EMAIL', '')
        self.amazon_password = get_env('AMAZON_PASSWORD', '')

    async def scrape_order_confirmation(self, order_number: str) -> OrderDetails:
        """
        Navigate to Amazon invoice page and extract order details
        """
        logger.info(f"Scraping order confirmation for: {order_number}")

        invoice_url = f"https://www.amazon.com/gp/css/summary/print.html?ie=UTF8&orderID={order_number}"

        task = f"""
        IMPORTANT: Look at the screenshot of the page after EVERY action. Do NOT try to return data until you can actually see order information on the page.

        Step 1: Navigate to {invoice_url}

        Step 2: Look at the page screenshot. If you see a sign-in/login form:
        a) Click on the email input field
        b) Type: {self.amazon_email}
        c) Click the "Continue" button
        d) Click on the password input field
        e) Type: {self.amazon_password}
        f) Click the "Sign in" button
        g) If you see a 2FA/OTP prompt, wait — the user will complete it manually
        h) After login completes, navigate to {invoice_url}

        Step 3: You should now see the Amazon invoice page with order details. Extract:
        - Items with quantities (e.g., "iPad 128GB Blue" x2)
        - Subtotal (before cashback/discounts)
        - Grand total (final amount charged)
        - Cashback percentage (usually 5% or 6%, look for rewards/cashback text)
        - Estimated delivery date

        Only return structured data AFTER you can see the actual invoice page with items listed.
        """

        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision=True,
            max_actions_per_step=5,
            browser_profile=browser_profile,
            output_model_schema=OrderDetails,
            generate_gif='./logs/agent.gif',
            save_conversation_path="./logs/agent_conversations",
            max_failures=10,
            max_steps=25,
            step_timeout=180,
        )

        try:
            result = await agent.run()
            errors = [err for err in result.errors() if err]
            if errors:
                raise RuntimeError(
                    f"Agent failed during order scrape. last_error={errors[-1]!r} "
                    f"final_result={result.final_result()!r}"
                )
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Agent returned no structured output for order {order_number}. final_result={result.final_result()!r}")
            return structured
        finally:
            await agent.close()

    async def scrape_shipping_confirmation(self, order_number: str) -> ShippingDetails:
        """
        Navigate to Amazon tracking page and extract shipping details
        """
        logger.info(f"Scraping shipping confirmation for: {order_number}")

        order_details_url = f"https://www.amazon.com/gp/your-account/order-details?orderID={order_number}"

        task = f"""
        IMPORTANT: Look at the screenshot of the page after EVERY action. Do NOT try to return data until you can actually see order/tracking information on the page.

        Step 1: Navigate to {order_details_url}

        Step 2: Look at the page screenshot. If you see a sign-in/login form:
        a) Click on the email input field
        b) Type: {self.amazon_email}
        c) Click the "Continue" button
        d) Click on the password input field
        e) Type: {self.amazon_password}
        f) Click the "Sign in" button
        g) If you see a 2FA/OTP prompt, wait — the user will complete it manually
        h) After login completes, navigate to {order_details_url}

        Step 3: You should now see the Amazon order details page. Find and extract:
        - Tracking number
        - Carrier (UPS, USPS, FedEx, Amazon Logistics, etc.)
        - Delivery/arrival date
        - Items in this shipment with quantities

        Step 4: If there's a "Track package" link, click it to get more tracking details.

        Only return structured data AFTER you can see the actual order details page with tracking info.
        """

        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision=True,
            max_actions_per_step=5,
            browser_profile=browser_profile,
            output_model_schema=ShippingDetails,
            generate_gif='./logs/agent.gif',
            save_conversation_path="./logs/agent_conversations",
            max_failures=10,
            max_steps=25,
            step_timeout=180,
        )

        try:
            result = await agent.run()
            errors = [err for err in result.errors() if err]
            if errors:
                raise RuntimeError(
                    f"Agent failed during shipping scrape. last_error={errors[-1]!r} "
                    f"final_result={result.final_result()!r}"
                )
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Agent returned no structured output for order {order_number}. final_result={result.final_result()!r}")
            return structured
        finally:
            await agent.close()
