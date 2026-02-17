# Codebase Structure

**Analysis Date:** 2026-02-17

## Directory Layout

```
amazon-email-automation ship/
├── amazon_scraper.py                # Amazon deterministic scraping logic
├── browser_agent.py                 # Top-level orchestration router
├── electronics_buyer.py             # EB deterministic auth + tracking/deal gateways
├── electronics_buyer_llm.py         # EB browser-use constrained executor
├── main.py                          # FastAPI service entrypoint
├── models.py                        # Pydantic domain contracts
├── eb_contracts.py                  # Deal-result semantic contract enforcement
├── utils.py                         # env loading + shared logger + local state helpers
├── stealth_utils.py                 # Playwright/browser-use stealth profile helpers
├── runtime_checks.py                # runtime compatibility warnings
├── scripts/                         # PM2 operations helpers
├── docs/                            # runbook and operational docs
├── data/                            # persistent browser profiles and local state
├── logs/                            # runtime and PM2 logs
├── n8n-workflows/                   # exported n8n artifacts (currently empty)
├── requirements.txt                 # Python dependencies
├── ecosystem.config.js              # PM2 app definitions
└── test_*.py                        # script-style regression/contract tests
```

## Directory Purposes

**`scripts/`:**
- Purpose: service lifecycle and environment utilities
- Contains: `services-up.sh`, `services-down.sh`, `services-status.sh`, `services-logs.sh`, `rebuild_py39_env.sh`
- Key files: PM2 start/stop/status wrappers

**`docs/`:**
- Purpose: operations documentation
- Contains: `OPERATIONS.md`
- Key files: runbook for startup, recovery, and persistence safety

**`data/`:**
- Purpose: persistent browser profiles/session state
- Contains: `browser-profile/`, `browser-profile-personal/`, `browser-profile-business/`
- Key behavior: deleting these forces re-authentication

**`logs/`:**
- Purpose: runtime logs and PM2 output/error files
- Contains: `agent.log`, `pm2-*.log`, generated gif/conversation artifacts

## Key File Locations

**Entry Points:**
- `main.py` - FastAPI application entrypoint
- `manual_login.py` - manual profile login utility

**Configuration:**
- `.env` - runtime secrets/environment
- `requirements.txt` - Python dependency manifest
- `ecosystem.config.js` - PM2 runtime config

**Core Logic:**
- `browser_agent.py` - orchestrates email type flows
- `amazon_scraper.py` - Amazon extraction and fallback logic
- `electronics_buyer.py` - deterministic EB auth + submit wrappers
- `electronics_buyer_llm.py` - constrained browser-use deal/tracking tasks

**Testing:**
- `test_*.py` at repository root (contract + diagnostic scripts)

**Documentation:**
- `README.md` - service overview and quickstart
- `docs/OPERATIONS.md` - operational runbook

## Naming Conventions

**Files:**
- Python modules use `snake_case.py`
- Test scripts follow `test_*.py`
- Markdown docs use uppercase canonical names in `.planning/codebase/*.md`

**Directories:**
- lowercase with hyphen or simple words (`docs`, `scripts`, `n8n-workflows`)

**Special Patterns:**
- Root-level operational scripts instead of nested package layout
- Browser profile directories treated as runtime state, not source code

## Where to Add New Code

**New API endpoint:**
- Implementation: `main.py`
- Orchestration logic: `browser_agent.py`
- Contracts: `models.py`
- Tests: add `test_<feature>_contract.py` at root

**New Amazon extraction rule:**
- Primary implementation: `amazon_scraper.py`
- Regression checks: add/extend static or AST contract tests

**New EB flow safeguards:**
- Deterministic safeguards: `electronics_buyer.py`
- LLM task constraints: `electronics_buyer_llm.py`
- Semantic result checks: `eb_contracts.py`

**Operational changes:**
- Process settings: `ecosystem.config.js`
- Commands/runbook: `scripts/` and `docs/OPERATIONS.md`

## Special Directories

**`venv/`, `venv39/`, `venv314/`:**
- Purpose: local Python virtual environments
- Source: manually created by scripts
- Committed: no (environment artifacts)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Source: runtime generated
- Committed: no

---

*Structure analysis: 2026-02-17*
*Update when directory structure changes*
