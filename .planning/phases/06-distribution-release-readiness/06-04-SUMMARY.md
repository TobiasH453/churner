---
phase: 06-distribution-release-readiness
plan: "04"
subsystem: release-integrity
tags: [release, reproducibility, git, metadata, audit]
requires:
  - phase: 06-distribution-release-readiness
    plan: "03"
    provides: Stable first-run contract across installer and docs
provides:
  - Release builder tied to committed source state
  - Readiness gate that checks committed required inputs and archive integrity
  - Normalized milestone metadata after audit gap closure
affects: [phase-06 release-readiness, packaging trust, planning metadata]
tech-stack:
  added: [bash, git]
  patterns: [HEAD-backed packaging, committed-input verification, metadata normalization]
key-files:
  created: [main.py, manual_login.py, .planning/phases/06-distribution-release-readiness/06-04-SUMMARY.md]
  modified: [scripts/build-release-bundle.sh, scripts/verify-release-readiness.sh, docs/RELEASE.md, .planning/REQUIREMENTS.md, .planning/PROJECT.md, .planning/STATE.md, .planning/phases/01-installer-secure-bootstrap/01-UAT.md]
key-decisions:
  - "Required release inputs must exist in committed repository state"
  - "Release bundles are built from committed HEAD contents so unrelated dirty worktree changes are not shipped"
  - "Stale milestone metadata is normalized once the release gate is trustworthy again"
patterns-established:
  - "Committed-source packaging gate: verify tracked inputs, build archive from HEAD, audit resulting zip"
duration: 14 min
completed: 2026-03-10
---

# Phase 6 Plan 04: Release Reproducibility and Metadata Summary

**Release packaging now comes from committed source state, and milestone metadata no longer contradicts completion**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-10T20:50:41Z
- **Completed:** 2026-03-10T21:01:16Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Brought `main.py` and `manual_login.py` under version control so the documented runtime entrypoints are part of committed release state.
- Changed `scripts/build-release-bundle.sh` to package committed `HEAD` inputs, and changed `scripts/verify-release-readiness.sh` to assert that required release files/directories are committed before shipment.
- Normalized stale milestone metadata by syncing the top-level requirements checklist, resolving pending decision outcomes in `PROJECT.md`, updating `STATE.md`, and closing the stale Phase 1 UAT session.

## Verification Run

Executed and passed:
- `PYTHONPYCACHEPREFIX=/tmp/pyc python3 -m py_compile main.py manual_login.py`
- `bash -n scripts/build-release-bundle.sh`
- `bash -n scripts/verify-release-readiness.sh`
- `bash scripts/verify-release-readiness.sh`
- `rm -rf /tmp/phase6-gap-release && bash scripts/build-release-bundle.sh --version v1.0.1 --output-dir /tmp/phase6-gap-release`
- `bash scripts/audit-bundle.sh --archive /tmp/phase6-gap-release/1step-cashouts-v1.0.1-macos-apple-silicon.zip`
- `bash scripts/verify-release-readiness.sh --archive /tmp/phase6-gap-release/1step-cashouts-v1.0.1-macos-apple-silicon.zip`

## Task Commits

1. **Task 1: Eliminate dirty-worktree release inputs** - `5a8fd08` (`feat`)
2. **Task 2: Add reproducibility checks to the release gate** - `829bc5f` (`test`), `f4551ec` (`fix`)
3. **Task 3: Normalize milestone metadata after the release blockers are fixed** - `1046502` (`docs`)

**Plan metadata:** written in subsequent docs commit for this plan

## Files Created/Modified

- `main.py` - Committed FastAPI entrypoint required by PM2 and release packaging.
- `manual_login.py` - Committed manual login helper required by the documented browser-profile bootstrap path.
- `scripts/build-release-bundle.sh` - Builds release archives from committed `HEAD` inputs instead of local-only files.
- `scripts/verify-release-readiness.sh` - Verifies required release inputs exist in committed source and warns when local drift would be ignored by the build.
- `docs/RELEASE.md` - Documents the committed-source packaging rule.
- `.planning/REQUIREMENTS.md` - Syncs top-level completion checkboxes with the traceability table.
- `.planning/PROJECT.md` - Replaces stale `Pending` outcomes with current milestone reality.
- `.planning/STATE.md` - Records the gap-closure state and next audit gate.
- `.planning/phases/01-installer-secure-bootstrap/01-UAT.md` - Closes the stale Phase 1 UAT session.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Clean-worktree enforcement would have blocked valid committed-source packaging**
- **Found during:** first release-gate implementation
- **Issue:** the repo contains unrelated dirty runtime files, and failing on those would have made release reproducibility depend on cleaning user work instead of packaging committed state
- **Fix:** switched the builder to archive committed `HEAD` contents directly and changed readiness drift checks from hard-fail to explicit warnings
- **Committed in:** `f4551ec`

**2. [Rule 3 - Blocking] `mapfile` is unavailable in the default macOS bash runtime**
- **Found during:** release build/readiness execution on macOS bash 3.x
- **Issue:** the new git-backed file collection logic used `mapfile`, which is not available in the default shell this project targets
- **Fix:** replaced `mapfile` with portable `while read` loops in both release scripts
- **Committed in:** `f4551ec`

---

*Phase: 06-distribution-release-readiness*
*Completed: 2026-03-10*
