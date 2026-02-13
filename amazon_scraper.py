import asyncio
import os
import time
from browser_use import Agent
from langchain_anthropic import ChatAnthropic
from playwright.async_api import Page, async_playwright
from pydantic import SecretStr
from models import OrderDetails, ShippingDetails
from utils import logger, get_env
from typing import Union
from stealth_utils import (
    STEALTH_BROWSER_ARGS,
    STEALTH_IGNORE_DEFAULT_ARGS,
    create_stealth_profile,
    get_chromium_executable,
)
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

    async def _selector_exists(self, page: Page, selector: str) -> bool:
        return await page.locator(selector).count() > 0

    async def _click_first(self, page: Page, selectors: list[str]) -> bool:
        for selector in selectors:
            if await self._selector_exists(page, selector):
                await page.locator(selector).first.click()
                return True
        return False

    async def _fill_first(self, page: Page, selectors: list[str], value: str) -> bool:
        for selector in selectors:
            if await self._selector_exists(page, selector):
                await page.locator(selector).first.fill(value)
                return True
        return False

    async def _is_sign_in_page(self, page: Page) -> bool:
        if "ap/signin" in page.url:
            return True
        return any(
            [
                await self._selector_exists(page, "#ap_email"),
                await self._selector_exists(page, "input[name='email']"),
                await self._selector_exists(page, "#ap_password"),
                await self._selector_exists(page, "input[name='password']"),
            ]
        )

    async def _is_mfa_page(self, page: Page) -> bool:
        if "ap/mfa" in page.url:
            return True
        return any(
            [
                await self._selector_exists(page, "input[name='otpCode']"),
                await self._selector_exists(page, "input[name='cvf_captcha_input']"),
                await self._selector_exists(page, "#auth-mfa-otpcode"),
            ]
        )

    async def _wait_for_auth_completion(self, page: Page, timeout_seconds: int = 180) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if not await self._is_sign_in_page(page) and not await self._is_mfa_page(page):
                return
            await asyncio.sleep(2)
        raise RuntimeError("Amazon login did not complete within 180 seconds. Still on auth page.")

    async def _prime_amazon_session(self, target_url: str) -> None:
        """
        Deterministic login/session priming before agent run.
        This removes login responsibilities from the LLM agent.
        """
        if not self.amazon_email or not self.amazon_password:
            raise RuntimeError("Missing AMAZON_EMAIL or AMAZON_PASSWORD for session priming.")

        logger.info(f"Priming Amazon session for target URL: {target_url}")
        chromium_path = get_chromium_executable()

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                executable_path=chromium_path,
                args=STEALTH_BROWSER_ARGS,
                ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
            )

            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(target_url, wait_until="domcontentloaded")
                await asyncio.sleep(1)

                if await self._is_sign_in_page(page):
                    logger.info("Amazon sign-in detected. Performing deterministic login sequence...")

                    email_filled = await self._fill_first(
                        page,
                        ["#ap_email", "input[name='email']", "input[type='email']"],
                        self.amazon_email,
                    )
                    if not email_filled:
                        raise RuntimeError("Could not find Amazon email input field.")

                    await self._click_first(page, ["#continue", "input#continue", "input[name='continue']"])
                    await asyncio.sleep(1)

                    password_filled = await self._fill_first(
                        page,
                        ["#ap_password", "input[name='password']", "input[type='password']"],
                        self.amazon_password,
                    )
                    if not password_filled:
                        raise RuntimeError("Could not find Amazon password input field.")

                    await self._click_first(page, ["#signInSubmit", "input#signInSubmit"])

                    if await self._is_mfa_page(page):
                        logger.warning(
                            "Amazon 2FA detected. Complete the challenge in the browser window; "
                            "waiting up to 180 seconds."
                        )

                    await self._wait_for_auth_completion(page, timeout_seconds=180)
                    await page.goto(target_url, wait_until="domcontentloaded")
                    await asyncio.sleep(1)
            finally:
                await context.close()

    async def scrape_order_confirmation(self, order_number: str) -> OrderDetails:
        """
        Navigate to Amazon invoice page and extract order details
        """
        logger.info(f"Scraping order confirmation for: {order_number}")

        invoice_url = f"https://www.amazon.com/gp/css/summary/print.html?ie=UTF8&orderID={order_number}"

        # Ensure login/session is ready before the LLM agent starts extracting.
        await self._prime_amazon_session(invoice_url)

        task = f"""
        IMPORTANT: Session is already authenticated. Do NOT attempt login.
        Look at the screenshot after every action. Do not return data until you can
        actually see order information on the page.

        Step 1: Navigate to {invoice_url}

        Step 2: If sign-in page appears, navigate to {invoice_url} once more.
        If sign-in still appears after retry, stop and do not fabricate data.

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

        # Ensure login/session is ready before the LLM agent starts extracting.
        await self._prime_amazon_session(order_details_url)

        task = f"""
        IMPORTANT: Session is already authenticated. Do NOT attempt login.
        Look at the screenshot after every action. Do not return data until you can
        actually see order/tracking information on the page.

        Step 1: Navigate to {order_details_url}

        Step 2: If sign-in page appears, navigate to {order_details_url} once more.
        If sign-in still appears after retry, stop and do not fabricate data.

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
