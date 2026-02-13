# Testing Patterns

**Analysis Date:** 2026-02-13

## Test Framework

**Current State:**
- No formal unit/integration test framework (no `pytest`, `unittest` suites, or `tests/` package).
- Validation currently relies on executable diagnostic scripts against live systems.

**Active Test Scripts:**
- `test_scraper.py` - primary smoke test for order and shipping extraction with structured output.
- `test_debug.py` - DEBUG-level browser-use trace helper for diagnosing agent failures.
- `test_diagnose.py` - visual page-state diagnosis without structured schema constraints.

## Test File Organization

- Test scripts are top-level files adjacent to production modules.
- Naming follows `test_*.py`, but they are CLI tools rather than automated suite files.
- No shared testing utilities directory.

## Test Structure

- Async `main()` pattern with direct invocation via `asyncio.run(...)`.
- Runtime configuration loaded via `.env` in each script.
- Scripts print operator-facing status and artifact locations to terminal.
- Pass/fail semantics are manual (human reads output and debug artifacts).

## Mocking

- No mocking framework usage detected.
- Tests hit real external dependencies: Anthropic API, Amazon pages, and local Chromium profile.
- Failure modes include network/session instability and live-site UI changes.

## Fixtures and Factories

- No reusable fixture/factory layer.
- Test input is provided interactively or via CLI args (order number + mode).
- Persistent session state in `data/browser-profile` effectively acts as an implicit runtime fixture.

## Coverage

- No code coverage tooling or reports.
- Coverage is unknown and likely low for utility/error branches.
- Current scripts primarily validate happy-path runtime behavior.

## Test Types

**Smoke / End-to-End-ish:**
- `test_scraper.py` verifies agent can navigate, extract, and return typed output.

**Diagnostics:**
- `test_debug.py` and `test_diagnose.py` are troubleshooting utilities, not regression guards.

**Missing Types:**
- Unit tests for transformation/validation logic.
- Contract tests for webhook payload handling.
- Integration tests with controlled stubs for external services.

## Common Patterns

- Manual execution from virtualenv (e.g., `venv/bin/python3 test_scraper.py shipping <order>`).
- Debugging through generated artifacts in `logs/` (GIF + conversation JSON).
- Operator-in-the-loop intervention for auth/2FA via `manual_login.py`.

## GSD Context Additions

**Planned Verification Flow (from workflows):**
- `get-shit-done/workflows/verify-work.md` and phase verification workflows indicate a UAT-oriented acceptance layer on top of code execution.
- `.planning/phases/*/*-SUMMARY.md` acts as a historical verification artifact after each plan.

**Current Gap vs Planned Process:**
- Workflow-level verification docs exist, but automated Python test harnessing (unit/integration suite) is not yet established.

---

*Testing analysis: 2026-02-13*
*Update when formal automated test framework is introduced*
