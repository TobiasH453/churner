# Architecture

**Analysis Date:** 2026-02-17

## Pattern Overview

**Overall:** Single-process API orchestrator with deterministic browser automation and constrained LLM-assisted browser tasks.

**Key Characteristics:**
- FastAPI ingress layer for n8n-triggered event handling
- Per-request orchestration in `BrowserAgent` that branches by email type
- Strongly typed Pydantic contracts at boundaries (`models.py`, `eb_contracts.py`)
- Hybrid execution: deterministic Playwright for auth/critical steps + browser-use for selected deal/tracking automation

## Layers

**API Layer:**
- Purpose: Expose HTTP endpoints and validate request payloads
- Contains: `main.py` FastAPI app (`/`, `/health`, `/process-order`, `/test`)
- Depends on: `BrowserAgent`, `models.py`, logging utilities
- Used by: n8n/local callers

**Orchestration Layer:**
- Purpose: Route order/shipping flows and aggregate outcomes
- Contains: `BrowserAgent.process_email()` and routing helpers in `browser_agent.py`
- Depends on: Amazon scraper and ElectronicsBuyer agent
- Used by: API layer

**Automation Layer:**
- Purpose: Perform Amazon + EB browser tasks
- Contains: `amazon_scraper.py`, `electronics_buyer.py`, `electronics_buyer_llm.py`
- Depends on: Playwright, browser-use, Anthropic, stealth profile helpers
- Used by: Orchestration layer

**Contract/Model Layer:**
- Purpose: Enforce schema and semantic correctness of automation outcomes
- Contains: `models.py`, `eb_contracts.py`
- Depends on: Pydantic
- Used by: all runtime layers

**Operational Utility Layer:**
- Purpose: logging/env/bootstrap/runtime compatibility checks and process management
- Contains: `utils.py`, `runtime_checks.py`, `stealth_utils.py`, PM2 scripts/config
- Used by: automation and API layers

## Data Flow

**Order Confirmation Flow:**
1. n8n sends `POST /process-order` payload (`email_type=order_confirmation`)
2. FastAPI validates payload into `EmailData`
3. `BrowserAgent` chooses personal/business `AmazonScraper` via `account_type`
4. Amazon deterministic fallback scraper extracts order details
5. EB deal submission is intentionally skipped for this flow
6. `AgentResponse` returned with Amazon payload and execution metadata

**Shipping Confirmation Flow:**
1. n8n sends `POST /process-order` payload (`email_type=shipping_confirmation`)
2. `BrowserAgent` selects correct Amazon profile and scrapes tracking details
3. `ElectronicsBuyerAgent.submit_tracking()` runs deterministic auth + bounded retries
4. EB result warnings/errors merged into `AgentResponse`
5. Final response returned to caller

**State Management:**
- Request-level state in memory only
- Persistent auth/session state in local Chromium profile directories under `data/`
- Logs and optional utility state persisted to filesystem

## Key Abstractions

**Scraper/Agent Classes:**
- `AmazonScraper` - deterministic Amazon extraction with strict item-scope controls
- `ElectronicsBuyerAgent` - deterministic auth + submission guardrails
- `ElectronicsBuyerLLMExecutor` - constrained browser-use tasks with contract enforcement

**Result Contracts:**
- `OrderDetails`, `ShippingDetails`, `EBDealResult`, `EBTrackingResult`, `AgentResponse`
- `enforce_deal_contract()` applies success semantics and warning flags

## Entry Points

**HTTP Service:**
- Location: `main.py`
- Trigger: FastAPI/uvicorn startup
- Responsibilities: endpoint registration, request handling, error wrapping

**Manual/Diagnostic Entrypoints:**
- `test_scraper.py`, `test_debug.py`, `test_diagnose.py` for interactive automation diagnostics
- `manual_login.py` for profile priming by account mode

**Operations Entrypoints:**
- `scripts/services-up.sh`, `scripts/services-down.sh`, `scripts/services-status.sh`, `scripts/services-logs.sh`
- PM2 app bootstrap via `ecosystem.config.js`

## Error Handling

**Strategy:** Catch-and-wrap at orchestration/API boundaries, plus explicit semantic flags for EB outcomes.

**Patterns:**
- Broad `try/except` in `BrowserAgent.process_email()` returning structured failure responses
- EB flag-based error categorization (`FLAG_*`) in `electronics_buyer.py` and `eb_contracts.py`
- Fallback recovery for malformed LLM JSON output in `amazon_scraper.py` and `electronics_buyer_llm.py`

## Cross-Cutting Concerns

**Logging:**
- Central logger from `utils.py`, writes to file + stdout
- Step-level logs in scraper/agent flows for auditability

**Validation:**
- Pydantic validation on request/response payloads
- Additional semantic contract enforcement for deal outcomes

**Authentication:**
- In-browser auth flows with optional TOTP and OTP prompt gating
- Persistent browser profiles for session continuity

---

*Architecture analysis: 2026-02-17*
*Update when major patterns change*
