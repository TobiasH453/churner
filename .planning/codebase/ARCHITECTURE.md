# Architecture

**Analysis Date:** 2026-02-13

## Pattern Overview

**Overall:** Local webhook-driven automation service with LLM-guided browser workers.

**Key Characteristics:**
- Single-process Python service exposes FastAPI endpoints.
- Request routing branches by email type (`order_confirmation` vs `shipping_confirmation`).
- Browser tasks are delegated to specialized agent wrappers (`AmazonScraper`, `ElectronicsBuyerAgent`).
- Strong schema boundary at IO points through Pydantic models.

## Layers

**API Layer:**
- Purpose: expose health and processing endpoints.
- Contains: FastAPI app and route handlers in `main.py`.
- Depends on: `BrowserAgent`, model contracts, logger utilities.
- Used by: n8n HTTP nodes and local manual tests.

**Orchestration Layer:**
- Purpose: process-level workflow coordination and branching.
- Contains: `BrowserAgent` in `browser_agent.py`.
- Depends on: scraper adapters and Pydantic models.
- Used by: API layer (`main.py`).

**Automation Adapters:**
- Purpose: execute website-specific steps and return typed results.
- Contains: `AmazonScraper` (`amazon_scraper.py`) and `ElectronicsBuyerAgent` (`electronics_buyer.py`).
- Depends on: `browser_use.Agent`, `ChatAnthropic`, browser profile helpers.
- Used by: orchestration layer.

**Shared Foundations:**
- Purpose: contracts, logging, environment access, browser profile policy.
- Contains: `models.py`, `utils.py`, `stealth_utils.py`.
- Used by: all layers.

## Data Flow

**Order Confirmation Flow:**
1. n8n sends payload to `POST /process-order` (`main.py`).
2. FastAPI validates payload into `EmailData` (`models.py`).
3. `BrowserAgent.process_email()` routes to `_process_order_confirmation()` (`browser_agent.py`).
4. `AmazonScraper.scrape_order_confirmation()` extracts typed `OrderDetails` (`amazon_scraper.py`).
5. `ElectronicsBuyerAgent.submit_deal()` submits and returns `EBDealResult` (`electronics_buyer.py`).
6. `AgentResponse` is returned to caller.

**Shipping Confirmation Flow:**
1. Same entry as above.
2. `BrowserAgent` routes to `_process_shipping_confirmation()`.
3. `AmazonScraper.scrape_shipping_confirmation()` extracts `ShippingDetails`.
4. `ElectronicsBuyerAgent.submit_tracking()` returns `EBTrackingResult`.
5. Unified `AgentResponse` returns success/failure metadata.

**State Management:**
- Mostly stateless per request.
- Persistent browser authentication state in `data/browser-profile`.
- Optional local key-value state available in `data/state.json` via `utils.py`.

## Key Abstractions

**Typed Contracts (Pydantic Models):**
- Purpose: define stable payload/result schemas.
- Examples: `EmailData`, `OrderDetails`, `ShippingDetails`, `AgentResponse` in `models.py`.
- Pattern: schema-first boundary validation.

**Site Agent Wrappers:**
- Purpose: isolate prompt/tool configuration per target site.
- Examples: `AmazonScraper`, `ElectronicsBuyerAgent`.
- Pattern: adapter around `browser_use.Agent` with structured output enforcement.

**LLM Compatibility Wrapper:**
- Purpose: normalize provider/model access expected by browser-use.
- Examples: `AnthropicWrapper` in both scraper modules.
- Pattern: thin proxy via `__getattr__`.

## Entry Points

**API Service:**
- Location: `main.py`.
- Triggers: HTTP requests from n8n/manual callers.
- Responsibilities: validation, invocation, response shaping, error translation.

**Manual Session Bootstrap:**
- Location: `manual_login.py`.
- Triggers: manual CLI run.
- Responsibilities: open persistent Chromium context and let user log in interactively.

**Diagnostic Runners:**
- Location: `test_scraper.py`, `test_debug.py`, `test_diagnose.py`.
- Triggers: manual CLI run.
- Responsibilities: isolated troubleshooting of browser agent behavior.

## Error Handling

**Strategy:**
- Exception capture near API boundary and orchestration boundary.
- Agent-level structured-output guard rails (`structured_output is None` -> `RuntimeError`).

**Patterns:**
- Broad `except Exception` in `main.py` and `browser_agent.py`.
- Fail-safe response object on orchestration failures (`success=False`, populated `errors`).
- Resource cleanup via `finally: await agent.close()` in scraper modules.

## Cross-Cutting Concerns

**Logging:**
- Shared logger from `utils.py`; route, orchestration, and scraper steps emit info/error logs.

**Validation:**
- FastAPI/Pydantic validate inbound request and structured outputs.

**Authentication:**
- `.env` for API keys/credentials; persistent browser profile for session continuity.

**Operational Debugging:**
- Browser-use GIF + conversation trace files written to `logs/`.

## GSD Context Additions

**Roadmap Alignment:**
- Architecture is documented in `.planning/ROADMAP.md` as a 5-phase progression where current code corresponds mainly to Phase 1 foundations.
- `.planning/STATE.md` tracks this as a blocked/fix-focused phase around browser automation reliability.

**System Boundary Context:**
- Full end-to-end design in `CLAUDE.md` includes n8n orchestration plus Sheets/Telegram side effects, while this codebase currently represents the Python automation boundary within that larger system.

---

*Architecture analysis: 2026-02-13*
*Update when orchestration pattern, entry points, or layer boundaries change*
