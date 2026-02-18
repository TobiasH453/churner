# n8n Integration Guide

This guide connects runtime setup to workflow import and payload contract validation.

Canonical workflow artifact:

- `n8n-workflows/03-process-order-v1.0.0.json`

## 1) Prerequisites

Run these checks from repository root before importing the workflow:

```bash
bash scripts/services-status.sh
bash scripts/verify-runtime-operations.sh
```

Expected cues:

- `[PASS] Runtime status check passed.`
- `[PASS] Runtime operations validation passed.`

If either command fails, resolve runtime issues first via `docs/RUNTIME_VALIDATION.md`.

## 2) Open n8n and import workflow

1. Open n8n in browser:
   - `http://localhost:${N8N_PORT:-15678}`
2. In n8n, choose **Import from File**.
3. Select:
   - `n8n-workflows/03-process-order-v1.0.0.json`

Expected cue:

- Workflow appears as `03 Process Order v1.0.0`.

## 3) Rebind credentials and endpoint config

After import, complete this checklist in the n8n editor:

- Confirm HTTP Request node target still points to local API `/process-order`.
- Rebind any credentials required by your upstream trigger/source nodes.
- Ensure imported workflow has no placeholder credential references left unresolved.
- Save workflow after credential updates.

## 4) Webhook mode caution (test vs production)

n8n uses different webhook behavior for testing versus active/published execution.

- Use test URL flow only during editor testing.
- Use active workflow/production URL flow for normal runtime processing.

If behavior differs between test and active runs, publish/activate workflow and retest.

## 5) Post-import contract verification

Run contract checks after import/configuration:

```bash
bash scripts/verify-n8n-workflow-contract.sh
```

Expected result:

- `[PASS] n8n workflow contract verification passed.`

If verification fails:

1. Review the failing assertion output.
2. Compare workflow fields against `docs/N8N_PAYLOAD_CONTRACT.md`.
3. Re-import canonical JSON if manual edits drifted contract behavior.
4. Re-run verification command.

## 6) Minimal smoke request (optional)

For a quick manual payload check in n8n test mode, send a payload containing:

- `email_type`
- `order_number`
- optional `account_type` (defaults to `amz_personal` when omitted)

Unknown extra fields are accepted but should surface warning metadata in workflow handling.

## 7) Related docs

- Install flow: `docs/INSTALL.md`
- Runtime operations: `docs/OPERATIONS.md`
- Runtime troubleshooting: `docs/RUNTIME_VALIDATION.md`
- Payload contract details: `docs/N8N_PAYLOAD_CONTRACT.md`
