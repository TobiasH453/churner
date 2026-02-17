# External Integrations

**Analysis Date:** 2026-02-17

## APIs & External Services

**Amazon (website automation):**
- Service: Amazon consumer + Amazon Business web flows
  - Integration method: Browser automation via Playwright persistent contexts (`amazon_scraper.py`)
  - Auth: `AMAZON_EMAIL` / `AMAZON_PASSWORD` and `AMAZON_BUSINESS_EMAIL` / `AMAZON_BUSINESS_PASSWORD`
  - Optional MFA: `AMAZON_TOTP_SECRET` and `AMAZON_BUSINESS_TOTP_SECRET`
  - Key URLs: order details, print summary, tracking pages

**ElectronicsBuyer.gg:**
- Service: deal submission + tracking submission workflow
  - Integration method: deterministic Playwright auth flow in `electronics_buyer.py` plus browser-use LLM execution in `electronics_buyer_llm.py`
  - Auth: email-login + OTP gate in web app (`/app/login`) with interactive code entry path
  - Endpoints used: `/app/deals`, `/app/tracking-submissions`

**Anthropic API:**
- Service: Claude model used by browser-use agents
  - SDK/Client: `browser_use.llm.ChatAnthropic`
  - Auth: `ANTHROPIC_API_KEY`
  - Usage: constrained task prompts for EB deal/tracking execution and historical scraper recovery paths

**n8n local workflow engine:**
- Service: upstream orchestration and webhook sender
  - Integration method: HTTP POST to FastAPI `/process-order`
  - Runtime target: local `n8n` process managed via PM2 (`http://localhost:5678`)

## Data Storage

**Databases:**
- None in repository (no SQL/NoSQL client usage in runtime flow)

**File Storage (local filesystem):**
- Browser sessions: `data/browser-profile/`, `data/browser-profile-personal/`, `data/browser-profile-business/`
- Logs: `logs/` plus PM2 logs (`logs/pm2-*.log`)
- Optional state blobs: `data/state.json`, `data/cookies.json` (utility helpers)

**Caching:**
- No dedicated cache service (Redis/Memcached not present)
- Browser profile snapshot caching in temp directories via `stealth_utils.py`

## Authentication & Identity

**Auth Provider:**
- Amazon account auth handled in-browser by deterministic selectors and optional TOTP
- ElectronicsBuyer auth handled in-browser; OTP may require terminal interaction

**OAuth Integrations:**
- None implemented in codebase

## Monitoring & Observability

**Error Tracking:**
- No third-party APM/exception tracker configured (Sentry/Datadog absent)

**Logs:**
- Python logging via `logging` module to `logs/agent.log` and stdout (`utils.py`)
- PM2 process logs configured in `ecosystem.config.js`

## CI/CD & Deployment

**Hosting:**
- Local/self-hosted service model with PM2
- No cloud deployment manifests in repo

**CI Pipeline:**
- No GitHub Actions or CI config files detected
- Tests appear to be run manually via direct Python execution

## Environment Configuration

**Development:**
- Secrets in `.env` (gitignored expected)
- Requires valid Anthropic key and account credentials for Amazon + EB flows
- Uses persistent local Chromium profiles to reduce repeated login friction

**Staging:**
- No separate staging environment configuration found

**Production:**
- Operations documented in `docs/OPERATIONS.md`
- Resilience primarily via PM2 autorestart and persistent browser profiles

## Webhooks & Callbacks

**Incoming:**
- `POST /process-order` in `main.py`
  - Source: n8n
  - Payload model: `EmailData` from `models.py`

**Outgoing:**
- Browser-driven interactions to Amazon and ElectronicsBuyer web UIs
- No server-to-server webhook posts implemented by this app layer

---

*Integration audit: 2026-02-17*
*Update when adding/removing external services*
