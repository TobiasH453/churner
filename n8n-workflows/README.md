# n8n Workflows

This directory stores versioned, importable workflow artifacts for local runtime.

## Canonical Phase 3 Artifact

- `03-process-order-v1.0.0.json`

Use this file as the default import target for Phase 3 setup.

## Import Prerequisites

1. Runtime services pass health checks:
   - `bash scripts/services-status.sh`
2. n8n server is up:
   - `bash scripts/services-up.sh`
3. API endpoint is reachable at `/process-order`:
   - `http://localhost:${SERVER_PORT:-18080}/process-order`

## Versioning Rules

Workflow filenames follow SemVer in the pattern:

- `<phase>-<workflow-name>-vMAJOR.MINOR.PATCH.json`

Example:

- `03-process-order-v1.0.0.json`

Bump guidance:

- `PATCH`: non-breaking fixes that keep payload contract stable
- `MINOR`: backward-compatible additions (must retain warning compatibility path)
- `MAJOR`: breaking contract changes that require docs/test updates and migration notes

When updating a workflow version:

1. Keep previous versions unless explicitly retired.
2. Update contract checks and docs references.
3. Re-run `bash scripts/verify-n8n-workflow-contract.sh`.
