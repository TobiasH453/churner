# Release Checklist

**Release version:** `vX.Y.Z`  
**Checklist run date:** `YYYY-MM-DD`  
**Result:** `GO` only if every required item below is checked. Any failed required command or missing required artifact is `NO SHIP`.

## Artifact Gate

- [ ] Release archive exists: `dist/1step-cashouts-vX.Y.Z-macos-apple-silicon.zip`
- [ ] Stage directory exists: `dist/1step-cashouts-vX.Y.Z-macos-apple-silicon/`
- [ ] Archive contains `README.md`, `docs/`, `scripts/`, `n8n-workflows/`, `.env`, `.env.example`, and `RELEASE_MANIFEST.txt`
- [ ] Archive excludes tests, `.n8n/`, `.pm2/`, `logs/`, `diagnostics/`, and `data/browser-profile*`
- [ ] Bundle audit passed:

```bash
bash scripts/audit-bundle.sh --archive dist/1step-cashouts-vX.Y.Z-macos-apple-silicon.zip
```

## Documentation Gate

- [ ] `README.md` starts with prerequisites before first-run commands
- [ ] `README.md` states what is included in the download
- [ ] `README.md` states what the user must provide locally
- [ ] `README.md` gives the exact first-run command sequence
- [ ] `README.md` points to JSON workflow import, smoke verification, and diagnostics guidance
- [ ] `docs/RELEASE.md` matches the implemented packaging command and output naming

## Validation Flow Gate

### Install

- [ ] Passed:

```bash
bash install.sh
```

Expected cues:
- preflight pass/fail output
- bootstrap summary
- `Env Validation PASS`, `PENDING`, or `FAIL`
- next command guidance

- [ ] If install ended with `Env Validation PENDING`, `.env` was edited locally and validation then passed:

```bash
bash scripts/validate-env.sh
```

### Run

- [ ] Passed:

```bash
bash scripts/services-up.sh
bash scripts/services-status.sh
bash scripts/verify-runtime-operations.sh
```

### Verify

- [ ] Passed:

```bash
bash scripts/verify-n8n-workflow-contract.sh
SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh
```

### Troubleshoot / Diagnostics

- [ ] Diagnostics bundle completes successfully:

```bash
bash scripts/collect-diagnostics.sh
```

- [ ] Diagnostics output path is printed and safe to share

## Hard Blockers

- Missing required archive or staged directory
- Any failed required command above
- Any missing required document or script
- Any forbidden path present in the archive
- Any `.env` in the archive that is not identical to `.env.example`

If any blocker is hit, stop and fix it before sharing the `.zip`.
