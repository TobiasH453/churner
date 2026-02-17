# Architecture Research

**Domain:** Local downloadable automation workflow product (subsequent milestone)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Onboarding / UX Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ install.sh   │  │ README/Guide │  │ Smoke Test CLI   │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                   │             │
├─────────┴─────────────────┴───────────────────┴─────────────┤
│                    Runtime Service Layer                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐   ┌───────────────┐   ┌────────────────┐ │
│  │ FastAPI Agent │   │ n8n Workflow  │   │ PM2 Supervisor │ │
│  └──────┬────────┘   └──────┬────────┘   └──────┬─────────┘ │
│         │                   │                   │           │
├─────────┴───────────────────┴───────────────────┴───────────┤
│                 Automation + State Layer                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ Amazon Flows  │  │ EB Flows      │  │ Local Profiles   │ │
│  │ (Playwright)  │  │ (Playwright + │  │ + Logs + .env    │ │
│  │               │  │ browser-use)  │  │                  │ │
│  └───────────────┘  └───────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Installer | Provision local prerequisites and project runtime | `install.sh` + preflight checks + deterministic command order |
| Runtime supervisor | Keep API + n8n alive and visible | PM2 ecosystem config + helper scripts |
| Workflow import boundary | Ensure n8n side is reproducible | Versioned workflow JSON + import guide |
| API boundary | Typed request/response entrypoint for automation | FastAPI + Pydantic models |
| Browser automation | Execute fragile third-party web flows reliably | Deterministic Playwright steps with constrained LLM fallback |
| Diagnostics | Shorten recovery/support cycle | log collection + env validation + troubleshooting mapping |

## Recommended Project Structure

```
.planning/
  PROJECT.md
  REQUIREMENTS.md
  ROADMAP.md
  STATE.md
  research/

scripts/
  install.sh
  services-up.sh
  services-down.sh
  services-status.sh
  services-logs.sh
  smoke-test.sh
  collect-diagnostics.sh

n8n-workflows/
  1step_cashouts.workflow.json

docs/
  QUICKSTART.md
  TROUBLESHOOTING.md
  SECURITY.md

src (current root python modules retained for v1)
```

### Structure Rationale

- **`scripts/`:** keeps operator-facing commands centralized and script-auditable.
- **`n8n-workflows/`:** creates a versioned source of truth for workflow import.
- **`docs/`:** separates quickstart from deep troubleshooting and security guidance.
- **Current Python layout:** retained for v1 to avoid destabilizing a working system during ship hardening.

## Architectural Patterns

### Pattern 1: Preflight -> Install -> Verify pipeline

**What:** Installer is split into strict phases with explicit fail-fast checks.
**When to use:** Any local tool targeting non-technical operators.
**Trade-offs:** Slightly more scripting work up front, much less support entropy.

**Example:**
```bash
check_prereqs || exit 1
install_runtime || exit 1
run_smoke_test || exit 1
```

### Pattern 2: Generated local config from templates

**What:** Keep committed examples only; generate local secret-bearing config at install time.
**When to use:** Any flow handling API keys/account credentials.
**Trade-offs:** Slightly longer setup, materially safer distribution.

**Example:**
```bash
cp .env.example .env
./scripts/validate-env.sh
```

### Pattern 3: Deterministic core + constrained LLM edge handling

**What:** Keep auth-critical and high-risk actions deterministic; use LLM for limited matching tasks.
**When to use:** Browser automation against unstable third-party UIs.
**Trade-offs:** More code than pure-agent flows, much stronger reliability.

## Data Flow

### Request Flow

```
[Amazon email event in n8n]
    ↓
[n8n workflow parses payload]
    ↓
[POST /process-order]
    ↓
[BrowserAgent route by email type/account]
    ↓
[Amazon scrape + EB submission path]
    ↓
[Structured response to n8n]
```

### State Management

```
[.env + local profiles + logs]
    ↓
[Runtime services read local state]
    ↓
[Automation executes]
    ↓
[Diagnostics and smoke tests verify state]
```

### Key Data Flows

1. **Install flow:** prerequisites -> environment -> dependency installation -> service startup -> smoke test.
2. **Operational flow:** webhook ingestion -> deterministic browser actions -> typed response -> observability logs.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-10 operators | Current single-machine local model is sufficient |
| 10-100 operators | Harden installer idempotency, diagnostics quality, and docs coverage |
| 100+ operators | Introduce managed distribution/update channel and platform abstraction |

### Scaling Priorities

1. **First bottleneck:** support load from setup drift -> solve with strict preflight + diagnostics.
2. **Second bottleneck:** external UI breakage -> solve with contract tests and selector update playbook.

## Anti-Patterns

### Anti-Pattern 1: "Just run these 20 commands"

**What people do:** Put setup in README only without enforced sequencing.
**Why it's wrong:** Non-technical users diverge quickly and failures are hard to reproduce.
**Do this instead:** Script setup path and keep docs as explanation, not execution engine.

### Anti-Pattern 2: Bundled stateful profiles/secrets

**What people do:** Ship pre-populated browser/session data for convenience.
**Why it's wrong:** Security exposure and machine-specific breakage.
**Do this instead:** Local-first login initialization with explicit session persistence steps.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| n8n | importable workflow + webhook contract | keep JSON artifact versioned and documented |
| Amazon web UI | Playwright persistent profile automation | expect selector drift; maintain fallback strategy |
| ElectronicsBuyer web UI | deterministic auth + constrained deal/tracking flows | OTP/session handling must remain user-aware |
| Anthropic API | env-provided key for browser-use LLM tasks | never log key; validate presence and shape |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| n8n -> FastAPI | HTTP JSON contract | typed by `EmailData`/`AgentResponse` |
| FastAPI -> automation classes | direct Python calls | preserve clear exception boundaries |
| installer -> runtime scripts | shell command orchestration | keep idempotent and explicit |

## Sources

- `.planning/PROJECT.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- https://docs.n8n.io/workflows/export-import/
- https://docs.n8n.io/hosting/installation/npm/

---
*Architecture research for: local automation productization milestone*
*Researched: 2026-02-17*
