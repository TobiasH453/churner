import asyncio
import json
import os
import re
import time
from typing import Any
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from playwright.async_api import Page, async_playwright
from models import OrderDetails, ShippingDetails
from utils import logger, get_env
from typing import Union
from pydantic import ValidationError
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

# Paths to persistent browser profile directories
PERSONAL_USER_DATA_DIR = "./data/browser-profile-personal"
BUSINESS_USER_DATA_DIR = "./data/browser-profile-business"

class AmazonScraper:
    KNOWN_ORDER_QUANTITY_SELECTORS = [
        "#orderDetails > div > div.a-cardui > div > div:nth-child(1) > div:nth-child(7) > div > div > div > div > div > div > div > div > div:nth-child(2) > div > div > div > div:nth-child(1) > div > div > div > div",
        "#orderDetails [aria-label*='quantity' i]",
        "#orderDetails select[name*='quantity' i]",
        "#orderDetails input[name*='quantity' i]",
    ]
    ORDER_DETAILS_ITEM_TITLE_SELECTOR_TEMPLATES = [
        "#orderDetails > div > div.a-cardui > div > div:nth-child(1) > div:nth-child(8) > div > div > div > div > div > div > div:nth-child(1) > div > div:nth-child({row}) > div > div > div > div:nth-child(2) > div > div:nth-child(1)",
        "#orderDetails > div > div.a-cardui > div > div:nth-child(1) > div:nth-child(7) > div > div > div > div > div > div > div > div > div:nth-child(2) > div > div:nth-child({row}) > div > div:nth-child(2) > div > div:nth-child(1)",
    ]
    ORDER_DETAILS_ITEM_QUANTITY_SELECTOR_TEMPLATES = [
        "#orderDetails > div > div.a-cardui > div > div:nth-child(1) > div:nth-child(7) > div > div > div > div > div > div > div > div > div:nth-child(2) > div > div:nth-child({row}) > div > div:nth-child(1) > div > div > div > div",
    ]
    ORDER_DETAILS_ROW_LOCAL_QUANTITY_SELECTORS = [
        ".od-item-view-qty span",
        ".od-item-view-qty",
    ]
    ORDER_DETAILS_ITEM_BLOCKED_TERMS = (
        "buy it again",
        "recommended",
        "sponsored",
        "customers also",
        "inspired by",
        "related to",
        "browsing history",
        "view history",
        "your recommendations",
        "search",
        "typical:",
        "/count",
    )

    def __init__(self, account_type: str = "amz_personal"):
        ensure_browser_runtime_compatibility()
        normalized_account_type = str(account_type or "amz_personal").strip().lower()
        if normalized_account_type not in {"amz_personal", "amz_business"}:
            normalized_account_type = "amz_personal"
        self.account_type = normalized_account_type
        self.account_label = "business" if self.account_type == "amz_business" else "personal"

        if self.account_type == "amz_business":
            self.user_data_dir = BUSINESS_USER_DATA_DIR
            email_env = "AMAZON_BUSINESS_EMAIL"
            password_env = "AMAZON_BUSINESS_PASSWORD"
            totp_env = "AMAZON_BUSINESS_TOTP_SECRET"
        else:
            self.user_data_dir = PERSONAL_USER_DATA_DIR
            email_env = "AMAZON_EMAIL"
            password_env = "AMAZON_PASSWORD"
            totp_env = "AMAZON_TOTP_SECRET"

        # Use browser-use native ChatAnthropic implementation for structured output compatibility.
        self.llm = ChatAnthropic(
            model='claude-sonnet-4-5-20250929',
            api_key=get_env('ANTHROPIC_API_KEY'),
            temperature=0.0,
            timeout=60,
            max_retries=10,
        )
        self.amazon_email = get_env(email_env, '')
        self.amazon_password = get_env(password_env, '')
        self.amazon_totp_secret = get_env(totp_env, '').replace(' ', '')

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

    async def _wait_for_any_selector(self, page: Page, selectors: list[str], timeout_seconds: int = 20) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            for selector in selectors:
                if await self._selector_exists(page, selector):
                    return True
            await asyncio.sleep(0.5)
        return False

    async def _dismiss_passkey_prompt(self, page: Page) -> bool:
        """
        Try common passkey-interstitial escapes so password auth can continue.
        """
        clicked = await self._click_first(
            page,
            [
                "button:has-text('Not now')",
                "button:has-text('Cancel')",
                "a:has-text('Use your password')",
                "button:has-text('Use password')",
                "a:has-text('Sign in with your password')",
                "button:has-text('Use password instead')",
                "button:has-text('Try another way')",
                "a:has-text('Try another way')",
                "button:has-text('Use a one-time code')",
            ],
        )
        if clicked:
            await asyncio.sleep(1)
            return True

        try:
            await page.keyboard.press("Escape")
            await asyncio.sleep(1)
            return True
        except Exception:
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

    async def _try_totp_if_available(self, page: Page) -> bool:
        """
        If AMAZON_TOTP_SECRET is configured and we're on an MFA page,
        generate a TOTP and try submitting it automatically.
        """
        if not self.amazon_totp_secret:
            return False

        try:
            import pyotp
        except Exception as exc:
            logger.warning("pyotp not available for automatic 2FA: %s", exc)
            return False

        code = pyotp.TOTP(self.amazon_totp_secret).now()
        filled = await self._fill_first(
            page,
            [
                "input[name='otpCode']",
                "#auth-mfa-otpcode",
                "input[name='cvf_captcha_input']",
                "input[name='code']",
                "#cvf-input-code",
                "input[name='auth-mfa-otpcode']",
                "input#input-box-otp",
            ],
            code,
        )
        if not filled:
            logger.warning("2FA page detected but OTP input field was not found.")
            return False

        submitted = await self._click_first(
            page,
            [
                "input#auth-signin-button",
                "input[name='rememberDevice'] + span input",
                "#cvf-submit-otp-button input",
                "input[name='cvf-submit-otp-button']",
                "input[type='submit']",
            ],
        )
        if not submitted:
            # Fallback: hit Enter in the OTP input.
            locator = page.locator(
                "input[name='otpCode'], #auth-mfa-otpcode, input[name='cvf_captcha_input'], "
                "input[name='code'], #cvf-input-code, input[name='auth-mfa-otpcode'], input#input-box-otp"
            ).first
            await locator.press("Enter")

        logger.info("Submitted TOTP code automatically.")
        await asyncio.sleep(2)
        return True

    async def _wait_for_auth_completion(self, page: Page, timeout_seconds: int = 180) -> None:
        deadline = time.time() + timeout_seconds
        last_totp_attempt = 0.0
        while time.time() < deadline:
            if not await self._is_sign_in_page(page) and not await self._is_mfa_page(page):
                return

            if await self._is_mfa_page(page):
                now = time.time()
                if now - last_totp_attempt >= 5:
                    if await self._try_totp_if_available(page):
                        last_totp_attempt = now
                        continue

            await asyncio.sleep(2)
        raise RuntimeError("Amazon login did not complete within 180 seconds. Still on auth page.")

    async def _perform_sign_in_if_needed(self, page: Page, target_url: str) -> None:
        """
        Deterministic sign-in flow that can run in any active context/page.
        """
        if not await self._is_sign_in_page(page):
            return

        logger.info("Amazon sign-in detected. Performing deterministic login sequence...")

        # Prefer password flow over passkey interstitials if present.
        await self._dismiss_passkey_prompt(page)

        if await self._selector_exists(page, "#ap_email") or await self._selector_exists(page, "input[name='email']") or await self._selector_exists(page, "input[type='email']"):
            email_filled = await self._fill_first(
                page,
                ["#ap_email", "input[name='email']", "input[type='email']"],
                self.amazon_email,
            )
            if not email_filled:
                raise RuntimeError("Could not find Amazon email input field.")

        if not await self._wait_for_any_selector(page, ["#ap_password", "input[name='password']", "input[type='password']"], timeout_seconds=4):
            await self._click_first(page, ["#continue", "input#continue", "input[name='continue']"])
            await asyncio.sleep(1)

        if not await self._wait_for_any_selector(page, ["#ap_password", "input[name='password']", "input[type='password']"], timeout_seconds=10):
            await self._dismiss_passkey_prompt(page)
            await self._wait_for_any_selector(page, ["#ap_password", "input[name='password']", "input[type='password']"], timeout_seconds=10)

        password_filled = await self._fill_first(
            page,
            ["#ap_password", "input[name='password']", "input[type='password']"],
            self.amazon_password,
        )
        if not password_filled:
            current_url = page.url
            raise RuntimeError(f"Could not find Amazon password input field. Current URL: {current_url}")

        await self._click_first(page, ["#signInSubmit", "input#signInSubmit"])

        if await self._is_mfa_page(page):
            if self.amazon_totp_secret:
                logger.warning("Amazon 2FA detected. TOTP secret is configured; trying automatic code entry.")
            else:
                logger.warning(
                    "Amazon 2FA detected. Complete the challenge in the browser window; "
                    "waiting up to 180 seconds."
                )

        await self._wait_for_auth_completion(page, timeout_seconds=180)
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(1)

    async def _prime_amazon_session(self, target_url: str) -> None:
        """
        Deterministic login/session priming before agent run.
        This removes login responsibilities from the LLM agent.
        """
        if not self.amazon_email or not self.amazon_password:
            if self.account_type == "amz_business":
                raise RuntimeError(
                    "Missing AMAZON_BUSINESS_EMAIL or AMAZON_BUSINESS_PASSWORD for business session priming."
                )
            raise RuntimeError("Missing AMAZON_EMAIL or AMAZON_PASSWORD for personal session priming.")

        logger.info(f"Priming Amazon session for target URL: {target_url}")
        chromium_path = get_chromium_executable()

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                executable_path=chromium_path,
                args=STEALTH_BROWSER_ARGS,
                ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
            )

            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(target_url, wait_until="domcontentloaded")
                await asyncio.sleep(1)
                await self._perform_sign_in_if_needed(page, target_url)
            finally:
                await context.close()

    @staticmethod
    def _extract_first_json_object(text: str) -> str | None:
        """
        Extract the first balanced JSON object from a mixed string.
        """
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

    @staticmethod
    def _clean_json_candidate(raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            # Remove optional leading 'json' label after fences.
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        return cleaned

    def _recover_structured_output(self, raw_output: Any, model_cls: type[OrderDetails] | type[ShippingDetails]) -> OrderDetails | ShippingDetails | None:
        """
        Recover structured output when model returns JSON plus trailing text.
        """
        if raw_output is None:
            return None

        if isinstance(raw_output, dict):
            return model_cls.model_validate(raw_output)

        if not isinstance(raw_output, str):
            return None

        candidate = self._clean_json_candidate(raw_output)

        # First try direct JSON parse.
        try:
            return model_cls.model_validate_json(candidate)
        except Exception:
            pass

        # Fallback: extract the first balanced JSON object.
        obj_text = self._extract_first_json_object(candidate)
        if not obj_text:
            return None

        try:
            parsed = json.loads(obj_text)
            return model_cls.model_validate(parsed)
        except Exception:
            return None

    def _get_validated_structured_output(
        self,
        result: Any,
        model_cls: type[OrderDetails] | type[ShippingDetails],
        context_label: str,
    ) -> OrderDetails | ShippingDetails:
        """
        Get validated structured output with recovery from common JSON formatting drift.
        """
        try:
            structured = result.structured_output
        except ValidationError as exc:
            logger.warning(
                "Structured output validation failed for %s; attempting recovery from final_result. Error: %s",
                context_label,
                exc,
            )
            recovered = self._recover_structured_output(result.final_result(), model_cls)
            if recovered is not None:
                logger.info("Recovered structured output for %s from raw final_result JSON.", context_label)
                return recovered
            raise RuntimeError(
                f"Structured output validation failed for {context_label}: {exc}. "
                f"final_result={result.final_result()!r}"
            ) from exc

        if structured is None:
            recovered = self._recover_structured_output(result.final_result(), model_cls)
            if recovered is not None:
                logger.info("Recovered missing structured output for %s from raw final_result JSON.", context_label)
                return recovered
            raise RuntimeError(f"Agent returned no structured output for {context_label}. final_result={result.final_result()!r}")

        return structured

    @staticmethod
    def _looks_like_placeholder_shipping(data: ShippingDetails) -> bool:
        joined = " ".join(
            [
                str(data.tracking_number or ""),
                str(data.carrier or ""),
                str(data.delivery_date or ""),
            ]
        ).lower()
        return (
            "unable to retrieve" in joined
            or "authentication required" in joined
            or "not available" in joined
        )

    @staticmethod
    def _guess_carrier(text: str, tracking_number: str) -> str:
        lower = text.lower()
        if "amazon logistics" in lower or tracking_number.upper().startswith("TBA"):
            return "Amazon Logistics"
        if "ups" in lower or tracking_number.upper().startswith("1Z"):
            return "UPS"
        if "usps" in lower:
            return "USPS"
        if "fedex" in lower:
            return "FedEx"
        if "dhl" in lower:
            return "DHL"
        if "ontrac" in lower:
            return "OnTrac"
        return "Unknown"

    @staticmethod
    def _extract_tba_tracking_number(text: str) -> str | None:
        if not text or not isinstance(text, str):
            return None
        match = re.search(r"\bTBA[\s\-]*([0-9A-Z][0-9A-Z\-\s]{6,30})\b", text, flags=re.IGNORECASE)
        if not match:
            return None
        suffix = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
        if len(suffix) < 6:
            return None
        return f"TBA{suffix}"

    @staticmethod
    def _extract_tracking_number(text: str) -> str | None:
        if not text or not isinstance(text, str):
            return None

        def _normalize_candidate(raw: str) -> str | None:
            candidate = re.sub(r"[^A-Z0-9]", "", (raw or "").upper())
            if len(candidate) < 8 or len(candidate) > 34:
                return None
            digit_count = sum(ch.isdigit() for ch in candidate)
            if digit_count < 3:
                return None
            if re.fullmatch(r"(\d)\1{7,}", candidate):
                return None
            return candidate

        patterns = [
            r"\b1Z[0-9A-Z]{16}\b",       # UPS
            r"\bTBA[0-9A-Z\-]{8,}\b",    # Amazon Logistics
            r"\b[A-Z]{2}[0-9]{9}[A-Z]{2}\b",  # USPS international-style
            r"\b9[0-9]{21,23}\b",        # USPS style
            r"\b[0-9]{12,22}\b",         # Generic numeric carriers
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                normalized = _normalize_candidate(match.group(0))
                if normalized:
                    return normalized

        label_patterns = [
            r"(?:tracking(?:\s*(?:number|id|#))?|shipment(?:\s*(?:id|#))?)\s*[:#]?\s*([A-Z0-9][A-Z0-9\-\s]{7,40})",
        ]
        for pattern in label_patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                normalized = _normalize_candidate(match.group(1))
                if normalized:
                    return normalized

        for token in re.findall(r"\b[A-Z0-9][A-Z0-9\-]{7,34}\b", text.upper()):
            normalized = _normalize_candidate(token)
            if normalized:
                return normalized

        return None

    async def _extract_tracking_from_progress_tracker_card(self, page: Page) -> str | None:
        selectors = [
            "#pt-page-container-inner > div.a-row.pt-main-container > div.pt-map-outer-container.pt-map-type-static > div.pt-floating-map-card > section.pt-card.delivery-card > div > div:nth-child(1) > div",
            "#pt-page-container-inner section.pt-card.delivery-card",
            "section.pt-card.delivery-card",
        ]
        for selector in selectors:
            try:
                loc = page.locator(selector)
                count = min(await loc.count(), 8)
                for i in range(count):
                    node = loc.nth(i)
                    if not await node.is_visible():
                        continue
                    text = await node.inner_text()
                    tba = self._extract_tba_tracking_number(text)
                    if tba:
                        return tba
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_delivery_date(text: str) -> str | None:
        patterns = [
            r"(?:Arriving|Delivered|Delivery by|Expected by|Arrives)\s+([A-Za-z]{3,9}\s+\d{1,2}(?:,\s+\d{4})?)",
            r"(?:Arriving|Delivered)\s+([A-Za-z]{3,9}\s+\d{1,2})",
            r"(?:Estimated arrival|Estimated delivery)\s+([A-Za-z]{3,9}\s+\d{1,2}(?:,\s+\d{4})?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _normalize_shipping_delivery_date(raw_date: str | None) -> str | None:
        if not raw_date or not isinstance(raw_date, str):
            return None

        cleaned = re.sub(r"\s+", " ", raw_date).strip(" ,")
        if not cleaned:
            return None

        cleaned = re.sub(
            r"^(?:arriving|arrives|delivery by|expected by|delivered)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip(" ,")
        if not cleaned:
            return None

        month_day_match = re.match(
            (
                r"^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
                r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+"
                r"(\d{1,2})(?:st|nd|rd|th)?(?:,\s*\d{4})?$"
            ),
            cleaned,
            flags=re.IGNORECASE,
        )
        if month_day_match:
            month = month_day_match.group(1).rstrip(".")
            day = int(month_day_match.group(2))
            return f"{month} {day}"

        weekday_with_number_match = re.match(
            (
                r"^(Mon(?:day)?|Tue(?:s(?:day)?)?|Wed(?:nesday)?|Thu(?:r(?:s(?:day)?)?)?|"
                r"Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)(?:,)?\s+\d{1,2}(?:st|nd|rd|th)?"
                r"(?:,\s*\d{4})?$"
            ),
            cleaned,
            flags=re.IGNORECASE,
        )
        if weekday_with_number_match:
            return weekday_with_number_match.group(1)

        return cleaned

    @staticmethod
    def _normalize_money(value: str) -> str:
        cleaned = re.sub(r"\s+", "", value)
        if not cleaned.startswith("$"):
            cleaned = f"${cleaned}"
        return cleaned

    def _extract_order_totals(self, text: str) -> tuple[str, str]:
        collapsed = " ".join(text.split())

        def find_amount(labels_regex: str) -> str | None:
            pattern = rf"(?:{labels_regex})[^$]{{0,60}}(\$\s?\d[\d,]*(?:\.\d{{2}})?)"
            m = re.search(pattern, collapsed, flags=re.IGNORECASE)
            return self._normalize_money(m.group(1)) if m else None

        subtotal = find_amount(r"Item\(s\)\s*Subtotal|Subtotal")
        grand_total = find_amount(r"Grand\s*Total|Order\s*Total|Total")

        all_amounts = [self._normalize_money(v) for v in re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", collapsed)]
        if subtotal is None and all_amounts:
            subtotal = all_amounts[0]
        if grand_total is None and all_amounts:
            grand_total = all_amounts[-1]

        if subtotal is None:
            subtotal = "$0.00"
        if grand_total is None:
            grand_total = subtotal

        return subtotal, grand_total

    @staticmethod
    def _extract_cashback_percent(text: str) -> float:
        collapsed = " ".join(text.split())
        candidates: list[float] = []

        # Handle "Earns 5% back and extra 1% ..." style phrases.
        combined_patterns = [
            r"(?:earns?|get)\s+(\d+(?:\.\d+)?)%\s+back.{0,140}?(?:extra|additional)\s+(\d+(?:\.\d+)?)%",
            r"(?:extra|additional)\s+(\d+(?:\.\d+)?)%.{0,140}?(?:earns?|get)\s+(\d+(?:\.\d+)?)%\s+back",
        ]
        for pattern in combined_patterns:
            for m in re.finditer(pattern, collapsed, flags=re.IGNORECASE):
                try:
                    first = float(m.group(1))
                    second = float(m.group(2))
                    candidates.append(first + second)
                except Exception:
                    pass

        # Handle plain "Earns 5% back" / "Get 5% back".
        for m in re.finditer(r"(?:earns?|get)\s+(\d+(?:\.\d+)?)%\s+back", collapsed, flags=re.IGNORECASE):
            try:
                candidates.append(float(m.group(1)))
            except Exception:
                pass

        # Generic fallback patterns.
        fallback_patterns = [
            r"(\d+(?:\.\d+)?)\s*%\s*(?:cashback|back|reward)",
            r"(?:cashback|reward)[^\d]{0,20}(\d+(?:\.\d+)?)\s*%",
        ]
        for pattern in fallback_patterns:
            for m in re.finditer(pattern, collapsed, flags=re.IGNORECASE):
                try:
                    candidates.append(float(m.group(1)))
                except Exception:
                    pass

        if candidates:
            return max(candidates)

        return 0.0

    @staticmethod
    def _parse_quantity_from_text(text: str) -> int | None:
        source = (text or "").strip()
        if not source:
            return None
        if re.fullmatch(r"\d{1,2}", source):
            qty = int(source)
            if 0 < qty < 100:
                return qty

        patterns = [
            r"(?:qty|quantity)\s*[:x]?\s*(\d{1,2})\b",
            r"\b(\d{1,2})\s*x\b",
            r"\b(\d{1,2})\s+of\b",
            r"\b(\d{1,2})\s+(?:items?|units?)\b",
            r"(?:quantity|qty)\s*of\s*(\d{1,2})\b",
        ]
        matches: list[int] = []
        for pattern in patterns:
            for match in re.finditer(pattern, source, flags=re.IGNORECASE):
                try:
                    qty = int(match.group(1))
                except (TypeError, ValueError):
                    continue
                if 0 < qty < 100:
                    matches.append(qty)
        return max(matches) if matches else None

    async def _extract_quantity_hints(self, page: Page) -> list[int]:
        hints: list[int] = []
        seen: set[int] = set()

        def add_hint(value: int | None) -> None:
            if value is None:
                return
            if value <= 0 or value >= 100:
                return
            if value in seen:
                return
            seen.add(value)
            hints.append(value)

        for selector in self.KNOWN_ORDER_QUANTITY_SELECTORS:
            try:
                loc = page.locator(selector)
                count = await loc.count()
                if count == 0:
                    continue
                for i in range(min(count, 8)):
                    node = loc.nth(i)
                    samples: list[str] = []
                    try:
                        samples.append(" ".join((await node.inner_text()).split()))
                    except Exception:
                        pass
                    try:
                        payload = await node.evaluate(
                            """
                            (el) => {
                              const selected = (el.tagName === 'SELECT' && el.selectedOptions && el.selectedOptions.length)
                                ? Array.from(el.selectedOptions).map((o) => (o.textContent || o.value || '')).join(' ')
                                : '';
                              const value = (typeof el.value === 'string') ? el.value : '';
                              return [
                                selected,
                                value,
                                el.getAttribute('value') || '',
                                el.getAttribute('aria-label') || '',
                                el.getAttribute('title') || '',
                                el.textContent || '',
                                (el.querySelector("select[name*='quantity' i], input[name*='quantity' i], option[selected]") || {}).value || '',
                                (el.querySelector("select[name*='quantity' i], input[name*='quantity' i], option[selected]") || {}).textContent || '',
                              ].join(' ');
                            }
                            """
                        )
                        if isinstance(payload, str):
                            samples.append(payload)
                    except Exception:
                        pass

                    for sample in samples:
                        qty = self._parse_quantity_from_text(sample)
                        add_hint(qty)

            except Exception:
                continue

        # Global quantity hints across the order details module.
        try:
            payload = await page.evaluate(
                """
                () => {
                  const selectors = [
                    "#orderDetails [aria-label*='quantity' i]",
                    "#orderDetails select[name*='quantity' i]",
                    "#orderDetails input[name*='quantity' i]",
                    "#orderDetails option[selected]",
                    "#orderDetails .a-dropdown-prompt",
                  ];
                  const chunks = [];
                  for (const selector of selectors) {
                    document.querySelectorAll(selector).forEach((el) => {
                      chunks.push(
                        [
                          el.value || '',
                          el.getAttribute('value') || '',
                          el.getAttribute('aria-label') || '',
                          el.getAttribute('title') || '',
                          el.textContent || '',
                        ].join(' ')
                      );
                    });
                  }
                  return chunks;
                }
                """
            )
            if isinstance(payload, list):
                for chunk in payload:
                    if isinstance(chunk, str):
                        add_hint(self._parse_quantity_from_text(chunk))
        except Exception:
            pass

        # Textual quantity hints rendered as plain labels (Qty/Quantity) near order rows.
        try:
            payload = await page.evaluate(
                """
                () => {
                  const chunks = [];
                  const nodes = document.querySelectorAll("#orderDetails div, #orderDetails span, #orderDetails li, #orderDetails p");
                  for (const node of nodes) {
                    const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                    if (!text || text.length > 140) continue;
                    const lower = text.toLowerCase();
                    if (
                      lower.includes('qty') ||
                      lower.includes('quantity') ||
                      /\\b\\d{1,2}\\s+of\\b/i.test(text)
                    ) {
                      chunks.push(text);
                    }
                  }
                  return chunks.slice(0, 400);
                }
                """
            )
            if isinstance(payload, list):
                for chunk in payload:
                    if isinstance(chunk, str):
                        add_hint(self._parse_quantity_from_text(chunk))
        except Exception:
            pass

        if hints:
            logger.info("Amazon quantity hints detected: %s", hints)
        return hints

    async def _apply_quantity_hints(self, page: Page, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return items
        if any(int(item.get("quantity", 1)) > 1 for item in items):
            return items

        hints = await self._extract_quantity_hints(page)
        if not hints:
            return items

        normalized_hints = [h for h in hints if h > 1]
        if not normalized_hints:
            return items

        patched = [dict(item) for item in items]
        if len(normalized_hints) == 1:
            for item in patched:
                item["quantity"] = normalized_hints[0]
            return patched

        if len(normalized_hints) >= len(patched):
            for i, item in enumerate(patched):
                item["quantity"] = normalized_hints[i]
            return patched

        if len(set(normalized_hints)) == 1:
            for item in patched:
                item["quantity"] = normalized_hints[0]
            return patched

        # If hints are mixed but we can't map confidently, use strongest repeated hint.
        freq: dict[int, int] = {}
        for hint in normalized_hints:
            freq[hint] = freq.get(hint, 0) + 1
        most_common = sorted(freq.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]
        if most_common > 1:
            for item in patched:
                item["quantity"] = most_common
            return patched

        return patched

    async def _extract_items_from_order_page(self, page: Page, order_number: str) -> list[dict]:
        """
        Strict item extraction from the order details shipment rows only.
        This intentionally avoids global product link scans to prevent recommendation leakage.
        """
        extraction_payload = await page.evaluate(
            """
            (config) => {
              const collapse = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              const cleanTitle = (s) => collapse((s || '')
                .replace(/\\$\\s*\\d+[\\d,]*(?:\\.\\d{2})?/g, ' ')
                .replace(/\\(\\$\\s*\\d+[\\d,]*(?:\\.\\d{2})?(?:\\/count)?\\)/gi, ' ')
                .replace(/\\bQty\\s*:?\\s*\\d+\\b/gi, ' ')
              );
              const blocked = new Set((config.blockedTerms || []).map((v) => String(v).toLowerCase()));

              const isVisible = (el) => {
                if (!el) return false;
                try {
                  if (el.offsetParent !== null) return true;
                  return el.getClientRects().length > 0;
                } catch {
                  return false;
                }
              };

              const firstVisibleBySelectors = (selectors) => {
                for (const selector of selectors) {
                  try {
                    const el = document.querySelector(selector);
                    if (isVisible(el)) return el;
                  } catch {}
                }
                return null;
              };

              const parseQtyFromText = (text) => {
                const source = collapse(text).toLowerCase();
                if (!source) return 1;
                if (/^x?\\s*\\d{1,2}$/.test(source)) {
                  const digits = source.replace(/[^0-9]/g, '');
                  const qty = parseInt(digits, 10);
                  if (Number.isFinite(qty) && qty > 0 && qty < 100) return qty;
                }
                const patterns = [
                  /(?:qty|quantity)\\s*[:x]?\\s*(\\d{1,2})\\b/i,
                  /\\b(\\d{1,2})\\s*x\\b/i,
                  /\\bx\\s*(\\d{1,2})\\b/i,
                  /\\b(\\d{1,2})\\s+of\\b/i,
                  /\\b(\\d{1,2})\\s+(?:items?|units?)\\b/i,
                  /(?:quantity|qty)\\s*of\\s*(\\d{1,2})\\b/i,
                ];
                let best = 1;
                for (const pattern of patterns) {
                  const match = source.match(pattern);
                  if (!match) continue;
                  const qty = parseInt(match[1], 10);
                  if (Number.isFinite(qty) && qty > 0 && qty < 100) best = Math.max(best, qty);
                }
                return best;
              };

              const makeSelectorsForRow = (templates, row) =>
                (templates || []).map((tpl) => String(tpl).replace("{row}", String(row)));

              const findRowLocalQuantity = (titleEl) => {
                const selectors = config.rowLocalQuantitySelectors || [];
                let node = titleEl;
                for (let depth = 0; depth < 8 && node; depth += 1) {
                  try {
                    for (const selector of selectors) {
                      const qtyEl = node.querySelector(selector);
                      if (!isVisible(qtyEl)) continue;
                      const qtyRaw = [
                        qtyEl.textContent || "",
                        qtyEl.getAttribute("aria-label") || "",
                        qtyEl.getAttribute("title") || "",
                        qtyEl.getAttribute("value") || "",
                      ].join(" ");
                      const qty = parseQtyFromText(qtyRaw);
                      if (qty > 1) return qty;
                    }
                  } catch {}
                  node = node.parentElement;
                }
                return null;
              };

              const results = [];
              const seen = new Map();
              let titleHits = 0;
              const maxRows = Number(config.maxRows || 20);

              for (let row = 1; row <= maxRows; row += 1) {
                const titleEl = firstVisibleBySelectors(makeSelectorsForRow(config.titleTemplates, row));
                if (!titleEl) continue;
                titleHits += 1;

                const rawTitle = cleanTitle(titleEl.textContent || '');
                if (!rawTitle || rawTitle.length < 8 || rawTitle.length > 220) continue;
                const lower = rawTitle.toLowerCase();
                if ([...blocked].some((term) => lower.includes(term))) continue;

                let quantity = 1;
                const rowLocalQuantity = findRowLocalQuantity(titleEl);
                if (typeof rowLocalQuantity === "number" && rowLocalQuantity > 0) {
                  quantity = rowLocalQuantity;
                } else {
                  const qtyEl = firstVisibleBySelectors(makeSelectorsForRow(config.quantityTemplates, row));
                  if (qtyEl) {
                    const qtyRaw = [
                      qtyEl.textContent || "",
                      qtyEl.getAttribute("aria-label") || "",
                      qtyEl.getAttribute("title") || "",
                      qtyEl.getAttribute("value") || "",
                    ].join(" ");
                    quantity = Math.max(quantity, parseQtyFromText(qtyRaw));
                  }

                  let parent = titleEl;
                  for (let i = 0; i < 4 && parent; i++) {
                    quantity = Math.max(quantity, parseQtyFromText(parent.textContent || ""));
                    parent = parent.parentElement;
                  }
                }

                const key = rawTitle.toLowerCase();
                if (seen.has(key)) {
                  const idx = seen.get(key);
                  results[idx].quantity = Math.max(results[idx].quantity || 1, quantity);
                  continue;
                }

                seen.set(key, results.length);
                results.push({ name: rawTitle, quantity: Math.max(1, quantity) });
              }

              return {
                mode: "strict-order-details-rows",
                rows_scanned: maxRows,
                title_hits: titleHits,
                items: results.slice(0, 10),
              };
            }
            """,
            {
                "titleTemplates": self.ORDER_DETAILS_ITEM_TITLE_SELECTOR_TEMPLATES,
                "quantityTemplates": self.ORDER_DETAILS_ITEM_QUANTITY_SELECTOR_TEMPLATES,
                "rowLocalQuantitySelectors": self.ORDER_DETAILS_ROW_LOCAL_QUANTITY_SELECTORS,
                "blockedTerms": list(self.ORDER_DETAILS_ITEM_BLOCKED_TERMS),
                "maxRows": 20,
            },
        )

        extracted: list[dict[str, Any]] = []
        mode = "strict-order-details-rows"
        rows_scanned = 0
        title_hits = 0
        if isinstance(extraction_payload, dict):
            mode = str(extraction_payload.get("mode") or "unknown")
            rows_scanned = int(extraction_payload.get("rows_scanned") or 0)
            title_hits = int(extraction_payload.get("title_hits") or 0)
            items = extraction_payload.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).strip()
                    if not name:
                        continue
                    try:
                        quantity = int(item.get("quantity", 1))
                    except (TypeError, ValueError):
                        quantity = 1
                    extracted.append({"name": name, "quantity": max(1, quantity)})
        if extracted:
            logger.info(
                "Amazon item extraction mode=%s accepted=%s rows_scanned=%s title_hits=%s",
                mode,
                len(extracted),
                rows_scanned,
                title_hits,
            )
            return extracted

        logger.warning(
            "Amazon item extraction mode=%s found no strict order-details rows. rows_scanned=%s title_hits=%s",
            mode,
            rows_scanned,
            title_hits,
        )
        return []

    async def _scrape_shipping_fallback(self, order_number: str) -> ShippingDetails:
        """
        Deterministic Playwright fallback when LLM navigation/extraction fails.
        """
        order_details_url = f"https://www.amazon.com/gp/your-account/order-details?orderID={order_number}"
        chromium_path = get_chromium_executable()

        logger.warning("Using deterministic fallback shipping scrape for order %s", order_number)

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                executable_path=chromium_path,
                args=STEALTH_BROWSER_ARGS,
                ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
            )

            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(order_details_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                normalized_order_number = re.sub(r"\D", "", order_number or "")

                def _accept_tracking(candidate: str | None) -> str | None:
                    if not candidate:
                        return None
                    compact = re.sub(r"\D", "", candidate)
                    if normalized_order_number and compact == normalized_order_number:
                        logger.warning(
                            "Discarded tracking candidate because it matched order number. candidate=%s order=%s",
                            candidate,
                            order_number,
                        )
                        return None
                    return candidate

                # Login in this same context if Amazon still prompts for auth.
                await self._perform_sign_in_if_needed(page, order_details_url)
                if await self._is_sign_in_page(page):
                    raise RuntimeError("Fallback scrape still on sign-in page after deterministic login attempt.")

                # Extract items/tracking from order details context before possible page transition.
                order_page_text = await page.locator("body").inner_text()
                items = await self._extract_items_from_order_page(page, order_number)
                tracking_number = _accept_tracking(
                    self._extract_tba_tracking_number(order_page_text)
                    or self._extract_tba_tracking_number(page.url)
                )

                await self._click_first(
                    page,
                    [
                        "a:has-text('Track package')",
                        "button:has-text('Track package')",
                        "a:has-text('Track')",
                    ],
                )
                await asyncio.sleep(2)

                body_text = await page.locator("body").inner_text()
                tracking_number = _accept_tracking(
                    tracking_number
                    or await self._extract_tracking_from_progress_tracker_card(page)
                    or self._extract_tba_tracking_number(body_text)
                    or self._extract_tba_tracking_number(page.url)
                    or self._extract_tracking_number(body_text)
                    or self._extract_tracking_number(page.url)
                )
                delivery_date = self._normalize_shipping_delivery_date(
                    self._extract_delivery_date(body_text) or self._extract_delivery_date(order_page_text)
                )
                carrier = self._guess_carrier(body_text, tracking_number or "")

                if not items:
                    # Retry item extraction after possible page transition.
                    items = await self._extract_items_from_order_page(page, order_number)
                if not items:
                    raise RuntimeError(
                        "Strict item extraction found no order-details rows; refusing broad fallback."
                    )

                # Final recovery: hidden tracking tokens can exist in hrefs/HTML even when not visible in body text.
                if not tracking_number:
                    for _ in range(2):
                        await asyncio.sleep(1)
                        refreshed_text = await page.locator("body").inner_text()
                        tracking_number = _accept_tracking(
                            await self._extract_tracking_from_progress_tracker_card(page)
                            or self._extract_tba_tracking_number(refreshed_text)
                            or self._extract_tba_tracking_number(page.url)
                            or self._extract_tracking_number(refreshed_text)
                            or self._extract_tracking_number(page.url)
                        )
                        if tracking_number:
                            body_text = refreshed_text
                            break

                if not tracking_number:
                    try:
                        html_text = await page.content()
                    except Exception:
                        html_text = ""
                    tracking_number = _accept_tracking(
                        self._extract_tba_tracking_number(html_text)
                        or self._extract_tba_tracking_number(body_text)
                        or self._extract_tba_tracking_number(order_page_text)
                        or
                        self._extract_tracking_number(html_text)
                        or self._extract_tracking_number(body_text)
                        or self._extract_tracking_number(order_page_text)
                    )

                if not tracking_number:
                    raise RuntimeError(
                        "Fallback scrape could not find a tracking number after multi-source extraction."
                    )

                return ShippingDetails(
                    tracking_number=tracking_number,
                    carrier=carrier,
                    delivery_date=delivery_date or "Unknown",
                    items=items,
                )
            finally:
                await context.close()

    async def _scrape_order_fallback(self, order_number: str) -> OrderDetails:
        """
        Deterministic Playwright extraction for order confirmation/invoice details.
        """
        if self.account_type == "amz_business":
            invoice_url = (
                "https://www.amazon.com/your-orders/order-details"
                f"?orderID={order_number}&ref=ab_ppx_yo_dt_b_fed_order_details"
            )
            invoice_url_kind = "business-order-details"
        else:
            invoice_url = f"https://www.amazon.com/gp/css/summary/print.html?ie=UTF8&orderID={order_number}"
            invoice_url_kind = "personal-legacy-print"
        chromium_path = get_chromium_executable()

        logger.warning(
            "Using deterministic fallback order scrape for order %s account=%s url_kind=%s url=%s",
            order_number,
            self.account_type,
            invoice_url_kind,
            invoice_url,
        )

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                executable_path=chromium_path,
                args=STEALTH_BROWSER_ARGS,
                ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
            )
            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(invoice_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                await self._perform_sign_in_if_needed(page, invoice_url)
                if await self._is_sign_in_page(page):
                    raise RuntimeError("Order fallback still on sign-in page after deterministic login attempt.")

                body_text = await page.locator("body").inner_text()
                items = await self._extract_items_from_order_page(page, order_number)
                subtotal, grand_total = self._extract_order_totals(body_text)
                cashback_percent = self._extract_cashback_percent(body_text)
                arrival_date = self._extract_delivery_date(body_text) or "Unknown"

                return OrderDetails(
                    items=items,
                    total_before_cashback=subtotal,
                    grand_total=grand_total,
                    cashback_percent=cashback_percent,
                    arrival_date=arrival_date,
                    invoice_url=invoice_url,
                )
            finally:
                await context.close()

    async def scrape_order_confirmation(self, order_number: str) -> OrderDetails:
        """
        Navigate to Amazon invoice page and extract order details
        """
        logger.info(f"Scraping order confirmation for: {order_number}")
        return await self._scrape_order_fallback(order_number)

    async def scrape_shipping_confirmation(self, order_number: str) -> ShippingDetails:
        """
        Navigate to Amazon tracking page and extract shipping details
        """
        logger.info(f"Scraping shipping confirmation for: {order_number}")
        return await self._scrape_shipping_fallback(order_number)
