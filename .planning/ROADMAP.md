# Roadmap: 1step_cashouts

## Overview

This roadmap turns an already-working local automation system into a shippable macOS product for semi-technical users. The phases are ordered to reduce launch risk: first make installation and security deterministic, then lock workflow integration, then add executable verification, support tooling, and finally release packaging.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Installer & Secure Bootstrap** - Build deterministic setup path with strict local secret handling
- [x] **Phase 2: Runtime Service Operations** - Standardize start/stop/status/log operations for user-facing reliability
- [x] **Phase 3: n8n Workflow Packaging & Contract Alignment** - Ship importable workflow and guarantee payload compatibility
- [ ] **Phase 4: Smoke Verification Harness** - Add one-command functional verification for health + order + shipping
- [ ] **Phase 5: Troubleshooting & Diagnostics** - Ship support tooling and recovery guidance
- [ ] **Phase 6: Distribution & Release Readiness** - Produce downloadable package and release checklist for v1 ship

## Phase Details

### Phase 1: Installer & Secure Bootstrap
**Goal**: A fresh Mac user can run one installer path that sets up prerequisites and secure local configuration.
**Depends on**: Nothing (first phase)
**Requirements**: INST-01, INST-02, SECR-01, SECR-02, SECR-03
**Success Criteria** (what must be TRUE):
1. User can execute `install.sh` and receive explicit preflight pass/fail results for required dependencies.
2. Installer creates local config from template without printing secret values.
3. A clean-machine setup run completes in 20 minutes or less on documented baseline hardware/network conditions.
4. Distributed artifact excludes browser profile directories and secret-bearing files by default.
**Plans**: 4 plans

Plans:
- [x] 01-01: Build prerequisite detection and install flow skeleton
- [x] 01-02: Implement secure env template/bootstrap validation
- [x] 01-03: Add package exclusion rules for sensitive state
- [x] 01-04: Validate clean-machine timing and installer reliability

### Phase 2: Runtime Service Operations
**Goal**: Users can consistently run and observe required services with a stable command surface.
**Depends on**: Phase 1
**Requirements**: INST-03
**Success Criteria** (what must be TRUE):
1. User can bring up required services with one documented command path.
2. User can get clear status output for API and n8n runtime health.
3. User can access consolidated logs through documented helper commands.
**Plans**: 2 plans

Plans:
- [x] 02-01: Harden service lifecycle scripts and command UX
- [x] 02-02: Validate operational script behavior from fresh install state

### Phase 3: n8n Workflow Packaging & Contract Alignment
**Goal**: Workflow import is reproducible and its payload contract is explicitly aligned to API expectations.
**Depends on**: Phase 2
**Requirements**: N8N-01, N8N-02, N8N-03
**Success Criteria** (what must be TRUE):
1. User can import a versioned workflow JSON from `n8n-workflows/` using published instructions.
2. Imported workflow sends required fields for `/process-order` contract without manual patching.
3. Setup guide links n8n import/config to service runtime setup in one coherent path.
**Plans**: 3 plans

Plans:
- [x] 03-01: Export/version workflow artifact(s) for distribution
- [x] 03-02: Add payload contract checks and alignment notes
- [x] 03-03: Publish n8n integration guide tied to runtime setup

### Phase 4: Smoke Verification Harness
**Goal**: One command proves functional readiness beyond simple uptime checks.
**Depends on**: Phase 3
**Requirements**: VER-01, VER-02, VER-03
**Success Criteria** (what must be TRUE):
1. User can run one smoke-test command after install.
2. Smoke test verifies API health endpoint behavior.
3. Smoke test verifies order-confirmation contract path.
4. Smoke test verifies shipping-confirmation contract path.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Build smoke test runner and output format
- [ ] 04-02: Add order path validation checks
- [ ] 04-03: Add shipping path validation checks and failure guidance

### Phase 5: Troubleshooting & Diagnostics
**Goal**: Support workflows are fast, safe, and reproducible for non-technical users.
**Depends on**: Phase 4
**Requirements**: SUP-01, SUP-02
**Success Criteria** (what must be TRUE):
1. User can follow troubleshooting docs to resolve common install/runtime issues.
2. User can generate a diagnostics bundle/script output without exposing raw secrets.
3. Support instructions reference exact commands and expected outputs.
**Plans**: 2 plans

Plans:
- [ ] 05-01: Author troubleshooting doc from observed failure modes
- [ ] 05-02: Implement diagnostics collector with redaction rules

### Phase 6: Distribution & Release Readiness
**Goal**: Package and docs are release-ready for macOS-first user distribution.
**Depends on**: Phase 5
**Requirements**: DIST-01, DIST-02
**Success Criteria** (what must be TRUE):
1. User can download a package containing required project artifacts, excluding sensitive local state.
2. Package documentation clearly states prerequisites, included files, and first-run sequence.
3. Release checklist confirms install -> run -> verify -> troubleshoot flow end-to-end.
**Plans**: 2 plans

Plans:
- [ ] 06-01: Define bundle structure and packaging steps
- [ ] 06-02: Finalize release checklist and docs QA

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Installer & Secure Bootstrap | 4/4 | Complete | 2026-02-17 |
| 2. Runtime Service Operations | 2/2 | Complete | 2026-02-18 |
| 3. n8n Workflow Packaging & Contract Alignment | 3/3 | Complete | 2026-02-18 |
| 4. Smoke Verification Harness | 0/3 | Not started | - |
| 5. Troubleshooting & Diagnostics | 0/2 | Not started | - |
| 6. Distribution & Release Readiness | 0/2 | Not started | - |
