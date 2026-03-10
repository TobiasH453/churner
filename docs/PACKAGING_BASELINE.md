# Packaging Baseline (Security First)

This document defines the distribution safety baseline for any shared archive built from this repository.

## Canonical Policy Files

- `.bundleignore` - never-ship patterns
- `scripts/audit-bundle.sh` - enforcement command

## Never-Ship Paths

These paths must not appear in a shared bundle:

- `.env` with local secrets or user-specific values
- `.env.*` (except committed `.env.example` in repo)
- `.n8n/`
- `.pm2/`
- `logs/`
- `diagnostics/`
- `data/browser-profile/`
- `data/browser-profile-personal/`
- `data/browser-profile-business/`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`

Rationale: these files can contain credentials, local session state, or other sensitive runtime artifacts.

## Placeholder `.env` Exception

A top-level `.env` may ship only when it is a release-safe placeholder identical to `.env.example`.
Any `.env` with operator-specific values remains a hard fail.

## Required Check Before Distribution

Run audit against your candidate bundle input:

```bash
# Default: audit git-tracked repository files
bash scripts/audit-bundle.sh

# Audit a generated list
bash scripts/audit-bundle.sh --file-list /path/to/bundle-files.txt

# Audit an archive
bash scripts/audit-bundle.sh --archive /path/to/bundle.tar.gz
```

Interpretation:
- `[PASS]` = no forbidden paths matched `.bundleignore`
- `[PASS]` also allows the placeholder `.env` exception only when `.env` and `.env.example` are identical
- `[FAIL]` = remove listed forbidden paths, regenerate candidate, rerun audit

## Operating Rule

No archive should be shared unless `scripts/audit-bundle.sh` reports `[PASS]`.

## Related Release Guidance

For bundle structure, versioning, and upload flow, use `docs/RELEASE.md`.
