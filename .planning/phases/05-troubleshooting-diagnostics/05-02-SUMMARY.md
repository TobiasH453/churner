---
phase: 05-troubleshooting-diagnostics
plan: "02"
subsystem: infra
tags: [diagnostics, redaction, supportability, bash, logs]
requires:
  - phase: 05-troubleshooting-diagnostics
    provides: Canonical troubleshooting runbook and escalation entrypoint
provides:
  - Deterministic diagnostics collector script with bounded evidence capture
  - Redaction and exclusion enforcement for secret/session-safe support bundles
  - Operator docs updated with diagnostics collection and share workflow
affects: [phase-06 distribution-readiness, support workflows, verification]
tech-stack:
  added: []
  patterns: [timeout-guarded command capture, redaction-first artifact generation]
key-files:
  created: [scripts/collect-diagnostics.sh, .planning/phases/05-troubleshooting-diagnostics/05-02-SUMMARY.md]
  modified: [docs/TROUBLESHOOTING.md, docs/OPERATIONS.md, docs/INSTALL.md]
key-decisions:
  - "Use bounded per-command timeouts to prevent diagnostics hangs"
  - "Include explicit redaction probe + exclusion audit artifacts in each bundle"
patterns-established:
  - "Diagnostics bundle contract: commands/, logs/, system/, manifest.txt"
  - "Safe-by-default collection with redaction + forbidden path exclusions"
duration: 1 min
completed: 2026-03-06
---

# Phase 5 Plan 02: Diagnostics Collector Summary

**Redaction-safe diagnostics collector with deterministic bundle outputs and documented support escalation flow**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-06T22:01:47Z
- **Completed:** 2026-03-06T22:03:02Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Added `scripts/collect-diagnostics.sh` with deterministic output structure, bounded log capture, and non-interactive operation.
- Implemented redaction filtering and forbidden-path exclusion auditing to avoid raw secret/session leakage.
- Wired diagnostics usage and share-path guidance into troubleshooting, operations, and install docs.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create deterministic diagnostics collector entrypoint** - `f7aaaac` (feat)
2. **Task 2: Enforce redaction and exclusion rules** - `f8b6fa8` (fix)
3. **Task 3: Document diagnostics collection and escalation flow** - `9dbe5b0` (docs)

**Plan metadata:** pending (written in subsequent docs commit for this plan)

## Files Created/Modified
- `scripts/collect-diagnostics.sh` - One-command diagnostics collector with timeout-guarded captures, redaction filters, exclusion audit, and manifest output.
- `docs/TROUBLESHOOTING.md` - Added diagnostics escalation details, output contract, and support share instructions.
- `docs/OPERATIONS.md` - Added diagnostics escalation command in canonical operator flow.
- `docs/INSTALL.md` - Added diagnostics collection step for unresolved smoke failures.

## Decisions Made
- Avoid `services-logs.sh` in diagnostics capture path due potential blocking behavior; use direct PM2 log snapshots with timeouts.
- Keep diagnostics collection best-effort and completion-oriented (captures warnings/timeouts in artifacts instead of hard failing early).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Diagnostics collector stalled on log capture commands**
- **Found during:** Task 1 (collector implementation verification)
- **Issue:** service-log collection could hang and prevent bundle completion.
- **Fix:** Added timeout-guarded command execution and direct PM2 snapshot capture with bounded lines.
- **Files modified:** `scripts/collect-diagnostics.sh`
- **Verification:** Local collection run completes and writes manifest/log artifacts under timeout constraints.
- **Committed in:** `f7aaaac`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for deterministic collector behavior; no scope expansion.

## Issues Encountered

- Initial timeout handling interacted with shell `errexit` and caused early exits on timed-out commands. Resolved by controlling error handling only at capture-call boundaries.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 5 supportability deliverables are now present (runbook + diagnostics collector).
- Ready for phase-level verification and transition to Phase 6 planning/discussion.

---
*Phase: 05-troubleshooting-diagnostics*
*Completed: 2026-03-06*
