# Smoke Verification Guide

Use this guide after runtime and n8n contract validation to confirm functional API readiness.

## Prerequisites

- Runtime status is healthy:
  - `bash scripts/services-status.sh`
- n8n workflow contract check has passed:
  - `bash scripts/verify-n8n-workflow-contract.sh`
- You have representative test order number(s) available for order and shipping checks.

## Canonical Command

From repository root:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh
```

Optional routing override:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 SMOKE_ORDER_ACCOUNT_TYPE=amz_business bash scripts/verify-smoke-readiness.sh
```

Optional separate shipping order input:

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 SMOKE_SHIPPING_ORDER_NUMBER=222-3333333-4444444 bash scripts/verify-smoke-readiness.sh
```

## Stage Coverage

This command validates:
1. API health endpoint (`GET /health`)
2. Order-confirmation contract path (`POST /process-order`)
3. Shipping-confirmation contract path (`POST /process-order`)

## Pass/Fail Interpretation

Pass cues:
- `[PASS] Check API health endpoint`
- `[PASS] Check order-confirmation contract path`
- `[PASS] Check shipping-confirmation contract path`
- `PASS: response contract valid (order_confirmation, success=...)`
- `PASS: response contract valid (shipping_confirmation, success=...)`
- `[PASS] Smoke readiness checks passed: health + order + shipping.`

Fail cues:
- `[FAIL] ...` stage failure line
- `Next:` remediation command
- Non-zero exit code
- Final aggregate fail cue:
  - `[FAIL] Smoke readiness checks failed.`

## Common Failure Cases

1. Missing smoke input for order/shipping
- Symptom: `[FAIL] Missing smoke input: SMOKE_ORDER_NUMBER`
- Action:

```bash
SMOKE_ORDER_NUMBER=<order-id> bash scripts/verify-smoke-readiness.sh
```

If shipping should use a different order number:

```bash
SMOKE_SHIPPING_ORDER_NUMBER=<shipping-order-id> bash scripts/verify-smoke-readiness.sh
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

4. Shipping response contract mismatch
- Symptom: `FAIL: email_type mismatch: expected shipping_confirmation ...` or schema validation failure
- Action:

```bash
bash scripts/services-logs.sh amazon-agent 120
bash scripts/services-status.sh
```

Review API contract sources:
- `models.py`
- `main.py`
- `browser_agent.py`

For full remediation flow, see:
- `docs/OPERATIONS.md`
