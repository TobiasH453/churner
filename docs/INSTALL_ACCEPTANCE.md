# Installer Acceptance (Clean-Machine Readiness)

This checklist validates Phase 1 installer reliability on a fresh or freshly reset macOS environment.

## Purpose

Confirm that setup is reproducible and that operators receive a clear readiness signal before deeper smoke testing.

## Baseline conditions for timing

Use these assumptions when interpreting runtime:
- Stable internet connectivity (dependency download capable)
- macOS user with terminal access and Homebrew available
- Repository cloned locally with writable workspace
- No intentional network throttling or VPN packet filtering

The 20-minute duration target is a usability recommendation, not a hard fail gate.

## Acceptance procedure

Run from repository root:

```bash
start_ts=$(date +%s)
bash install.sh
bash scripts/installer-self-check.sh
end_ts=$(date +%s)
echo "Elapsed: $((end_ts - start_ts)) seconds"
```

If installer pauses for manual actions, complete the requested command and continue.

## Pass criteria

A run is accepted when all are true:
1. `install.sh` reports deterministic preflight and summary output.
2. `scripts/installer-self-check.sh` returns `RESULT: PASS`.
3. Self-check output includes:
   - `READY FOR SMOKE VERIFICATION`
   - `NEXT COMMAND: bash scripts/services-status.sh`
4. No secret values are printed in installer or validator output.

## Fail criteria

Treat run as failed when any occur:
- Installer preflight returns blocking failures.
- Self-check returns `RESULT: FAIL`.
- Required artifacts/scripts are missing.
- Environment validation fails for required key names.

## Timing interpretation

- `<= 20 minutes`: on target for v1 onboarding.
- `> 20 minutes`: investigate but do not hard-fail solely on time.

Suggested investigation for slow runs:
- Network latency to package registries
- First-time dependency installation overhead
- Manual pause duration by operator

## Troubleshooting pointers

- Env issues: `bash scripts/validate-env.sh`
- Service runtime status: `bash scripts/services-status.sh`
- Packaging policy check: `bash scripts/audit-bundle.sh`
