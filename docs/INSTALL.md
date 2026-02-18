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

## 2) Preflight results

Preflight is deterministic and blocks setup changes if requirements are missing.

### Pass

You will see:
- `[PASS] Found dependency: ...`
- `[PASS] Network probe ok: ...`
- `[PASS] Preflight completed with no blocking issues.`

### Fail

You will see one aggregated failure summary, for example:
- `[FAIL] Preflight failed with N blocking issue(s)`
- Numbered issue list
- Numbered manual remediation commands (with exact command, directory, and reason)

Fix all listed issues, then rerun:

```bash
bash install.sh
```

## 3) Manual-required step contract

When a manual step is required, installer output always includes:
- `Command: ...`
- `Directory: ...`
- `Reason: ...`

Then the installer pauses for confirmation:

```text
Press Enter after completing this step to continue...
```

## 4) Bootstrap behavior

Bootstrap currently performs safe local setup steps:
- Creates `logs/` and `data/` directories if missing
- Creates `.env` from `.env.example` when possible
- Runs `scripts/validate-env.sh` when available

No secret values are printed by installer output.

## 5) End-of-install handoff

At the end of install, the script prints:
- `Done` checklist
- `Remaining` checklist
- `Next command` (service startup)

Current runtime handoff command:

```bash
bash scripts/services-up.sh
```

Then run readiness self-check:

```bash
bash scripts/installer-self-check.sh
```

Self-check is the final Phase 1 readiness gate. It always prints:
- `RESULT: PASS` or `RESULT: FAIL`
- `READY FOR SMOKE VERIFICATION` or `NOT READY FOR SMOKE VERIFICATION`
- `NEXT COMMAND: bash scripts/services-status.sh` on pass

If self-check fails, fix reported blockers and rerun:

```bash
bash scripts/installer-self-check.sh
```

## 6) Runtime validation handoff

After self-check passes, run runtime validation in this order:

```bash
bash scripts/services-status.sh
bash scripts/verify-runtime-operations.sh
```

Expected runtime validation result:
- `[PASS] Runtime operations validation passed.`
- Exit code `0`

If runtime validation fails:
- Follow the printed `Next:` remediation command
- Refer to `docs/RUNTIME_VALIDATION.md` for troubleshooting flow

## 7) n8n integration handoff

After runtime validation passes, continue directly to n8n workflow setup:

```bash
bash scripts/verify-n8n-workflow-contract.sh
```

Then follow:

- `docs/N8N_INTEGRATION.md` for import + credential rebind + webhook mode guidance
- `docs/N8N_PAYLOAD_CONTRACT.md` for field-level payload contract rules

Expected verification cue before/after import:

- `[PASS] n8n workflow contract verification passed.`
