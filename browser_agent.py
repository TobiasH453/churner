import asyncio
import time
from typing import Any
from models import EmailData, AgentResponse, OrderDetails, ShippingDetails
from amazon_scraper import AmazonScraper
from electronics_buyer import ElectronicsBuyerAgent
from utils import logger

class BrowserAgent:
    def __init__(self):
        self.amazon_scraper = AmazonScraper()
        self.eb_agent = ElectronicsBuyerAgent()

    @staticmethod
    def _contains_placeholder(value: Any) -> bool:
        """Detect known placeholder artifacts that should never pass as success."""
        if isinstance(value, str):
            normalized = value.strip().upper()
            return normalized in {"NEEDS_PARSING", "TBD", "YOUR_USERNAME_HERE", "YOUR_PASSWORD_HERE"}

        if isinstance(value, dict):
            return any(BrowserAgent._contains_placeholder(v) for v in value.values())

        if isinstance(value, list):
            return any(BrowserAgent._contains_placeholder(v) for v in value)

        return False

    def _assert_no_placeholder_payload(self, amazon_data: Any, eb_result: Any) -> None:
        amazon_payload = amazon_data.model_dump() if hasattr(amazon_data, "model_dump") else amazon_data
        eb_payload = eb_result.model_dump() if hasattr(eb_result, "model_dump") else eb_result

        if self._contains_placeholder(amazon_payload):
            raise RuntimeError(f"Amazon payload contains placeholder values: {amazon_payload!r}")

        if self._contains_placeholder(eb_payload):
            raise RuntimeError(f"ElectronicsBuyer payload contains placeholder values: {eb_payload!r}")

    async def process_email(self, email_data: EmailData) -> AgentResponse:
        """
        Main orchestration function
        Receives email data from n8n, performs browser automation, returns results
        """
        start_time = time.time()
        errors = []

        try:
            logger.info(f"Processing {email_data.email_type} for order: {email_data.order_number}")

            # Route based on email type
            if email_data.email_type == "order_confirmation":
                amazon_data, eb_result = await self._process_order_confirmation(email_data)
            elif email_data.email_type == "shipping_confirmation":
                amazon_data, eb_result = await self._process_shipping_confirmation(email_data)
            else:
                raise ValueError(f"Unknown email type: {email_data.email_type}")

            # Never return success=true when placeholder artifacts leak through.
            self._assert_no_placeholder_payload(amazon_data, eb_result)

            execution_time = time.time() - start_time

            return AgentResponse(
                success=True,
                order_number=email_data.order_number,
                email_type=email_data.email_type,
                amazon_data=amazon_data,
                eb_result=eb_result,
                errors=errors,
                execution_time_seconds=round(execution_time, 2)
            )

        except Exception as e:
            logger.error(f"Error processing email: {str(e)}", exc_info=True)
            execution_time = time.time() - start_time

            return AgentResponse(
                success=False,
                order_number=email_data.order_number,
                email_type=email_data.email_type,
                amazon_data=None,
                eb_result=None,
                errors=[str(e)],
                execution_time_seconds=round(execution_time, 2)
            )

    async def _process_order_confirmation(self, email_data: EmailData):
        """Handle order confirmation emails"""

        # Step 1: Scrape Amazon invoice page
        logger.info("Step 1: Scraping Amazon invoice...")
        amazon_data = await self.amazon_scraper.scrape_order_confirmation(
            email_data.order_number
        )

        # Step 2: Submit deal to electronicsbuyer.gg
        logger.info("Step 2: Submitting deal to ElectronicsBuyer...")

        # Convert items to quantities dict
        quantities = {item['name']: item['quantity'] for item in amazon_data.items}

        eb_result = await self.eb_agent.submit_deal(
            items=[item['name'] for item in amazon_data.items],
            quantities=quantities
        )

        return amazon_data, eb_result

    async def _process_shipping_confirmation(self, email_data: EmailData):
        """Handle shipping confirmation emails"""

        # Step 1: Scrape Amazon tracking page
        logger.info("Step 1: Scraping Amazon tracking...")
        amazon_data = await self.amazon_scraper.scrape_shipping_confirmation(
            email_data.order_number
        )

        # Step 2: Submit tracking to electronicsbuyer.gg
        logger.info("Step 2: Submitting tracking to ElectronicsBuyer...")
        eb_result = await self.eb_agent.submit_tracking(
            tracking_number=amazon_data.tracking_number,
            items=amazon_data.items
        )

        return amazon_data, eb_result
