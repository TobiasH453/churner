---
phase: 06-distribution-release-readiness
plan: "02"
subsystem: docs
tags: [release, readme, checklist, verification, docs-qa]
requires:
  - phase: 06-distribution-release-readiness
    plan: "01"
    provides: Release artifact naming, packaging command, and archive audit contract
provides:
  - Canonical first-run README for the download bundle
  - Strict release checklist with go/no-go blockers
  - Deterministic release docs QA helper
affects: [phase-06 release-readiness, operator onboarding, maintainer QA]
tech-stack:
  added: [bash]
  patterns: [README-as-front-door, checklist gate, docs command-surface verification]
key-files:
  created: [README.md, docs/RELEASE_CHECKLIST.md, scripts/verify-release-readiness.sh, .planning/phases/06-distribution-release-readiness/06-02-SUMMARY.md]
  modified: []
key-decisions:
  - "README.md is the canonical first-run document for the shipped bundle"
  - "Release checklist remains binary: failed command or missing artifact means no ship"
  - "Docs QA verifies command references against actual repository files and scripts"
patterns-established:
  - "Release docs gate: README + RELEASE.md + RELEASE_CHECKLIST.md + verify-release-readiness.sh"
duration: 5 min
completed: 2026-03-10
---

# Phase 6 Plan 02: Release Checklist and Docs QA Summary

**Canonical release-facing README, strict go/no-go checklist, and one-command docs/readiness verification**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T20:28:40Z
- **Completed:** 2026-03-10T20:33:30Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Replaced the minimal README with a release-facing front door that starts with prerequisites, included files, user-provided inputs, and the exact first-run command sequence.
- Added `docs/RELEASE_CHECKLIST.md` with strict version/date tracking and explicit `NO SHIP` blockers.
- Added `scripts/verify-release-readiness.sh` to validate release docs, command references, required files, and optional archive audit in one command.

## Verification Run

Executed and passed:
- `bash -n scripts/verify-release-readiness.sh`
- `rm -rf /tmp/phase6-release && bash scripts/build-release-bundle.sh --version v1.0.0 --output-dir /tmp/phase6-release`
- `bash scripts/verify-release-readiness.sh --archive /tmp/phase6-release/1step-cashouts-v1.0.0-macos-apple-silicon.zip`

## Task Commits

1. **Task 1: Make `README.md` the canonical first-run release path** - `85d59a2` (`chore`)
2. **Task 2: Create a strict release checklist with hard blockers** - `fa9c55f` (`chore`)
3. **Task 3: Add release docs QA automation tied to the real command surface** - `be53f60` (`test`)

**Plan metadata:** written in subsequent docs commit for this plan

## Files Created/Modified

- `README.md` - Canonical release-facing operator flow with prerequisites, included bundle contents, local inputs, and exact command order.
- `docs/RELEASE_CHECKLIST.md` - Versioned go/no-go release gate covering artifact integrity plus install/run/verify/diagnostics flow.
- `scripts/verify-release-readiness.sh` - Deterministic release docs QA helper with optional archive audit.

## Deviations from Plan

None.

## Next Phase Readiness

- Phase 6 now has its user-facing release docs and maintainer QA gate.
- The phase can move to must-have verification and completion updates.

---
*Phase: 06-distribution-release-readiness*
*Completed: 2026-03-10*
