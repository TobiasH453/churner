# Phase 3: ElectronicsBuyer Submission Hardening - Context

**Gathered:** 2026-02-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers reliable ElectronicsBuyer deal and tracking submission behavior for daily operation, with clear failure signaling. This phase hardens submission behavior and error outcomes; it does not add new product capabilities outside EB submission reliability.

</domain>

<decisions>
## Implementation Decisions

### Deal Submission Success Criteria
- Deal submission is only successful when commit succeeds and payout value is captured for all submitted items.
- Multi-item orders must commit and capture payout per item; partial payout capture is a failure state.
- Submission may proceed for matched items, but unmatched items must be explicitly flagged.

### Deal Matching and Duplicate Policy
- Matching is fuzzy by name, but meaningful specs must be preserved (example: model/capacity/color such as "iPad 128GB Blue").
- Quantity must match exactly.
- If some items are unmatched: submit matched items and flag unmatched items.
- Retry duplicate policy: allow retry only when no prior confirmation ID exists.

### Tracking Submission Success Criteria
- Tracking submission success is based on successful submit outcome/message.
- Required inputs: tracking number + items.
- If item content is incomplete or messy at submit time: treat as failure and flag.
- If tracking number already exists on EB side: block submission and flag duplicate.

### Run-Time Guardrail for Validation
- Validation/test cycles for this phase should remain short (target: about 2 minutes max).
- Avoid long retry loops during verification and iteration.

### Codex's Discretion
- Exact structure/wording of flags and error messages returned to callers.
- Retry/backoff tuning details within the 2-minute validation constraint.
- Internal ordering of field validation and pre-submit checks.
- Operator-facing review formatting for flagged unmatched/duplicate cases.

</decisions>

<specifics>
## Specific Ideas

- Current process already has major working pieces: persistent login is stable and dashboard button commands work.
- Manual baseline test has been run before making changes.
- Baseline failure signature to preserve in planning/research context:
  - Tracking submission reached EB tracking page but failed with:
    - `Tracking number input not found in tracking modal on page: https://electronicsbuyer.gg/app/tracking-submissions`
    - occurred after 2 deterministic attempts
  - Example response showed `execution_time_seconds: 16.37`
- Baseline data quality signal observed in extracted shipping items: noisy entries appeared (e.g., `"( /count)"`, `"Typical:"`) mixed with valid items.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within the Phase 3 boundary.

</deferred>

---

*Phase: 03-electronicsbuyer-submission-hardening*
*Context gathered: 2026-02-15*
