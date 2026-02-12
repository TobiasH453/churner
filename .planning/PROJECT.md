# Amazon Email Automation

## What This Is

A business automation system that processes Amazon order and shipping confirmation emails autonomously. The system monitors Gmail via n8n, qualifies emails using AI, then uses Python browser automation to scrape data from Amazon and electronicsbuyer.gg, updating Google Sheets and sending Telegram notifications. Currently operational through n8n → Python webhook layer, blocked on browser automation stability.

## Core Value

Browser automation must successfully navigate Amazon and extract real order/shipping data - not placeholders. Without reliable data extraction, the entire downstream workflow (electronicsbuyer.gg submission, Sheet updates, notifications) processes invalid data.

## Requirements

### Validated

**Working infrastructure (Phases 1-2 complete):**
- ✓ n8n workflow orchestration installed and running — Phase 1
- ✓ Python FastAPI webhook server receives POST requests successfully — Phase 2
- ✓ n8n Gmail trigger, Claude qualification, HTTP Request node working — Phase 2
- ✓ Email data correctly formatted and sent to Python server — Phase 2
- ✓ Browser profile and cookie persistence configured — Phase 2
- ✓ Python environment with browser-use, Playwright, Anthropic SDK — Phase 1

### Active

**Browser automation layer (currently blocked):**
- [ ] Browser-use agent stays open and navigates Amazon (currently crashes after opening)
- [ ] Scrape Amazon order confirmation: items, quantities, prices, cashback %, arrival date
- [ ] Scrape Amazon shipping confirmation: tracking number, carrier, delivery date
- [ ] Parse extracted content into structured OrderDetails/ShippingDetails models (currently returns NEEDS_PARSING placeholders)
- [ ] Submit deal to electronicsbuyer.gg and extract payout value
- [ ] Submit tracking to electronicsbuyer.gg
- [ ] Return parsed data to n8n for Google Sheets update
- [ ] Error handling that propagates failures (not silent placeholders)

**Integration layer:**
- [ ] Google Sheets append for order confirmations (columns A-G, J)
- [ ] Google Sheets update for shipping confirmations (find by order number, update J and M)
- [ ] Telegram success notifications
- [ ] Telegram error alerts

**Reliability:**
- [ ] 95%+ success rate on email processing
- [ ] Retry logic for transient failures
- [ ] Graceful error handling with user-visible alerts
- [ ] Processing time <5 minutes per email

### Out of Scope

- Mobile app interface — Web automation only
- Real-time processing — 15-minute polling acceptable
- Multi-account support — Single Amazon account only
- Historical email processing — Future emails only
- Automatic 2FA handling — Manual intervention acceptable for auth challenges

## Context

**Existing Documentation:**
- `CLAUDE.md` — Complete project overview, business rules, architecture decisions, troubleshooting
- `IMPLEMENTATION_PLAN.md` — 8-phase implementation plan with exact commands
- `.planning/codebase/` — Codebase analysis (STACK.md, ARCHITECTURE.md, CONCERNS.md, etc.)

**Current Blocker:**
Browser opens to Amazon homepage then closes within seconds. No Python errors shown, but returns placeholder "NEEDS_PARSING" data. Testing via n8n webhook with real email data.

**Key Business Rules (from CLAUDE.md):**
- ONLY process emails where recipient is "CSC LLC" OR "CSG"
- REJECT California addresses and "Tobias Halpern"
- Order confirmations → scrape invoice, submit deal to EB.gg, append Sheet row
- Shipping confirmations → scrape tracking, submit to EB.gg, update existing Sheet row

**Architecture:**
```
Gmail → n8n (orchestration) → Python FastAPI (browser automation) → Google Sheets
                                        ↓
                             Amazon + electronicsbuyer.gg
                                        ↓
                                  Telegram alerts
```

**Critical Files:**
- `main.py` — FastAPI webhook server (port 8080)
- `browser_agent.py` — Routes order vs shipping, coordinates scrapers
- `amazon_scraper.py` — browser-use agent for Amazon navigation (BROKEN)
- `electronics_buyer.py` — browser-use agent for EB.gg (untested)
- `models.py` — Pydantic data models (OrderDetails, ShippingDetails, etc.)
- `data/amazon_cookies.json` — Saved session (already configured)

**Known Issues (from CONCERNS.md):**
- Data parsing completely stubbed (lines 75-91, 136-142 in amazon_scraper.py)
- Broad exception handling masks real errors
- LLM timeout set to 60s (may be too low)
- No retry logic implemented despite MAX_RETRIES env var
- Agent max_actions_per_step may be too low (3 for orders, 5 for shipping)

## Constraints

- **Platform**: macOS (Darwin 25.2.0), must run locally on MacBook 24/7
- **Browser**: Visible mode (headless=false) for supervision
- **API Costs**: Minimize Claude API calls where possible, budget $5-15/month
- **Reliability**: 95%+ success rate critical - this processes real business transactions
- **User Skill**: Beginner technical level - needs copy/paste commands, clear error messages
- **Dependencies**: Python 3.9.6, Node.js 22.22.0, n8n, pm2, browser-use 0.1.15+
- **Authentication**: Amazon session cookies (monthly refresh), EB.gg username/password
- **Processing Time**: Target <5 minutes per email, <20 minutes end-to-end

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid n8n + Python architecture | n8n handles integrations visually, Python handles complex browser work | ✓ Good - n8n layer working, Python layer needs debugging |
| browser-use library with Claude | AI-powered navigation more reliable than brittle selectors | — Pending - library works but agent crashes immediately |
| Visible browser mode | User wants supervision, easier debugging | ✓ Good - can see browser open to Amazon before crash |
| Local execution (not cloud) | Privacy, supervision, no deployment complexity | ✓ Good - matches user's comfort level |
| FastAPI webhook bridge | Decouples n8n from browser automation, easier testing | ✓ Good - clean separation, webhook working |
| Cookie-based Amazon auth | Avoid login on every request, session persistence | — Pending - cookies saved but browser exits before using them |

---
*Last updated: 2026-02-12 after initialization*
