# Roadmap: Amazon Email Automation

## Overview

This roadmap transforms a broken browser automation system into a reliable end-to-end workflow. Phase 1 fixes the immediate blocker (browser crashes on launch), Phase 2 implements data extraction from Amazon, Phase 3 hardens reliability to 95%+ success rate, Phase 4 integrates ElectronicsBuyer submission, and Phase 5 completes the workflow with Google Sheets updates and Telegram notifications. The existing n8n orchestration layer and FastAPI webhook server are already operational - this roadmap focuses exclusively on making browser automation extract real data instead of placeholders.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Browser Automation Fix** - Fix structured output validation causing immediate crashes
- [ ] **Phase 2: Amazon Data Extraction** - Extract real order/shipping data from Amazon pages
- [ ] **Phase 3: Reliability Hardening** - Achieve 95%+ success rate with retries and timeouts
- [ ] **Phase 4: ElectronicsBuyer Integration** - Submit deals/tracking to EB.gg and extract payout values
- [ ] **Phase 5: End-to-End Integration** - Complete workflow with Sheets updates and notifications

## Phase Details

### Phase 1: Browser Automation Fix
**Goal**: Browser agent completes Amazon navigation tasks without crashing
**Depends on**: Nothing (first phase)
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04
**Success Criteria** (what must be TRUE):
  1. Browser agent launches and navigates to Amazon order pages without crashing
  2. Agent returns structured data matching Pydantic models (no validation errors)
  3. Agent completes task without placeholder "NEEDS_PARSING" returns
  4. Debug artifacts (GIF recording, conversation logs) show successful navigation
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 2: Amazon Data Extraction
**Goal**: Extract real order/shipping data from Amazon pages
**Depends on**: Phase 1
**Requirements**: EXTRACT-01, EXTRACT-02, EXTRACT-03, EXTRACT-04
**Success Criteria** (what must be TRUE):
  1. Order confirmations return all required fields: items, quantities, prices, cashback %, arrival date
  2. Shipping confirmations return all required fields: tracking number, carrier, delivery date
  3. Extracted data passes semantic validation (prices > $0, valid date formats, tracking patterns match carriers)
  4. Items are formatted in natural language ("3x iPad 128GB Blue, 1x Amazon Fire Stick HD")
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 3: Reliability Hardening
**Goal**: System achieves 95%+ success rate on email processing
**Depends on**: Phase 2
**Requirements**: RELIABLE-01, RELIABLE-02, RELIABLE-03, RELIABLE-04
**Success Criteria** (what must be TRUE):
  1. Transient failures (timeouts, network issues) automatically retry with exponential backoff
  2. Agent completes 95%+ of test orders within timeout limits
  3. Failed attempts produce debug artifacts (GIFs, logs, screenshots) for troubleshooting
  4. Expired Amazon sessions are detected and trigger re-login before agent runs
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 4: ElectronicsBuyer Integration
**Goal**: Submit deals/tracking to EB.gg and extract payout values
**Depends on**: Phase 2
**Requirements**: EB-01, EB-02, EB-03
**Success Criteria** (what must be TRUE):
  1. Agent submits order deals to electronicsbuyer.gg and returns total payout value
  2. Agent submits shipping tracking to electronicsbuyer.gg successfully
  3. EB.gg transient errors (maintenance, timeouts) retry automatically without failing workflow
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 5: End-to-End Integration
**Goal**: Complete workflow from email to Sheet update with notifications
**Depends on**: Phase 4
**Requirements**: SHEETS-01, SHEETS-02, NOTIFY-01, NOTIFY-02
**Success Criteria** (what must be TRUE):
  1. Order confirmation emails trigger new Google Sheets rows with all columns (A-G, J) populated
  2. Shipping confirmation emails update existing Google Sheets rows (find by order number, update columns J and M)
  3. Successful processing sends Telegram notification with key details (order number, items, payout value)
  4. Failed processing sends Telegram error alert with failure reason for user intervention
**Plans**: TBD

Plans:
- [ ] TBD during planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Browser Automation Fix | 0/TBD | Not started | - |
| 2. Amazon Data Extraction | 0/TBD | Not started | - |
| 3. Reliability Hardening | 0/TBD | Not started | - |
| 4. ElectronicsBuyer Integration | 0/TBD | Not started | - |
| 5. End-to-End Integration | 0/TBD | Not started | - |
