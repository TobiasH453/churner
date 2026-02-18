# n8n Payload Contract: `/process-order`

This document defines the payload contract for n8n workflow handoff to the local API endpoint:

- `POST /process-order`

Canonical workflow artifact:

- `n8n-workflows/03-process-order-v1.0.0.json`

## Required Fields

These fields must be present before the API request is sent:

- `email_type`
  - Allowed values: `order_confirmation`, `shipping_confirmation`
- `order_number`

If either required field is missing, workflow returns a structured error response and does not call the API.

## Optional / Defaulted Fields

- `account_type`
  - Optional in API model
  - Workflow default when missing: `amz_personal`
- Optional passthrough fields (sent when available):
  - `grand_total`
  - `subject`
  - `body`
  - `recipient`
  - `sender`
  - `timestamp`

## Unknown Field Policy

Unknown incoming payload keys are accepted and do not block execution.

Workflow behavior:

- Adds warning entry: `unknown_fields_accepted:<comma-separated-keys>`
- Preserves normal processing path if required fields are valid

## Compatibility Warning Policy

Workflow checks incoming contract version hints:

- Input keys considered: `contract_version` or `version`
- Baseline supported contract: `1.0`
- If version is not `1.0`, workflow adds warning:
  - `compatibility_mode_minor_variant:<version>`

This is warning-only behavior for compatible minor variants; it does not hard-fail by itself.

## Verification Commands

Run these commands from repository root:

```bash
python3 test_n8n_process_order_contract.py
bash scripts/verify-n8n-workflow-contract.sh
```

Expected success cues:

- `PASS: n8n process-order contract checks`
- `[PASS] n8n workflow contract verification passed.`

## Implementation Source Links

- API contract model: `models.py` (`EmailData`)
- API endpoint: `main.py` (`/process-order`)
- Workflow artifact: `n8n-workflows/03-process-order-v1.0.0.json`
- Verification test: `test_n8n_process_order_contract.py`
- Verification wrapper: `scripts/verify-n8n-workflow-contract.sh`
