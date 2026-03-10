---
milestone: v1
audited: 2026-03-10T20:40:00Z
status: gaps_found
scores:
  requirements: 14/16
  phases: 5/6
  integration: 2/4
  flows: 3/4
gaps:
  requirements:
    - "DIST-01: release packaging is not reproducible from committed repository state because required runtime files are currently untracked"
    - "DIST-02: shipped first-run sequence is inconsistent with installer behavior and can fail before users edit placeholder .env values"
  integration:
    - "Phase 1 installer bootstrap validates .env immediately, but Phase 6 release docs instruct editing .env after running install.sh"
    - "Phase 6 release bundle builder copies untracked files from the working tree, so the release artifact is not guaranteed to match the committed project state"
  flows:
    - "Release download -> install -> edit .env breaks at install/bootstrap because validation runs before the documented env-edit step"
tech_debt:
  - phase: 0-project-metadata
    items:
      - "Top-level v1 requirement checklist in REQUIREMENTS.md still leaves most completed requirements unchecked while the traceability table marks them Complete"
      - "PROJECT.md key decision outcomes remain marked Pending even though the milestone has been executed and verified"
      - "A stale UAT session remains open for Phase 1, which can confuse later verify-work runs"
---

# v1 Milestone Audit

## Status

`gaps_found`

The milestone is close, but two Phase 6 issues block calling v1 fully complete:
- the release flow documented for new users does not match the installer's actual env-validation behavior
- the release bundle currently depends on untracked files in the dirty workspace, so it is not reproducible from committed state

## Requirements Coverage

| Requirement | Owner | Audit Status | Notes |
|-------------|-------|--------------|-------|
| INST-01 | Phase 1 | satisfied | Verified by `01-VERIFICATION.md` |
| INST-02 | Phase 1 | satisfied | Acceptance path exists; no new audit blocker found |
| INST-03 | Phase 2 | satisfied | Runtime script surface is coherent |
| SECR-01 | Phase 1 | satisfied | Redacted env-validation contract remains intact |
| SECR-02 | Phase 1 | satisfied | Validator remains present and explicit |
| SECR-03 | Phase 1 | satisfied | Bundle audit still blocks secret/session state by default |
| N8N-01 | Phase 3 | satisfied | Workflow artifact and import docs remain present |
| N8N-02 | Phase 3 | satisfied | Contract verification remains present |
| N8N-03 | Phase 3 | satisfied | Runtime -> import -> verify handoff remains coherent |
| VER-01 | Phase 4 | satisfied | Smoke health stage remains wired |
| VER-02 | Phase 4 | satisfied | Order smoke contract path remains wired |
| VER-03 | Phase 4 | satisfied | Shipping smoke contract path remains wired |
| SUP-01 | Phase 5 | satisfied | Troubleshooting runbook remains coherent |
| SUP-02 | Phase 5 | satisfied | Diagnostics flow remains coherent |
| DIST-01 | Phase 6 | unsatisfied | Release build is not reproducible from committed repository state |
| DIST-02 | Phase 6 | unsatisfied | User-facing first-run flow is inconsistent with actual installer behavior |

## Phase Verification Summary

| Phase | Verification | Audit Result | Notes |
|-------|--------------|--------------|-------|
| 1 | passed | pass | No new blocker found |
| 2 | passed | pass | No new blocker found |
| 3 | passed | pass | No new blocker found |
| 4 | passed | pass | No new blocker found |
| 5 | passed | pass | No new blocker found |
| 6 | passed | fail at milestone level | Cross-phase release flow and reproducibility gaps invalidate the phase as a final ship gate |

## Cross-Phase Integration Review

### Passes

- Install -> runtime docs still hand off cleanly via `docs/INSTALL.md`, `docs/OPERATIONS.md`, and runtime scripts.
- Runtime -> n8n -> smoke handoff remains coherent across `docs/OPERATIONS.md`, `docs/N8N_INTEGRATION.md`, and `docs/SMOKE_VERIFICATION.md`.
- Troubleshooting and diagnostics remain properly linked from install/runtime/smoke docs.

### Gaps

1. **Release docs vs installer behavior**
- `README.md` tells users to run `bash install.sh` before editing `.env`.
- `install.sh` runs `scripts/validate-env.sh` during bootstrap.
- `.env.example` intentionally contains placeholder values that fail validation.
- Result: the documented first-run flow can fail before the user reaches the "edit `.env`" step.

2. **Release artifact vs committed source state**
- `scripts/build-release-bundle.sh` requires `main.py` and `manual_login.py`.
- Those files are currently untracked in git in this workspace.
- Result: the release builder succeeds only from the current dirty worktree, not from the committed project state implied by the audit trail.

## Broken Flow Detail

### Flow: Downloaded release -> first run

Expected:
1. User unpacks release
2. User runs `bash install.sh`
3. User edits `.env`
4. User validates env and continues

Actual:
1. User unpacks release with placeholder `.env`
2. `bash install.sh` copies or uses placeholder `.env`
3. Installer immediately runs `bash scripts/validate-env.sh`
4. Validation fails on placeholder values before the documented edit step

## Tech Debt and Metadata Drift

- `REQUIREMENTS.md` has conflicting completion signals: the traceability table is current, but the top-level v1 checklist is mostly still unchecked.
- `PROJECT.md` key decisions remain marked `Pending`, even though the milestone has implemented and verified those decisions.
- `.planning/phases/01-installer-secure-bootstrap/01-UAT.md` remains open in `testing` status and will be surfaced by future verify-work sessions.

## Recommended Next Steps

1. Fix the Phase 6 first-run ordering so the release docs and installer agree on when `.env` must be edited and validated.
2. Make the release builder depend only on committed artifacts, or commit the required runtime files before using it as a ship gate.
3. Clean up planning metadata drift after the blocking release issues are resolved.

## Evidence Used

- All six phase verification reports under `.planning/phases/*/*-VERIFICATION.md`
- `README.md`
- `install.sh`
- `scripts/validate-env.sh`
- `scripts/build-release-bundle.sh`
- `git status --porcelain`
- `git ls-files main.py manual_login.py amazon_scraper.py browser_agent.py models.py`
