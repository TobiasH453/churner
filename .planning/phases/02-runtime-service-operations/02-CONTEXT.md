# Phase 2: Runtime Service Operations - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Standardize the runtime command surface so operators can start, stop, inspect status, and access logs for required services in one stable, documented path after installation.

</domain>

<decisions>
## Implementation Decisions

### Command surface shape
- Keep shell-script commands as the canonical operator path:
  - `bash scripts/services-up.sh`
  - `bash scripts/services-down.sh`
  - `bash scripts/services-status.sh`
  - `bash scripts/services-logs.sh`
- Avoid introducing alternate command interfaces in this phase.
- Commands should stay copy-paste-friendly for semi-technical users.

### Status output contract
- Status output should be concise by default, with explicit PASS/FAIL style signals.
- Health checks must include both API and n8n runtime visibility.
- Failure output must include actionable remediation text (what to run next).

### Logs workflow
- Keep one default logs entrypoint with sensible defaults (`all`, bounded line count).
- Preserve service-specific targeting for API vs n8n logs.
- Make log usage deterministic and documented so support flows can reference exact commands.

### Failure and recovery UX
- Fail fast on missing runtime dependencies with clear install commands.
- Return non-zero exit codes on blocking failures.
- Handle partially running service states safely and predictably.
- Prefer explicit guidance over silent retries or ambiguous behavior.

### Codex's Discretion
User explicitly delegated this phase's discussion decisions to Codex.
Codex may choose detailed implementation mechanics for command formatting, output wording, and script internals as long as they satisfy Phase 2 roadmap scope and success criteria.

</decisions>

<specifics>
## Specific Ideas

- Keep the command surface simple and stable for non-technical and semi-technical operators.
- Preserve consistency with Phase 1 installer handoff and reliability posture.

</specifics>

<deferred>
## Deferred Ideas

None — discussion was intentionally skipped and authority delegated for in-scope Phase 2 implementation choices.

</deferred>

---

*Phase: 02-runtime-service-operations*
*Context gathered: 2026-02-17*
