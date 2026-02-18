# Requirements: 1step_cashouts

**Defined:** 2026-02-17
**Core Value:** A new Mac user can install and run the workflow locally in under 20 minutes, with both order-confirmation and shipping-confirmation paths working end-to-end.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Installer & Onboarding

- [ ] **INST-01**: Operator can run a single `install.sh` command that checks required macOS prerequisites before making changes.
- [ ] **INST-02**: Operator can complete initial setup on a fresh Mac in 20 minutes or less using the documented default path.
- [ ] **INST-03**: Operator can start all required services with one documented command path after installation.

### Security & Secrets

- [ ] **SECR-01**: Operator can create local runtime config from a committed `.env.example` without exposing secret values in command output.
- [ ] **SECR-02**: Operator can run a validator that confirms required secrets/config are present and plausibly formatted without printing secret contents.
- [ ] **SECR-03**: Distributed package excludes browser profile/session state and secret-bearing files by default.

### n8n Workflow Integration

- [ ] **N8N-01**: Operator can import a versioned workflow JSON file from `n8n-workflows/` into n8n using documented steps.
- [ ] **N8N-02**: Imported workflow sends payloads that match `/process-order` contract fields required by the API.
- [ ] **N8N-03**: Operator can follow a guide that connects n8n workflow setup to API runtime setup end-to-end.

### Verification

- [ ] **VER-01**: Operator can run one smoke-test command that verifies API health endpoint availability.
- [ ] **VER-02**: Smoke test verifies the order-confirmation processing path produces a valid structured response contract.
- [ ] **VER-03**: Smoke test verifies the shipping-confirmation processing path produces a valid structured response contract.

### Supportability

- [ ] **SUP-01**: Operator has a troubleshooting document with clear recovery paths for common install/runtime failures.
- [ ] **SUP-02**: Operator can run a diagnostics script that collects actionable logs/config metadata with secret redaction.

### Distribution

- [ ] **DIST-01**: Operator can download a package bundle containing everything needed for local macOS setup except secrets and local session state.
- [ ] **DIST-02**: Package documentation clearly identifies what is included, what must be user-provided, and expected first-run steps.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Platform Expansion

- **PLAT-01**: Operator can install and run on Linux with parity to macOS install/verify flow.
- **PLAT-02**: Operator can install and run on Windows with parity to macOS install/verify flow.

### Packaging Enhancements

- **PACK-01**: Operator can run the same workflow via Dockerized packaging.
- **PACK-02**: Operator can bootstrap via optional one-liner download-and-run path.
- **PACK-03**: Optional macOS Keychain integration can store selected secrets while preserving local-only security model.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Linux support in v1 | macOS-first focus to meet shippable target quickly |
| Windows support in v1 | platform variance would delay stable v1 ship |
| Docker packaging in v1 | adds packaging complexity beyond current milestone goal |
| Fully automatic secret provisioning | conflicts with secure local-only secret handling |
| Fully automatic Amazon/EB auth bypass | external OTP/session controls require user-in-the-loop setup |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INST-01 | Phase 1 | Complete |
| INST-02 | Phase 1 | Complete |
| INST-03 | Phase 2 | Complete |
| SECR-01 | Phase 1 | Complete |
| SECR-02 | Phase 1 | Complete |
| SECR-03 | Phase 1 | Complete |
| N8N-01 | Phase 3 | Pending |
| N8N-02 | Phase 3 | Pending |
| N8N-03 | Phase 3 | Pending |
| VER-01 | Phase 4 | Pending |
| VER-02 | Phase 4 | Pending |
| VER-03 | Phase 4 | Pending |
| SUP-01 | Phase 5 | Pending |
| SUP-02 | Phase 5 | Pending |
| DIST-01 | Phase 6 | Pending |
| DIST-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-18 after Phase 2 completion*
