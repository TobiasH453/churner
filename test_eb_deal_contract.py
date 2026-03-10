"""Fast contract checks for ElectronicsBuyer deal result semantics."""

from pathlib import Path

from eb_contracts import (
    FLAG_DEAL_NO_SUBMISSIONS,
    FLAG_DEAL_PAYOUT_INCOMPLETE,
    FLAG_UNMATCHED_ITEMS,
    enforce_deal_contract,
)
from models import EBDealResult


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    quantities = {"Item A": 1, "Item B": 1}

    payout_incomplete = enforce_deal_contract(
        EBDealResult(
            success=True,
            deal_id="D-1",
            payout_value=42.0,
            submitted_items=["Item A", "Item B"],
            payout_captured_items=["Item A"],
        ),
        quantities,
    )
    _assert(not payout_incomplete.success, "Success must be false when payout capture is incomplete.")
    _assert(
        FLAG_DEAL_PAYOUT_INCOMPLETE in (payout_incomplete.error_message or ""),
        "Incomplete payout must include FLAG_DEAL_PAYOUT_INCOMPLETE.",
    )

    unmatched_allowed = enforce_deal_contract(
        EBDealResult(
            success=True,
            deal_id="D-2",
            payout_value=65.0,
            submitted_items=["Item A"],
            payout_captured_items=["Item A"],
            unmatched_items=["Item B"],
        ),
        quantities,
    )
    _assert(unmatched_allowed.success, "Matched submissions with captured payout can still succeed.")
    _assert(
        FLAG_UNMATCHED_ITEMS in unmatched_allowed.warnings,
        "Unmatched items must be explicitly flagged in warnings.",
    )

    missing_submission = enforce_deal_contract(
        EBDealResult(
            success=True,
            deal_id="D-3",
            payout_value=25.0,
            submitted_items=[],
            payout_captured_items=[],
        ),
        quantities,
    )
    _assert(not missing_submission.success, "Success must be false when no submitted items are reported.")
    _assert(
        FLAG_DEAL_NO_SUBMISSIONS in (missing_submission.error_message or ""),
        "Missing submissions must include FLAG_DEAL_NO_SUBMISSIONS.",
    )

    buyer_src = Path("electronics_buyer.py").read_text(encoding="utf-8")
    llm_src = Path("electronics_buyer_llm.py").read_text(encoding="utf-8")
    _assert(
        "deadline = time.monotonic() + 120" in buyer_src and "asyncio.wait_for" in buyer_src,
        "Deal runtime guardrail timeout in electronics_buyer.py must stay bounded.",
    )
    _assert(
        "self.llm_executor.submit_deal(" in buyer_src and "browser_context=None" in buyer_src,
        "Deal flow must use browser-use as the primary execution path.",
    )
    _assert(
        "auth_error = await self._ensure_authenticated_app(page)" in buyer_src,
        "Deal flow must run EB auth gate before launching browser-use deal agent.",
    )
    _assert(
        'get_env("EB_LOGIN_EMAIL", "tobias.halpern@gmail.com")' not in buyer_src
        and 'get_env("EB_LOGIN_EMAIL", "tobias.halpern@gmail.com")' not in llm_src,
        "EB login email must come from .env without a hardcoded personal fallback.",
    )
    _assert(
        "supports_handoff = self.llm_executor.supports_browser_context_handoff()" not in buyer_src,
        "Deal flow must not hard-gate on browser_context handoff support.",
    )
    _assert(
        "DEAL_TIMEOUT_SECONDS = 120" in llm_src and "max_steps=self.DEAL_MAX_STEPS" in llm_src,
        "LLM deal execution limits must remain bounded at 120 seconds and configured max steps.",
    )
    _assert(
        "_deal_browser_session" in llm_src and "keep_alive\": True" in llm_src,
        "Deal flow must reuse a keep-alive browser session for browser-use execution.",
    )
    _assert(
        "def _build_deal_search_specs" in llm_src and "SEARCH SPECS (use exactly; do not invent extra products)" in llm_src,
        "LLM deal flow must construct and use constrained per-item search specs.",
    )

    print("PASS: deal contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
