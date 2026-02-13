# Codebase Concerns

**Analysis Date:** 2026-02-13

## Tech Debt

- `AnthropicWrapper` is duplicated in both `amazon_scraper.py` and `electronics_buyer.py`; drift risk if browser-use compatibility requirements change.
- Automation prompts are large inline strings inside code modules, making iterative prompt updates hard to diff/test.
- Utility typing in `utils.py` uses `any` instead of `typing.Any` (`save_state`, `get_state`), weakening static analysis value.
- Some dependencies listed in `requirements.txt` appear unused in current runtime modules (maintenance/cve surface area).

## Known Bugs

- `main.py` constructs `BrowserAgent()` at import time; missing required env vars can fail startup before endpoint availability.
- `utils.py` logging setup writes to `logs/agent.log` but does not create `logs/` directory defensively; startup can fail in clean environments.
- Browser actions are dependent on live UI text/content; site changes on Amazon or electronicsbuyer.gg can silently degrade extraction quality.

## Security Considerations

- Credentials for Amazon are interpolated directly into LLM task text in `amazon_scraper.py`; sensitive values may appear in model context and trace files.
- API error responses return raw exception text via `HTTPException(detail=str(e))` in `main.py`, which can leak internals to callers.
- Persistent authenticated browser session in `data/browser-profile` is powerful and local-file protected only.

## Performance Bottlenecks

- Every request runs live browser automation and remote LLM reasoning; latency variance is high and bounded by external systems.
- Single process handles heavy async browser tasks; no queueing/backpressure or concurrency policy implemented.
- Artifact generation (`generate_gif`) adds overhead during every run.

## Fragile Areas

- Chromium executable discovery in `stealth_utils.py` is macOS-cache specific and path-heuristic-based.
- Automation depends on anti-detection launch args and persistent profile behavior that can break after browser-use/playwright upgrades.
- `browser_agent.py` assumes expected `items` shape in returned models and converts directly without defensive schema normalization.

## Scaling Limits

- Current architecture is optimized for one operator and low request volume.
- No job queue, distributed worker model, or idempotency handling for repeated webhook deliveries.
- Shared debug artifact filenames (`logs/agent.gif`, `logs/agent_conversation.json`) are vulnerable to overwrite/race conditions under concurrent runs.

## Dependencies at Risk

- `browser-use` and `langchain-anthropic` are fast-moving integrations where API changes can break wrappers/prompts.
- `playwright` binary/cache behavior can change, affecting `stealth_utils.py` executable detection.
- External websites (Amazon, electronicsbuyer.gg) are uncontrolled dependencies with frequent UI drift.

## Missing Critical Features

- Retry policy is not implemented despite `MAX_RETRIES` health signal in `main.py`.
- No dedicated validation layer for extracted semantic correctness (price/date/tracking sanity checks).
- Google Sheets updates and Telegram notifications are documented goals but not implemented in current Python modules.
- No auth/token protection on webhook endpoint (`/process-order`) beyond network placement assumptions.

## Test Coverage Gaps

- No automated regression suite for parser/orchestration behavior.
- No contract tests around `EmailData` input edge cases from n8n payloads.
- No deterministic tests for failures in external service steps (Anthropic timeout, login expired, selector/page mismatch).
- Current tests require live credentials and manual supervision, limiting repeatability.

## GSD Context Additions

**Documentation Drift Risk:**
- Some high-level docs (e.g., sections in `CLAUDE.md`, `PROJECT_SUMMARY.md`) still describe future-state components as if fully present; this can cause planning/execution mismatch if not reconciled with current code.

**Operational Risk from Split System Ownership:**
- End-to-end behavior depends on configuration in external n8n workspace plus local Python code; without versioned n8n exports in `n8n-workflows/`, reproducibility and rollback are limited.

---

*Concerns analysis: 2026-02-13*
*Update when major risks are resolved or new critical fragility is discovered*
