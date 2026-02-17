# Pitfalls Research

**Domain:** Shipping a local automation workflow to non-technical macOS users (subsequent milestone)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Installer drift from documentation

**What goes wrong:**
Users follow docs but scripts changed (or vice versa), producing inconsistent setup states.

**Why it happens:**
Docs and scripts evolve separately without a release checklist tying them together.

**How to avoid:**
Treat `install.sh` + smoke test as canonical execution path; docs reference commands instead of duplicating logic.

**Warning signs:**
Support issues contain "I followed README" but environment differs from expected script output.

**Phase to address:**
Phase 1 (Installer and onboarding baseline)

---

### Pitfall 2: Secret leakage during setup or diagnostics

**What goes wrong:**
Credentials leak into logs, screenshots, or bundled files.

**Why it happens:**
Convenience logging and quick debug scripts print full env or copy sensitive files.

**How to avoid:**
Never echo secret values; redact diagnostics output; keep `.env` local-only and gitignored; include explicit secret-handling checks.

**Warning signs:**
Logs contain full API keys/email credentials; diagnostics tarball includes `.env` raw.

**Phase to address:**
Phase 1 and Phase 4 (security hardening and support tooling)

---

### Pitfall 3: n8n workflow/package mismatch

**What goes wrong:**
Shipped package does not include the exact workflow version expected by the API contract.

**Why it happens:**
Workflow edits happen in n8n UI but exports are not versioned back into repo.

**How to avoid:**
Version workflow JSON in `n8n-workflows/`, include import guide, and include contract check in smoke test.

**Warning signs:**
POST payloads missing required fields or wrong `email_type`/`account_type` values after import.

**Phase to address:**
Phase 2 (workflow packaging and contract verification)

---

### Pitfall 4: One-machine assumptions fail on fresh installs

**What goes wrong:**
Workflow runs on maintainer machine but fails on clean Mac due missing runtime dependencies.

**Why it happens:**
Implicit local assumptions (brew packages, Playwright browser install, PM2 global install).

**How to avoid:**
Preflight checks for Node/Python/Playwright/PM2 with actionable install steps and explicit pass/fail output.

**Warning signs:**
Install issues cluster around first run (`command not found`, browser launch failures, pm2 missing).

**Phase to address:**
Phase 1 (installer preflight)

---

### Pitfall 5: False-positive "it works" validation

**What goes wrong:**
Health endpoints pass but order/shipping business paths still fail.

**Why it happens:**
Validation only checks process uptime, not functional flow.

**How to avoid:**
Ship a smoke test that checks health + representative order and shipping flow contract outcomes.

**Warning signs:**
`/health` is green but user reports failed cashout/tracking submissions.

**Phase to address:**
Phase 3 (ship-gate verification)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Manual one-off setup commands | Faster initial hacking | Non-reproducible installs and fragile onboarding | Never for v1 shipping |
| Hardcoding local paths in scripts | Quick local success | Breakage on other machines/users | Only temporary during prototyping |
| Mixing install and runtime scripts | Fewer files initially | Hard to debug or rerun safely | Never for supportable release |
| Skipping workflow versioning | Less process overhead | Hidden contract drift between n8n and API | Never once shipping to users |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| n8n workflow import | Editing workflow in UI but not re-exporting into repo | Keep exported JSON under version control and tie release to that artifact |
| PM2 service runtime | Starting processes manually outside ecosystem config | Use `ecosystem.config.js` as single runtime source and script wrappers |
| Playwright setup | Installing Python deps but skipping browser install | Run `python -m playwright install chromium` in installer |
| Env validation | Checking only existence, not shape | Validate required fields and obvious format expectations (without printing values) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Reinstall-every-run scripts | Setup takes too long, users abandon flow | Make install idempotent and separate from runtime start | Breaks immediately for repeated usage |
| Verbose debug logging by default | Large logs and accidental sensitive context capture | Default to concise logs, gated debug mode | Breaks with real user support volume |
| No bounded retries in automation | Hangs and long support loops | Keep explicit timeouts/retries with clear failure flags | Breaks under external site instability |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing `.env` or secret-bearing files | Credential compromise | Strict gitignore + preflight guard + release checklist |
| Bundling browser profile directories in zip | Session hijack and portability failures | Exclude profile dirs from distribution, recreate locally |
| Printing env in diagnostics | Secret exfiltration during support | Redaction-first diagnostics script and explicit denylist |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Generic installer errors | User cannot self-recover | Actionable error text with exact next command |
| Hidden required manual steps | User believes install is complete when it is not | Explicit checklist for manual login/session priming |
| Too many branching options in docs | Decision fatigue and mistakes | Linear default path, advanced options in separate section |

## "Looks Done But Isn't" Checklist

- [ ] **Installer:** Often missing Playwright browser install — verify Chromium binary exists post-install
- [ ] **Workflow packaging:** Often missing actual JSON artifact — verify `n8n-workflows/*.json` is present and import-tested
- [ ] **Security:** Often missing secret redaction — verify diagnostics output never contains full key values
- [ ] **Verification:** Often missing business-path tests — verify both order and shipping smoke tests pass
- [ ] **Supportability:** Often missing recovery tooling — verify diagnostics script and troubleshooting doc are both available

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Installer drift | MEDIUM | Regenerate docs from canonical script path, rerun smoke test on clean machine |
| Secret leak risk | HIGH | Rotate exposed secrets, patch scripts/docs, add guard tests |
| Workflow mismatch | MEDIUM | Re-export and version workflow JSON, rerun contract smoke tests |
| Fresh-machine failures | LOW-MEDIUM | Improve preflight checks and rerun install path |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Installer drift | Phase 1 | Clean-machine install succeeds using docs and scripts only |
| Secret leakage | Phase 1 + 4 | Diagnostics/log review confirms redaction and local-only secret handling |
| Workflow mismatch | Phase 2 | Import workflow and run contract smoke test payloads |
| False-positive validation | Phase 3 | Smoke test includes order + shipping functional checks |

## Sources

- `.planning/PROJECT.md`
- `.planning/codebase/CONCERNS.md`
- https://docs.n8n.io/workflows/export-import/
- https://docs.n8n.io/hosting/installation/npm/
- Project-specific operational constraints from existing scripts and architecture

---
*Pitfalls research for: local automation productization milestone*
*Researched: 2026-02-17*
