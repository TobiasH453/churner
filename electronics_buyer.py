import asyncio
import os
import select
import sys
import time
from urllib.parse import urlparse

from playwright.async_api import Locator, Page, async_playwright

from electronics_buyer_llm import ElectronicsBuyerLLMExecutor
from eb_contracts import FLAG_DEAL_TIMEOUT
from models import EBDealResult, EBTrackingResult
from runtime_checks import ensure_browser_runtime_compatibility
from stealth_utils import STEALTH_BROWSER_ARGS, STEALTH_IGNORE_DEFAULT_ARGS, get_chromium_executable
from utils import get_env, logger

os.makedirs("./logs", exist_ok=True)

USER_DATA_DIR = "./data/browser-profile"

EB_HOME_URL = "https://electronicsbuyer.gg"
EB_APP_URL = "https://electronicsbuyer.gg/app"
EB_LOGIN_URL = "https://electronicsbuyer.gg/app/login"
EB_DEALS_URL = "https://electronicsbuyer.gg/app/deals"
EB_TRACKING_URL = "https://electronicsbuyer.gg/app/tracking-submissions"


class ElectronicsBuyerAgent:
    OTP_TIMEOUT_SECONDS = 20
    DASHBOARD_SELECTORS = [
        "body > div.MuiBox-root.mui-zf0iqh > div > header > div > div > div > a.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-colorPrimary.mui-m67vcq",
        "a:has-text('Dashboard')",
        "button:has-text('Dashboard')",
        "text=Dashboard",
    ]
    LOGIN_EMAIL_SELECTORS = [
        "input[id='«rc»']",
        "input[placeholder='you@example.com']",
        "input[type='email']",
        "input[name*='email' i]",
        "input[placeholder*='email' i]",
    ]
    LOGIN_CONTINUE_SELECTORS = [
        "body > div.MuiBox-root.mui-zf0iqh > div > div > main > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation1.mui-tdctb3 > button",
        "button:has-text('Continue')",
        "button:has-text('Next')",
        "button:has-text('Send code')",
        "button:has-text('Email me a code')",
        "button:has-text('Sign in')",
        "input[type='submit']",
    ]
    OTP_INPUT_SELECTORS = [
        "body > div.MuiBox-root.mui-zf0iqh > div > div > main > div > div > div > div.MuiBox-root.mui-lm3loy input",
        "div.MuiBox-root.mui-lm3loy input",
        "input[name*='code' i]",
        "input[inputmode='numeric']",
        "input[autocomplete='one-time-code']",
        "input[type='tel']",
    ]
    OTP_SUBMIT_SELECTORS = [
        "body > div.MuiBox-root.mui-zf0iqh > div > div > main > div > div > div > button",
        "button:has-text('Verify Code')",
        "button:has-text('Verify')",
        "button:has-text('Continue')",
        "button:has-text('Sign in')",
        "button:has-text('Submit')",
        "input[type='submit']",
    ]
    WELCOME_BACK_SELECTORS = [
        "body > div > div > div > main > div > div > div > div.MuiBox-root.mui-1yjvs5a > h1",
        "h1:has-text('Welcome back')",
        "text=Welcome back",
    ]
    TRACKING_FORM_SELECTORS = [
        "input[name*='tracking' i]",
        "input[placeholder*='tracking' i]",
        "textarea[name*='package' i]",
        "textarea[name*='content' i]",
    ]
    TRACKING_LAUNCHER_SELECTORS = [
        "button:has-text('Submit Tracking')",
        "button:has-text('Add Tracking')",
        "a:has-text('Submit Tracking')",
        "a:has-text('Add Tracking')",
        "button:has-text('Submit')",
    ]
    DEALS_READY_SELECTORS = [
        "button:has-text('Commit')",
        "button:has-text('Submit Deal')",
        "input[type='search']",
        "input[name*='search' i]",
    ]
    DEALS_REFRESH_SELECTORS = [
        "button:has-text('Refresh')",
        "button[aria-label='Refresh']",
        "button[title='Refresh']",
    ]
    DEALS_FETCH_ERROR_TEXT_HINTS = (
        "failed to fetch vendor deals",
        "failed to fetch deals",
    )
    DEALS_LOADING_TEXT_HINTS = (
        "loading categories",
        "loading deals",
    )
    DEALS_EMPTY_TEXT_HINTS = (
        "no deals found",
        "no deals are currently available in this category",
    )
    DEALS_STATE_READY = "ready"
    DEALS_STATE_LOADING = "loading"
    DEALS_STATE_FETCH_ERROR = "fetch_error"
    DEALS_STATE_NO_DEALS = "no_deals"
    DEALS_STATE_LOGIN_REDIRECT = "login_redirect"
    DEALS_STATE_WRONG_ROUTE = "wrong_route"
    DEALS_STATE_TEXT_ONLY = "text_only"
    DEALS_STATE_UNKNOWN = "unknown"
    TRACKING_NUMBER_INPUT_SELECTORS = [
        "input[name*='tracking' i]",
        "input[placeholder*='tracking' i]",
        "input[id*='tracking' i]",
        "input[type='text']",
    ]
    TRACKING_CONTENT_INPUT_SELECTORS = [
        "textarea[name*='package' i]",
        "textarea[placeholder*='package' i]",
        "textarea[name*='content' i]",
        "textarea",
    ]
    TRACKING_INSURANCE_SELECTORS = [
        "input[type='checkbox'][name*='insurance' i]",
        "input[type='checkbox'][id*='insurance' i]",
    ]
    TRACKING_FINAL_SUBMIT_SELECTORS = [
        "button:has-text('Submit')",
        "button:has-text('Add Tracking')",
        "button:has-text('Submit Tracking')",
        "input[type='submit']",
    ]
    TRACKING_SUCCESS_TEXT_HINTS = (
        "success",
        "submitted",
        "tracking added",
        "submission received",
    )
    TRACKING_ERROR_TEXT_HINTS = (
        "failed",
        "invalid",
        "error",
        "unable to",
        "something went wrong",
    )
    TRACKING_DUPLICATE_TEXT_HINTS = (
        "already submitted",
        "already exists",
        "duplicate",
        "already added",
        "tracking number already",
        "already in use",
    )
    TRACKING_MODAL_ROOT_SELECTORS = [
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k",
        "div.MuiDialog-root.MuiModal-root",
        "div[role='dialog']",
    ]
    TRACKING_MODAL_NUMBER_SELECTORS = [
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k > div.MuiDialog-container.MuiDialog-scrollPaper.mui-8azq84 > div > div.MuiDialogContent-root.mui-1vjk3m0 > div.MuiBox-root.mui-0 > div.MuiFormControl-root.MuiFormControl-fullWidth.MuiTextField-root.mui-f679ks > div input",
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k textarea[name*='tracking' i]",
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k textarea[placeholder*='tracking' i]",
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k textarea",
        "div.MuiDialogContent-root > div.MuiBox-root.mui-0 div.MuiTextField-root input",
        "div.MuiDialogContent-root textarea[name*='tracking' i]",
        "div.MuiDialogContent-root textarea[placeholder*='tracking' i]",
        "div.MuiDialogContent-root textarea[id]",
        "div.MuiDialogContent-root input[name*='tracking' i]",
        "div.MuiDialogContent-root input[placeholder*='tracking' i]",
        "div[role='dialog'] textarea",
        "div[role='dialog'] input",
    ]
    TRACKING_MODAL_CONTENTS_SELECTORS = [
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k > div.MuiDialog-container.MuiDialog-scrollPaper.mui-8azq84 > div > div.MuiDialogContent-root.mui-1vjk3m0 > div:nth-child(4) > div textarea",
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k > div.MuiDialog-container.MuiDialog-scrollPaper.mui-8azq84 > div > div.MuiDialogContent-root.mui-1vjk3m0 > div:nth-child(4) > div input",
        "div.MuiDialogContent-root > div:nth-child(4) textarea",
        "div.MuiDialogContent-root > div:nth-child(4) input",
        "div.MuiDialogContent-root textarea[name*='package' i]",
        "div.MuiDialogContent-root textarea[name*='content' i]",
    ]
    TRACKING_MODAL_INSURED_SELECTORS = [
        "body > div.MuiDialog-root.MuiModal-root.mui-1egf66k > div.MuiDialog-container.MuiDialog-scrollPaper.mui-8azq84 > div > div.MuiDialogContent-root.mui-1vjk3m0 > div:nth-child(5) > div input",
        "div.MuiDialogContent-root > div:nth-child(5) input",
        "div.MuiDialogContent-root > div:nth-child(5) textarea",
    ]
    TRACKING_MODAL_SUBMIT_SELECTORS = [
        "div.MuiDialogActions-root button:has-text('Submit Tracking')",
        "div.MuiDialogActions-root button:has-text('Add Tracking')",
        "div.MuiDialogActions-root button:has-text('Submit')",
        "div[role='dialog'] button:has-text('Submit Tracking')",
        "div[role='dialog'] button:has-text('Add Tracking')",
        "div[role='dialog'] button:has-text('Submit')",
        "div[role='dialog'] input[type='submit']",
    ]
    TRACKING_SEMANTIC_NUMBER_KEYWORDS = ("tracking", "awb", "shipment", "waybill")
    TRACKING_SEMANTIC_CONTENT_KEYWORDS = ("package", "content", "item", "description")
    FLAG_REQUIRED_FIELD_MISSING = "FLAG_REQUIRED_FIELD_MISSING"
    FLAG_DUPLICATE_TRACKING = "FLAG_DUPLICATE_TRACKING"
    FLAG_TRACKING_SUBMIT_ERROR = "FLAG_TRACKING_SUBMIT_ERROR"
    FLAG_NO_SUCCESS_SIGNAL = "FLAG_NO_SUCCESS_SIGNAL"
    FLAG_DEAL_FETCH_ERROR = "FLAG_DEAL_FETCH_ERROR"
    FLAG_DEAL_NOT_AVAILABLE = "FLAG_DEAL_NOT_AVAILABLE"
    FLAG_DEAL_READINESS_FAILED = "FLAG_DEAL_READINESS_FAILED"

    def __init__(self):
        ensure_browser_runtime_compatibility()
        self.login_email = get_env("EB_LOGIN_EMAIL", "")
        self.llm_executor = ElectronicsBuyerLLMExecutor()

    @staticmethod
    def _flagged_error(flag: str, message: str) -> str:
        return f"{flag}: {message}"

    @staticmethod
    def _extract_flag(error_message: str | None) -> str | None:
        if not error_message or not isinstance(error_message, str):
            return None
        candidate = error_message.split(":", 1)[0].strip()
        if candidate.startswith("FLAG_"):
            return candidate
        return None

    @staticmethod
    def _strip_flag_prefix(error_message: str | None) -> str:
        if not error_message or not isinstance(error_message, str):
            return ""
        if error_message.startswith("FLAG_") and ":" in error_message:
            return error_message.split(":", 1)[1].strip()
        return error_message

    def _result_has_flag(self, result: EBTrackingResult | None, flag: str) -> bool:
        if not result:
            return False
        if flag in (result.warnings or []):
            return True
        return self._extract_flag(result.error_message) == flag

    def _tracking_failure(self, flag: str, message: str) -> EBTrackingResult:
        return EBTrackingResult(
            success=False,
            tracking_id=None,
            error_message=self._flagged_error(flag, message),
            warnings=[flag],
        )

    def _deal_failure(self, flag: str, message: str) -> EBDealResult:
        return EBDealResult(
            success=False,
            deal_id=None,
            payout_value=0.0,
            error_message=self._flagged_error(flag, message),
            warnings=[flag],
        )

    def _classify_tracking_page_failure(self, body: str, page_url: str) -> EBTrackingResult | None:
        lower = (body or "").lower()
        if any(term in lower for term in self.TRACKING_DUPLICATE_TEXT_HINTS):
            return self._tracking_failure(
                self.FLAG_DUPLICATE_TRACKING,
                f"Tracking appears to be already submitted on EB. URL: {page_url}",
            )
        if any(term in lower for term in self.TRACKING_ERROR_TEXT_HINTS):
            return self._tracking_failure(
                self.FLAG_TRACKING_SUBMIT_ERROR,
                f"EB tracking page showed an error state after submit. URL: {page_url}",
            )
        return None

    async def _selector_exists(self, page: Page, selector: str) -> bool:
        return await page.locator(selector).count() > 0

    async def _any_selector_exists(self, page: Page, selectors: list[str]) -> bool:
        for selector in selectors:
            if await self._selector_exists(page, selector):
                return True
        return False

    async def _click_first(self, page: Page, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.click()
                    return True
            except Exception:
                continue
        return False

    async def _fill_first(self, page: Page, selectors: list[str], value: str) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.fill(value)
                    return True
            except Exception:
                continue
        return False

    async def _wait_for_any_selector(self, page: Page, selectors: list[str], timeout_seconds: int) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            for selector in selectors:
                if await self._selector_exists(page, selector):
                    return True
            await asyncio.sleep(0.25)
        return False

    async def _safe_page_text(self, page: Page) -> str:
        try:
            return await page.locator("body").inner_text()
        except Exception:
            return ""

    @staticmethod
    def _path(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return path or "/"

    def _is_tracking_route(self, url: str) -> bool:
        return self._path(url).startswith("/app/tracking-submissions")

    def _is_deals_route(self, url: str) -> bool:
        return self._path(url).startswith("/app/deals")

    @classmethod
    def _classify_deals_snapshot(
        cls,
        *,
        current_url: str,
        body_text: str,
        has_ready_controls: bool,
    ) -> tuple[str, str]:
        current_path = cls._path(current_url)
        lower = (body_text or "").lower()

        if current_path == "/app/login":
            return cls.DEALS_STATE_LOGIN_REDIRECT, f"Deals page redirected to login: {current_url}"

        if not current_path.startswith("/app/deals"):
            if current_path.startswith("/app/"):
                return cls.DEALS_STATE_WRONG_ROUTE, f"Unexpected app route while waiting for deals page: {current_url}"
            return cls.DEALS_STATE_WRONG_ROUTE, f"Unexpected route while waiting for deals page: {current_url}"

        if any(term in lower for term in cls.DEALS_FETCH_ERROR_TEXT_HINTS):
            return cls.DEALS_STATE_FETCH_ERROR, f"EB deals page shows vendor fetch error. URL: {current_url}"

        if any(term in lower for term in cls.DEALS_EMPTY_TEXT_HINTS):
            return cls.DEALS_STATE_NO_DEALS, f"EB deals page shows no available deals. URL: {current_url}"

        if has_ready_controls:
            return cls.DEALS_STATE_READY, "deals_controls_visible"

        if any(term in lower for term in cls.DEALS_LOADING_TEXT_HINTS) or ("loading" in lower and "deal" in lower):
            return cls.DEALS_STATE_LOADING, "deals_loading"

        if "available deals" in lower or ("deal" in lower and "category" in lower):
            return cls.DEALS_STATE_TEXT_ONLY, "deals_page_text_visible_without_controls"

        return cls.DEALS_STATE_UNKNOWN, "deals_state_unknown"

    @classmethod
    def _deal_state_to_flag(cls, state: str) -> str:
        if state == cls.DEALS_STATE_FETCH_ERROR:
            return cls.FLAG_DEAL_FETCH_ERROR
        if state == cls.DEALS_STATE_NO_DEALS:
            return cls.FLAG_DEAL_NOT_AVAILABLE
        return cls.FLAG_DEAL_READINESS_FAILED

    @staticmethod
    def _extract_tracking_id(text: str) -> str | None:
        import re

        match = re.search(
            r"(?:tracking|submission)\s*(?:id|#)\s*[:#]?\s*([A-Z0-9-]{6,})",
            text or "",
            flags=re.IGNORECASE,
        )
        return match.group(1) if match else None

    def _read_line_with_timeout(self, prompt: str, timeout_seconds: int) -> str | None:
        if not sys.stdin or not sys.stdin.isatty():
            logger.warning("No interactive terminal available for EB login code prompt.")
            return None

        sys.stdout.write(prompt)
        sys.stdout.flush()
        try:
            ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
        except Exception as exc:
            logger.warning("Could not read EB login code from terminal: %s", exc)
            return None

        if not ready:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return None

        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()

    async def _prompt_for_login_code(self) -> str | None:
        logger.info("ElectronicsBuyer requested a login code. Waiting up to %ss.", self.OTP_TIMEOUT_SECONDS)
        return await asyncio.to_thread(
            self._read_line_with_timeout,
            f"Enter ElectronicsBuyer login code ({self.OTP_TIMEOUT_SECONDS}s timeout): ",
            self.OTP_TIMEOUT_SECONDS,
        )

    async def _has_welcome_back(self, page: Page) -> bool:
        for selector in self.WELCOME_BACK_SELECTORS:
            if await self._selector_exists(page, selector):
                return True
        body = await self._safe_page_text(page)
        return "welcome back" in body.lower()

    async def _wait_for_post_dashboard_state(self, page: Page, timeout_seconds: int = 10) -> str:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            current_path = self._path(page.url)
            if current_path == "/app/login":
                return "login"
            if current_path.startswith("/app/") and current_path != "/app/login":
                return "app_subpath"
            if current_path == "/app":
                if await self._has_welcome_back(page):
                    return "app"
            await asyncio.sleep(0.25)

        current_path = self._path(page.url)
        if current_path == "/app":
            return "app_missing_welcome"
        if current_path.startswith("/app/") and current_path != "/app/login":
            return "app_subpath"
        if current_path == "/app/login":
            return "login"
        return "unknown"

    async def _authenticate_from_login_page(self, page: Page) -> str | None:
        if not self.login_email:
            return "Missing EB_LOGIN_EMAIL in .env; configure it before attempting ElectronicsBuyer login."
        email_filled = await self._fill_first(page, self.LOGIN_EMAIL_SELECTORS, self.login_email)
        if not email_filled:
            return "EB login page detected, but email field was not found."

        clicked_continue = await self._click_first(page, self.LOGIN_CONTINUE_SELECTORS)
        if not clicked_continue:
            return "EB login page detected, but Continue button was not found."

        await self._wait_for_any_selector(page, self.OTP_INPUT_SELECTORS, timeout_seconds=8)

        code = await self._prompt_for_login_code()
        if not code:
            return "EB login code not entered within 20 seconds; skipped EB task."

        code_filled = await self._fill_first(page, self.OTP_INPUT_SELECTORS, code)
        if not code_filled:
            return "EB OTP input field not found after Continue."

        clicked_submit = await self._click_first(page, self.OTP_SUBMIT_SELECTORS)
        if not clicked_submit:
            return "EB OTP submit button was not found."

        state = await self._wait_for_post_dashboard_state(page, timeout_seconds=10)
        if state in {"app", "app_subpath"}:
            return None
        if state == "app_missing_welcome":
            return "Reached /app after OTP, but 'Welcome back' was not visible."
        return "EB login did not complete after OTP submission."

    async def _ensure_authenticated_app(self, page: Page) -> str | None:
        await page.goto(EB_HOME_URL, wait_until="domcontentloaded")
        await asyncio.sleep(1)

        clicked_dashboard = await self._click_first(page, self.DASHBOARD_SELECTORS)
        if not clicked_dashboard:
            return "Could not find the Dashboard button on electronicsbuyer.gg homepage."

        state = await self._wait_for_post_dashboard_state(page, timeout_seconds=10)
        logger.info("EB post-dashboard state=%s url=%s", state, page.url)
        if state in {"app", "app_subpath"}:
            return None
        if state == "login":
            if self._path(page.url) != "/app/login":
                await page.goto(EB_LOGIN_URL, wait_until="domcontentloaded")
            return await self._authenticate_from_login_page(page)
        if state == "app_missing_welcome":
            return "Reached /app, but 'Welcome back' text was not visible."

        return f"After clicking Dashboard, landed on unexpected page: {page.url}"

    async def _wait_for_tracking_readiness(self, page: Page, timeout_seconds: int = 20) -> tuple[bool, str]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            current_url = page.url
            current_path = self._path(current_url)

            if current_path == "/app/login":
                return False, f"Tracking page redirected to login: {current_url}"
            if not self._is_tracking_route(current_url):
                if current_path.startswith("/app/"):
                    await asyncio.sleep(0.5)
                    continue
                return False, f"Unexpected path while waiting for tracking readiness: {current_url}"

            if await self._wait_for_any_selector(page, self.TRACKING_FORM_SELECTORS, timeout_seconds=1):
                return True, "tracking_form_visible"

            if await self._wait_for_any_selector(page, self.TRACKING_LAUNCHER_SELECTORS, timeout_seconds=1):
                return True, "tracking_launcher_visible"

            body = (await self._safe_page_text(page)).lower()
            if "loading tracking submissions" in body:
                await asyncio.sleep(0.5)
                continue

            if "tracking" in body and "submission" in body:
                return True, "tracking_page_text_visible"

            await asyncio.sleep(0.5)

        return False, f"Timed out waiting for tracking page readiness. Current URL: {page.url}"

    async def _open_tracking_form_if_needed(self, page: Page) -> None:
        if await self._click_first(page, self.TRACKING_LAUNCHER_SELECTORS):
            logger.info("EB clicked tracking form launcher before deterministic submit.")
            await asyncio.sleep(0.75)
            return

        logger.info("EB no explicit tracking launcher found before deterministic submit; continuing.")

    async def _read_first_input_value(self, page: Page, selectors: list[str]) -> str | None:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    value = await locator.input_value()
                    return (value or "").strip()
            except Exception:
                continue
        return None

    def _resolve_scoped_locator(self, page: Page, modal: Locator | None, selector: str) -> Locator:
        selector_text = selector.strip().lower()
        if modal is None or selector_text.startswith("body ") or selector_text.startswith("html "):
            return page.locator(selector).first
        return modal.locator(selector).first

    async def _has_visible_tracking_modal(self, page: Page) -> bool:
        for selector in self.TRACKING_MODAL_ROOT_SELECTORS:
            try:
                modal = page.locator(selector).first
                if await modal.count() > 0 and await modal.is_visible():
                    return True
            except Exception:
                    continue
        return False

    async def _modal_looks_like_tracking_form(self, modal: Locator) -> bool:
        try:
            text = (await modal.inner_text()).lower()
            if "tracking" in text and ("submit" in text or "number" in text):
                return True
        except Exception:
            pass

        for selector in [
            "textarea[name*='tracking' i]",
            "textarea[placeholder*='tracking' i]",
            "input[name*='tracking' i]",
            "input[placeholder*='tracking' i]",
            "div.MuiDialogContent-root textarea",
            "div.MuiDialogContent-root input",
        ]:
            try:
                locator = modal.locator(selector)
                if await locator.count() > 0:
                    return True
            except Exception:
                continue
        return False

    async def _wait_for_tracking_modal(self, page: Page, timeout_seconds: int = 8) -> Locator | None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            for selector in self.TRACKING_MODAL_ROOT_SELECTORS:
                try:
                    modal = page.locator(selector).first
                    if await modal.count() > 0 and await modal.is_visible() and await self._modal_looks_like_tracking_form(modal):
                        return modal
                except Exception:
                    continue
            await asyncio.sleep(0.25)
        return None

    async def _open_tracking_modal_if_needed(self, page: Page) -> Locator | None:
        existing_modal = await self._wait_for_tracking_modal(page, timeout_seconds=1)
        if existing_modal:
            logger.info("EB tracking submit modal already visible.")
            return existing_modal

        if await self._click_first(page, self.TRACKING_LAUNCHER_SELECTORS):
            logger.info("EB clicked tracking launcher and is waiting for modal.")
            return await self._wait_for_tracking_modal(page, timeout_seconds=8)

        logger.info("EB could not find a tracking launcher button.")
        return None

    async def _fill_first_scoped(
        self, page: Page, modal: Locator | None, selectors: list[str], value: str
    ) -> bool:
        for selector in selectors:
            try:
                locator = self._resolve_scoped_locator(page, modal, selector)
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.fill(value)
                    return True
            except Exception:
                continue
        return False

    async def _resolve_first_visible_scoped(
        self, page: Page, modal: Locator | None, selectors: list[str]
    ) -> Locator | None:
        for selector in selectors:
            try:
                locator = self._resolve_scoped_locator(page, modal, selector)
                if await locator.count() > 0 and await locator.is_visible():
                    return locator
            except Exception:
                continue
        return None

    async def _collect_locator_semantic_text(self, locator: Locator) -> str:
        try:
            payload = await locator.evaluate(
                """
                (el) => {
                  const attrs = [
                    el.getAttribute('name') || '',
                    el.getAttribute('id') || '',
                    el.getAttribute('placeholder') || '',
                    el.getAttribute('aria-label') || '',
                    el.getAttribute('data-testid') || '',
                    el.getAttribute('type') || '',
                    el.getAttribute('autocomplete') || '',
                    (el.previousElementSibling && el.previousElementSibling.textContent) || '',
                    (el.parentElement && el.parentElement.textContent) || '',
                  ];
                  const ariaLabelledBy = el.getAttribute('aria-labelledby');
                  if (ariaLabelledBy) {
                    const labelled = ariaLabelledBy
                      .split(' ')
                      .map((id) => document.getElementById(id))
                      .filter(Boolean)
                      .map((node) => node.textContent || '')
                      .join(' ');
                    attrs.push(labelled);
                  }
                  if (el.id) {
                    const explicit = document.querySelector(`label[for=\"${el.id}\"]`);
                    if (explicit && explicit.textContent) attrs.push(explicit.textContent);
                  }
                  return attrs.join(' ').toLowerCase();
                }
                """
            )
            return payload or ""
        except Exception:
            return ""

    async def _resolve_semantic_tracking_field(
        self,
        page: Page,
        modal: Locator | None,
        *,
        keywords: tuple[str, ...],
        prefer_textarea: bool = False,
    ) -> Locator | None:
        scope: Locator = modal if modal is not None else page.locator("body")
        query = "textarea,input" if prefer_textarea else "input,textarea"
        candidates = scope.locator(query)
        try:
            count = await candidates.count()
        except Exception:
            return None

        for index in range(min(count, 200)):
            locator = candidates.nth(index)
            try:
                if not await locator.is_visible():
                    continue
                if not await locator.is_enabled():
                    continue
            except Exception:
                continue

            semantic_text = await self._collect_locator_semantic_text(locator)
            if any(keyword in semantic_text for keyword in keywords):
                return locator
        return None

    async def _fill_required_tracking_field(
        self,
        page: Page,
        modal: Locator | None,
        *,
        semantic_keywords: tuple[str, ...],
        fallback_selectors: list[str],
        value: str,
        field_label: str,
        exact_value_required: bool,
        prefer_textarea: bool = False,
    ) -> tuple[bool, str | None]:
        normalized = (value or "").strip()
        if not normalized:
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING, f"{field_label} value was empty before fill."
            )

        locator = await self._resolve_semantic_tracking_field(
            page,
            modal,
            keywords=semantic_keywords,
            prefer_textarea=prefer_textarea,
        )
        if locator is None and not prefer_textarea:
            locator = await self._resolve_semantic_tracking_field(
                page,
                modal,
                keywords=semantic_keywords,
                prefer_textarea=True,
            )
        if locator is None:
            locator = await self._resolve_first_visible_scoped(page, modal, fallback_selectors)

        if locator is None:
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING, f"{field_label} input not found in tracking modal."
            )

        try:
            await locator.fill(normalized)
            actual = (await locator.input_value()).strip()
        except Exception:
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING, f"{field_label} input could not be filled/read."
            )

        if not actual:
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING, f"{field_label} remained empty after fill."
            )

        if exact_value_required and normalized.lower() not in actual.lower():
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING,
                f"{field_label} round-trip mismatch after fill: expected={normalized!r} actual={actual!r}",
            )

        if not exact_value_required and len(actual) < min(3, len(normalized)):
            return False, self._flagged_error(
                self.FLAG_REQUIRED_FIELD_MISSING,
                f"{field_label} value did not persist after fill: actual={actual!r}",
            )

        return True, None

    async def _tracking_value_still_in_form(self, page: Page, tracking_number: str) -> bool:
        needle = (tracking_number or "").strip().lower()
        if not needle:
            return False

        selectors = [
            "textarea[name*='tracking' i]",
            "textarea[placeholder*='tracking' i]",
            "input[name*='tracking' i]",
            "input[placeholder*='tracking' i]",
            "div[role='dialog'] textarea",
            "div[role='dialog'] input",
        ]
        for selector in selectors:
            try:
                loc = page.locator(selector)
                count = min(await loc.count(), 20)
            except Exception:
                continue
            for i in range(count):
                candidate = loc.nth(i)
                try:
                    if not await candidate.is_visible():
                        continue
                    value = (await candidate.input_value()).strip().lower()
                    if needle in value:
                        return True
                except Exception:
                    continue
        return False

    async def _read_first_input_value_scoped(
        self, page: Page, modal: Locator | None, selectors: list[str]
    ) -> str | None:
        for selector in selectors:
            try:
                locator = self._resolve_scoped_locator(page, modal, selector)
                if await locator.count() > 0 and await locator.is_visible():
                    return (await locator.input_value()).strip()
            except Exception:
                continue
        return None

    async def _click_first_enabled_scoped(
        self, page: Page, modal: Locator | None, selectors: list[str], timeout_seconds: int = 8
    ) -> tuple[bool, str | None]:
        def _looks_like_submit(label: str) -> bool:
            lower = (label or "").strip().lower()
            if not lower:
                return False
            if any(term in lower for term in ("cancel", "close", "back", "dismiss")):
                return False
            return any(term in lower for term in ("submit", "add tracking", "save"))

        async def _control_label(locator: Locator) -> str:
            parts: list[str] = []
            try:
                text = (await locator.inner_text()).strip()
                if text:
                    parts.append(text)
            except Exception:
                pass
            for attr in ("value", "aria-label", "title", "name", "id", "class"):
                try:
                    value = (await locator.get_attribute(attr) or "").strip()
                    if value:
                        parts.append(value)
                except Exception:
                    continue
            return " ".join(parts).strip()

        deadline = time.monotonic() + timeout_seconds
        saw_visible_disabled = False
        saw_any = False

        while time.monotonic() < deadline:
            for selector in selectors:
                try:
                    locator = self._resolve_scoped_locator(page, modal, selector)
                    if await locator.count() == 0:
                        continue
                    saw_any = True
                    if not await locator.is_visible():
                        continue
                    if not await locator.is_enabled():
                        saw_visible_disabled = True
                        continue

                    # Guard against accidentally clicking cancel/close action buttons.
                    label = await _control_label(locator)
                    if not _looks_like_submit(label):
                        continue

                    try:
                        await locator.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await locator.click(force=True)
                    return True, None
                except Exception:
                    continue

            # Fallback: choose the right-most enabled action button in dialog actions if it looks like submit.
            try:
                scope: Locator = modal if modal is not None else page.locator("body")
                actions = scope.locator("div.MuiDialogActions-root button, div.MuiDialogActions-root input[type='submit']")
                action_count = min(await actions.count(), 12)
                candidate: Locator | None = None
                best_x = -1.0
                for i in range(action_count):
                    btn = actions.nth(i)
                    try:
                        if not await btn.is_visible() or not await btn.is_enabled():
                            continue
                        label = await _control_label(btn)
                        if not _looks_like_submit(label):
                            continue
                        box = await btn.bounding_box()
                        x = float(box["x"]) if box else 0.0
                        if x >= best_x:
                            best_x = x
                            candidate = btn
                    except Exception:
                        continue
                if candidate is not None:
                    try:
                        await candidate.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await candidate.click(force=True)
                    return True, None
            except Exception:
                pass

            await asyncio.sleep(0.25)

        if saw_visible_disabled:
            return False, "Final tracking submit button stayed disabled."
        if saw_any:
            return False, "Final tracking submit button was found but never became clickable."
        return False, "Final tracking submit button not found in tracking modal."

    async def _submit_tracking_deterministic_once(self, page: Page, tracking_number: str, items_str: str) -> EBTrackingResult:
        ready, readiness_state = await self._wait_for_tracking_readiness(page, timeout_seconds=20)
        logger.info("EB tracking readiness=%s detail=%s url=%s", ready, readiness_state, page.url)
        if not ready:
            return self._tracking_failure(self.FLAG_TRACKING_SUBMIT_ERROR, readiness_state)

        modal = await self._open_tracking_modal_if_needed(page)
        if not modal:
            return EBTrackingResult(
                success=False,
                tracking_id=None,
                error_message=self._flagged_error(
                    self.FLAG_REQUIRED_FIELD_MISSING,
                    f"Could not open tracking submit modal on page: {page.url}",
                ),
            )

        insured_before = await self._read_first_input_value_scoped(page, modal, self.TRACKING_MODAL_INSURED_SELECTORS)
        tracking_filled, tracking_error = await self._fill_required_tracking_field(
            page,
            modal,
            semantic_keywords=self.TRACKING_SEMANTIC_NUMBER_KEYWORDS,
            fallback_selectors=self.TRACKING_MODAL_NUMBER_SELECTORS,
            value=tracking_number,
            field_label="Tracking number",
            exact_value_required=True,
            prefer_textarea=False,
        )
        if not tracking_filled:
            flag = self._extract_flag(tracking_error) or self.FLAG_REQUIRED_FIELD_MISSING
            return self._tracking_failure(
                flag,
                f"{self._strip_flag_prefix(tracking_error)} page={page.url}",
            )

        contents_filled, contents_error = await self._fill_required_tracking_field(
            page,
            modal,
            semantic_keywords=self.TRACKING_SEMANTIC_CONTENT_KEYWORDS,
            fallback_selectors=self.TRACKING_MODAL_CONTENTS_SELECTORS,
            value=items_str,
            field_label="Package contents",
            exact_value_required=False,
            prefer_textarea=True,
        )
        if not contents_filled:
            flag = self._extract_flag(contents_error) or self.FLAG_REQUIRED_FIELD_MISSING
            return self._tracking_failure(
                flag,
                f"{self._strip_flag_prefix(contents_error)} page={page.url}",
            )

        insured_after_fill = await self._read_first_input_value_scoped(page, modal, self.TRACKING_MODAL_INSURED_SELECTORS)
        if (insured_after_fill or "").strip() != (insured_before or "").strip():
            return self._tracking_failure(
                self.FLAG_TRACKING_SUBMIT_ERROR,
                "Insured value changed during deterministic fill; aborting submit.",
            )

        submitted, submit_error = await self._click_first_enabled_scoped(
            page,
            modal,
            self.TRACKING_MODAL_SUBMIT_SELECTORS,
            timeout_seconds=10,
        )
        if not submitted:
            return self._tracking_failure(
                self.FLAG_TRACKING_SUBMIT_ERROR,
                submit_error or f"Final tracking submit button not found in modal on page: {page.url}",
            )

        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            current_path = self._path(page.url)
            if current_path == "/app/login":
                return self._tracking_failure(
                    self.FLAG_TRACKING_SUBMIT_ERROR,
                    f"Tracking submit redirected to login: {page.url}",
                )

            body = await self._safe_page_text(page)
            lower = body.lower()
            classified_failure = self._classify_tracking_page_failure(body, page.url)
            if classified_failure:
                return classified_failure

            modal_still_open = await self._has_visible_tracking_modal(page)
            success_hint_visible = any(term in lower for term in self.TRACKING_SUCCESS_TEXT_HINTS)
            tracking_id = self._extract_tracking_id(body)
            tracking_still_in_form = await self._tracking_value_still_in_form(page, tracking_number)

            if success_hint_visible and not modal_still_open and not tracking_still_in_form:
                return EBTrackingResult(
                    success=True,
                    tracking_id=tracking_id,
                    error_message=None,
                )

            if tracking_id and not modal_still_open and not tracking_still_in_form:
                return EBTrackingResult(
                    success=True,
                    tracking_id=tracking_id,
                    error_message=None,
                )

            await asyncio.sleep(0.5)

        modal_after_wait = await self._wait_for_tracking_modal(page, timeout_seconds=1)
        persisted_value = await self._read_first_input_value_scoped(
            page,
            modal_after_wait,
            self.TRACKING_MODAL_NUMBER_SELECTORS,
        )
        if modal_after_wait and persisted_value and tracking_number in persisted_value:
            return self._tracking_failure(
                self.FLAG_NO_SUCCESS_SIGNAL,
                (
                    "No success signal after tracking submit; modal stayed open and tracking field still "
                    f"contains submitted value. URL: {page.url}"
                ),
            )

        final_body = await self._safe_page_text(page)
        final_classified_failure = self._classify_tracking_page_failure(final_body, page.url)
        if final_classified_failure:
            return final_classified_failure

        # EB often emits no explicit success confirmation after a valid submit.
        # If no concrete error signal is present, treat this as successful to avoid duplicate resubmits.
        return EBTrackingResult(
            success=True,
            tracking_id=self._extract_tracking_id(final_body),
            error_message=None,
        )

    async def _wait_for_deals_readiness(self, page: Page, timeout_seconds: int = 12) -> tuple[bool, str, str]:
        deadline = time.monotonic() + timeout_seconds
        last_state = self.DEALS_STATE_UNKNOWN
        last_detail = "deals_state_unknown"
        while time.monotonic() < deadline:
            current_url = page.url
            body = await self._safe_page_text(page)
            has_ready_controls = await self._any_selector_exists(page, self.DEALS_READY_SELECTORS)
            state, detail = self._classify_deals_snapshot(
                current_url=current_url,
                body_text=body,
                has_ready_controls=has_ready_controls,
            )

            if state == self.DEALS_STATE_READY:
                return True, state, detail

            if state in {
                self.DEALS_STATE_LOGIN_REDIRECT,
                self.DEALS_STATE_WRONG_ROUTE,
                self.DEALS_STATE_FETCH_ERROR,
                self.DEALS_STATE_NO_DEALS,
            }:
                return False, state, detail

            last_state = state
            last_detail = detail
            await asyncio.sleep(0.5)

        return (
            False,
            last_state,
            f"Timed out waiting for deals page readiness. last_state={last_state} detail={last_detail} URL: {page.url}",
        )

    async def _refresh_deals_page(self, page: Page) -> str:
        clicked_refresh = await self._click_first(page, self.DEALS_REFRESH_SELECTORS)
        if clicked_refresh:
            await asyncio.sleep(1.0)
            return "clicked_refresh_button"

        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(0.75)
        return "page_reloaded"

    async def _prepare_deals_page_preflight(
        self,
        page: Page,
        *,
        max_refresh_attempts: int = 2,
        timeout_seconds: int = 12,
    ) -> tuple[bool, str, str]:
        await page.goto(EB_DEALS_URL, wait_until="domcontentloaded")

        for attempt in range(max_refresh_attempts + 1):
            ready, state, detail = await self._wait_for_deals_readiness(page, timeout_seconds=timeout_seconds)
            logger.info(
                "EB deals preflight attempt=%s/%s ready=%s state=%s detail=%s url=%s",
                attempt + 1,
                max_refresh_attempts + 1,
                ready,
                state,
                detail,
                page.url,
            )
            if ready:
                return True, state, detail
            if attempt >= max_refresh_attempts:
                return False, state, detail

            refresh_action = await self._refresh_deals_page(page)
            logger.info(
                "EB deals preflight retrying after non-ready state=%s via action=%s",
                state,
                refresh_action,
            )

        return False, self.DEALS_STATE_UNKNOWN, f"Unexpected deals preflight fallthrough. URL: {page.url}"

    async def submit_tracking(self, tracking_number: str, items: list) -> EBTrackingResult:
        logger.info("Preparing deterministic EB auth gate for tracking submission.")
        items_str = ", ".join([f"{item['quantity']}x {item['name']}" for item in items])

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
                auth_error = await self._ensure_authenticated_app(page)
                if auth_error:
                    logger.info("EB tracking gate failed during auth: %s", auth_error)
                    return self._tracking_failure(self.FLAG_TRACKING_SUBMIT_ERROR, auth_error)

                await page.goto(EB_TRACKING_URL, wait_until="domcontentloaded")
                first_attempt = await self._submit_tracking_deterministic_once(page, tracking_number, items_str)
                if first_attempt.success:
                    return first_attempt
                if self._result_has_flag(first_attempt, self.FLAG_DUPLICATE_TRACKING):
                    logger.info("EB tracking duplicate detected on first attempt; blocking retry.")
                    return first_attempt

                logger.info(
                    "EB tracking deterministic attempt #1 failed; retrying once. reason=%s",
                    first_attempt.error_message,
                )
                await page.goto(EB_TRACKING_URL, wait_until="domcontentloaded")
                retry_attempt = await self._submit_tracking_deterministic_once(page, tracking_number, items_str)
                if retry_attempt.success:
                    return retry_attempt
                if self._result_has_flag(retry_attempt, self.FLAG_DUPLICATE_TRACKING):
                    logger.info("EB tracking duplicate detected on retry; returning duplicate block.")
                    return retry_attempt

                warnings = list(
                    dict.fromkeys(
                        (first_attempt.warnings or [])
                        + (retry_attempt.warnings or [])
                        + [self.FLAG_NO_SUCCESS_SIGNAL]
                    )
                )
                return EBTrackingResult(
                    success=False,
                    tracking_id=None,
                    error_message=self._flagged_error(
                        self.FLAG_NO_SUCCESS_SIGNAL,
                        (
                            "Deterministic tracking submission failed after 2 attempts. "
                            f"first_error={first_attempt.error_message!r}; "
                            f"second_error={retry_attempt.error_message!r}"
                        ),
                    ),
                    warnings=warnings,
                )
            finally:
                await context.close()

    async def submit_deal(self, items: list, quantities: dict) -> EBDealResult:
        logger.info("Preparing EB auth gate before browser-use deal submission.")

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
                auth_error = await self._ensure_authenticated_app(page)
                if auth_error:
                    logger.info("EB deals auth gate failed: %s", auth_error)
                    return self._deal_failure(self.FLAG_DEAL_READINESS_FAILED, auth_error)
            finally:
                await context.close()

        logger.info("EB auth gate complete; launching browser-use primary deal agent.")
        deadline = time.monotonic() + 120
        try:
            remaining = max(1.0, deadline - time.monotonic())
            return await asyncio.wait_for(
                self.llm_executor.submit_deal(
                    items=items,
                    quantities=quantities,
                    browser_context=None,
                ),
                timeout=remaining,
            )
        except asyncio.TimeoutError:
            return EBDealResult(
                success=False,
                deal_id=None,
                payout_value=0.0,
                error_message=f"{FLAG_DEAL_TIMEOUT}: EB deal submission timed out after 120s",
                warnings=[FLAG_DEAL_TIMEOUT],
            )
