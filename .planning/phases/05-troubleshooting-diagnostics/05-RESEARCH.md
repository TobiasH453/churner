# Phase 5 Research: Troubleshooting & Diagnostics

**Phase:** 05  
**Date:** 2026-03-06  
**Mode:** ecosystem  
**Outcome:** Prescriptive implementation guidance for planning/execution

## Standard Stack

Use this exact stack for Phase 5:

1. **Troubleshooting source of truth**
- Create one canonical troubleshooting runbook at `docs/TROUBLESHOOTING.md`.
- Use command-first remediation (copy/paste commands) with expected pass/fail cues.
- Keep issue coverage anchored to observed failure surfaces already in this repo (installer, runtime, n8n contract, smoke checks).
- Confidence: **High** (roadmap scope + current docs/script contracts)

2. **Diagnostics collector implementation**
- Implement a script-first collector in `scripts/collect-diagnostics.sh` (bash) with deterministic, non-interactive behavior.
- Reuse existing script conventions from `scripts/service-env.sh` (`[INFO]/[PASS]/[WARN]/[FAIL]` + `Next:`).
- Use bounded snapshots for logs and command outputs; no streaming collectors.
- Confidence: **High** (existing operations script patterns)

3. **Redaction and privacy model**
- Redact secret-like values before writing bundle artifacts.
- Exclude sensitive local state by default: `.env`, browser profiles, auth/session material, full PM2 dumps containing env.
- Capture metadata and derived diagnostics instead of raw secrets.
- Confidence: **High** (project security constraints + Phase 1 secrecy baseline)

4. **Bundle packaging contract**
- Output one timestamped diagnostics directory and optional tarball in a predictable location.
- Include a human-readable manifest describing what was collected and what was redacted/skipped.
- Confidence: **Medium-High** (best-practice inference aligned with supportability goals)

## Architecture Patterns

### 1) Symptom -> Signal -> Action Troubleshooting Pattern

For each known failure mode, encode:
- **Symptom**: what user sees (`[FAIL]` line, script exit behavior, missing dependency message)
- **Signal to collect**: exact command(s) to gather evidence
- **Action**: first-response recovery sequence with rerun command

Recommended scope buckets:
1. Install/preflight blockers
2. Runtime process or health failures
3. n8n workflow contract/integration failures
4. Smoke order/shipping contract failures

Why:
- Matches non-technical operator needs: identify what happened, run exact command, know next step.
- Preserves script-first supportability contract established in Phases 1-4.

Confidence: **High**

### 2) Redaction-First Diagnostics Pipeline

Collector order:
1. Gather candidate outputs (status, versions, bounded logs, script checks)
2. Apply redaction filters before persistence
3. Write sanitized artifacts
4. Emit manifest with capture timestamp and file inventory

Redaction classes to handle:
- key/value secrets (`PASSWORD=...`, `TOKEN=...`, `SECRET=...`, `API_KEY=...`)
- auth headers (`Authorization: Bearer ...`)
- cookie/session lines (`cookie`, `session`, `set-cookie`)

Why:
- Prevents accidental leakage while still producing actionable support evidence.

Confidence: **High**

### 3) Bounded Evidence Collection Pattern

Collect only deterministic, bounded data:
- `services-status` output
- `services-logs` snapshots with fixed max lines per service
- smoke verification output rerun snapshot (if inputs provided)
- environment/config shape checks without raw values

Avoid:
- unbounded live log streaming
- full recursive repo dumps
- binary or user-personal artifacts unrelated to debugging

Why:
- Keeps bundle size stable and reviewable; avoids excessive sensitive surface.

Confidence: **High**

### 4) Support Bundle Contract Pattern

Define explicit operator contract:
- one command to collect: `bash scripts/collect-diagnostics.sh`
- output path printed clearly
- clear share guidance: which directory/archive to attach to support request

Bundle structure suggestion:
- `manifest.txt`
- `commands/` (sanitized command output)
- `logs/` (bounded sanitized logs)
- `system/` (safe metadata: tool versions, ports, process list)

Confidence: **Medium-High**

## Don't Hand-Roll

1. **Do not include raw `.env` contents or browser profile data in diagnostics.**
2. **Do not collect unbounded PM2 logs (`pm2 logs --nostream` without explicit line limits).**
3. **Do not depend on interactive prompts in diagnostics collection.**
4. **Do not document remediation without exact runnable commands.**
5. **Do not duplicate conflicting troubleshooting steps across docs without canonical cross-links.**

## Common Pitfalls

1. **Secret leakage through "helpful" env dumps**
- Symptom: diagnostics bundle includes token/password lines.
- Mitigation: strict regex redaction + explicit denylist for secret-bearing files.
- Confidence: **High**

2. **Oversized, noisy bundle from unbounded log collection**
- Symptom: multi-MB/GB attachments with low signal.
- Mitigation: enforce line caps (`80-200` range) and service-targeted snapshots.
- Confidence: **High**

3. **Troubleshooting docs that reference stale or mismatched commands**
- Symptom: operators run documented commands that no longer exist or differ in flags.
- Mitigation: validate docs command snippets against current `scripts/` interfaces.
- Confidence: **High**

4. **Failure guidance that stops at "check logs"**
- Symptom: user does not know what to run next.
- Mitigation: every failure path must end with exact `Next:` command and rerun step.
- Confidence: **High**

5. **Diagnostics script fails when services are down (worst time)**
- Symptom: collector exits early and captures nothing useful.
- Mitigation: best-effort collection with per-step warnings; keep non-zero only for collector-level fatal issues.
- Confidence: **Medium-High**

## Code Examples

### Example A: Secret redaction helper for key/value lines

```bash
redact_line() {
  sed -E \
    -e 's/((^|[[:space:]])(API_KEY|SECRET|TOKEN|PASSWORD|PASS|AUTH|COOKIE)[^=:{ ]*[=:][[:space:]]*)[^[:space:]]+/\1[REDACTED]/Ig' \
    -e 's/(Authorization:[[:space:]]*Bearer[[:space:]]+)[^[:space:]]+/\1[REDACTED]/Ig' \
    -e 's/(set-cookie:[[:space:]]*)[^;]+/\1[REDACTED]/Ig'
}
```

### Example B: Bounded log capture pattern

```bash
capture_logs() {
  local target="$1"
  local lines="$2"
  bash scripts/services-logs.sh "$target" "$lines" 2>&1 | redact_line > "${OUT_DIR}/logs/${target}.log" || true
}
```

### Example C: Deterministic bundle manifest

```bash
{
  echo "diagnostics_generated_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo=$(pwd)"
  echo "files_collected=$(find "$OUT_DIR" -type f | wc -l | tr -d ' ')"
} > "${OUT_DIR}/manifest.txt"
```

## Sources

Project sources:
- `scripts/service-env.sh`
- `scripts/services-up.sh`
- `scripts/services-status.sh`
- `scripts/services-logs.sh`
- `scripts/verify-runtime-operations.sh`
- `scripts/verify-smoke-readiness.sh`
- `scripts/smoke-validate-response.py`
- `docs/INSTALL.md`
- `docs/OPERATIONS.md`
- `docs/RUNTIME_VALIDATION.md`
- `docs/SMOKE_VERIFICATION.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`

Primary references:
- Bash manual (shell behavior): https://www.gnu.org/software/bash/manual/
- GNU tar manual (archive options): https://www.gnu.org/software/tar/manual/
- `sed`/regex usage references for redaction patterns: https://www.gnu.org/software/sed/manual/sed.html

---

### Quality Gate Check

- [x] Domains investigated (operator docs, diagnostics workflow, redaction, support handoff)
- [x] Guidance aligned to existing repo script/document conventions
- [x] Security constraints preserved (no secret-bearing collection by default)
- [x] Planner-consumable structure provided for downstream executable plans
