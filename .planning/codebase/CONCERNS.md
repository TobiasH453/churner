# Codebase Concerns

**Analysis Date:** 2026-02-17

## Tech Debt

**Selector-heavy UI coupling (Amazon + EB):**
- Issue: Large hard-coded selector matrices are tightly coupled to third-party UI DOM shape (`amazon_scraper.py`, `electronics_buyer.py`).
- Why: Needed for deterministic operation against dynamic sites.
- Impact: Minor UI changes can break extraction or submission without compile-time signal.
- Fix approach: Add selector health checks, fallback heuristics, and lower-level semantic locators where possible.

**Hybrid deterministic + LLM complexity:**
- Issue: Behavioral logic is split across deterministic Playwright code and browser-use prompt logic (`electronics_buyer.py`, `electronics_buyer_llm.py`).
- Why: Deterministic auth is more reliable, while deal selection still benefits from LLM flexibility.
- Impact: Debugging failures requires inspecting both code and prompt semantics.
- Fix approach: Continue pushing critical operations into deterministic code and narrow LLM scope further.

## Known Bugs

**Interactive OTP dependency can dead-end automation:**
- Symptoms: EB auth can fail when no interactive TTY is available for OTP entry.
- Trigger: Running `submit_tracking`/`submit_deal` in non-interactive environments.
- Workaround: Ensure authenticated persistent profile exists before unattended runs.
- Root cause: `_prompt_for_login_code()` relies on terminal stdin with timeout.

**Potential mutable default in response model:**
- Symptoms: `AgentResponse.errors` uses `errors: List[str] = []` in `models.py`.
- Trigger: Repeated object construction under atypical mutation scenarios.
- Workaround: Current code passes explicit lists in main path.
- Root cause: Default mutable list literal in model declaration.

## Security Considerations

**Credentials and session state on local disk:**
- Risk: `.env` secrets and persistent browser profiles in `data/browser-profile*` are high-value assets.
- Current mitigation: Operational guidance says do not delete/expose these; expected gitignore usage.
- Recommendations: Enforce strict filesystem permissions and optional OS keychain/secret manager usage.

**Default EB login email fallback:**
- Risk: `EB_LOGIN_EMAIL` has a hardcoded fallback in code.
- Current mitigation: Env override is supported.
- Recommendations: Remove personal default from code and require explicit env variable.

## Performance Bottlenecks

**Cold browser context startup:**
- Problem: Launching persistent Chromium contexts for each request is expensive.
- Measurement: Not instrumented, but design implies multi-second overhead per run.
- Cause: Auth/session safety and deterministic isolation strategy.
- Improvement path: Reuse managed contexts safely per queue/worker where practical.

**LLM deal execution latency:**
- Problem: Deal flow allows up to 120s execution with retries and constrained navigation.
- Measurement: Hard timeout guards indicate expected long tail.
- Cause: External UI variability + model-driven interaction.
- Improvement path: Increase deterministic deal automation share and cache canonical deal mappings.

## Fragile Areas

**Amazon item extraction strictness:**
- Why fragile: Strict row-scoped extraction intentionally avoids broad fallbacks.
- Common failures: Empty item list when Amazon layout deviates from known selectors.
- Safe modification: Update selector templates conservatively and keep fail-closed behavior.
- Test coverage: Guarded by `test_amazon_item_scope_contract.py`.

**EB tracking modal field resolution:**
- Why fragile: Multiple modal variants and dynamic form controls handled by selector + semantic matching.
- Common failures: missing/disabled submit controls, false success/no-signal states.
- Safe modification: Preserve flag semantics (`FLAG_REQUIRED_FIELD_MISSING`, `FLAG_NO_SUCCESS_SIGNAL`) and bounded retries.
- Test coverage: Source-level checks in `test_eb_tracking_contract.py`.

## Scaling Limits

**Single-instance local process model:**
- Current capacity: effectively one-machine, browser-bound throughput.
- Limit: Concurrent request scaling constrained by browser session contention and UI automation runtime.
- Symptoms at limit: queueing, timeout frequency, and potential profile lock contention.
- Scaling path: Move to explicit job queue + worker isolation with account/profile affinity.

## Dependencies at Risk

**Third-party website DOM stability (Amazon, ElectronicsBuyer):**
- Risk: External DOM changes are outside project control.
- Impact: Core business flows can fail without code changes.
- Migration plan: maintain regression contracts and modular selector refresh process.

**browser-use / langchain compatibility drift:**
- Risk: Runtime incompatibility already acknowledged for Python 3.14+ in `runtime_checks.py`.
- Impact: Agent failures or unstable behavior in LLM-driven steps.
- Migration plan: pin tested versions and add periodic compatibility validation matrix.

## Missing Critical Features

**No non-interactive OTP/channel strategy for EB login:**
- Problem: unattended operation still depends on human OTP entry when session expires.
- Current workaround: rely on persistent logged-in browser profiles.
- Blocks: fully autonomous recovery after session expiry.
- Implementation complexity: medium (requires secure OTP retrieval or alternative auth mechanism).

**No idempotency or request dedupe at API boundary:**
- Problem: repeated webhook delivery could replay expensive automation tasks.
- Current workaround: none in FastAPI endpoint.
- Blocks: robust retry safety with n8n or external callers.
- Implementation complexity: medium.

## Test Coverage Gaps

**End-to-end automated integration coverage:**
- What's not tested: full live run from `/process-order` through Amazon + EB under CI-like conditions.
- Risk: integration drift may pass source contracts but fail operationally.
- Priority: High.
- Difficulty to test: high due to external auth, OTP, and third-party UI volatility.

**Operational script validation:**
- What's not tested: PM2 script behavior and environment boot scripts under automation.
- Risk: runtime drift in deployment scripts may go unnoticed.
- Priority: Medium.
- Difficulty to test: medium.

---

*Concerns audit: 2026-02-17*
*Update as issues are fixed or newly discovered*
