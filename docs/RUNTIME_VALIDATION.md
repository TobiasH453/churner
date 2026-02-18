# Runtime Validation Guide

Use this guide after installation to confirm runtime service operations are healthy.

## Prerequisites

- Installer completed: `bash install.sh`
- Environment validated: `bash scripts/validate-env.sh`
- PM2 is available (`pm2 --version`)

## Canonical Validation Command

From repository root:

```bash
bash scripts/verify-runtime-operations.sh
```

This script runs the runtime lifecycle in order:
1. `bash scripts/services-up.sh`
2. `bash scripts/services-status.sh`
3. `bash scripts/services-logs.sh all 80`
4. `bash scripts/services-down.sh`

## Pass/Fail Interpretation

Pass signal:
- `[PASS] Runtime operations validation passed.`
- Exit code `0`

Fail signal:
- A stage prints `[FAIL] ...`
- A `Next:` remediation command is printed
- Exit code is non-zero

## Recommended Manual Follow-up

After a pass, confirm status explicitly:

```bash
bash scripts/services-status.sh
```

If status fails, run:

```bash
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-logs.sh n8n-server 120
bash scripts/services-up.sh
bash scripts/services-status.sh
```

## Common Failure Patterns

1. Missing PM2 dependency
- Symptom: `[FAIL] Missing dependency: pm2`
- Action: `npm install -g pm2`

2. Process starts but endpoint checks fail
- Symptom: `[FAIL] API /health ...` or `[FAIL] n8n /healthz ...`
- Action: inspect service logs, then rerun `bash scripts/services-up.sh`

3. Port collisions
- Symptom: services do not stay online after startup
- Action:

```bash
lsof -nP -iTCP:18080 -sTCP:LISTEN
lsof -nP -iTCP:15678 -sTCP:LISTEN
kill <pid>
bash scripts/services-up.sh
```

## Notes

- Validation script output is designed for operator readability (`[INFO]/[PASS]/[FAIL]`).
- The harness uses service scripts directly, so results reflect the real operator command surface.
