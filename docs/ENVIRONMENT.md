# Environment Setup (Template-First)

This project uses a file-based secret onboarding flow.

Do not paste secrets into terminal prompts. Edit `.env` directly.

## Canonical sequence

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

## Required key groups

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

## Validator output contract

Validation never prints secret values. Output references key names only.

### Pass example

```text
[PASS] Environment validation succeeded. Required keys are present and format checks passed.
```

### Fail example

```text
[FAIL] Environment validation failed with N issue(s):
  - Missing required key: AMAZON_PASSWORD. Add it to .env and rerun validation.
  - Invalid SERVER_PORT. Expected numeric port.
```

When validation fails:
1. Edit `.env`
2. Rerun `bash scripts/validate-env.sh`
3. Proceed only after a pass result

## Security guardrails

- Keep `.env` local; never commit it.
- Do not screenshot or share secret values.
- Use `.env.example` as the source of key names and defaults.
