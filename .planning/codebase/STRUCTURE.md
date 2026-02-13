# Codebase Structure

**Analysis Date:** 2026-02-13

## Directory Layout

```text
.
|- main.py
|- browser_agent.py
|- amazon_scraper.py
|- electronics_buyer.py
|- models.py
|- utils.py
|- stealth_utils.py
|- manual_login.py
|- test_scraper.py
|- test_debug.py
|- test_diagnose.py
|- requirements.txt
|- docs/
|- prompts/
|- get-shit-done/
|- .planning/
|- data/
|- logs/
|- n8n-workflows/
|- venv/
```

## Directory Purposes

- `.planning/`: active project docs (project context, roadmap/state, and phase plans/summaries).
- `.planning/phases/`: plan execution artifacts by phase (`01-browser-automation-fix/...`).
- `.planning/research/`: ecosystem research notes.
- `docs/`: beginner-oriented operational docs (`docs/QUICKSTART.md`).
- `get-shit-done/`: reusable workflow/templates/reference library powering GSD prompts.
- `prompts/`: command prompt entry files (`prompts/gsd-*.md`).
- `data/`: local persistent runtime state (currently `data/browser-profile/`).
- `logs/`: runtime/debug outputs from API and browser agents.
- `n8n-workflows/`: placeholder for exported workflow JSON.

## Key File Locations

**Runtime API + Orchestration:**
- `main.py` - FastAPI routes and process startup.
- `browser_agent.py` - branch routing for order/shipping handling.

**Website Automation:**
- `amazon_scraper.py` - Amazon extraction tasks.
- `electronics_buyer.py` - ElectronicsBuyer submission tasks.
- `stealth_utils.py` - browser profile/executable selection logic.
- `manual_login.py` - manual session bootstrap utility.

**Contracts + Utilities:**
- `models.py` - all Pydantic request/response models.
- `utils.py` - env loading, logging config, and lightweight local persistence helpers.

**Testing/Diagnostics:**
- `test_scraper.py` - main smoke test for order/shipping scraping.
- `test_debug.py` - debug logging focused probe.
- `test_diagnose.py` - no-schema visual diagnosis helper.

**Planning Framework:**
- `get-shit-done/workflows/*.md` - workflow logic.
- `get-shit-done/templates/codebase/*.md` - templates for codebase docs.

## Naming Conventions

- Snake_case for Python modules and functions (`browser_agent.py`, `scrape_shipping_confirmation`).
- PascalCase for classes/models (`BrowserAgent`, `OrderDetails`).
- Environment variable names are uppercase snake case (`ANTHROPIC_API_KEY`).
- Test helpers use `test_*.py` prefix but behave as executable scripts.

## Where to Add New Code

- New API endpoints: `main.py` (or split to dedicated route modules if API grows).
- New orchestration branch logic: `browser_agent.py`.
- New external site automation adapter: add module parallel to `amazon_scraper.py` / `electronics_buyer.py`.
- New shared data contracts: `models.py`.
- New operational helpers/utilities: `utils.py` or focused helper module.
- New automated tests: convert/add under a dedicated `tests/` directory (currently absent).

## Special Directories

- `data/browser-profile/`: required for persistent browser-auth sessions.
- `logs/`: contains GIF and JSON traces useful for post-failure inspection.
- `venv/`: local virtual environment (not source-controlled).
- `.git/`: repository metadata.

## GSD Context Additions

**Planning/Execution Artifacts:**
- `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` are active control files for ongoing work sequencing.
- `.planning/phases/01-browser-automation-fix/` contains active PLAN/SUMMARY execution artifacts tied to current implementation state.
- `prompts/gsd-*.md` and `get-shit-done/workflows/*.md` are operational command/workflow assets used to drive iterative changes.

---

*Structure analysis: 2026-02-13*
*Update after directory moves, new top-level modules, or test layout changes*
