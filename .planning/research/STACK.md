# Stack Research

**Domain:** Local macOS automation productization (n8n + Python browser automation), subsequent milestone
**Researched:** 2026-02-17
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| n8n | 2.7.x | Email workflow orchestration and webhook trigger | Official docs define supported Node/runtime matrix and this is the cleanest no-code handoff layer for non-technical operators. (Confidence: HIGH) |
| Python | 3.12 or 3.13 | Runtime for FastAPI + Playwright + browser-use integration | Keeps compatibility with current dependencies while avoiding known project warnings seen on 3.14+ for browser-use stack. (Confidence: HIGH, project-specific) |
| FastAPI | 0.129.x | Local API boundary for order/shipping processing | Stable typed API boundary already in place; current package line supports modern Python and Pydantic v2. (Confidence: HIGH) |
| Playwright (Python) | 1.58.x | Deterministic browser automation against Amazon/EB | Required for controlled auth/navigation and robust fallback extraction. (Confidence: HIGH) |
| browser-use | 0.11.x | Constrained LLM browser actions where deterministic selectors are costly | Keeps hard parts deterministic while preserving flexibility for deal-matching steps. (Confidence: MEDIUM-HIGH) |
| PM2 | 6.0.x | Local process supervision for API + n8n | Existing operational model already uses PM2; keeps start/stop/status simple for semi-technical users. (Confidence: HIGH) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.x | Request/response contracts and semantic result schemas | Always; this is the safety boundary for automation output correctness |
| python-dotenv | 1.x | Local secret/env loading | Always for `.env` template driven setup |
| pyotp | 2.x | Optional TOTP support for Amazon auth flow | When user configures MFA secret for auto-entry |
| shellcheck | latest | Validate installer shell scripts | During CI/pre-ship checks for `install.sh` and service scripts |
| shfmt | latest | Deterministic shell formatting | During CI/pre-ship checks for predictable script maintenance |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `venv` + `pip` | Python environment bootstrap | Lowest-friction for macOS semi-technical setup, easy to explain in docs |
| PM2 ecosystem file | Multi-service runtime management | Existing `ecosystem.config.js` should remain the single source of process config |
| Contract tests + smoke test runner | Ship-gate verification | Keep source-level contracts, add post-install smoke command for end-to-end proof |

## Installation

```bash
# Core runtime prerequisites (macOS)
brew install node@22
brew install python@3.13
npm install -g pm2

# Python env
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# Runtime services
pm2 start ecosystem.config.js --update-env
pm2 save
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PM2 service management | `launchd` plists only | Use `launchd` when PM2 global install is blocked by local policy |
| `venv` + pip installer | `uv` managed Python environments | Use `uv` when you want faster deterministic env provisioning and team is comfortable with it |
| Manual n8n import guide | scripted n8n API import flow | Use API import only after auth/token handling is standardized for your operators |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Shipping browser profile directories in bundles | Leaks session/auth state and creates brittle machine-bound installs | Generate local profiles post-install via guided login |
| Auto-writing real secrets into repo-managed files | High accidental secret exposure risk | `.env.example` + interactive/local `.env` creation and validation |
| Cross-platform installer in v1 | Increases branching and support surface before ship criteria are met | macOS-first hardened installer, then platform expansion |

## Stack Patterns by Variant

**If operator is semi-technical and local-only:**
- Use `install.sh` + `services-up.sh` + smoke test command
- Because this minimizes setup ambiguity while keeping user control

**If operator is more technical and wants quick bootstrap:**
- Add optional one-liner wrapper that downloads and executes `install.sh`
- Because it speeds setup without replacing the audited installer path

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| n8n 2.7.x | Node.js 20.19+, 22.12+, 24.0+ | Use Node 22 LTS branch for v1 stability |
| FastAPI 0.129.x | Python >=3.10 | Python 3.12/3.13 recommended for this project's dependency mix |
| Playwright 1.58.x | Python >=3.9 | Ensure `python -m playwright install chromium` is run during install |
| browser-use 0.11.x | Python >=3.11 | Keep runtime check + pinning due rapid upstream changes |

## Sources

- https://docs.n8n.io/hosting/installation/npm/ (official Node.js compatibility for n8n)
- https://docs.n8n.io/workflows/export-import/ (official workflow export/import flow)
- https://pypi.org/project/fastapi/ (current FastAPI release line)
- https://pypi.org/project/playwright/ (current Playwright Python release line)
- https://pypi.org/project/browser-use/ (current browser-use release line and Python requirement)
- https://www.npmjs.com/package/pm2 (current PM2 release line)

---
*Stack research for: local automation productization (subsequent milestone)*
*Researched: 2026-02-17*
