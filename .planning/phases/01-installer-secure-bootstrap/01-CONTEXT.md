# Phase 1: Installer & Secure Bootstrap - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a deterministic, secure onboarding path where a fresh macOS user can run one installer flow, set local secrets safely, and reach a clearly reported ready state for downstream smoke verification. This phase clarifies installer behavior and secure bootstrap UX only; new product capabilities remain out of scope.

</domain>

<decisions>
## Implementation Decisions

### Installer flow style
- Installer should be as guided as possible for semi-technical/non-technical users.
- When automation cannot proceed, installer must print exact command(s), exact directory, and why the step is needed.
- Installer should pause for user confirmation (Enter) after manual-required instructions.
- Automation posture: auto-run all safe steps, pause only for manual-required steps.
- End of installer must show explicit `Done` and `Remaining` checklist with exact next command.

### Preflight failure behavior
- Preflight should aggregate failures and report all missing prerequisites before stopping (not first-failure abort).
- Network-dependent checks are hard failures.
- If partial setup is detected, stop and instruct user to clean/fix manually before continuing.
- Output should be concise in terminal; detailed diagnostics can live in logs.

### Secrets onboarding experience
- Secrets setup uses template-guided flow: copy `.env.example` to `.env`, then user edits manually.
- Validate immediately after `.env` setup.
- Validation messaging should identify missing/invalid key names with fix instructions, without exposing secret values.
- Secret input remains file-based/manual (no interactive secret prompts in Phase 1).

### Setup acceptance shape
- "20-minute setup" is a usability target/recommendation, not a strict hard-limit gate.
- Time expectation applies to installer/setup flow, not manual authentication/session priming time.
- Phase 1 completion proof: installer completes, services report healthy, and user receives clear next command for order/shipping verification.
- Final setup output should explicitly show pass/fail summary and "ready for smoke verification" status.

### Codex's Discretion
- Choose installer invocation style (`./install.sh` vs `bash install.sh`) based on safest and clearest default for this repository and target users.
- Determine exact concise-vs-detailed split between terminal output and log output during preflight reporting.

</decisions>

<specifics>
## Specific Ideas

- "Guided as much as possible" means users should be told exactly what to run, where to run it, and why.
- User wants setup experience that is easy and linear, not opaque.
- End-to-end order/shipping confirmation validation remains essential, but Phase 1 should hand off clearly into smoke verification rather than embed full live verification in installer.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-installer-secure-bootstrap*
*Context gathered: 2026-02-17*
