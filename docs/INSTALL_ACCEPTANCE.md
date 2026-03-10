# Installer Acceptance (Clean-Machine Readiness)

This checklist validates installer reliability on a fresh or freshly reset macOS environment.

## Purpose

Confirm that setup is reproducible and that operators receive a clear readiness signal before deeper smoke testing.

## Baseline Conditions for Timing

Use these assumptions when interpreting runtime:
- stable internet connectivity for dependency downloads
- macOS user with terminal access and Homebrew available
- repository cloned locally with writable workspace
- no intentional network throttling or VPN packet filtering

The 20-minute duration target is a usability recommendation, not a hard fail gate.

## Acceptance Procedure

Run from repository root:

```bash
start_ts=$(date +%s)
bash install.sh
bash scripts/installer-self-check.sh
end_ts=$(date +%s)
echo "Elapsed: $((end_ts - start_ts)) seconds"
```

## Pass Criteria

A run is accepted when all are true:
1. `install.sh` reports deterministic preflight and summary output.
2. `scripts/installer-self-check.sh` returns `RESULT: PASS`.
3. Self-check output includes:
   - `READY FOR SMOKE VERIFICATION`
   - `NEXT COMMAND: bash scripts/services-status.sh`
4. No secret values are printed in installer or validator output.

## Fail Criteria

Treat run as failed when any occur:
- installer preflight returns blocking failures
- self-check returns `RESULT: FAIL`
- required artifacts/scripts are missing
- environment validation fails for required key names

## Timing Interpretation

- `<= 20 minutes`: on target for v1 onboarding
- `> 20 minutes`: investigate but do not hard-fail solely on time

Suggested investigation for slow runs:
- network latency to package registries
- first-time dependency installation overhead
- manual steps performed outside the scripted flow

## Troubleshooting Pointers

- Env issues: `bash scripts/validate-env.sh`
- Service runtime status: `bash scripts/services-status.sh`
- Packaging policy check: `bash scripts/audit-bundle.sh`
