# Phase 2: Runtime Service Operations - Research

**Researched:** 2026-02-17
**Domain:** User-facing runtime start/stop/status/log operations for local FastAPI + n8n services
**Confidence:** HIGH

<research_summary>
## Summary

Phase 2 should harden the existing script-first runtime surface around PM2, not replace it. The best implementation path is:
1. Keep `scripts/services-up.sh`, `scripts/services-down.sh`, `scripts/services-status.sh`, `scripts/services-logs.sh` as the single operator interface.
2. Use PM2 ecosystem config as the one process declaration source.
3. Make status checks two-layered: process layer (PM2 app state) + HTTP layer (API health + n8n health endpoint).
4. Keep logs centralized through PM2 and add bounded/targeted retrieval behavior for supportability.

Critical unknown-now-known for this phase: n8n health endpoints are disabled by default for self-hosted and must be explicitly enabled (`QUEUE_HEALTH_CHECK_ACTIVE=true`) for reliable status checks.
</research_summary>

<standard_stack>
## Standard Stack

Use this stack for Phase 2 work.

| Component | Use | Why |
|---|---|---|
| PM2 ecosystem file (`ecosystem.config.js`) | Canonical service declaration and lifecycle config | PM2 supports start/stop/restart/reload directly from ecosystem files and exposes lifecycle controls (`kill_timeout`, `wait_ready`, `listen_timeout`) |
| PM2 CLI (`pm2 start/stop/delete/status/logs/save/resurrect`) | Runtime orchestration and operator commands | Established process-manager contract for local reliability and reboot restore |
| Shell scripts (`bash`, strict mode) | User command surface | Matches delegated decision for copy-paste-friendly, deterministic command UX |
| `curl` | HTTP health probing | Simple, deterministic status checks in scripts |
| n8n monitoring endpoints (`/healthz`, `/healthz/readiness`) | n8n runtime observability | Official readiness semantics; `/healthz/readiness` verifies DB-ready state |
| n8n env vars (`QUEUE_HEALTH_CHECK_ACTIVE`, `N8N_LOG_*`, `N8N_USER_FOLDER`) | Health endpoint enablement + log behavior + repo-local state | Required for accurate health checks and stable local operator logs |
| n8n Node runtime requirement | Runtime compatibility gate | n8n npm installs require Node.js versions between 20.19 and 24.x |
| FastAPI + Uvicorn runtime controls (`lifespan`, graceful timeout) | Clean shutdown behavior under PM2 restarts | Avoids dirty shutdown and restart flapping |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Single command surface, single process declaration
Use shell scripts as the only operator-facing interface and PM2 ecosystem config as the only process declaration source. Scripts should never duplicate process settings already owned by `ecosystem.config.js`.

### Pattern 2: Layered status contract (process + endpoint)
`services-status.sh` should report both:
- PM2 state (process online/offline/errored)
- HTTP health checks:
  - API: `http://localhost:${SERVER_PORT}/health`
  - n8n: `http://localhost:${N8N_PORT}/healthz` (or readiness endpoint where appropriate)

This avoids false positives from process-up-but-app-down cases.

### Pattern 3: Explicit health endpoint enablement for n8n
Phase 2 should set and document `QUEUE_HEALTH_CHECK_ACTIVE=true` for self-hosted runs so n8n health checks are valid and deterministic.

### Pattern 4: Graceful lifecycle defaults for restart safety
Use PM2 lifecycle controls in ecosystem config (`kill_timeout`, optionally `wait_ready`/`listen_timeout` where needed) and align API process shutdown with FastAPI lifespan/Uvicorn graceful shutdown behavior.

### Pattern 5: Logs as first-class operator workflow
Use PM2 log retrieval modes with bounded lines and explicit service targeting. Keep script defaults concise and support-oriented.

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

- Do not build a custom process supervisor. Use PM2 lifecycle + persistence (`save`/`resurrect`).
- Do not invent custom log rotation logic. Use PM2-supported rotation (`pm2-logrotate`) when needed.
- Do not create ad-hoc n8n health probes against random pages. Use official health endpoints.
- Do not implement bespoke shutdown signaling frameworks for this phase. Use PM2 signal flow + application graceful shutdown hooks.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

1. **n8n health checks fail even when UI appears reachable**
   - Cause: health endpoints disabled by default.
   - Fix: set `QUEUE_HEALTH_CHECK_ACTIVE=true` and verify endpoint behavior.

2. **Process appears online but runtime is not truly ready**
   - Cause: relying only on `pm2 status`.
   - Fix: always pair PM2 state with HTTP health checks.

3. **Service collisions across local repos**
   - Cause: shared PM2/n8n state directories or non-unique process names.
   - Fix: enforce repo-local `PM2_HOME`, `N8N_USER_FOLDER`, and repo-scoped process names.

4. **Restart loops or forced kills on deploy/restart**
   - Cause: insufficient graceful-shutdown timing.
   - Fix: tune PM2 `kill_timeout` and app shutdown handling.

5. **Unbounded log usage frustrates operators**
   - Cause: raw stream-only log behavior without bounded defaults.
   - Fix: default bounded line retrieval and predictable target selection in log helper script (use `--nostream` for non-interactive summaries).

6. **n8n launches fail on unsupported Node.js**
   - Cause: local Node version outside n8n supported range.
   - Fix: validate Node runtime against n8n documented support range before start operations.

</common_pitfalls>

<code_examples>
## Code Examples

### 1) PM2 ecosystem lifecycle hardening

```js
module.exports = {
  apps: [
    {
      name: process.env.AMAZON_AGENT_PM2_NAME,
      script: process.env.PYTHON_BIN,
      args: "main.py",
      kill_timeout: 5000,
      restart_delay: 3000,
      env: {
        SERVER_PORT: process.env.SERVER_PORT,
      },
    },
    {
      name: process.env.N8N_PM2_NAME,
      script: process.env.N8N_BIN || "n8n",
      args: `start --port ${process.env.N8N_PORT}`,
      kill_timeout: 5000,
      restart_delay: 3000,
      env: {
        N8N_USER_FOLDER: process.env.N8N_USER_FOLDER,
        QUEUE_HEALTH_CHECK_ACTIVE: "true",
      },
    },
  ],
};
```

### 2) Status check contract (script pattern)

```bash
# process layer
pm2 status

# endpoint layer
curl -fsS "http://localhost:${SERVER_PORT}/health" >/dev/null || exit 1
curl -fsS "http://localhost:${N8N_PORT}/healthz" >/dev/null || exit 1

echo "[PASS] API and n8n health endpoints reachable"
```

### 3) Logs helper contract (script pattern)

```bash
# all services, bounded and non-streaming
pm2 logs --lines "${LINES:-100}" --nostream

# targeted
pm2 logs "${AMAZON_AGENT_PM2_NAME}" --lines "${LINES:-100}" --nostream
pm2 logs "${N8N_PM2_NAME}" --lines "${LINES:-100}" --nostream
```

</code_examples>

<phase_implications>
## Phase Implications for Planning

- **Plan 02-01 (harden scripts + UX):**
  - Normalize exit codes and pass/fail output across all service scripts.
  - Add explicit dependency and endpoint enablement checks.
  - Tighten status and logs output contracts for operator clarity.

- **Plan 02-02 (validate from fresh install state):**
  - Add reproducible verification script/checklist for start->status->logs->stop cycle.
  - Verify behavior under expected failures (dependency missing, endpoint down, partial process state).

</phase_implications>

<sources>
## Sources

### Primary (official docs)
- PM2 Ecosystem File: https://pm2.keymetrics.io/docs/usage/application-declaration/
- PM2 Graceful Start/Shutdown: https://pm2.keymetrics.io/docs/usage/signals-clean-restart/
- PM2 Startup / save / resurrect: https://pm2.keymetrics.io/docs/usage/startup/
- PM2 Log Management: https://pm2.keymetrics.io/docs/usage/log-management/
- n8n Monitoring endpoints (`/healthz`, `/healthz/readiness`, `/metrics`): https://docs.n8n.io/hosting/logging-monitoring/monitoring/
- n8n User folder configuration (`N8N_USER_FOLDER`): https://docs.n8n.io/hosting/configuration/configuration-examples/user-folder/
- n8n Logs env variables (`N8N_LOG_*`): https://docs.n8n.io/hosting/configuration/environment-variables/logs/
- n8n npm install requirements (Node.js version range): https://docs.n8n.io/hosting/installation/npm/
- FastAPI lifespan guidance: https://fastapi.tiangolo.com/advanced/events/
- Uvicorn timeout and graceful shutdown settings: https://www.uvicorn.org/settings/

### Local project context
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/02-runtime-service-operations/02-CONTEXT.md`
- `scripts/services-up.sh`
- `scripts/services-down.sh`
- `scripts/services-status.sh`
- `scripts/services-logs.sh`
- `scripts/service-env.sh`
- `ecosystem.config.js`

</sources>

---
*Phase: 02-runtime-service-operations*
*Research completed: 2026-02-17*
*Ready for planning: yes*
