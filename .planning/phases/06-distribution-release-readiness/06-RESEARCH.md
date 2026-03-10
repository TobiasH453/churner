# Phase 6 Research: Distribution & Release Readiness

**Phase:** 06  
**Date:** 2026-03-10  
**Mode:** ecosystem  
**Outcome:** Prescriptive implementation guidance for planning/execution

## Standard Stack

Use this exact stack for Phase 6:

1. **Script-first release packaging**
- Add one deterministic packaging entrypoint under `scripts/` so release creation matches the existing operator pattern (`bash scripts/...`).
- Build the release from a clean staged directory, then produce one `.zip` artifact named with `vX.Y.Z`.
- Confidence: **High** (Phases 1-5 consistently use script-first operator surfaces)

2. **Existing exclusion policy as release gate**
- Reuse `.bundleignore` and `bash scripts/audit-bundle.sh` as the canonical safety gate for release packaging.
- Treat any audit failure as a hard block before the archive is considered shippable.
- Confidence: **High** (Phase 1 already established and verified this policy)

3. **README-led first-run flow**
- Keep `README.md` as the canonical first-run document.
- Support it with targeted detail docs where needed, but avoid competing entrypoints for the happy path.
- Put prerequisites before commands and keep command order aligned with the existing install/runtime/n8n/smoke/diagnostics flow.
- Confidence: **High** (user decision + current doc structure already points users through phased handoffs)

4. **Checklist-based release gate**
- Add a release checklist document with strict go/no-go items and simple version/date evidence fields.
- The checklist should explicitly validate `install -> run -> smoke verify -> diagnostics`.
- Confidence: **High** (locked by context + roadmap success criteria)

## Architecture Patterns

### 1) Stage -> Audit -> Archive Packaging Pattern

Recommended flow:
1. Resolve release version and output paths
2. Stage only required files into a clean temporary release directory
3. Materialize release-only config/doc artifacts there
4. Audit the staged file list or final archive with `bash scripts/audit-bundle.sh`
5. Produce the final `.zip`
6. Emit a small manifest/checklist cue telling the operator what was built

Why:
- Prevents accidental leakage from the working tree
- Makes release contents explicit and reviewable
- Fits the existing security baseline without inventing a second policy system

Confidence: **High**

### 2) Canonical Bundle Manifest Pattern

The release bundle should make its own contents obvious. Include:
- top-level project files needed to run the product
- `docs/` content required for install, runtime, smoke, troubleshooting, and release guidance
- `scripts/` entrypoints required by the documented flow
- `n8n-workflows/` artifact(s) already approved for shipment
- a short release inventory doc stating included files, excluded local state, supported platform, and version

Why:
- DIST-01 and DIST-02 are about a usable downloadable package, not just a raw source archive
- Users need to know what is already provided versus what they must add locally

Confidence: **High**

### 3) README-As-Front-Door Documentation Pattern

Recommended README structure for release distribution:
1. Supported platform and prerequisites
2. What is included in the download
3. What the user must provide locally
4. Exact first-run command sequence
5. Handoffs to detailed docs for n8n import, smoke verification, and troubleshooting

Why:
- Matches the user's request for a strict, copy/paste-first canonical path
- Avoids fragmentation between `README.md` and docs

Confidence: **High**

### 4) Release QA as Artifact + Flow Verification

The release checklist should verify two classes of things:
- **Artifact integrity:** required files present, forbidden files absent, version naming correct
- **Operator flow integrity:** docs point to real commands in the right order, and the release path ends in smoke verification plus diagnostics escalation

Why:
- A safe archive can still fail users if docs drift from the actual command surface
- The release phase is the last chance to catch packaging/docs mismatch before distribution

Confidence: **High**

## Don't Hand-Roll

1. **Do not create release instructions that bypass the existing installer/runtime/verification commands.**
2. **Do not package raw local state** such as `.env`, `.n8n`, `.pm2`, `logs/`, browser profiles, or diagnostics outputs.
3. **Do not make the workflow package a new workstream in this phase.** Bundle the provided/canonical JSON artifact and document JSON import only.
4. **Do not split first-run guidance across multiple equally-authoritative docs.** `README.md` must stay canonical.
5. **Do not ship a release without an explicit audit pass and checklist pass.**

## Common Pitfalls

1. **Release archive accidentally reflects the developer machine instead of the intended product**
- Symptom: archive includes local caches, logs, venvs, or session state
- Mitigation: stage from an allowlist mindset and run `bash scripts/audit-bundle.sh` against the staged file list or archive
- Confidence: **High**

2. **README and support docs drift from the real command surface**
- Symptom: first-run guide references commands or files that no longer match the repo
- Mitigation: release QA should grep docs for canonical commands and verify the install/runtime/n8n/smoke/diagnostics sequence
- Confidence: **High**

3. **Bundle claims to be self-contained but still hides critical user-provided inputs**
- Symptom: users discover late that secrets, authenticated browser state, or workflow import inputs are not included
- Mitigation: list "included" and "you must provide" explicitly in release docs
- Confidence: **High**

4. **Packaging work reopens platform scope**
- Symptom: phase grows into Intel/universal/macOS installer variants
- Mitigation: keep v1 target fixed to Apple Silicon only and record broader support as deferred
- Confidence: **High**

5. **Release checklist becomes advisory instead of a hard gate**
- Symptom: shipping with missing artifacts or failed commands because the checklist has no block criteria
- Mitigation: make failures binary and encode them as explicit checklist blockers
- Confidence: **High**

## Code Examples

### Example A: Stage-file audit before archiving

```bash
find "$STAGE_DIR" -type f | sed "s#^$STAGE_DIR/##" >"$STAGE_DIR/.release-file-list.txt"
bash scripts/audit-bundle.sh --file-list "$STAGE_DIR/.release-file-list.txt"
```

### Example B: Deterministic release naming

```bash
RELEASE_VERSION="${RELEASE_VERSION:?set RELEASE_VERSION like v1.0.0}"
RELEASE_NAME="amazon-email-automation-${RELEASE_VERSION}-macos-apple-silicon"
ZIP_PATH="dist/${RELEASE_NAME}.zip"
```

### Example C: Checklist evidence header

```markdown
- Release version: `v1.0.0`
- Checklist run date: `2026-03-10`
- Result: `GO` only if every required box below is checked
```

## Sources

Project sources:
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/06-distribution-release-readiness/06-CONTEXT.md`
- `README.md`
- `docs/INSTALL.md`
- `docs/OPERATIONS.md`
- `docs/N8N_INTEGRATION.md`
- `docs/SMOKE_VERIFICATION.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PACKAGING_BASELINE.md`
- `.bundleignore`
- `scripts/audit-bundle.sh`
- `scripts/services-up.sh`
- `scripts/services-status.sh`
- `scripts/verify-runtime-operations.sh`
- `scripts/verify-n8n-workflow-contract.sh`
- `scripts/verify-smoke-readiness.sh`
- `scripts/collect-diagnostics.sh`
- `n8n-workflows/03-process-order-v1.0.0.json`

---

### Quality Gate Check

- [x] Research stays within Phase 6 scope: packaging, release docs, and release checklist
- [x] Existing security baseline reused instead of replaced
- [x] User decisions from `06-CONTEXT.md` are treated as locked
- [x] Guidance is planner-consumable and grounded in current repo artifacts
