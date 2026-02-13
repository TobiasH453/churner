# External Integrations

**Analysis Date:** 2026-02-13

## APIs & External Services

**Inbound Trigger:**
- n8n calls `POST /process-order` in `main.py` with normalized email payloads (`EmailData`).

**LLM Provider:**
- Anthropic Claude via `langchain_anthropic.ChatAnthropic` in `amazon_scraper.py` and `electronics_buyer.py`.
- Model currently pinned to `claude-sonnet-4-5-20250929`.

**Browser Targets:**
- Amazon order/invoice pages (`https://www.amazon.com/...`) for extraction (`amazon_scraper.py`).
- ElectronicsBuyer pages (`https://electronicsbuyer.gg/app/deals`, `https://electronicsbuyer.gg/app/tracking-submissions`) for submission (`electronics_buyer.py`).

## Data Storage

**Local Persistent Storage:**
- Browser session profile in `data/browser-profile/` (Playwright persistent context).
- Optional cookie/state helpers in `utils.py` writing under `data/`.

**Logs and Artifacts:**
- Text logs via Python logging to `logs/agent.log` and stdout (`utils.py`).
- Visual/debug artifacts: `logs/agent.gif`, `logs/eb_agent.gif`, `logs/diagnose.gif`.
- Conversation traces: `logs/agent_conversation.json`, `logs/eb_agent_conversation.json`.

## Authentication & Identity

**Credential Sources:**
- `.env` keys: `ANTHROPIC_API_KEY`, `AMAZON_EMAIL`, `AMAZON_PASSWORD`, `EB_USERNAME`, `EB_PASSWORD`.

**Session Strategy:**
- Primary auth method is persistent browser profile (`data/browser-profile`) created/maintained with `manual_login.py`.
- Amazon login steps are also embedded in the LLM task prompt as fallback (`amazon_scraper.py`).

## Monitoring & Observability

**Current Signals:**
- Structured app logs through `logger` from `utils.py`.
- Endpoint-level logs in `main.py` and orchestration-level logs in `browser_agent.py`.
- Debug replay assets from browser-use agents (GIF + conversation JSON).

**Gaps:**
- No centralized metrics, tracing, alerting, or health history.

## CI/CD & Deployment

- No CI pipeline definitions detected.
- No container/deployment manifests detected.
- Expected execution is local/manual service lifecycle.

## Environment Configuration

**Configuration Model:**
- `.env` + runtime defaults in code.
- `get_env()` enforces required values when no default is provided (`utils.py`).

**Notable Runtime Params:**
- Server binding from `SERVER_PORT` (`main.py`).
- Timeout behavior partly configured through environment defaults in scraper modules.

## Webhooks & Callbacks

**Inbound Webhook:**
- `POST /process-order` in `main.py` receives order/shipping events and returns `AgentResponse`.

**Outbound Callback Pattern:**
- No direct webhook callbacks from this service.
- Response body is synchronous and expected to be consumed by n8n HTTP Request node.

## GSD Context Additions

**Documented Integration Targets (existing planning context):**
- Gmail trigger and Claude-based email qualification/categorization are specified in `CLAUDE.md` and `IMPLEMENTATION_PLAN.md`.
- Google Sheets row append/update behavior is specified in `.planning/PROJECT.md` and `CLAUDE.md`.
- Telegram success/error notifications are specified in `.planning/PROJECT.md` and `CLAUDE.md`.

**Implementation Status Snapshot:**
- Inbound webhook integration from n8n to FastAPI is present.
- Google Sheets and Telegram outbound integrations are planned but not present in current Python code paths.

---

*Integrations analysis: 2026-02-13*
*Update when external services, auth flow, or webhook contracts change*
