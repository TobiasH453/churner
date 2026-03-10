# 1step_cashouts

## What This Is

1step_cashouts is a local macOS automation package that processes Amazon order and shipping confirmation emails through an n8n workflow, scrapes Amazon details, and submits required data to ElectronicsBuyer. It is aimed at semi-technical and non-technical users who can follow clear instructions but should not need to assemble the system manually. The focus is turning the existing working workflow into a shippable, downloadable, secure, and repeatable setup.

## Core Value

A new Mac user can install and run the workflow locally in under 20 minutes, with both order-confirmation and shipping-confirmation paths working end-to-end.

## Requirements

### Validated

- ✓ Receive and process `order_confirmation` and `shipping_confirmation` payloads via FastAPI `POST /process-order` — existing
- ✓ Route Amazon automation by account type (`amz_personal` vs `amz_business`) with separate persistent profiles — existing
- ✓ Scrape Amazon order/tracking data with deterministic Playwright flows and typed response contracts — existing
- ✓ Submit ElectronicsBuyer tracking with deterministic auth gate, flag-based failure semantics, and bounded retry behavior — existing
- ✓ Run local operations through PM2-managed services (`amazon-agent`, `n8n-server`) with health/status scripts — existing
- ✓ Maintain operational runbook and contract-style regression checks for fragile automation logic — existing

### Delivered in v1

- [x] Ship a one-step local installer flow (`install.sh`) suitable for semi-technical users on macOS
- [x] Include importable n8n workflow artifact(s) and a clear setup guide for n8n integration
- [x] Add secure secrets/bootstrap flow (template + validation) without exposing secret values
- [x] Provide a downloadable distribution format with clear installation and usage instructions
- [x] Provide one smoke-test command that verifies health + order confirmation path + shipping confirmation path
- [x] Provide troubleshooting documentation and a diagnostics collection script for support cases

### Deferred Beyond v1

- Optional one-command bootstrap in addition to `install.sh` for faster onboarding

### Out of Scope

- Linux/Windows support in v1 — macOS-first ship target
- Docker packaging in v1 — local runtime and PM2 flow prioritized
- Fully automatic secret provisioning — security risk and environment-specific complexity
- Fully automatic bypass of Amazon/EB login challenges — external auth controls require user-in-the-loop session setup

## Context

This is a brownfield project: core workflow logic already exists and runs locally with FastAPI, Playwright/browser-use, PM2, and n8n. The repository already contains operational scripts (`scripts/services-*.sh`), environment bootstrap expectations (`requirements.txt`, `.env`), and persistent browser profile storage (`data/browser-profile*`). Codebase mapping has been completed in `.planning/codebase/` and confirms the system architecture and current integrations.

The current milestone is not feature invention; it is productization and distribution hardening. The user goal is to make the existing automation reliably downloadable and operable by non-technical users with clear guardrails, secure defaults, and clear recovery instructions.

## Constraints

- **Platform**: macOS first — initial release targets fastest path to real users
- **User profile**: Non-technical to semi-technical local operators — setup must be guided and low-friction
- **Setup time**: Fresh-machine setup must complete within 20 minutes — onboarding cannot be open-ended
- **Security**: Secrets must stay local and never be committed/bundled — secure-by-default distribution is required
- **Architecture continuity**: Keep existing local FastAPI + n8n + Playwright/PM2 model for v1 — avoid major platform rewrite during ship-hardening
- **Verification**: Both order and shipping workflows must be demonstrably testable after install — ship criteria requires end-to-end functional proof

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Product name is `1step_cashouts` | Aligns project identity with one-step shipping goal | Accepted and shipped |
| v1 packaging prioritizes one-step local installer | Lowest cognitive overhead for non-technical users | Accepted and shipped via `install.sh` |
| Keep optional one-command bootstrap as secondary path | Helpful acceleration without replacing primary guided flow | Deferred beyond v1 |
| Include importable n8n workflow + guide (not auto-import) | Easier and lower-risk than brittle automation of n8n UI/import paths | Accepted and shipped |
| Enforce strict secret handling baseline | User explicitly prioritized secure shipping posture | Accepted and shipped |
| Provide smoke test + troubleshooting docs + diagnostics script in v1 | Required for supportability and confidence after install | Accepted and shipped |
| Confirm explicit v1 exclusions (no Linux/Windows, no Docker, no full auth bypass) | Prevents scope creep and protects timeline | Accepted and preserved |

---
*Last updated: 2026-03-10 after Phase 6 gap closure*
