# Troubleshooting Guide

Canonical troubleshooting runbook for install, runtime, n8n integration, and smoke verification failures.

## Scope

This guide covers the v1 command surface only:
- Installer / preflight issues
- Runtime service operations (`services-*`)
- n8n workflow contract checks
- Smoke verification checks

## Quick Triage Snapshot

Run these in order before deep troubleshooting:

```bash
bash scripts/services-status.sh
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-logs.sh n8n-server 120
bash scripts/verify-n8n-workflow-contract.sh
SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh
```

## Failure-Mode Catalog

| Category | Symptom cue | Likely cause | First-response command sequence | Rerun command |
|---|---|---|---|---|
| Install / preflight | `[FAIL] Preflight failed with N blocking issue(s)` | Missing dependency, failed network probe, or incompatible runtime tools | `bash install.sh` (read numbered remediation), install missing dependencies from output, rerun preflight | `bash install.sh` |
| Installer self-check | `RESULT: FAIL` / `NOT READY FOR SMOKE VERIFICATION` | Environment validation failed or packaging/runtime baseline check failed | `bash scripts/installer-self-check.sh`, follow listed failing checks, run listed `Next:` commands | `bash scripts/installer-self-check.sh` |
| Runtime dependency | `[FAIL] Missing dependency: pm2` (or curl) | Required CLI not installed in active shell | Install missing dependency (`npm install -g pm2` or `brew install curl`) | `bash scripts/services-status.sh` |
| Runtime process health | `[FAIL] PM2 <service>: ...` or `[FAIL] Runtime status check failed.` | Service crashed, stale PM2 state, or startup failure | `bash scripts/services-logs.sh amazon-agent 120`; `bash scripts/services-logs.sh n8n-server 120`; `bash scripts/services-up.sh` | `bash scripts/services-status.sh` |
| Runtime endpoint health | `[FAIL] API /health: ...` or `[FAIL] n8n /healthz: ...` | Service online in PM2 but endpoint unhealthy, port conflict, startup regression | `bash scripts/services-logs.sh <service> 120`; check ports with `lsof -nP -iTCP:18080 -sTCP:LISTEN` and `lsof -nP -iTCP:15678 -sTCP:LISTEN`; restart services | `bash scripts/services-status.sh` |
| Logs command misuse | `[FAIL] Unknown target: ...` or invalid line count | Invalid logs target or non-numeric line argument | Run help usage and retry with valid target: `bash scripts/services-logs.sh [all|amazon-agent|agent|n8n-server|n8n] [lines]` | `bash scripts/services-logs.sh all 100` |
| n8n contract check | `[FAIL] Missing workflow artifact...` or `[FAIL] Workflow contract checks failed.` | Workflow file missing, JSON invalid, or contract test regression | Verify artifact path and JSON validity; re-import canonical workflow; inspect failing contract output | `bash scripts/verify-n8n-workflow-contract.sh` |
| Smoke input missing | `[FAIL] Missing smoke input: SMOKE_ORDER_NUMBER` (or shipping equivalent) | Required smoke environment variable not provided | Export required smoke vars and rerun command | `SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh` |
| Smoke request failure | `[FAIL] Order smoke request failed` / `[FAIL] Shipping smoke request failed` | API unavailable, endpoint error, or runtime unstable | `bash scripts/services-status.sh`; `bash scripts/services-logs.sh amazon-agent 120`; ensure runtime healthy before smoke | `SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh` |
| Smoke contract mismatch | `FAIL: response did not satisfy AgentResponse contract ...` or `FAIL: email_type mismatch ...` | API response schema mismatch or routing mismatch | `bash scripts/services-logs.sh amazon-agent 120`; verify payload + response expectations in `models.py`/`main.py` | `SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh` |

## Escalation

If first-response commands do not resolve the issue, collect diagnostics and attach bundle output for support review:

```bash
bash scripts/collect-diagnostics.sh
```

(Collector is added in Phase 5 Plan 02.)

## Guided Recovery Flows

Use these when you need a deterministic path from failure to rerun.

### Flow A: Runtime Status Failure

Start when you see:
- `[FAIL] Runtime status check failed.`
- `[FAIL] PM2 ...`
- `[FAIL] API /health ...` or `[FAIL] n8n /healthz ...`

Run in order:

```bash
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-logs.sh n8n-server 120
bash scripts/services-up.sh
bash scripts/services-status.sh
```

Success cues:
- `[PASS] PM2 <service>: online` for both services
- `[PASS] API /health: ...`
- `[PASS] n8n /healthz: ...`
- `[PASS] Runtime status check passed.`

Next:
- Continue with `bash scripts/verify-runtime-operations.sh`
- Then continue with n8n/smoke verification flow

### Flow B: n8n Contract Verification Failure

Start when you see:
- `[FAIL] Workflow contract checks failed.`
- Missing workflow artifact or invalid workflow JSON errors

Run in order:

```bash
python3 -m json.tool n8n-workflows/03-process-order-v1.0.0.json >/dev/null
python3 test_n8n_process_order_contract.py
bash scripts/verify-n8n-workflow-contract.sh
```

If still failing:
- Re-import `n8n-workflows/03-process-order-v1.0.0.json` in n8n
- Rebind credentials and confirm local API target
- Re-run `bash scripts/verify-n8n-workflow-contract.sh`

Success cue:
- `[PASS] n8n workflow contract verification passed.`

Next:
- Resume smoke verification

### Flow C: Smoke Verification Failure

Start when you see:
- `[FAIL] Missing smoke input: ...`
- `[FAIL] Order smoke request failed ...`
- `[FAIL] Shipping smoke request failed ...`
- `FAIL: response did not satisfy AgentResponse contract ...`

Run in order:

```bash
bash scripts/services-status.sh
bash scripts/services-logs.sh amazon-agent 120
SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh
```

If shipping uses a different order id:

```bash
SMOKE_ORDER_NUMBER=<order-id> SMOKE_SHIPPING_ORDER_NUMBER=<shipping-order-id> bash scripts/verify-smoke-readiness.sh
```

Success cue:
- `[PASS] Smoke readiness checks passed: health + order + shipping.`

Next:
- Return to normal operator flow in `docs/INSTALL.md` / `docs/OPERATIONS.md`
