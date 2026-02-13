# Coding Conventions

**Analysis Date:** 2026-02-13

## Naming Patterns

**Classes and Models:**
- PascalCase is consistent for major classes (`BrowserAgent`, `AmazonScraper`, `ElectronicsBuyerAgent`) and Pydantic models (`EmailData`, `AgentResponse`).

**Functions and Methods:**
- snake_case for regular functions and methods (`process_email`, `scrape_order_confirmation`, `create_stealth_profile`).
- Internal helpers use leading underscore (`_process_order_confirmation`, `_find_chromium_executable`).

**Files and Variables:**
- snake_case module filenames (`amazon_scraper.py`, `manual_login.py`).
- Env vars in uppercase snake case and accessed centrally via `get_env()`.

## Code Style

- Type hints are used broadly, especially in orchestration and model boundaries.
- Docstrings are present for classes and many functions, mostly concise and task-focused.
- Async/await is used for browser and API workflows end-to-end.
- F-strings are the standard string formatting style.

## Import Organization

- Imports are mostly grouped as: stdlib -> third-party -> local modules.
- Some files include light deviations (e.g., mixed import ordering in test scripts), but style remains readable.
- No dedicated import formatter/linter config detected.

## Error Handling

- Boundary-level broad exception handling is common (`main.py`, `browser_agent.py`).
- Agent wrappers enforce structured-output presence and raise explicit runtime errors when missing.
- Cleanup is explicit with `finally: await agent.close()` around browser agents.

## Logging

- Shared logger from `utils.py` is reused across modules.
- Logs combine informational workflow checkpoints with full exception traces (`exc_info=True`).
- File + stdout dual handlers are configured in `utils.py`.

## Comments

- Comments are sparse and pragmatic, typically used for non-obvious runtime constraints (timeouts, anti-detection args, browser profile behavior).
- Large inline prompt strings in scraper modules are self-explanatory and act as executable guidance.

## Function Design

- Public methods are task-oriented and coarse-grained (one method per workflow stage).
- Core orchestration functions return typed Pydantic models instead of raw dicts.
- Helper utility functions are mostly pure I/O wrappers (`save_cookies`, `load_cookies`, `save_state`, `get_state`).

## Module Design

- Responsibility boundaries are mostly clear:
- `main.py`: transport boundary
- `browser_agent.py`: orchestration
- `amazon_scraper.py` / `electronics_buyer.py`: external site adapters
- `models.py`: schema contracts
- `utils.py` / `stealth_utils.py`: shared runtime helpers
- Codebase favors a small-module monolith over package-heavy structure.

## GSD Context Additions

**Documentation Conventions in Active Use:**
- Project and phase control follows explicit markdown artifacts under `.planning/` rather than inline code comments.
- Operational guidance emphasizes beginner-safe, copy/paste command style (`docs/QUICKSTART.md`, `IMPLEMENTATION_PLAN.md`).

**Behavioral Convention:**
- Runtime debugging leans on observable artifacts (`logs/*.gif`, `logs/*conversation*.json`) and manual verification scripts rather than assertion-heavy automated tests.

---

*Conventions analysis: 2026-02-13*
*Update when linting/formatting policy changes or module boundaries are refactored*
