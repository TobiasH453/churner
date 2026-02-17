# Packaging Baseline (Security First)

This document defines the Phase 1 distribution safety baseline.

Scope here is policy and audit guardrails, not final release packaging workflow.

## Canonical policy files

- `.bundleignore` - never-ship patterns
- `scripts/audit-bundle.sh` - enforcement command

## Never-ship paths

These paths must not appear in a shared bundle:

- `.env`
- `.env.*` (except committed `.env.example` in repo)
- `.n8n/`
- `.pm2/`
- `logs/`
- `data/browser-profile/`
- `data/browser-profile-personal/`
- `data/browser-profile-business/`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`

Rationale: these files can contain credentials, local session state, or other sensitive runtime artifacts.

## Required operator check before distribution

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
- `[FAIL]` = remove listed forbidden paths, regenerate candidate, rerun audit

## Baseline operating rule

No archive should be shared unless `scripts/audit-bundle.sh` reports `[PASS]`.

## Deferred to Phase 6

- Final bundle structure
- Release artifact naming/versioning
- End-user release packaging checklist
