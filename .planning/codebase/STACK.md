# Technology Stack

**Analysis Date:** 2026-02-13

## Languages

**Primary:**
- Python 3.9+ - All runtime code in `main.py`, `browser_agent.py`, `amazon_scraper.py`, `electronics_buyer.py`, and support modules.

**Secondary:**
- Markdown - Operational workflow docs in `.planning/`, `get-shit-done/`, and `prompts/`.
- JSON - Runtime/debug artifacts in `logs/*.json` and local state files under `data/`.

## Runtime

**Environment:**
- CPython (local virtualenv at `venv/`).
- ASGI server via Uvicorn for webhook handling in `main.py`.
- Browser runtime via Playwright Chromium launched by `browser-use` through `stealth_utils.py`.

**Package Manager:**
- pip + `requirements.txt`.
- Lockfile: none detected (`requirements.txt` only).

## Frameworks

**Core:**
- FastAPI - HTTP API endpoints (`main.py`).
- browser-use - LLM-guided browser automation (`amazon_scraper.py`, `electronics_buyer.py`).
- Pydantic v2 - request/response and extraction models (`models.py`).

**Testing:**
- No formal test framework detected.
- Script-based diagnostics in `test_scraper.py`, `test_debug.py`, and `test_diagnose.py`.

**Build/Dev:**
- python-dotenv for env loading (`utils.py`, test scripts).
- Playwright for persistent browser profile and manual login bootstrap (`manual_login.py`).

## Key Dependencies

**Critical:**
- `browser-use` - drives multi-step automation agents and structured output.
- `langchain-anthropic` + `anthropic` - Claude model access for browser reasoning.
- `playwright` - browser runtime and persistent profile support.
- `fastapi` + `uvicorn` - webhook API surface consumed by n8n.
- `pydantic` - schema contracts for email payloads and agent outputs.

**Infrastructure:**
- `python-dotenv` - config ingestion from `.env`.
- `httpx`/`requests`/`beautifulsoup4`/`python-telegram-bot` are listed in `requirements.txt` but not materially used in current Python modules.

## Configuration

**Environment:**
- Secrets and runtime knobs come from `.env` via `get_env()` in `utils.py`.
- Key vars referenced in code: `ANTHROPIC_API_KEY`, `AMAZON_EMAIL`, `AMAZON_PASSWORD`, `EB_USERNAME`, `EB_PASSWORD`, `SERVER_PORT`, `MAX_RETRIES`, `BROWSER_HEADLESS`.
- Browser watchdog defaults are set in code with `TIMEOUT_BrowserStartEvent`, `TIMEOUT_BrowserLaunchEvent`, `TIMEOUT_BrowserConnectedEvent`.

**Build:**
- No build system (interpreted Python scripts).
- Runtime scripts are executed directly (`python main.py`, `python manual_login.py`, `python test_scraper.py`).

## Platform Requirements

**Development:**
- macOS-oriented by default because `stealth_utils.py` searches Playwright Chromium in `~/Library/Caches/ms-playwright`.
- Requires local GUI session (`headless=False`) for normal operation and manual login fallback.

**Production:**
- Intended as a long-running local service on port `8080` (or `SERVER_PORT`).
- Depends on persistent local browser state at `data/browser-profile`.

## GSD Context Additions

**Planned Stack (from existing project docs):**
- n8n is the intended orchestration runtime for Gmail trigger + branching + downstream integrations (`.planning/PROJECT.md`, `CLAUDE.md`).
- pm2 is the intended local process supervisor for always-on operation (`IMPLEMENTATION_PLAN.md`).
- Google Sheets + Telegram are documented as downstream outputs, but no runtime calls exist yet in current Python modules.

**Current vs Planned Reality:**
- Current implemented Python code covers webhook intake and browser automation adapters.
- Planned infrastructure in docs includes additional integration/runtime pieces that are partially implemented outside this repository state.

---

*Stack analysis: 2026-02-13*
*Update after major dependency or runtime changes*
