# Installation Guide

This is the canonical setup path for this repository.

## 1) Run the installer

From the repository root:

```bash
bash install.sh
```

The installer always runs in this order:
1. `Preflight`
2. `Bootstrap`
3. `Summary`

It writes logs to `logs/install/`.

## 2) Read preflight results

Preflight blocks setup changes if required dependencies or network access are missing.

### Pass

You will see:
- `[PASS] Found dependency: ...`
- `[PASS] Network probe ok: ...`
- `[PASS] Preflight completed with no blocking issues.`

### Fail

You will see one aggregated failure summary, for example:
- `[FAIL] Preflight failed with N blocking issue(s)`
- numbered issue list
- numbered remediation commands with exact command, directory, and reason

Fix all listed issues, then rerun:

```bash
bash install.sh
```

## 3) Bootstrap behavior

Bootstrap performs safe local setup steps:
- creates `logs/` and `data/` directories if missing
- creates `.env` from `.env.example` when possible
- runs `scripts/validate-env.sh --allow-template-placeholders`

No secret values are printed by installer output.

## 4) Interpret env validation

The installer summary is authoritative:

- `Env Validation PASS`: `.env` is filled well enough to continue to service startup.
- `Env Validation PENDING`: `.env` still contains the shipped placeholder values. Edit `.env` locally, then run `bash scripts/validate-env.sh`.
- `Env Validation FAIL`: `.env` contains real values that are incomplete or malformed. Fix `.env`, then run `bash scripts/validate-env.sh`.

Canonical first-run order:

```bash
bash install.sh
bash scripts/validate-env.sh
bash scripts/services-up.sh
```

The second command is only expected after you have edited `.env` locally.

## 5) Next command after install

At the end of install, the script prints:
- `Done` checklist
- `Remaining` checklist
- `Next command` based on env validation state

When the installer ends with `Env Validation PENDING` or `FAIL`, the next command is:

```bash
bash scripts/validate-env.sh
```

When the installer ends with `Env Validation PASS`, the next command is:

```bash
bash scripts/services-up.sh
```

Optional deeper replay after services are up:

```bash
bash scripts/installer-self-check.sh
```

Self-check always prints:
- `RESULT: PASS` or `RESULT: FAIL`
- `READY FOR SMOKE VERIFICATION` or `NOT READY FOR SMOKE VERIFICATION`
- `NEXT COMMAND: bash scripts/services-status.sh` on pass

If self-check fails, fix reported blockers and rerun:

```bash
bash scripts/installer-self-check.sh
```

## 6) Validate runtime operations

After self-check passes, run runtime validation in this order:

```bash
bash scripts/services-status.sh
bash scripts/verify-runtime-operations.sh
```

Expected runtime validation result:
- `[PASS] Runtime operations validation passed.`
- exit code `0`

If runtime validation fails:
- follow the printed `Next:` remediation command
- refer to `docs/RUNTIME_VALIDATION.md` for troubleshooting flow
- use `docs/TROUBLESHOOTING.md` for consolidated recovery paths

## 7) Import the n8n workflow JSON

After runtime validation passes, continue to workflow setup:

```bash
bash scripts/verify-n8n-workflow-contract.sh
```

Then follow:
- `docs/N8N_INTEGRATION.md` for import, credential rebind, and webhook mode guidance
- `docs/N8N_PAYLOAD_CONTRACT.md` for field-level payload rules

Expected verification cue before or after import:
- `[PASS] n8n workflow contract verification passed.`

## 8) Run smoke verification

After runtime and n8n contract verification pass, run smoke verification:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh
```

Expected smoke verification cue:
- `[PASS] Smoke readiness checks passed: health + order + shipping.`

If smoke verification fails:
- follow printed `Next:` commands first
- review `docs/SMOKE_VERIFICATION.md` for stage-specific rerun guidance
- use `docs/TROUBLESHOOTING.md` for full triage flow if still blocked
- collect a diagnostics bundle if needed:

```bash
bash scripts/collect-diagnostics.sh
```
