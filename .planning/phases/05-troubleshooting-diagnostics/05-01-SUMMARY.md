---
phase: 05-troubleshooting-diagnostics
plan: "01"
subsystem: docs
tags: [troubleshooting, runbook, operations, smoke, n8n]
requires:
  - phase: 04-smoke-verification-harness
    provides: Smoke verification command contract and failure cues
provides:
  - Canonical troubleshooting runbook covering install/runtime/n8n/smoke failures
  - Command-first recovery flows with explicit success cues
  - Cross-linked handoff from install/operations/runtime/smoke docs
affects: [05-02 diagnostics collector, supportability, operator-runbooks]
tech-stack:
  added: []
  patterns: [command-first troubleshooting, symptom-signal-action triage]
key-files:
  created: [docs/TROUBLESHOOTING.md]
  modified: [docs/INSTALL.md, docs/OPERATIONS.md, docs/RUNTIME_VALIDATION.md, docs/SMOKE_VERIFICATION.md]
key-decisions:
  - "Use docs/TROUBLESHOOTING.md as canonical recovery source across all operator docs"
  - "Keep remediation command-first with explicit pass/fail cues and rerun commands"
patterns-established:
  - "Single-source troubleshooting handoff across install/runtime/n8n/smoke docs"
  - "Guided flow format: symptom -> commands -> success cue -> next"
duration: 1 min
completed: 2026-03-06
---

# Phase 5 Plan 01: Troubleshooting Runbook Summary

**Canonical troubleshooting runbook with command-first recovery for install/runtime/n8n/smoke failures and unified doc handoffs**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-06T21:54:57Z
- **Completed:** 2026-03-06T21:55:59Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added `docs/TROUBLESHOOTING.md` as the canonical support runbook with a failure-mode matrix.
- Added deterministic guided recovery flows for runtime status, n8n contract, and smoke verification failures.
- Updated install/operations/runtime/smoke docs to route unresolved failures to one canonical troubleshooting path.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build a failure-mode catalog from existing operator surfaces** - `38851cd` (docs)
2. **Task 2: Add command-first guided recovery flows for non-technical operators** - `80e60b9` (docs)
3. **Task 3: Wire troubleshooting handoff into existing docs** - `9d0033e` (docs)

**Plan metadata:** pending (written in subsequent docs commit for this plan)

## Files Created/Modified
- `docs/TROUBLESHOOTING.md` - Canonical troubleshooting matrix and guided recovery flows.
- `docs/INSTALL.md` - Failure handoff now points to canonical troubleshooting runbook.
- `docs/OPERATIONS.md` - Runtime and n8n recovery sections now route unresolved issues to troubleshooting runbook.
- `docs/RUNTIME_VALIDATION.md` - Failure routes include troubleshooting runbook; smoke success cue corrected to current script output.
- `docs/SMOKE_VERIFICATION.md` - Full remediation references include troubleshooting runbook.

## Decisions Made
- Use a single troubleshooting source (`docs/TROUBLESHOOTING.md`) to prevent divergent remediation guidance across docs.
- Keep flows strictly command-first and cue-based to support non-technical operators.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan `05-02` can now implement diagnostics collection and plug into the runbook escalation path.
- No blockers.

---
*Phase: 05-troubleshooting-diagnostics*
*Completed: 2026-03-06*
