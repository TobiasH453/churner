# Smoke Verification Guide

Use this guide after runtime and n8n contract validation to confirm functional API readiness.

## Prerequisites

- Runtime status is healthy:
  - `bash scripts/services-status.sh`
- n8n workflow contract check has passed:
  - `bash scripts/verify-n8n-workflow-contract.sh`
- You have a representative test order number available for smoke validation.

## Canonical Command

From repository root:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh
```

Optional routing override:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 SMOKE_ORDER_ACCOUNT_TYPE=amz_business bash scripts/verify-smoke-readiness.sh
```

## Current Stage Coverage

This command currently validates:
1. API health endpoint (`GET /health`)
2. Order-confirmation contract path (`POST /process-order`)

Shipping-confirmation checks are added in Phase 4 plan `04-03`.

## Pass/Fail Interpretation

Pass cues:
- `[PASS] Check API health endpoint`
- `[PASS] Check order-confirmation contract path`
- `PASS: response contract valid (order_confirmation)`

Fail cues:
- `[FAIL] ...` stage failure line
- `Next:` remediation command
- Non-zero exit code

## Common Failure Cases

1. Missing smoke input
- Symptom: `[FAIL] Missing smoke input: SMOKE_ORDER_NUMBER`
- Action:

```bash
SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh
```

2. Service endpoint unavailable
- Symptom: health stage fails for `http://localhost:${SERVER_PORT:-18080}/health`
- Action:

```bash
bash scripts/services-status.sh
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-up.sh
```

3. Order response contract mismatch
- Symptom: `FAIL: response did not satisfy AgentResponse contract ...`
- Action:

```bash
bash scripts/services-logs.sh amazon-agent 120
```

Review API contract sources:
- `models.py`
- `main.py`
- `browser_agent.py`
