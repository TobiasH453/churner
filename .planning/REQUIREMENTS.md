# Requirements: Amazon Email Automation

**Defined:** 2026-02-12
**Core Value:** Browser automation must successfully navigate Amazon and extract real order/shipping data - not placeholders

## v1 Requirements

### Critical Fixes (Must Complete First)

- [ ] **FIX-01**: Add `output_model_schema` parameter to amazon_scraper.py Agent with OrderDetails/ShippingDetails Pydantic models
- [ ] **FIX-02**: Remove redundant login steps from task prompts (trust persistent session)
- [ ] **FIX-03**: Replace `except Exception` placeholder returns with proper error raising
- [ ] **FIX-04**: Validate `result.extracted_content` is not empty before returning data

### Data Extraction (Core Capability)

- [ ] **EXTRACT-01**: Parse Amazon order confirmation for: items, quantities, prices, cashback %, arrival date
- [ ] **EXTRACT-02**: Parse Amazon shipping confirmation for: tracking number, carrier, delivery date
- [ ] **EXTRACT-03**: Validate extracted data semantically (prices > $0, valid dates, tracking format)
- [ ] **EXTRACT-04**: Normalize item format to natural language ("3x iPad 128GB Blue")

### Reliability (95%+ Success Target)

- [ ] **RELIABLE-01**: Implement retry logic with exponential backoff (3 attempts: 1s, 2s, 4s)
- [ ] **RELIABLE-02**: Increase timeouts (step_timeout=180s, max_failures=6)
- [ ] **RELIABLE-03**: Add debug artifacts (GIF recording, conversation logs) for troubleshooting
- [ ] **RELIABLE-04**: Session validation before agent runs (check cookies, trigger re-login if expired)

### ElectronicsBuyer Integration

- [ ] **EB-01**: Submit deal to electronicsbuyer.gg and extract payout value
- [ ] **EB-02**: Submit tracking to electronicsbuyer.gg
- [ ] **EB-03**: Handle EB.gg errors gracefully (retry transient, alert fatal)

### Google Sheets Updates

- [ ] **SHEETS-01**: Append new row for order confirmations (columns A-G, J)
- [ ] **SHEETS-02**: Update existing row for shipping confirmations (find by order number, update J and M)

### Notifications

- [ ] **NOTIFY-01**: Telegram success notification with key details (order #, items, payout)
- [ ] **NOTIFY-02**: Telegram error alerts with failure reason

## v2 Requirements

Deferred to future milestones after v1 is stable.

### Advanced Reliability

- **RELIABLE-05**: Confidence scoring per extracted field
- **RELIABLE-06**: Partial success handling (return what parsed + flag missing fields)
- **RELIABLE-07**: Multi-strategy extraction (fallback to DOM if vision fails)

### Monitoring

- **MONITOR-01**: Duplicate detection (SQLite cache of processed order numbers)
- **MONITOR-02**: Rate limiting (60-90s cooldown between Amazon requests)
- **MONITOR-03**: Dashboard showing success rates, processing times, error trends

### Advanced Features

- **ADVANCED-01**: Multi-carrier auto-detection (UPS, FedEx, USPS patterns)
- **ADVANCED-02**: Invoice PDF parsing for complex line items
- **ADVANCED-03**: Historical email sync (backfill past orders)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Headless browser mode | User explicitly wants visible supervision |
| Real-time processing (<1 min) | Triggers Amazon bot detection, 15-min polling acceptable |
| 100% extraction accuracy | Impossible standard, 95% is industry-proven achievable |
| CSS selector parsing | Brittle approach, AI agents adapt better to UI changes |
| Multi-account support | Single Amazon account only, reduces complexity |
| 2FA automation | Requires manual intervention, acceptable for monthly re-auth |
| Alternative framework migration | Only if browser-use fundamentally broken after fixes |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIX-01 | Phase 1 | Pending |
| FIX-02 | Phase 1 | Pending |
| FIX-03 | Phase 1 | Pending |
| FIX-04 | Phase 1 | Pending |
| EXTRACT-01 | Phase 2 | Pending |
| EXTRACT-02 | Phase 2 | Pending |
| EXTRACT-03 | Phase 2 | Pending |
| EXTRACT-04 | Phase 2 | Pending |
| RELIABLE-01 | Phase 3 | Pending |
| RELIABLE-02 | Phase 3 | Pending |
| RELIABLE-03 | Phase 3 | Pending |
| RELIABLE-04 | Phase 3 | Pending |
| EB-01 | Phase 4 | Pending |
| EB-02 | Phase 4 | Pending |
| EB-03 | Phase 4 | Pending |
| SHEETS-01 | Phase 5 | Pending |
| SHEETS-02 | Phase 5 | Pending |
| NOTIFY-01 | Phase 5 | Pending |
| NOTIFY-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after roadmap creation*
