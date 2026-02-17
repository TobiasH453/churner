# Feature Research

**Domain:** Shippable local automation package for email-to-cashout workflow (subsequent milestone)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Guided installer (`install.sh`) | Non-technical users expect setup to be scripted, not assembled | MEDIUM | Must handle prereq checks, env template creation, dependency install |
| Clear setup documentation | Downloadable tools are expected to include exact startup steps | LOW | Quickstart + troubleshooting must match scripts exactly |
| Importable n8n workflow artifact | n8n-based products are expected to provide reusable workflow JSON | LOW | Keep JSON versioned and include import walkthrough |
| Secure secret bootstrap | Users expect credentials to stay local and never leak into repo/zip | MEDIUM | `.env.example` + validation + redaction-safe diagnostics |
| Service lifecycle commands | Operators expect `up/down/status/logs` commands | LOW | Already present; must be documented and verified |
| Post-install smoke test | Users expect proof it works on their machine | MEDIUM | Single command to validate health + order + shipping flow routing |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 20-minute setup target with measured preflight | Makes this realistically deployable by semi-technical users | MEDIUM | Enforce timed, linear install path with clear failure messages |
| Diagnostics bundle script | Reduces support turnaround and user frustration | MEDIUM | Collect logs/config metadata with secret redaction |
| Safety-first install guardrails | Builds trust for users handling real credentials | MEDIUM | Block risky defaults (secret echo, profile bundling, insecure perms) |
| Optional one-liner bootstrap wrapper | Faster onboarding for users comfortable with terminal | LOW | Secondary path that calls audited `install.sh` |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Fully automatic auth bypass for Amazon/EB | Users want zero login friction | Fragile and security-risky with OTP/session controls outside app control | Guided first-login step + persistent profile reuse |
| Cross-platform v1 installer | Desire broader audience quickly | Multiplies support matrix and delays shippable macOS baseline | Ship macOS first, expand after stable release |
| Hidden "magic" installer with no checkpoints | Feels easier initially | Hard to debug failures and creates support dead ends | Explicit preflight + actionable error output |

## Feature Dependencies

```
Installer Preflight
    └──requires──> Prerequisite Detection
                       └──requires──> Deterministic Install Steps

n8n Workflow Import Guide
    └──requires──> Versioned Workflow JSON

Smoke Test Command
    └──requires──> Running Services (API + n8n)
                       └──requires──> Valid .env and Local Profiles

Diagnostics Script ──enhances──> Troubleshooting Docs

One-liner Bootstrap ──enhances──> Installer UX
```

### Dependency Notes

- **Smoke test requires service lifecycle stability:** without reliable `up/status` behavior, pass/fail is ambiguous.
- **Workflow guide requires versioned JSON artifacts:** docs without a concrete import file create mismatch risk.
- **Diagnostics script enhances troubleshooting docs:** docs alone are slower when users cannot gather consistent debug data.

## MVP Definition

### Launch With (v1)

- [ ] One-step `install.sh` with clear preflight checks and actionable failures — essential for non-technical onboarding
- [ ] `.env.example` + secure env validator — essential for safe setup
- [ ] Importable n8n workflow JSON + import guide — essential for end-to-end operability
- [ ] Smoke test command covering health + order + shipping paths — essential for ship confidence
- [ ] Troubleshooting runbook + diagnostics collection script — essential for supportability

### Add After Validation (v1.x)

- [ ] Optional one-liner bootstrap wrapper — add after installer path is stable
- [ ] Optional macOS keychain helpers for selected secrets — add once baseline secure flow is stable
- [ ] Improved interactive UX in installer (progress display, richer prompts) — add after core reliability

### Future Consideration (v2+)

- [ ] Linux support — defer until macOS support burden is predictable
- [ ] Docker packaging — defer until local-first UX and auth/session assumptions are validated
- [ ] Windows support — defer until platform-specific browser/profile constraints are designed

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Guided installer | HIGH | MEDIUM | P1 |
| Secure env bootstrap | HIGH | MEDIUM | P1 |
| Importable workflow + guide | HIGH | LOW | P1 |
| Smoke test command | HIGH | MEDIUM | P1 |
| Troubleshooting + diagnostics | HIGH | MEDIUM | P1 |
| One-liner bootstrap wrapper | MEDIUM | LOW | P2 |
| Keychain helper integration | MEDIUM | MEDIUM | P2 |
| Cross-platform packaging | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Typical automation projects | Typical internal scripts | Our Approach |
|---------|-----------------------------|--------------------------|--------------|
| Installer UX | Often ad-hoc README steps | Usually maintainer-only setup | Scripted installer + explicit checks for semi-technical users |
| Workflow packaging | Sometimes missing import-ready assets | Usually manually reconstructed | Versioned n8n workflow artifact + guide |
| Diagnostics | Usually manual log collection | Often undocumented | First-class diagnostics command + troubleshooting map |
| Security defaults | Mixed; secrets sometimes leaked in docs/examples | Commonly weak in quick scripts | Strict local secrets flow and redacted diagnostics |

## Sources

- `.planning/PROJECT.md` and `.planning/codebase/*` (existing system capabilities and constraints)
- https://docs.n8n.io/workflows/export-import/ (workflow portability expectations)
- https://docs.n8n.io/hosting/installation/npm/ (runtime prerequisite expectations)
- Productization patterns inferred from local-operability requirements and supportability goals

---
*Feature research for: local automation productization milestone*
*Researched: 2026-02-17*
