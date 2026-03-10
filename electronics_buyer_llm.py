import asyncio
import inspect
import json
import os
import re
from typing import Any
from browser_use import Agent, BrowserSession
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
    DEAL_COLOR_HINTS = ("pink", "blue", "silver", "black", "white", "yellow", "green", "purple", "starlight")
    DEAL_MAX_STEPS = 12
    DEAL_TIMEOUT_SECONDS = 120

    def __init__(self):
        ensure_browser_runtime_compatibility()
        self.llm = ChatAnthropic(
            model='claude-sonnet-4-5-20250929',
            api_key=get_env('ANTHROPIC_API_KEY'),
            temperature=0.0,
            timeout=30,
            max_retries=10,
        )
        self.login_email = get_env("EB_LOGIN_EMAIL", "")
        signature = inspect.signature(Agent.__init__)
        self._agent_init_params = set(signature.parameters.keys())
        self._deal_browser_session: BrowserSession | None = None

    def _supports_agent_param(self, param_name: str) -> bool:
        return param_name in self._agent_init_params

    def supports_browser_context_handoff(self) -> bool:
        return self._supports_agent_param("browser_context")

    @staticmethod
    def _normalize_qty(raw_qty: Any) -> int | None:
        try:
            qty = int(raw_qty)
        except (TypeError, ValueError):
            return None
        if qty <= 0:
            return None
        return qty

    @classmethod
    def _build_item_search_spec(cls, item_name: str, quantity: int) -> dict[str, Any]:
        lower = (item_name or "").lower()

        tokens: list[str] = []
        required_tokens: list[str] = []

        if "ipad" in lower:
            tokens.append("ipad")
            required_tokens.append("ipad")

        if "a16" in lower:
            tokens.append("a16")
            required_tokens.append("a16")

        size_match = re.search(r"\b(\d{1,2})\s*(?:-|\s)?inch\b", lower)
        if size_match:
            tokens.append(size_match.group(1))

        storage_match = re.search(r"\b(\d{2,4})\s?gb\b", lower)
        if storage_match:
            storage_token = f"{storage_match.group(1)}gb"
            tokens.append(storage_token)
            required_tokens.append(storage_token)

        color_token = None
        for color in cls.DEAL_COLOR_HINTS:
            if color in lower:
                color_token = color
                break
        if color_token:
            tokens.append(color_token)
            required_tokens.append(color_token)

        if "wifi" in lower or "wi-fi" in lower:
            tokens.append("wifi")

        year_match = re.search(r"\b(20\d{2})\b", lower)
        if year_match:
            tokens.append(year_match.group(1))

        # Stable fallback so query is never empty.
        if not tokens:
            tokens.extend(part for part in re.findall(r"[a-z0-9]+", lower)[:6] if part)

        deduped_tokens = list(dict.fromkeys(tokens))
        deduped_required = list(dict.fromkeys(required_tokens))
        query = " ".join(deduped_tokens[:7]).strip()
        refine_query_parts = [color_token, storage_match.group(1) + "gb" if storage_match else None, "ipad", "a16"]
        refine_query = " ".join(part for part in refine_query_parts if part).strip() or query

        return {
            "item_name": item_name,
            "quantity": quantity,
            "query": query,
            "refine_query": refine_query,
            "required_tokens": deduped_required,
        }

    @classmethod
    def _build_deal_search_specs(cls, quantities: dict) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for raw_name, raw_qty in (quantities or {}).items():
            if not isinstance(raw_name, str):
                continue
            name = raw_name.strip()
            if not name:
                continue
            qty = cls._normalize_qty(raw_qty)
            if qty is None:
                continue
            specs.append(cls._build_item_search_spec(name, qty))
        return specs

    def _build_agent(
        self,
        *,
        task: str,
        output_model_schema: type[EBDealResult] | type[EBTrackingResult],
        max_steps: int,
        max_actions_per_step: int | None = None,
        browser_context: Any = None,
        browser_session: BrowserSession | None = None,
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
        elif browser_session is not None:
            if not self._supports_agent_param("browser_session"):
                raise RuntimeError(
                    "browser_use Agent does not expose browser_session in this runtime; "
                    "cannot reuse an authenticated keep-alive session."
                )
            agent_kwargs["browser_session"] = browser_session
        else:
            browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR)
            agent_kwargs["browser_profile"] = browser_profile

        return Agent(**agent_kwargs)

    def _get_or_create_deal_browser_session(self) -> BrowserSession:
        if self._deal_browser_session is not None:
            return self._deal_browser_session
        browser_profile = create_stealth_profile(user_data_dir=USER_DATA_DIR).model_copy(update={"keep_alive": True})
        self._deal_browser_session = BrowserSession(browser_profile=browser_profile)
        return self._deal_browser_session

    async def _reset_deal_browser_session(self) -> None:
        if self._deal_browser_session is None:
            return
        try:
            await self._deal_browser_session.kill()
        except Exception:
            logger.exception("Failed to kill stale EB deal browser session.")
        finally:
            self._deal_browser_session = None

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
        logger.info("EB LLM deal browser_session_support=%s", self._supports_agent_param("browser_session"))

        if not self.login_email:
            return EBDealResult(
                success=False,
                deal_id=None,
                payout_value=0.0,
                error_message="Missing EB_LOGIN_EMAIL in .env; configure it before running deal submission.",
            )

        search_specs = self._build_deal_search_specs(quantities)
        if not search_specs:
            return EBDealResult(
                success=False,
                deal_id=None,
                payout_value=0.0,
                error_message="No valid deal search specs could be built from requested quantities.",
            )
        search_specs_json = json.dumps(search_specs, ensure_ascii=True)

        task = f"""
        Execute this in the current browser-use session only.
        Keep the flow constrained and deterministic-like. Do not freestyle.

        1. Start at https://electronicsbuyer.gg/ (homepage).
        2. Click the "Dashboard" button to enter the app session.
           - Immediately click the first visible "Dashboard" / "Access Dashboard" control in the first viewport.
           - Do not pause to inspect cards, metrics, or other page sections before this click.
           - If redirected to login/OTP, fill email with "{self.login_email}", click Continue/Send code, then wait up to 20 seconds for the human to enter OTP and submit.
           - After the wait, continue only if app/dashboard access is visible. If still on login/OTP, STOP and return success=false with the current URL.
        3. Navigate to https://electronicsbuyer.gg/app/deals.
        4. Handle deals-page availability:
           - If you see "Failed to fetch vendor deals" (or similar), click Refresh and retry.
           - Retry at most 2 times total.
           - If still failing after retries, STOP and return success=false with the visible error text.
           - If you see "No deals found" / "No deals are currently available", STOP and return success=false.
        5. SEARCH SPECS (use exactly; do not invent extra products):
           {search_specs_json}
        6. Use each search spec independently:
           - Focus search input, clear existing text, enter spec.query.
           - Wait one step for filtered cards.
           - Choose a card only if visible text/title includes ALL spec.required_tokens (case-insensitive).
           - If no match, run exactly ONE refine attempt using spec.refine_query, then re-check.
           - If still no match, add spec.item_name to unmatched_items and continue to next spec.
        7. For each matched card:
           - Click that card's "Commit" button.
           - Enter spec.quantity.
           - Submit the commitment.
           - Record payout per unit and include item in payout_captured_items only if payout is visibly confirmed.
           - Include item in submitted_items only if commitment submit is visibly confirmed.
        8. Calculate total cashout: sum of (payout_per_unit × quantity) for committed items only.
        9. Wait briefly for result.
           - If you see any error/failed message, STOP immediately and return success=false with the error text.
        10. Success semantics:
            - success=true if at least one item is in submitted_items and payout is captured for submitted items.
            - success=false if zero items are committed.
            - If any requested items are unmatched, include them and add FLAG_UNMATCHED_ITEMS in warnings.
        11. Your structured output must include strict accounting fields:
            - submitted_items: item names that were actually committed/submitted
            - payout_captured_items: item names with confirmed payout values
            - unmatched_items: requested items you could not match/submit
            - warnings: include FLAG_UNMATCHED_ITEMS when unmatched_items is non-empty
        """

        deal_session_retry = 2 if browser_context is None else 1
        for attempt in range(1, deal_session_retry + 1):
            deal_browser_session = None
            if browser_context is None:
                deal_browser_session = self._get_or_create_deal_browser_session()

            try:
                agent = self._build_agent(
                    task=task,
                    output_model_schema=EBDealResult,
                    max_steps=self.DEAL_MAX_STEPS,
                    max_actions_per_step=4,
                    browser_context=browser_context,
                    browser_session=deal_browser_session,
                )
            except Exception as exc:
                logger.exception("EB deal agent initialization failed.")
                if attempt < deal_session_retry:
                    await self._reset_deal_browser_session()
                    continue
                return EBDealResult(
                    success=False,
                    deal_id=None,
                    payout_value=0.0,
                    error_message=f"Deal agent initialization failed: {exc}",
                )

            try:
                try:
                    result = await asyncio.wait_for(agent.run(), timeout=self.DEAL_TIMEOUT_SECONDS)
                except asyncio.TimeoutError:
                    return EBDealResult(
                        success=False,
                        deal_id=None,
                        payout_value=0.0,
                        error_message=f"EB deal submission timed out after {self.DEAL_TIMEOUT_SECONDS}s",
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
            except Exception as exc:
                if attempt < deal_session_retry:
                    logger.exception("EB deal agent run failed; resetting browser session for one retry.")
                    await self._reset_deal_browser_session()
                    continue
                logger.exception("EB deal agent run failed on final attempt.")
                return EBDealResult(
                    success=False,
                    deal_id=None,
                    payout_value=0.0,
                    error_message=f"Deal agent execution failed: {exc}",
                )
            finally:
                await agent.close()

        return EBDealResult(
            success=False,
            deal_id=None,
            payout_value=0.0,
            error_message="Deal submission failed before execution could complete.",
        )

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

        try:
            agent = self._build_agent(
                task=task,
                output_model_schema=EBTrackingResult,
                max_steps=12,
                browser_context=browser_context,
            )
        except Exception as exc:
            logger.exception("EB tracking agent initialization failed.")
            return EBTrackingResult(
                success=False,
                tracking_id=None,
                error_message=f"Tracking agent initialization failed: {exc}",
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
