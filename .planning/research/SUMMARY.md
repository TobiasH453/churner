# Project Research Summary

**Project:** 1step_cashouts
**Domain:** Brownfield local automation productization (installer, packaging, support hardening)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Executive Summary

This project is not about inventing new workflow logic; the core automation already exists. The research points to a productization-first roadmap: make installation reproducible, secure, and supportable for semi-technical users on macOS, while preserving the working FastAPI + n8n + Playwright architecture.

The recommended approach is to ship an audited `install.sh` path as the primary onboarding experience, include versioned n8n workflow JSON plus a clear import guide, and enforce a real smoke-test gate that validates business behavior (order + shipping), not just process uptime. This aligns directly with the 20-minute setup requirement.

The highest risk is operational drift: scripts, workflow exports, secrets handling, and docs diverging over time. Mitigation is explicit: canonical installer flow, strict local-only secret policy, versioned workflow artifacts, and diagnostics tooling that accelerates support without leaking credentials.

## Key Findings

### Recommended Stack

Keep the existing architecture and modernize only what affects shippability: n8n + Node LTS, Python 3.12/3.13 runtime, FastAPI, Playwright, browser-use (scoped use), and PM2 supervision. For this milestone, the stack decision is less about adding frameworks and more about pinning known-good versions and making setup deterministic.

**Core technologies:**
- n8n 2.7.x: workflow orchestration and webhook glue — official docs define supported Node matrix
- Python 3.12/3.13 + FastAPI 0.129.x: stable local API and typed contracts
- Playwright 1.58.x + browser-use 0.11.x: deterministic automation with constrained LLM flexibility
- PM2 6.0.x: operator-friendly process management already used by this codebase

### Expected Features

**Must have (table stakes):**
- Guided installer with preflight checks
- Importable n8n workflow artifact and guide
- Secure env bootstrap and validation
- Smoke test covering health, order path, and shipping path
- Troubleshooting docs plus diagnostics collection script

**Should have (competitive):**
- Optional one-liner bootstrap wrapper calling the audited installer
- Enhanced diagnostics and support ergonomics

**Defer (v2+):**
- Cross-platform support
- Docker packaging

### Architecture Approach

Recommended architecture is a three-layer ship model: onboarding layer (installer/docs/smoke test), runtime service layer (n8n + FastAPI + PM2), and automation/state layer (Playwright/browser-use + local profiles/logs). Keep core runtime modules mostly unchanged and add productization boundaries around them.

**Major components:**
1. Installer and preflight pipeline — deterministic setup and dependency gating
2. Workflow packaging boundary — versioned n8n JSON and import contract
3. Verification and support layer — smoke tests, diagnostics, and troubleshooting

### Critical Pitfalls

1. **Installer/docs drift** — keep installer canonical and docs command-referential
2. **Secret leakage** — redact diagnostics and enforce local-only secret handling
3. **Workflow/package mismatch** — version export artifacts and validate import contract
4. **Fresh-machine assumption failures** — preflight every dependency explicitly
5. **False-positive validation** — require functional smoke tests, not just service health

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Installer and Security Baseline
**Rationale:** Must unlock reliable onboarding before any release confidence exists.
**Delivers:** `install.sh`, preflight checks, `.env.example`, secret-safe validation.
**Addresses:** Guided install, secure bootstrap.
**Avoids:** Installer drift, secret leakage.

### Phase 2: Workflow Packaging and Runtime Contracts
**Rationale:** n8n importability must be versioned and reproducible.
**Delivers:** Versioned `n8n-workflows/*.json`, import guide, payload contract sanity checks.
**Uses:** n8n export/import conventions and existing API models.
**Implements:** Workflow packaging boundary.

### Phase 3: Ship-Gate Verification
**Rationale:** "works" must be measurable on clean machines.
**Delivers:** smoke test command for health + order + shipping.
**Uses:** Existing FastAPI routes and scriptable service controls.

### Phase 4: Troubleshooting and Diagnostics Hardening
**Rationale:** Supportability is part of shippability for non-technical users.
**Delivers:** troubleshooting docs + diagnostics script with redaction.
**Avoids:** slow support loops and unsafe ad-hoc debug collection.

### Phase 5: Distribution and Release Readiness
**Rationale:** Final packaging and release checklist close the loop.
**Delivers:** downloadable bundle shape, release checklist, optional one-liner bootstrap.

### Phase Ordering Rationale

- Installer/security first because all downstream verification depends on reproducible setup.
- Workflow packaging before smoke tests so tests run against actual shipped artifacts.
- Diagnostics after smoke tests so support tooling aligns with real failure modes.
- Distribution last so it bundles already-validated install/verify/support paths.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** installer implementation details and minimal privileged operations on macOS.
- **Phase 5:** distribution channel details (zip signing/notarization decisions if required).

Phases with standard patterns (skip research-phase):
- **Phase 2:** n8n export/import mechanics are documented and straightforward.
- **Phase 3:** smoke-test orchestration is a standard scriptable verification pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions and compatibility verified via official docs/PyPI/npm |
| Features | HIGH | Directly aligned to explicit user-defined shippability outcomes |
| Architecture | HIGH | Brownfield constraints and existing boundaries are clear |
| Pitfalls | HIGH | Matches known failure modes in local automation distribution projects |

**Overall confidence:** HIGH

### Gaps to Address

- Decide whether v1 needs macOS notarization/signing for distribution convenience.
- Decide if optional keychain integration is in-scope for v1.x or deferred.
- Validate clean-machine timing against the 20-minute target with at least one dry run.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — explicit goals and constraints
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` — current system boundaries and risks
- https://docs.n8n.io/hosting/installation/npm/ — Node compatibility for n8n
- https://docs.n8n.io/workflows/export-import/ — workflow import/export behavior
- https://pypi.org/project/fastapi/ — current FastAPI release line
- https://pypi.org/project/playwright/ — current Playwright release line
- https://pypi.org/project/browser-use/ — current browser-use release line and Python requirement
- https://www.npmjs.com/package/pm2 — current PM2 release line

### Secondary (MEDIUM confidence)
- Existing operational scripts/docs in repo (`scripts/`, `docs/`) for installability and support patterns

### Tertiary (LOW confidence)
- None

---
*Research completed: 2026-02-17*
*Ready for roadmap: yes*
