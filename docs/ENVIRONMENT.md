# Environment Setup (Template-First)

This project uses a file-based secret onboarding flow.

Do not paste secrets into terminal prompts. Edit `.env` directly.

## Canonical Sequence

Run these commands from the repository root.

1. Run installer/bootstrap first:

```bash
bash install.sh
```

If `.env` is missing, installer creates it from `.env.example`. If placeholders are still present, installer ends with `Env Validation PENDING`.

2. Edit `.env` manually and replace placeholders.

```bash
bash scripts/validate-env.sh
```

3. Continue runtime flow only after validation passes:

```bash
bash scripts/services-up.sh
```

## Required Key Groups

Personal Amazon route:
- `AMAZON_EMAIL`
- `AMAZON_PASSWORD`
- `AMAZON_TOTP_SECRET` (optional)

Business Amazon route:
- `AMAZON_BUSINESS_EMAIL`
- `AMAZON_BUSINESS_PASSWORD`
- `AMAZON_BUSINESS_TOTP_SECRET` (optional)

Core runtime keys:
- `ANTHROPIC_API_KEY`
- `EB_LOGIN_EMAIL`
- `SERVER_PORT`
- `N8N_PORT`

Optional runtime overrides:
- `AMAZON_AGENT_PM2_NAME`
- `N8N_PM2_NAME`
- `PM2_HOME`
- `N8N_USER_FOLDER`
- `PYTHON_BIN`
- `N8N_BIN`

`PYTHON_BIN=venv/bin/python` is the preferred local virtualenv path when you override it explicitly.

## Validator Output Contract

Validation never prints secret values. Output references key names only.

### Pass Example

```text
[PASS] Environment validation succeeded. Required keys are present and format checks passed.
```

### Fail Example

```text
[FAIL] Environment validation failed with N issue(s):
  - Missing required key: AMAZON_PASSWORD. Add it to .env and rerun validation.
  - Invalid SERVER_PORT. Expected numeric port.
```

When validation fails:
1. edit `.env`
2. rerun `bash scripts/validate-env.sh`
3. proceed only after a pass result

## Security Guardrails

- Keep `.env` local; never commit it.
- Do not screenshot or share secret values.
- Use `.env.example` as the source of key names and defaults.
