# Phase 6: Distribution & Release Readiness - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Package the existing macOS-first automation into a downloadable release bundle and publish the accompanying docs/checklist needed to install, run, verify, and troubleshoot it safely. This phase does not add new runtime features or create new workflow capabilities.

</domain>

<decisions>
## Implementation Decisions

### Release artifact shape
- Ship one `.zip` artifact for v1.
- Use `vX.Y.Z` semantic versioning in artifact naming.
- Release distribution channel is a shared cloud folder, not GitHub Releases.
- v1 target is Apple Silicon only; do not plan Intel/universal packaging in this phase.

### Bundle contents and exclusions
- Include app code, scripts, docs, and `n8n-workflows/` artifacts in the release bundle.
- Do not include tests in the shared release bundle.
- Ship both `.env.example` and a prefilled non-secret `.env` template for first-run setup.
- Hard-exclude secrets, browser profiles, logs, virtual environments, caches, and diagnostics outputs.
- Include smoke verification and diagnostics helpers in the release bundle.

### First-run documentation flow
- The canonical first-run path lives in `README.md`.
- Instructions should be strict, step-by-step, and copy/paste oriented.
- Put the full prerequisites block at the top before any commands.
- n8n guidance should assume JSON workflow import.
- Workflow package authoring is not part of this phase's implementation work; planning should treat the workflow artifact as provided input and focus on release packaging/docs around it.

### Release checklist gate style
- Release checklist is strict go/no-go; required items do not ship with exceptions.
- Required validation flow is `install -> run -> smoke verify -> diagnostics`.
- Evidence format is a simple checkbox list with date and version.
- Any failed required command or missing required artifact blocks release immediately.

### Codex's Discretion
- Exact bundle directory layout inside the `.zip`, as long as required contents and exclusions are honored.
- Exact filename convention around the locked `vX.Y.Z` versioning policy.
- Exact document split between `README.md` and supporting docs, as long as `README.md` remains the canonical first-run path.
- Exact wording and formatting of the release checklist.

</decisions>

<specifics>
## Specific Ideas

- Keep the operator journey linear and explicit: prerequisites -> install -> services up -> status/runtime validation -> n8n import -> smoke -> diagnostics.
- Reuse the existing security baseline from `.bundleignore` and `bash scripts/audit-bundle.sh` instead of inventing a new exclusion policy.
- Semi-technical users should be able to follow the release docs with copy/paste commands and obvious pass/fail cues.

</specifics>

<deferred>
## Deferred Ideas

- Intel or universal macOS packaging support.
- Publishing via GitHub Releases.
- Creating or revising the n8n workflow package itself beyond bundling the provided artifact.

</deferred>

---

*Phase: 06-distribution-release-readiness*
*Context gathered: 2026-03-10*
