# Testing Patterns

**Analysis Date:** 2026-02-17

## Test Framework

**Runner:**
- Script-style Python tests executed directly (`python test_*.py`)
- No pytest/unittest discovery configuration present

**Assertion style:**
- Custom `_assert()` helpers raising `AssertionError`
- Contract semantics validated through source scanning, AST extraction, and behavior-level checks

**Run Commands:**
```bash
venv314/bin/python test_eb_deal_contract.py
venv314/bin/python test_eb_tracking_contract.py
venv314/bin/python test_amazon_tracking_number_extraction.py
venv314/bin/python test_scraper.py shipping 123-4567890-1234567 amz_business
```

## Test File Organization

**Location:**
- Root-level `test_*.py` files
- No separate `tests/` package directory currently

**Naming:**
- Contract tests: `test_<domain>_contract.py`
- Behavior/regression tests: `test_<domain>_<behavior>.py`
- Diagnostics/manual helpers: `test_debug.py`, `test_diagnose.py`, `test_scraper.py`

**Structure:**
- Most test files expose `main() -> int` and execute via `if __name__ == "__main__"`
- Individual checks grouped as sequential `_assert(...)` calls

## Test Structure

**Suite organization pattern:**
- Static source contract checks (presence/absence of key strings or functions)
- AST-based extraction of targeted methods for fast deterministic validation
- Limited runtime/manual flows for browser behavior observation

**Setup/teardown:**
- Minimal fixture lifecycle; tests are intentionally lightweight
- Environment load via `dotenv` in diagnostic scripts when browser/LLM interaction is needed

## Mocking

**Framework:**
- No dedicated mocking framework in current tests

**Patterns:**
- Instead of mocks, tests inspect source and method outputs with synthesized inputs
- AST extraction isolates single method logic without importing full runtime dependencies

**What is mocked/stubbed:**
- Effectively none through mocking libraries
- Runtime-heavy browser calls avoided in most contract tests

## Fixtures and Factories

**Test data approach:**
- Inline dictionaries/strings for expected behavior checks
- No dedicated fixtures directory or factory module

## Coverage

**Requirements:**
- No formal percentage target configured
- Coverage strategy is targeted regression protection for fragile automation semantics

**Tooling:**
- No coverage config/tool (`coverage.py`, `pytest-cov`) detected

## Test Types

**Contract tests (dominant):**
- Verify required flags, guardrails, selectors, and routing contracts remain present
- Example files: `test_eb_deal_contract.py`, `test_amazon_item_scope_contract.py`

**Unit-like method tests:**
- AST extraction + direct function invocation for parsing/normalization methods
- Example files: `test_amazon_shipping_date_normalization.py`, `test_amazon_tracking_number_extraction.py`

**Manual/integration diagnostics:**
- Browser+LLM exploratory scripts for debugging live automation failures
- Example files: `test_scraper.py`, `test_debug.py`, `test_diagnose.py`

## Common Patterns

**Fast-fail checks:**
- `PASS:` print statements on success, immediate assertion failures otherwise
- Source-string checks used to lock in operational guardrails

**Risk tradeoff:**
- Strong at preventing known regressions in fragile paths
- Weaker on full end-to-end automated integration due to external site dependencies

---

*Testing analysis: 2026-02-17*
*Update when test tooling or structure changes*
