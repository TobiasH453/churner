# Technology Stack

**Analysis Date:** 2026-02-17

## Languages

**Primary:**
- Python 3.11+ (currently targeted at 3.14 in scripts) - all runtime logic in `main.py`, `browser_agent.py`, `amazon_scraper.py`, `electronics_buyer.py`

**Secondary:**
- JavaScript (Node.js ecosystem) - PM2 process manager config in `ecosystem.config.js`
- Bash - operational scripts in `scripts/services-*.sh`

## Runtime

**Environment:**
- Python virtualenv runtime (`venv314/bin/python` by default in PM2)
- Browser runtime through Playwright Chromium persistent contexts
- Node.js runtime for PM2 and `n8n`

**Package Manager:**
- `pip` with dependency list in `requirements.txt`
- Lockfile: no `poetry.lock`, `Pipfile.lock`, or pinned `requirements` lock generated

## Frameworks

**Core:**
- FastAPI - webhook API server in `main.py`
- Playwright (async API) - deterministic browser automation in `amazon_scraper.py` and `electronics_buyer.py`
- browser-use + Anthropic integration - LLM-driven constrained browser tasks in `electronics_buyer_llm.py`

**Testing:**
- Script-based Python contract tests (no pytest framework)
- Assertion style with direct `raise AssertionError` + `main()` in `test_*.py`

**Build/Dev:**
- PM2 process supervision for long-running services via `ecosystem.config.js`
- No packaging/build step; direct source execution

## Key Dependencies

**Critical:**
- `fastapi` + `uvicorn` - HTTP server and ASGI runtime
- `playwright` - browser automation engine and persistent profile contexts
- `browser-use` - LLM-guided browser action layer
- `anthropic`, `langchain`, `langchain-anthropic` - Claude model orchestration for browser-use agents
- `pydantic` - strict request/response and result contracts in `models.py`

**Infrastructure:**
- `python-dotenv` - environment bootstrapping in `utils.py`
- `pyotp` - optional Amazon TOTP automation for MFA
- `requests`, `beautifulsoup4`, `httpx` - available but mostly secondary in current runtime paths

## Configuration

**Environment:**
- `.env` loaded globally from `utils.py` (`load_dotenv(override=True)`)
- Critical variables include `ANTHROPIC_API_KEY`, Amazon credentials (`AMAZON_*` + business variants), and EB login email (`EB_LOGIN_EMAIL`)
- Runtime toggles include `SERVER_PORT`, `BROWSER_HEADLESS`, `MAX_RETRIES`

**Process/Runtime Config:**
- `ecosystem.config.js` defines PM2 apps (`amazon-agent`, `n8n-server`) and timezone env (`TZ`, `GENERIC_TIMEZONE`, `N8N_DEFAULT_TIMEZONE`)
- Browser profile state persisted in `data/browser-profile*`

## Platform Requirements

**Development:**
- macOS-oriented defaults (Playwright cache path in `stealth_utils.py` uses `~/Library/Caches/ms-playwright`)
- Python 3.11+ required; scripts prefer 3.14 when available
- Playwright Chromium installed locally

**Production/Operations:**
- Local host services managed with PM2, not containerized
- API expected at `http://localhost:8080`, n8n at `http://localhost:5678`
- State depends on persisted local profile directories and `.env` secrets

---

*Stack analysis: 2026-02-17*
*Update after major dependency or runtime changes*
