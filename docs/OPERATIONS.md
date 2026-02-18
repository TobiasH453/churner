# Operations Runbook

## Canonical Runtime Commands

Use only these commands for normal runtime operations:

```bash
bash scripts/services-up.sh
bash scripts/services-status.sh
bash scripts/services-logs.sh all 100
bash scripts/services-down.sh
```

Post-install validation handoff:

```bash
bash scripts/verify-runtime-operations.sh
```

See `docs/RUNTIME_VALIDATION.md` for pass/fail interpretation and first-response remediation.

Service-specific logs:

```bash
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-logs.sh n8n-server 120
```

Follow mode (streaming) is optional:

```bash
bash scripts/services-logs.sh all 100 --follow
```

## Output Contract

All runtime scripts use the same labels:
- `[INFO]` context and next-step hints
- `[PASS]` successful checks/actions
- `[WARN]` non-blocking edge cases
- `[FAIL]` blocking failures (non-zero exit)

If a dependency is missing (for example `pm2`), scripts print:
- `[FAIL] Missing dependency: ...`
- `Next: ...` remediation command

## Start Behavior (`services-up.sh`)

`bash scripts/services-up.sh`:
- starts API + n8n from `ecosystem.config.js`
- persists PM2 state with `pm2 save`
- prints resolved process names and health URLs
- prints `Next: bash scripts/services-status.sh`

Blocking failure behavior:
- prints `[FAIL] PM2 failed to start one or more services.`
- exits non-zero

## Status Behavior (`services-status.sh`)

`bash scripts/services-status.sh` performs two layers of checks:
1. PM2 process layer for both services
2. HTTP endpoint layer:
- `http://localhost:${SERVER_PORT:-18080}/health`
- `http://localhost:${N8N_PORT:-15678}/healthz`

Status exits non-zero on any blocking failure and prints remediation commands.

Expected success cue:
- `[PASS] Runtime status check passed.`

Expected failure cue:
- `[FAIL] Runtime status check failed.`

## Logs Behavior (`services-logs.sh`)

Default behavior is deterministic snapshot mode (`--nostream`) with bounded lines.

Usage:
```bash
bash scripts/services-logs.sh [all|amazon-agent|agent|n8n-server|n8n] [lines] [--follow]
```

Defaults:
- target: `all`
- lines: `100`
- mode: snapshot (non-streaming)

Invalid target or invalid line count returns non-zero with remediation output.

## Stop Behavior (`services-down.sh`)

`bash scripts/services-down.sh`:
- deletes both PM2 services when present
- saves PM2 state
- reports already-stopped services as `[WARN]`
- prints `Next: bash scripts/services-status.sh`

## Service Model

- Process manager: `pm2`
- PM2 config source: `ecosystem.config.js`
- API process: `amazon-agent-<repo-slug>` (`main.py`)
- n8n process: `n8n-server-<repo-slug>`

Runtime defaults:
- API port `18080` (`SERVER_PORT`)
- n8n port `15678` (`N8N_PORT`)
- `PM2_HOME=./.pm2` for repo-local process state
- `N8N_USER_FOLDER=./.n8n` for repo-local n8n state
- `QUEUE_HEALTH_CHECK_ACTIVE=true` for n8n health endpoint support

## First-Line Recovery

If status fails:
1. `bash scripts/services-logs.sh amazon-agent 120`
2. `bash scripts/services-logs.sh n8n-server 120`
3. `bash scripts/services-up.sh`
4. `bash scripts/services-status.sh`

Port collision checks:

```bash
lsof -nP -iTCP:18080 -sTCP:LISTEN
lsof -nP -iTCP:15678 -sTCP:LISTEN
```

Kill conflicting process and restart services:

```bash
kill <pid>
bash scripts/services-up.sh
bash scripts/services-status.sh
```
