# Codex Handoff - Resume Work Context

## Snapshot

- **Date:** 2026-02-13
- **Project:** Amazon Email Automation
- **Repo:** `/Users/pinkpanther/Desktop/amazon-email-automation`
- **Branch:** `main`
- **State:** Project is already initialized. Do **not** run `/prompts:gsd-new-project` again.

## Source of Truth Files

Read these first when resuming:

1. `.planning/STATE.md`
2. `.planning/ROADMAP.md`
3. `.planning/PROJECT.md`
4. `.planning/phases/01-browser-automation-fix/01-01-SUMMARY.md`
5. `.planning/phases/01-browser-automation-fix/01-02-PLAN.md`
6. `.planning/codebase/` (all 7 mapped docs)

## What Is Done

- `.planning/codebase/` exists with:
  - `STACK.md`
  - `ARCHITECTURE.md`
  - `STRUCTURE.md`
  - `CONVENTIONS.md`
  - `TESTING.md`
  - `INTEGRATIONS.md`
  - `CONCERNS.md`
- Codebase map commit exists at `447c60d` (`docs: map existing codebase`).
- Phase `01-01` is completed and summarized in:
  - `.planning/phases/01-browser-automation-fix/01-01-SUMMARY.md`
- Additional `01-02` implementation commits exist in history:
  - `f0fe4a8`, `37fae7d`, `ca2eebc`, `6dff5eb`, `b61a113`

## Current Working Reality

- GSD planning docs still show Phase 1 / Plan 02 pending human verification.
- `test_scraper.py` exists and supports testing order/shipping flows.
- Browser/agent behavior was improved in prior commits, but acceptance is not yet formally closed in `.planning` (no `01-02-SUMMARY.md` present).
- A stale long-running server process on port `8080` was observed serving old code in memory. Restart is required after code changes.
- `browser_agent.py` now includes a placeholder guard that forces failure if payload contains `NEEDS_PARSING`/`TBD`.
- `amazon_scraper.py` now performs deterministic Playwright login/session priming before LLM extraction, so login is no longer left to model behavior.

## Immediate Next Task (Resume Path)

Execute **Phase 1 / Plan 02** acceptance exactly as the active plan expects:

0. Rebuild runtime on Python 3.14 (or current active Python >=3.11):
   - `./scripts/rebuild_py39_env.sh`
   - `source venv314/bin/activate`

1. Run a real verification:
   - `python test_scraper.py shipping <REAL_ORDER_NUMBER>`
   - Optionally also:
   - `python test_scraper.py order <REAL_ORDER_NUMBER>`
2. Confirm success criteria from `.planning/phases/01-browser-automation-fix/01-02-PLAN.md`:
   - Browser opens and stays active
   - Navigation reaches target Amazon page
   - Structured output returned (not placeholder text)
   - Debug artifacts generated under `logs/`
3. If verification fails:
   - Run `python test_debug.py <REAL_ORDER_NUMBER>`
   - Capture terminal errors plus:
     - `logs/agent.gif`
     - `logs/agent_conversations/`
4. After successful verification:
   - Create `.planning/phases/01-browser-automation-fix/01-02-SUMMARY.md`
   - Update `.planning/STATE.md` current position/progress
   - Update Phase 1 completion state in `.planning/ROADMAP.md`

## Mandatory Before Next Verification

Restart the API process so latest code is loaded:

```bash
# find current listener
lsof -nP -iTCP:8080 -sTCP:LISTEN

# stop stale process (example PID 2669)
kill <PID>

# start fresh server from this repo
source venv314/bin/activate
python main.py
```

## Environment Requirements (for next run)

- `.env` must include valid:
  - `ANTHROPIC_API_KEY`
  - `AMAZON_EMAIL`
  - `AMAZON_PASSWORD` (if prompt fallback is used)
  - `AMAZON_TOTP_SECRET` (optional, for automatic 2FA code entry)
  - `EB_USERNAME`
  - `EB_PASSWORD`
- Browser profile/session expected at:
  - `data/browser-profile/`

## Known Planning Drift to Keep in Mind

- `.planning/ROADMAP.md` progress table is stale vs recent execution commits.
- `.planning/STATE.md` last activity entry only reflects completion of `01-01`.
- Handoff and phase state should be aligned after Plan 02 verification completes.

## Recommended Command Sequence

```bash
cd /Users/pinkpanther/Desktop/amazon-email-automation
./scripts/rebuild_py39_env.sh
source venv314/bin/activate
python test_scraper.py shipping <REAL_ORDER_NUMBER>
# if needed:
python test_debug.py <REAL_ORDER_NUMBER>
```

Then continue via:

- `/prompts:gsd-progress`
- `/prompts:gsd-plan-phase 2` (only after Phase 1 is verified and documented complete)
