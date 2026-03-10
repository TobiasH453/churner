---
phase: 06-distribution-release-readiness
plan: "01"
subsystem: distribution
tags: [release, packaging, audit, docs, macos]
requires:
  - phase: 01-installer-secure-bootstrap
    provides: Bundle audit baseline and secret-exclusion policy
  - phase: 05-troubleshooting-diagnostics
    provides: Diagnostics helper included in the release bundle
provides:
  - Deterministic Apple Silicon release bundle builder with SemVer naming
  - Audit-gated release archive flow with safe placeholder `.env` handling
  - Canonical release packaging guide for shared-folder distribution
affects: [phase-06 release-readiness, distribution safety, maintainer workflow]
tech-stack:
  added: [bash]
  patterns: [stage-audit-archive packaging, release-safe dotenv exception, shared-folder distribution]
key-files:
  created: [scripts/build-release-bundle.sh, docs/RELEASE.md, .planning/phases/06-distribution-release-readiness/06-01-SUMMARY.md]
  modified: [.gitignore, .bundleignore, scripts/audit-bundle.sh, docs/PACKAGING_BASELINE.md]
key-decisions:
  - "Release artifact slug fixed to 1step-cashouts-vX.Y.Z-macos-apple-silicon"
  - "Top-level .env is allowed in a release archive only when it is identical to .env.example"
  - "Release packaging remains audit-gated before shared-folder upload"
patterns-established:
  - "Release bundle contract: staged directory + zip archive + RELEASE_MANIFEST.txt"
  - "Archive audit strips archive root folder before matching policy patterns"
duration: 7 min
completed: 2026-03-10
---

# Phase 6 Plan 01: Bundle Structure and Packaging Summary

**Deterministic Phase 6 release builder with audited zip output and maintainer packaging guidance**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-10T20:21:00Z
- **Completed:** 2026-03-10T20:28:39Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `scripts/build-release-bundle.sh` to stage and archive one Apple Silicon `.zip` release artifact named with `vX.Y.Z`.
- Hardened the bundle audit path to handle archive-rooted zip contents, allow `.env.example`, and permit only a release-safe placeholder `.env` identical to `.env.example`.
- Added `docs/RELEASE.md` as the canonical maintainer guide for building and sharing the release bundle.

## Verification Run

Executed and passed:
- `bash -n scripts/build-release-bundle.sh`
- `bash -n scripts/audit-bundle.sh`
- `bash scripts/build-release-bundle.sh --help`
- `rm -rf /tmp/phase6-release && bash scripts/build-release-bundle.sh --version v1.0.0 --output-dir /tmp/phase6-release`
- `bash scripts/audit-bundle.sh --archive /tmp/phase6-release/1step-cashouts-v1.0.0-macos-apple-silicon.zip`
- Archive inspection confirming no bundled tests and expected docs/scripts/workflow files under the staged release root

## Task Commits

1. **Task 1: Implement a deterministic release bundle builder** - `60a1a9c` (`feat`)
2. **Task 2: Enforce release contents and exclusion rules through the existing audit contract** - `eef3e98` (`fix`)
3. **Task 3: Document bundle structure and packaging operator steps** - `1657dcc` (`chore`)

**Plan metadata:** written in subsequent docs commit for this plan

## Files Created/Modified

- `scripts/build-release-bundle.sh` - Builds a staged release directory, generates a release-safe `.env`, writes `RELEASE_MANIFEST.txt`, zips the bundle, and audits the archive.
- `.gitignore` - Ignores `dist/` and `diagnostics/` outputs from local release generation.
- `.bundleignore` - Explicitly excludes diagnostics artifacts in addition to prior secret/session paths.
- `scripts/audit-bundle.sh` - Normalizes archive-rooted paths and enforces the controlled placeholder `.env` exception.
- `docs/PACKAGING_BASELINE.md` - Documents the Phase 6 safe `.env` exception and diagnostics exclusion.
- `docs/RELEASE.md` - Documents versioning, build command, bundle contents, exclusions, and shared-folder handoff.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Archive audit failed on legitimate release inputs**
- **Found during:** local verification of the first generated Phase 6 zip
- **Issue:** `scripts/audit-bundle.sh` treated `.env.example` as forbidden and did not normalize archive-rooted paths, which would have made real release archives fail or miss nested forbidden paths.
- **Fix:** Added archive-root stripping, explicit `.env.example` allowance, and a strict safe-placeholder `.env` comparison rule.
- **Files modified:** `scripts/audit-bundle.sh`, `docs/PACKAGING_BASELINE.md`
- **Verification:** rebuilt `/tmp/phase6-release/1step-cashouts-v1.0.0-macos-apple-silicon.zip` and confirmed audit passes while tests and forbidden runtime state remain excluded.
- **Committed in:** `eef3e98`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to reconcile the locked release `.env` decision with the existing security baseline without weakening the audit gate.

## Next Phase Readiness

- The release packaging path is now deterministic and locally verified.
- Wave 2 can safely build README/checklist QA on top of the real release artifact contract.

---
*Phase: 06-distribution-release-readiness*
*Completed: 2026-03-10*
