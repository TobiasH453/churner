# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-12)

**Core value:** Browser automation must successfully navigate Amazon and extract real order/shipping data - not placeholders
**Current focus:** Phase 1 - Browser Automation Fix

## Current Position

Phase: 1 of 5 (Browser Automation Fix)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-13 — Resumed 01-02; confirmed post-login failure mode and patched LLM compatibility + auth-step robustness

Progress: [█░░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 6 min
- Total execution time: 0.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-browser-automation-fix | 1 | 6 min | 6 min |

**Recent Trend:**
- Last 5 plans: 01-01 (6 min)
- Trend: N/A (first plan)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Architecture: Hybrid n8n + Python architecture with browser-use library (n8n layer working, Python layer needs fixing)
- Browser automation: Visible browser mode for supervision and debugging
- Cookie-based auth: Session persistence configured, cookies saved but browser exits before using them
- browser-use structured output: Use output_model_schema parameter on Agent() + result.structured_output for Pydantic-validated extraction
- Error propagation: Raise RuntimeError on None structured_output (no silent placeholder returns)
- Task prompt hygiene: Remove login steps from EB prompts - persistent browser profile handles session

### Pending Todos

None yet.

### Blockers/Concerns

~~**Phase 1 (Critical):**~~
~~- Browser agent crashes immediately after opening Amazon - structured output validation failure (missing output_model_schema parameter)~~
~~- Returns placeholder "NEEDS_PARSING" data instead of real extraction~~
~~- Broad exception handling masks real errors in amazon_scraper.py~~

**RESOLVED in 01-01:** All four root-cause bugs fixed in amazon_scraper.py and electronics_buyer.py.

**Remaining Phase 1 work:**
- 01-02: (pending - next plan in phase)
- User-reported blocker: agent opens Amazon login page, performs no interactions, then closes.
- Active runtime: Python 3.14.3 (user-confirmed). Continue on 3.14 with enhanced diagnostics.
- Stabilization in progress: improved runtime diagnostics, debug mode (`--debug`), and conversation artifact paths to capture root-cause details on next run.
- Root-cause drift identified: long-running server process on port 8080 was still using old in-memory code path (old prompts/model + placeholder fallback behavior).
- Guard added in `browser_agent.py` to fail fast if payload contains placeholder markers (`NEEDS_PARSING`, `TBD`) so API can never report success=true with fake data.
- Login/extraction decoupling added: `amazon_scraper.py` now primes authenticated session with deterministic Playwright actions before invoking browser-use Agent.
- Optional automatic 2FA added: if `AMAZON_TOTP_SECRET` is set in `.env`, scraper attempts TOTP code entry on Amazon MFA pages before falling back to manual input.
- New root cause confirmed from logs: `AttributeError: items` came from using `langchain_anthropic.ChatAnthropic` with browser-use token wrapper calling `ainvoke(messages, output_format, ...)`.
- Fix applied: switched runtime agents to `browser_use.llm.ChatAnthropic` and hardened sign-in flow when password field is delayed/passkey-interrupted.
- Latest failure after login confirmed: Anthropic request rejected with `401 invalid x-api-key`.
- Runtime hardening added in `utils.py`: `.env` now loads with `override=True`; key values are trimmed/unquoted; `ANTHROPIC_API_KEY` fails fast with a clear validation error if malformed.
- New extraction hardening: when browser-use returns JSON with trailing text, `amazon_scraper.py` now attempts recovery by extracting the first balanced JSON object and validating against `ShippingDetails`/`OrderDetails` before failing.
- New resilience path for shipping: if LLM scrape fails (`site unavailable`, auth-placeholder output, or judge fail), scraper now attempts deterministic Playwright fallback extraction (tracking number/carrier/delivery/items) before returning failure.
- Login reliability update: sign-in flow was extracted to `_perform_sign_in_if_needed(...)` and is now used in both session priming and fallback extraction context.
- Shipping strategy update: deterministic Playwright extraction now runs first (sign-in + extraction in one context), with LLM path only as secondary fallback.
- Verified progress from live run: Amazon side successfully reached correct order page and extracted tracking data (`TBA...`) before handoff to EB submission.
- External dependency blocker confirmed: EB tracking submission currently fails server-side (`Failed to submit tracking numbers`) and can corrupt browser session afterward.
- Response contract fix applied: on EB failure, API now preserves `amazon_data`, returns `eb_result.success=false`, and includes EB error in `errors` rather than nulling both payloads.
- Login hardening update: added more passkey/alternate-auth selectors and broader OTP field selectors to reduce manual intervention on Amazon sign-in.
- Amazon data quality fix in progress: shipping item extraction now prioritizes product links near shipment/track-package containers and filters recommendation/search/price noise that caused wrong item names.

## Session Continuity

Last session: 2026-02-13
Stopped at: Session resumed via resume-project workflow, proceeding to complete 01-02-PLAN.md (human verification)
Resume file: CODEX_HANDOFF.md
