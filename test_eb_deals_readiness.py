"""Source-level regression checks for browser-use-primary EB deal execution."""

from pathlib import Path


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    buyer_src = Path("electronics_buyer.py").read_text(encoding="utf-8")
    llm_src = Path("electronics_buyer_llm.py").read_text(encoding="utf-8")

    _assert(
        "Preparing EB auth gate before browser-use deal submission." in buyer_src
        and "auth_error = await self._ensure_authenticated_app(page)" in buyer_src,
        "Deal flow should run deterministic EB auth gate before launching the deal agent.",
    )
    _assert(
        "supports_handoff = self.llm_executor.supports_browser_context_handoff()" not in buyer_src,
        "Deal flow must not hard-gate on browser_context handoff support.",
    )
    _assert(
        "self.llm_executor.submit_deal(" in buyer_src and "browser_context=None" in buyer_src,
        "Deal flow must call browser-use executor directly as primary.",
    )
    _assert(
        'get_env("EB_LOGIN_EMAIL", "tobias.halpern@gmail.com")' not in buyer_src
        and 'get_env("EB_LOGIN_EMAIL", "tobias.halpern@gmail.com")' not in llm_src,
        "EB login email should not fall back to a hardcoded personal address.",
    )
    _assert(
        "launch_persistent_context(" in buyer_src,
        "Tracking deterministic flow should still retain Playwright context launch in this file.",
    )
    _assert(
        "ready, readiness_state, readiness_detail = await self._prepare_deals_page_preflight(" not in buyer_src,
        "Deal flow should not perform deterministic deals preflight before agent execution.",
    )

    _assert(
        "Start at https://electronicsbuyer.gg/ (homepage)." in llm_src,
        "Deal agent instructions must begin at EB homepage.",
    )
    _assert(
        "def _build_deal_search_specs" in llm_src and "SEARCH SPECS (use exactly; do not invent extra products)" in llm_src,
        "Deal flow should build and use compact search specs for constrained matching.",
    )
    _assert(
        'Click the "Dashboard" button to enter the app session.' in llm_src,
        "Deal agent instructions must include Dashboard click step.",
    )
    _assert(
        'Immediately click the first visible "Dashboard" / "Access Dashboard" control in the first viewport.' in llm_src,
        "Deal instructions must prioritize immediate dashboard navigation.",
    )
    _assert(
        "Retry at most 2 times total." in llm_src,
        "Deal agent instructions must enforce 2 retries for vendor-fetch errors.",
    )
    _assert(
        "run exactly ONE refine attempt using spec.refine_query" in llm_src,
        "Deal matching should allow only one refine-search attempt per requested item.",
    )
    _assert(
        "wait up to 20 seconds for the human to enter OTP and submit." in llm_src,
        "Deal agent instructions must support OTP wait when login is required.",
    )
    _assert(
        "DEAL_MAX_STEPS = 12" in llm_src and "DEAL_TIMEOUT_SECONDS = 120" in llm_src,
        "Deal agent runtime bounds should be set to 12 steps and 120 seconds.",
    )
    _assert(
        "_deal_browser_session" in llm_src and "keep_alive\": True" in llm_src,
        "Deal flow should keep and reuse a browser-use keep-alive session.",
    )

    print("PASS: browser-use primary deal flow source checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
