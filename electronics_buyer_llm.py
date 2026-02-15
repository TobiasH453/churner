import asyncio
import inspect
import json
import os
from typing import Any
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from models import EBDealResult, EBTrackingResult
from eb_contracts import enforce_deal_contract
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

class ElectronicsBuyerLLMExecutor:
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
        signature = inspect.signature(Agent.__init__)
        self._agent_init_params = set(signature.parameters.keys())

    def _supports_agent_param(self, param_name: str) -> bool:
        return param_name in self._agent_init_params

    def supports_browser_context_handoff(self) -> bool:
        return self._supports_agent_param("browser_context")

    def _build_agent(
        self,
        *,
        task: str,
        output_model_schema: type[EBDealResult] | type[EBTrackingResult],
        max_steps: int,
        max_actions_per_step: int | None = None,
        browser_context: Any = None,
    ) -> Agent:
        agent_kwargs: dict[str, Any] = dict(
            task=task,
            llm=self.llm,  # type: ignore[arg-type]
            use_vision='auto',
            output_model_schema=output_model_schema,
            generate_gif='./logs/eb_agent.gif',
            save_conversation_path="./logs/eb_agent_conversations",
            max_failures=1,
            max_steps=max_steps,
            step_timeout=60,
            use_judge=False,
            enable_planning=False,
            final_response_after_failure=False,
        )

        if max_actions_per_step is not None:
            agent_kwargs["max_actions_per_step"] = max_actions_per_step

        if browser_context is not None:
            if not self._supports_agent_param("browser_context"):
                raise RuntimeError(
                    "browser_use Agent does not expose browser_context in this runtime; "
                    "cannot safely run EB LLM in the authenticated browser session."
                )
            agent_kwargs["browser_context"] = browser_context
        else:
            browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)
            agent_kwargs["browser_profile"] = browser_profile

        return Agent(**agent_kwargs)

    async def submit_deal(self, items: list, quantities: dict, browser_context: Any = None) -> EBDealResult:
        """
        Navigate to electronicsbuyer.gg deals page and submit deal

        Args:
            items: List of product names from Amazon order
            quantities: Dict mapping product names to quantities ordered
        """
        logger.info(f"Submitting deal for items: {items}")
        logger.info(
            "EB LLM deal handoff: browser_context_provided=%s supports_browser_context=%s",
            browser_context is not None,
            self.supports_browser_context_handoff(),
        )

        # Create task for the agent
        items_str = ", ".join([f"{q}x {name}" for name, q in quantities.items()])

        task = f"""
        IMPORTANT: Authentication and dashboard navigation are already complete.
        Do NOT attempt login or OTP.

        1. Navigate to https://electronicsbuyer.gg/app/deals if not already on deals.
        2. On the deals page, search or scroll to find deals for: {items_str}
        3. For each matching product:
           - Click the "Commit" or "Submit Deal" button on the deal card
           - Enter the quantity you're committing: {quantities}
           - Submit the commitment
           - Note the payout value per unit (shown on the deal card)
        4. Calculate total cashout: sum of (payout_per_unit × quantity) for all items
        5. Wait briefly for result.
           - If you see any error/failed message, STOP immediately and return success=false with the error text.
           - Do NOT retry submission more than once.
        6. Return success confirmation only if a real success confirmation is visible.
        7. Your structured output must include strict accounting fields:
           - submitted_items: item names that were actually committed/submitted
           - payout_captured_items: item names with confirmed payout values
           - unmatched_items: requested items you could not match/submit
           - warnings: include FLAG_UNMATCHED_ITEMS when unmatched_items is non-empty
        """

        agent = self._build_agent(
            task=task,
            output_model_schema=EBDealResult,
            max_steps=10,
            max_actions_per_step=4,
            browser_context=browser_context,
        )

        try:
            try:
                result = await asyncio.wait_for(agent.run(), timeout=50)
            except asyncio.TimeoutError:
                return EBDealResult(
                    success=False,
                    deal_id=None,
                    payout_value=0.0,
                    error_message="EB deal submission timed out after 50s",
                )

            errors = [err for err in result.errors() if err]
            if errors:
                return EBDealResult(
                    success=False,
                    deal_id=None,
                    payout_value=0.0,
                    error_message=f"Deal agent failed fast: {errors[-1]}",
                )

            try:
                structured = result.structured_output
            except ValidationError:
                structured = None

            if structured is None:
                recovered = self._recover_deal_output(result.final_result())
                if recovered is not None:
                    return enforce_deal_contract(recovered, quantities)
                return EBDealResult(
                    success=False,
                    deal_id=None,
                    payout_value=0.0,
                    error_message=f"Deal submission agent returned no structured output. final_result={result.final_result()!r}",
                )
            return enforce_deal_contract(structured, quantities)
        finally:
            await agent.close()

    async def submit_tracking(self, tracking_number: str, items: list, browser_context: Any = None) -> EBTrackingResult:
        """
        Navigate to electronicsbuyer.gg tracking submission page

        Args:
            tracking_number: Tracking number from Amazon
            items: List of items with quantities (natural language)
        """
        logger.info(f"Submitting tracking: {tracking_number}")
        logger.info(
            "EB LLM tracking handoff: browser_context_provided=%s supports_browser_context=%s",
            browser_context is not None,
            self.supports_browser_context_handoff(),
        )

        items_str = ", ".join([f"{item['quantity']}x {item['name']}" for item in items])

        task = f"""
        IMPORTANT: Authentication and dashboard navigation are already complete.
        Do NOT attempt login or OTP.

        1. Navigate to https://electronicsbuyer.gg/app/tracking-submissions if not already there.
        2. Confirm page is not in a loading-only state before interacting. If it shows "Loading tracking submissions..." wait for controls to appear.
        3. If tracking input fields are not visible yet, click the "Submit Tracking" / "Add Tracking" / "Submit" button to open the tracking form first.
        4. Fill in the tracking form:
           - Tracking number field: {tracking_number}
           - Package contents field: {items_str}
           - Leave insurance field blank (or unchecked)
        5. Click the final form submit button ("Submit", "Add Tracking", or similar confirmation button).
        6. Wait briefly for result.
           - If you see any error/failed message, STOP immediately and return success=false with the error text.
           - Do NOT retry submission more than once.
        7. Return success confirmation only if a real success confirmation is visible.
        """

        agent = self._build_agent(
            task=task,
            output_model_schema=EBTrackingResult,
            max_steps=12,
            browser_context=browser_context,
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

    def _recover_deal_output(self, raw_output) -> EBDealResult | None:
        if raw_output is None:
            return None
        if isinstance(raw_output, dict):
            try:
                return EBDealResult.model_validate(raw_output)
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
            return EBDealResult.model_validate_json(candidate)
        except Exception:
            pass

        obj_text = self._extract_first_json_object(candidate)
        if not obj_text:
            return None
        try:
            return EBDealResult.model_validate(json.loads(obj_text))
        except Exception:
            return None
