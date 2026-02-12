import asyncio
import os
from browser_use import Agent
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr
from models import OrderDetails, ShippingDetails
from utils import logger, get_env
from typing import Union
from stealth_utils import create_stealth_profile

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
        # Create ChatAnthropic with wrapper for browser-use compatibility
        base_llm = ChatAnthropic(
            model_name='claude-3-5-sonnet-20241022',
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

        # Direct navigation to invoice - no clicking needed!
        invoice_url = f"https://www.amazon.com/gp/css/summary/print.html?ie=UTF8&orderID={order_number}"

        task = f"""
        Step 1: Navigate directly to {invoice_url}

        Step 2: If you see a login/sign-in page instead of the invoice, log in first:
        - Email: {self.amazon_email}
        - Password: {self.amazon_password}
        - Handle any 2FA/OTP if prompted (wait for user to complete it)
        After logging in, navigate again to {invoice_url}

        Step 3: Extract the following information from the invoice page:
        - Items with quantities (e.g., "iPad 128GB Blue" x2)
        - Subtotal (before cashback/discounts)
        - Grand total (final amount charged)
        - Cashback percentage (usually 5% or 6%, look for rewards/cashback text)
        - Estimated delivery date

        Return the data in structured format.
        """

        # Load browser profile with saved session and randomized human-like timing
        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision='auto',  # Use screenshots to read the page
            max_actions_per_step=5,  # Navigate, possible login, read page
            browser_profile=browser_profile,
            output_model_schema=OrderDetails,
            generate_gif='./logs/agent.gif',
            save_conversation_path="./logs/agent_conversation.json",
            max_failures=5,
            step_timeout=180,
        )

        try:
            result = await agent.run()
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

        # Direct navigation to order details page
        order_details_url = f"https://www.amazon.com/gp/your-account/order-details?orderID={order_number}"

        task = f"""
        Step 1: Navigate directly to {order_details_url}

        Step 2: If you see a login/sign-in page instead of order details, log in first:
        - Email: {self.amazon_email}
        - Password: {self.amazon_password}
        - Handle any 2FA/OTP if prompted (wait for user to complete it)
        After logging in, navigate again to {order_details_url}

        Step 3: On the order details page, find and extract:
        - Tracking number
        - Carrier (UPS, USPS, FedEx, etc.)
        - Delivery/arrival date
        - Items in this shipment with quantities

        Step 4: If there's a "Track package" link, click it to get more tracking details.

        Return the data in structured format.
        """

        # Load browser profile with saved session and randomized human-like timing
        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision='auto',
            max_actions_per_step=5,  # May need to click "Track package" link
            browser_profile=browser_profile,
            output_model_schema=ShippingDetails,
            generate_gif='./logs/agent.gif',
            save_conversation_path="./logs/agent_conversation.json",
            max_failures=5,
            step_timeout=180,
        )

        try:
            result = await agent.run()
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Agent returned no structured output for order {order_number}. final_result={result.final_result()!r}")
            return structured
        finally:
            await agent.close()
