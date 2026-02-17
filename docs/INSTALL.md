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
- `Next command`

Current runtime handoff command:

```bash
bash scripts/services-up.sh
```

Then confirm runtime status:

```bash
bash scripts/services-status.sh
```
