import asyncio
import json
import os
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from models import EBDealResult, EBTrackingResult
from utils import logger, get_env
from stealth_utils import create_stealth_profile
from runtime_checks import ensure_browser_runtime_compatibility
from pydantic import ValidationError

os.makedirs("./logs", exist_ok=True)

# Increase browser-use watchdog timeouts (default 30s is too short for initial profile load)
os.environ.setdefault('TIMEOUT_BrowserStartEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserLaunchEvent', '120')
os.environ.setdefault('TIMEOUT_BrowserConnectedEvent', '90')

# Path to persistent browser profile directory
USER_DATA_DIR = "./data/browser-profile"

class ElectronicsBuyerAgent:
    def __init__(self):
        ensure_browser_runtime_compatibility()
        self.llm = ChatAnthropic(
            model='claude-sonnet-4-5-20250929',
            api_key=get_env('ANTHROPIC_API_KEY'),
            temperature=0.0,
            timeout=30,
            max_retries=10,
        )
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
            save_conversation_path="./logs/eb_agent_conversations",
            max_failures=5,
        )

        try:
            result = await agent.run()
            errors = [err for err in result.errors() if err]
            if errors:
                raise RuntimeError(
                    f"Deal agent failed. last_error={errors[-1]!r} "
                    f"final_result={result.final_result()!r}"
                )
            structured = result.structured_output
            if structured is None:
                raise RuntimeError(f"Deal submission agent returned no structured output. final_result={result.final_result()!r}")
            return structured
        finally:
            await agent.close()

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
        4. Wait briefly for result.
           - If you see any error/failed message, STOP immediately and return success=false with the error text.
           - Do NOT retry submission more than once.
        5. Return success confirmation only if a real success confirmation is visible.
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
            save_conversation_path="./logs/eb_agent_conversations",
            max_failures=1,
            max_steps=8,
            step_timeout=60,
            use_judge=False,
            enable_planning=False,
            final_response_after_failure=False,
        )

        try:
            try:
                result = await asyncio.wait_for(agent.run(), timeout=45)
            except asyncio.TimeoutError:
                return EBTrackingResult(
                    success=False,
                    tracking_id=None,
                    error_message="EB tracking submission timed out after 45s",
                )

            errors = [err for err in result.errors() if err]
            if errors:
                return EBTrackingResult(
                    success=False,
                    tracking_id=None,
                    error_message=f"Tracking agent failed fast: {errors[-1]}",
                )

            try:
                structured = result.structured_output
            except ValidationError:
                structured = None

            if structured is None:
                recovered = self._recover_tracking_output(result.final_result())
                if recovered is not None:
                    return recovered
                return EBTrackingResult(
                    success=False,
                    tracking_id=None,
                    error_message=f"Tracking submission agent returned no structured output. final_result={result.final_result()!r}",
                )

            return structured
        finally:
            await agent.close()

    @staticmethod
    def _extract_first_json_object(text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    def _recover_tracking_output(self, raw_output) -> EBTrackingResult | None:
        if raw_output is None:
            return None
        if isinstance(raw_output, dict):
            try:
                return EBTrackingResult.model_validate(raw_output)
            except Exception:
                return None
        if not isinstance(raw_output, str):
            return None

        candidate = raw_output.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()

        try:
            return EBTrackingResult.model_validate_json(candidate)
        except Exception:
            pass

        obj_text = self._extract_first_json_object(candidate)
        if not obj_text:
            return None
        try:
            return EBTrackingResult.model_validate(json.loads(obj_text))
        except Exception:
            return None
