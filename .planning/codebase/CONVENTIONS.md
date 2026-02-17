# Coding Conventions

**Analysis Date:** 2026-02-17

## Naming Patterns

**Files:**
- Python modules use `snake_case.py` (`amazon_scraper.py`, `electronics_buyer_llm.py`)
- Test scripts use `test_*.py` naming (`test_eb_deal_contract.py`)
- No package submodule export barrels; modules are imported directly

**Functions:**
- `snake_case` for function/method names
- Async methods prefixed by behavior, not `async_` (e.g., `submit_tracking`, `_wait_for_any_selector`)
- Helper methods often start with `_` for internal scope

**Variables:**
- locals/instance fields use `snake_case`
- constants use `UPPER_SNAKE_CASE` (e.g., `EB_DEALS_URL`, `FLAG_DEAL_TIMEOUT`)
- selector collections defined as class constants for reuse

**Types/Models:**
- Pydantic model classes in `PascalCase` (`EmailData`, `EBTrackingResult`)
- union hints use Python 3.10+ `|` syntax

## Code Style

**Formatting:**
- 4-space indentation, no formatter config file detected
- Mixed quote style but mostly single quotes in automation files
- Type hints used heavily in core runtime modules
- Docstrings present for major classes/functions and many test files

**Linting:**
- No lint config (`ruff`, `flake8`, `pylint`) found in repo root
- Style enforcement appears convention/manual-review based

## Import Organization

**Order pattern observed:**
1. Standard library imports
2. Third-party imports
3. Local project imports

**Grouping:**
- Typically grouped with blank lines between import classes
- No enforced alphabetical import tooling detected

## Error Handling

**Patterns:**
- Catch exceptions at workflow boundaries and return structured failure models
- Use explicit flagged error messages (`FLAG_*`) to encode machine-readable failure categories
- Use bounded retries for fragile browser actions (e.g., tracking submission retry once)

**Error types:**
- Runtime errors for missing env/auth requirements
- Contract functions normalize inconsistent LLM outputs before returning success
- API layer converts unexpected exceptions to HTTP 500

## Logging

**Framework:**
- Python `logging` with file + console handlers configured in `utils.py`
- Service-level logs include operational step messages and errors with traceback when needed

**Patterns:**
- `logger.info` around state transitions and major steps
- `logger.warning` for recoverable drift/unknown state
- `logger.error(..., exc_info=True)` for failure diagnostics

## Comments

**When used:**
- Explanation for fragile selector behavior or anti-detection choices
- Runtime safeguards and fallback intent
- Practical operational notes in scripts/docs

**TODO style:**
- No strong TODO tagging convention observed
- Work is mainly guarded by explicit contract tests instead of TODO markers

## Function Design

**Size:**
- Core automation modules include long methods; helper extraction used where flakiness requires localized logic
- Private helper methods encapsulate selector checks, field resolution, and classification

**Parameters/Returns:**
- Strong preference for explicit return models (`EBTrackingResult`, `OrderDetails`)
- Tuple returns used for readiness/classification helpers where lightweight status transport is needed

## Module Design

**Exports:**
- One primary class per module pattern in runtime files (`AmazonScraper`, `ElectronicsBuyerAgent`)
- Shared constants and helpers colocated with owning module

**Boundaries:**
- `models.py` and `eb_contracts.py` form stability boundaries for schema and semantics
- `browser_agent.py` centralizes high-level flow decisions and result shaping

---

*Convention analysis: 2026-02-17*
*Update when patterns change*
