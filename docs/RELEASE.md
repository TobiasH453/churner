# Release Packaging Guide

This is the canonical maintainer guide for creating the Phase 6 distribution bundle.

## Supported Release Target

- Platform: macOS on Apple Silicon
- Artifact format: one `.zip`
- Version format: `vX.Y.Z`
- Distribution channel: shared cloud folder

## Build the Release Bundle

Run from repository root:

```bash
bash scripts/build-release-bundle.sh --version v1.0.0
```

Optional output directory override:

```bash
bash scripts/build-release-bundle.sh --version v1.0.0 --output-dir /tmp/phase6-release
```

Expected outputs:
- Staged release directory: `dist/1step-cashouts-v1.0.0-macos-apple-silicon/`
- Shared artifact: `dist/1step-cashouts-v1.0.0-macos-apple-silicon.zip`

The build hard-fails if required inputs are missing, if the version is not `vX.Y.Z`, or if bundle audit fails.

## Committed Source Gate

Release packaging is intentionally tied to repository state, not a dirty workspace:

- every required release input must already be committed at `HEAD`
- the build and readiness checks fail if any required release input is untracked
- the build and readiness checks fail if required release inputs have staged-only or working-tree drift

This keeps the shipped `.zip` reproducible from committed source instead of silently packaging local-only files.

## What the Bundle Includes

- Application code required for runtime
- `install.sh`
- `requirements.txt`
- `ecosystem.config.js`
- `scripts/`
- `docs/`
- `n8n-workflows/`
- `.env.example`
- Release-safe `.env` placeholder template identical to `.env.example`
- `RELEASE_MANIFEST.txt`

Tests are intentionally excluded from the shared release bundle.

## Hard Exclusions

Never ship:
- `.n8n/`
- `.pm2/`
- `logs/`
- `diagnostics/`
- `data/browser-profile/`
- `data/browser-profile-personal/`
- `data/browser-profile-business/`
- Secret-bearing key/certificate files
- Any real operator `.env`

Bundle safety is enforced by:

```bash
bash scripts/audit-bundle.sh --archive dist/1step-cashouts-v1.0.0-macos-apple-silicon.zip
```

Allowed exception:
- A top-level `.env` is permitted only when it is identical to `.env.example`. This allows a ready-to-edit placeholder file in the download without allowing real local secrets into the archive.

## Shared Folder Handoff

Only upload the `.zip` after:
1. Bundle audit passes
2. Release checklist is complete
3. Release docs QA passes
4. `bash scripts/verify-release-readiness.sh` passes on committed release inputs

The file intended for users is the `.zip`, not the staged directory.

## Workflow Artifact Policy

- Bundle the provided canonical JSON workflow artifact from `n8n-workflows/`
- Document JSON import only
- Do not treat workflow authoring or workflow regeneration as part of the release packaging flow

## Related Docs

- User front door: `README.md`
- Install flow: `docs/INSTALL.md`
- Runtime commands: `docs/OPERATIONS.md`
- n8n import: `docs/N8N_INTEGRATION.md`
- Smoke verification: `docs/SMOKE_VERIFICATION.md`
- Troubleshooting and diagnostics: `docs/TROUBLESHOOTING.md`
