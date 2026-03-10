# 1step_cashouts

Local macOS automation for Amazon order and shipping emails using FastAPI, Playwright, PM2, and n8n.

## Supported Platform and Prerequisites

- macOS on Apple Silicon
- `bash`
- `python3` and `pip3`
  - Python 3.13 is preferred
  - Python 3.11-3.13 are the supported versions for this repo
- `node` and `npm`
- `pm2`
- `n8n`
- `curl`
- `git`
- `tar`
- network access to:
  - `https://pypi.org/simple/`
  - `https://registry.npmjs.org/`
  - `https://api.github.com/`

`bash install.sh` runs these preflight checks before making setup changes.

## Included in the Download

- Application runtime code
- `install.sh`
- `requirements.txt`
- `ecosystem.config.js`
- `scripts/`
- `docs/`
- `n8n-workflows/`
- `.env.example`
- A ready-to-edit placeholder `.env` identical to `.env.example`
- Smoke verification and diagnostics helpers

Tests, local browser sessions, logs, diagnostics outputs, and other machine-specific state are intentionally excluded from the shared release bundle.

## You Must Provide Locally

- `ANTHROPIC_API_KEY`
- Amazon personal account credentials
- Amazon business account credentials
- `EB_LOGIN_EMAIL`
- Authenticated local browser sessions after first login
- Representative order number(s) for smoke verification

## First-Run Sequence

Run everything from the unpacked repository root.

### 1) Install prerequisites and local scaffolding

```bash
bash install.sh
```

Expected outcome:
- deterministic preflight output
- bootstrap summary
- `.env` created from `.env.example` if missing
- `Env Validation PASS`, `PENDING`, or `FAIL` in the installer summary
- next command guidance based on that result

If the shipped placeholder `.env` is still in place, the installer ends with `Env Validation PENDING` and tells you to edit `.env` before starting services.

### 2) Fill local environment values and validate

The download includes both `.env` and `.env.example`. Edit `.env` only.

```bash
bash scripts/validate-env.sh
```

If validation fails, edit `.env` and rerun the same command until it passes.

### 3) Start services

```bash
bash scripts/services-up.sh
```

### 4) Confirm runtime status

```bash
bash scripts/services-status.sh
bash scripts/verify-runtime-operations.sh
```

### 5) Import the n8n workflow JSON

1. Open n8n at `http://localhost:15678`
2. Choose **Import from File**
3. Select `n8n-workflows/03-process-order-v1.0.0.json`
4. Rebind credentials and confirm the local API target

Then verify the workflow contract:

```bash
bash scripts/verify-n8n-workflow-contract.sh
```

For the full JSON import flow, see `docs/N8N_INTEGRATION.md`.

### 6) Run smoke verification

```bash
SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh
```

Use `SMOKE_SHIPPING_ORDER_NUMBER` as well if shipping should use a different order id.

### 7) Collect diagnostics if you are blocked

```bash
bash scripts/collect-diagnostics.sh
```

This creates a shareable diagnostics bundle with redaction and exclusion safeguards.

## Related Docs

- Install details: `docs/INSTALL.md`
- Environment editing rules: `docs/ENVIRONMENT.md`
- Runtime operations: `docs/OPERATIONS.md`
- n8n JSON import and rebinding: `docs/N8N_INTEGRATION.md`
- Smoke verification: `docs/SMOKE_VERIFICATION.md`
- Troubleshooting and diagnostics: `docs/TROUBLESHOOTING.md`
- Release packaging and checklist: `docs/RELEASE.md`, `docs/RELEASE_CHECKLIST.md`
- Contract/regression checks: `bash scripts/run-contract-tests.sh`
