import os
from browser_use import Agent
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr
from models import EBDealResult, EBTrackingResult
from utils import logger, get_env
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

class ElectronicsBuyerAgent:
    def __init__(self):
        base_llm = ChatAnthropic(
            model_name='claude-3-5-sonnet-20241022',
            api_key=SecretStr(get_env('ANTHROPIC_API_KEY')),
            temperature=0.0,
            timeout=30,
            stop=None
        )
        self.llm = AnthropicWrapper(base_llm)
        self.username = get_env('EB_USERNAME')
        self.password = get_env('EB_PASSWORD')

    async def submit_deal(self, items: list, quantities: dict) -> EBDealResult:
        """
        Navigate to electronicsbuyer.gg deals page and submit deal

        Args:
            items: List of product names from Amazon order
            quantities: Dict mapping product names to quantities ordered
        """
        logger.info(f"Submitting deal for items: {items}")

        # Create task for the agent
        items_str = ", ".join([f"{q}x {name}" for name, q in quantities.items()])

        task = f"""
        1. Navigate directly to: https://electronicsbuyer.gg/app/deals
        2. On the deals page, search or scroll to find deals for: {items_str}
        3. For each matching product:
           - Click the "Commit" or "Submit Deal" button on the deal card
           - Enter the quantity you're committing: {quantities}
           - Submit the commitment
           - Note the payout value per unit (shown on the deal card)
        4. Calculate total cashout: sum of (payout_per_unit × quantity) for all items
        5. Return the deal confirmation and total payout value
        """

        # Load browser profile with saved session and randomized human-like timing
        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision='auto',
            max_actions_per_step=4,
            browser_profile=browser_profile,
            output_model_schema=EBDealResult,
            generate_gif='./logs/eb_agent.gif',
            save_conversation_path="./logs/eb_agent_conversation.json",
            max_failures=5,
        )

        try:
            result = await agent.run()
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Deal submission agent returned no structured output. final_result={result.final_result()!r}")
            return structured
        finally:
            if agent.browser:
                await agent.browser.close()

    async def submit_tracking(self, tracking_number: str, items: list) -> EBTrackingResult:
        """
        Navigate to electronicsbuyer.gg tracking submission page

        Args:
            tracking_number: Tracking number from Amazon
            items: List of items with quantities (natural language)
        """
        logger.info(f"Submitting tracking: {tracking_number}")

        items_str = ", ".join([f"{item['quantity']}x {item['name']}" for item in items])

        task = f"""
        1. Navigate directly to: https://electronicsbuyer.gg/app/tracking-submissions
        2. On the tracking submission page, fill in the form:
           - Tracking number field: {tracking_number}
           - Package contents field: {items_str}
           - Leave insurance field blank (or unchecked)
        3. Click the "Submit" or "Add Tracking" button
        4. Wait for confirmation message
        5. Return success confirmation
        """

        # Load browser profile with saved session and randomized human-like timing
        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)

        agent = Agent(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision='auto',
            browser_profile=browser_profile,
            output_model_schema=EBTrackingResult,
            generate_gif='./logs/eb_agent.gif',
            save_conversation_path="./logs/eb_agent_conversation.json",
            max_failures=5,
        )

        try:
            result = await agent.run()
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Tracking submission agent returned no structured output. final_result={result.final_result()!r}")
            return structured
        finally:
            if agent.browser:
                await agent.browser.close()
