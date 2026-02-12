# Feature Research: E-commerce Data Scraping Workflows

**Domain:** Amazon order/shipping automation with AI-powered browser agents
**Researched:** 2026-02-12
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features without which the data extraction workflow fundamentally fails.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Structured Data Extraction** | Core functionality - must extract items, quantities, prices, dates into defined schema | MEDIUM | Uses Pydantic models + LLM structured output. Research shows 95-99% field-level accuracy achievable. Currently stubbed. |
| **Session Persistence** | Amazon login required - can't re-authenticate every run (rate limits, 2FA) | LOW | Cookie-based persistence via browser profile. Already implemented in project (USER_DATA_DIR). |
| **Page Navigation** | Must reach invoice/tracking pages to extract data | MEDIUM | Direct URL navigation better than multi-click flows. Currently implemented but agent exits prematurely. |
| **Multi-Field Parsing** | Invoice has ~10 fields (items, totals, dates), tracking has 4-5 fields | MEDIUM | LLM vision + structured prompts. Line item tables require table detection logic. |
| **Error Propagation** | Silent failures with placeholder data breaks downstream (Sheet updates, EB.gg) | LOW | Currently masked by broad try-except. Must raise exceptions on parse failures. |
| **Dynamic Content Handling** | Amazon pages load via JavaScript, not static HTML | LOW | Playwright handles this natively. Browser-use waits for page load. No action needed. |
| **Data Validation** | Must verify extracted values match expected formats before returning | MEDIUM | Pydantic validates schema. Need semantic validation (price > $0, date is future, tracking # format). |
| **Retry Logic** | Network timeouts, slow page loads require retries with backoff | MEDIUM | Currently not implemented despite MAX_RETRIES env var. Exponential backoff recommended. |

### Differentiators (Competitive Advantage)

Features that increase reliability and reduce maintenance burden.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-Powered Parsing** | Adapts to Amazon UI changes without code updates | HIGH | Browser-use + Claude 3.5 Sonnet. 89.1% WebVoyager benchmark success. Already chosen. |
| **Multi-Strategy Extraction** | If vision fails, try DOM parsing; if table fails, try line-by-line | HIGH | Research shows self-healing scrapers reduce downtime by 73%. Implement fallback selectors. |
| **Confidence Scoring** | LLM returns confidence per field (e.g., "tracking number: 85%") | MEDIUM | Enables soft validation - flag low confidence for human review vs hard failure. |
| **Partial Success Handling** | If 8/10 fields parse, return those 8 + flag missing 2 | MEDIUM | Better than all-or-nothing. Allows manual completion vs full re-run. |
| **Data Normalization** | Standardize "3 x iPad" vs "iPad (Qty: 3)" to consistent format | LOW | LLM-powered normalization cleans messy formats. Use structured output with JSON schema. |
| **Duplicate Detection** | Prevent processing same order twice (cache order numbers) | LOW | SQLite state tracking. Check before scraping, log after success. |
| **Stealth Patterns** | Human-like timing, randomized mouse movements, realistic browser fingerprint | MEDIUM | Already implemented (stealth_utils.py). Reduces bot detection risk. |
| **Rate Limiting** | Wait 60-90s between requests to avoid Amazon rate limits | LOW | Critical for ToS compliance. Implement per-order cooldown timer. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem valuable but create more problems than they solve.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-Time Extraction (<1min)** | "Faster is better" | Amazon rate limits at ~1 req/min. Rushing triggers bot detection. Target: 2-5 min/email is safer. | Use n8n 15-min polling. Batch requests if multiple emails. |
| **Headless Browser Mode** | "Runs faster, uses less CPU" | Can't supervise automation. Harder to debug. Amazon detects headless browsers more easily. | Keep visible mode (headless=false). User explicitly requested supervision. |
| **Historical Email Processing** | "Backfill old orders" | Cookie expiration, changed Amazon UI, missing order pages. High failure rate on old data. | Future emails only. Manual entry for historical data if needed. |
| **Perfect Extraction (100%)** | "Must never fail" | Amazon UI changes, network issues, bot detection make 100% impossible. 95% is industry standard. | Target 95%+. Human review queue for failures. Telegram alerts. |
| **CSS Selector Parsing** | "Faster than AI vision" | Breaks on every Amazon UI update. Maintenance nightmare. Research shows 90% less maintenance with AI. | Use browser-use vision mode ('auto'). Selector fallback only if needed. |
| **Multi-Page Scraping** | "Get all order history" | Each page = bot detection risk. User only needs order confirmations (1 invoice/email). | Single page per email. Direct URL navigation. |
| **Screenshot Storage** | "Debug failures later" | 5MB/screenshot × 100 orders = 500MB. Privacy risk (PII in screenshots). | Log text content only. Screenshots on-demand for errors. |

## Feature Dependencies

```
Session Persistence (cookies)
    └──requires──> Page Navigation
                       └──requires──> Structured Data Extraction
                                          └──requires──> Data Validation
                                                             └──requires──> Error Propagation

Retry Logic ──enhances──> Page Navigation
Retry Logic ──enhances──> Structured Data Extraction

AI-Powered Parsing ──enables──> Multi-Strategy Extraction
AI-Powered Parsing ──enables──> Confidence Scoring

Data Validation ──requires──> Data Normalization

Partial Success Handling ──conflicts──> Error Propagation (must choose: fail fast or return partial)

Stealth Patterns ──reduces detection risk for──> Page Navigation
Rate Limiting ──reduces detection risk for──> Page Navigation
```

### Dependency Notes

- **Session Persistence → Navigation → Extraction → Validation → Error Propagation:** Linear pipeline. Each requires previous step to succeed.
- **Retry Logic enhances Navigation and Extraction:** Orthogonal - wraps both operations independently.
- **AI-Powered Parsing enables Multi-Strategy Extraction:** AI can try multiple approaches (vision, DOM, table detection) in one run.
- **Partial Success vs Error Propagation:** Design decision needed. Current code returns placeholders (partial). Should raise exceptions (fail fast) instead.
- **Stealth + Rate Limiting reduce detection:** Both mitigate same risk from different angles. Implement both for maximum safety.

## MVP Definition

### Launch With (v1 - Current Milestone)

Minimum viable scraping - what's needed to replace "NEEDS_PARSING" placeholders.

- [x] **Session Persistence** — Already implemented (USER_DATA_DIR, cookies saved)
- [x] **Page Navigation** — Direct URL navigation implemented (lines 46, 100 in amazon_scraper.py)
- [x] **AI-Powered Parsing** — browser-use + Claude 3.5 Sonnet configured
- [ ] **Structured Data Extraction** — Parse result.extracted_content into Pydantic models (CRITICAL - currently stubbed)
- [ ] **Data Validation** — Pydantic + semantic checks (price > $0, valid date format)
- [ ] **Error Propagation** — Raise exceptions on parse failures, remove placeholders (CRITICAL)
- [ ] **Retry Logic** — 3 attempts with exponential backoff for network/timeout errors
- [ ] **Data Normalization** — Standardize item format ("3x iPad" vs "iPad x3" → consistent)

**v1 Success Criteria:** Extract real data from Amazon invoice/tracking pages with 80%+ success rate. No placeholder data returned.

### Add After Validation (v1.x)

Features to add once core extraction is working and proven.

- [ ] **Multi-Strategy Extraction** — Fallback to DOM parsing if vision fails (trigger: 3 consecutive vision failures)
- [ ] **Confidence Scoring** — LLM returns per-field confidence, flag <70% for human review
- [ ] **Partial Success Handling** — Return successfully parsed fields + list of missing fields
- [ ] **Duplicate Detection** — SQLite cache of processed order numbers (trigger: processing same order twice)
- [ ] **Rate Limiting** — 60-90s cooldown between Amazon requests (trigger: bot detection or rate limit error)

**v1.x Success Criteria:** 95%+ success rate. Self-healing on common errors. Reduced manual intervention.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Stealth Enhancement** — Advanced fingerprinting, canvas randomization (defer: current stealth sufficient)
- [ ] **Multi-Carrier Tracking** — Auto-detect carrier from tracking number format (defer: can parse carrier from page text)
- [ ] **Invoice PDF Parsing** — Extract from PDF if HTML invoice unavailable (defer: HTML sufficient for 95% of cases)
- [ ] **Historical Order Sync** — Backfill old orders from Amazon order history (defer: future emails only in scope)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Structured Data Extraction | HIGH (blocks everything) | MEDIUM (structured output + parsing) | P1 |
| Error Propagation | HIGH (prevents bad data) | LOW (remove try-except, add raises) | P1 |
| Data Validation | HIGH (ensures quality) | MEDIUM (Pydantic + semantic rules) | P1 |
| Retry Logic | HIGH (handles transients) | MEDIUM (backoff algorithm + state) | P1 |
| Data Normalization | MEDIUM (consistent format) | LOW (LLM prompt + schema) | P1 |
| Multi-Strategy Extraction | MEDIUM (increases reliability) | HIGH (multiple parsers + fallback logic) | P2 |
| Confidence Scoring | MEDIUM (enables review queue) | MEDIUM (structured output + threshold logic) | P2 |
| Duplicate Detection | MEDIUM (prevents re-processing) | LOW (SQLite check) | P2 |
| Partial Success Handling | LOW (nice to have) | MEDIUM (partial result model + merge logic) | P2 |
| Rate Limiting | HIGH (avoids bans) | LOW (sleep timer) | P2 |
| Stealth Enhancement | LOW (already sufficient) | HIGH (fingerprint randomization) | P3 |
| Multi-Carrier Tracking | LOW (parse from text) | MEDIUM (regex + API lookups) | P3 |
| Invoice PDF Parsing | LOW (rare edge case) | HIGH (OCR + PDF library) | P3 |
| Historical Order Sync | LOW (out of scope) | HIGH (multi-page scraping + date handling) | P3 |

**Priority key:**
- P1: Must have for milestone completion - blocks downstream workflow
- P2: Should have - increases reliability and reduces maintenance
- P3: Nice to have - defer until core is stable

## Implementation Patterns from Research

### Pattern 1: LLM Structured Output for Extraction

**What:** Use JSON schema to constrain LLM output to exact Pydantic model structure.

**When:** Extracting multi-field data from unstructured page content (invoices, tracking pages).

**Why:** Research shows structured outputs reduce hallucination and ensure schema compliance. Platforms (OpenAI, Anthropic, AWS Bedrock) now support this natively as of 2024.

**Example:**
```python
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic

class InvoiceData(BaseModel):
    items: list[dict[str, str]]
    subtotal: str
    grand_total: str
    cashback_percent: float
    arrival_date: str

# Claude returns JSON matching InvoiceData schema
result = agent.run()
parsed = InvoiceData.parse_raw(result.extracted_content)
```

**Implementation:** Modify amazon_scraper.py lines 75-91 and 136-143 to parse `result.extracted_content` into Pydantic models using structured output.

### Pattern 2: Exponential Backoff Retry

**What:** Retry failed operations with increasing delays (1s, 2s, 4s, 8s...).

**When:** Network timeouts, slow page loads, temporary Amazon errors (5xx, 429).

**Why:** Research shows exponential backoff reduces 429 errors and prevents overwhelming target servers. Industry standard pattern.

**Example:**
```python
import asyncio

MAX_RETRIES = 3
async def scrape_with_retry(order_number):
    for attempt in range(MAX_RETRIES):
        try:
            return await scraper.scrape_order_confirmation(order_number)
        except (TimeoutError, NetworkError) as e:
            if attempt == MAX_RETRIES - 1:
                raise  # Final attempt - propagate error
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
```

**Implementation:** Wrap `scrape_order_confirmation` and `scrape_shipping_confirmation` in retry decorator or explicit loop.

### Pattern 3: Table Detection for Line Items

**What:** Identify table structure in invoice, extract each row as line item.

**When:** Parsing multi-item orders (most orders have 1-5 items, but can have 20+).

**Why:** Research shows modern AI models detect tables without templates. 95-99% accuracy on invoice line items.

**Example:**
```python
task = """
Step 2: Find the line items table. For each row:
- Extract product name, quantity, unit price, total price
- Format as: {"name": "iPad 128GB", "quantity": 2, "price": "$299.99"}

Return array of line items.
"""
```

**Implementation:** Enhance prompt in amazon_scraper.py line 48 to explicitly request table parsing with per-row format.

### Pattern 4: Semantic Validation

**What:** Check extracted values make sense (price > $0, date is future, tracking # matches carrier format).

**When:** After Pydantic schema validation passes but before returning data.

**Why:** Research shows schema validation ensures syntax but not semantics. Must validate values separately.

**Example:**
```python
from datetime import datetime, timedelta

def validate_order_details(order: OrderDetails):
    # Check prices are positive
    if not order.grand_total.startswith('$') or float(order.grand_total[1:]) <= 0:
        raise ValueError(f"Invalid grand_total: {order.grand_total}")

    # Check cashback is reasonable (0-10%)
    if not 0 <= order.cashback_percent <= 10:
        raise ValueError(f"Unlikely cashback_percent: {order.cashback_percent}")

    # Check arrival date is future (or recent past for delays)
    arrival = datetime.strptime(order.arrival_date, '%Y-%m-%d')
    if arrival < datetime.now() - timedelta(days=7):
        raise ValueError(f"Arrival date too far in past: {order.arrival_date}")

    return order
```

**Implementation:** Add validation functions in utils.py, call after parsing in amazon_scraper.py.

### Pattern 5: Carrier Auto-Detection

**What:** Detect carrier from tracking number format using regex patterns.

**When:** Validating tracking numbers, displaying carrier in UI.

**Why:** Research shows tracking numbers follow carrier-specific patterns (UPS: 1Z + 16 chars, FedEx: 12 digits, USPS: 20-22 digits).

**Example:**
```python
import re

CARRIER_PATTERNS = {
    'UPS': r'^1Z[A-Z0-9]{16}$',
    'FedEx': r'^\d{12}$',
    'USPS': r'^\d{20,22}$',
}

def detect_carrier(tracking_number: str) -> str:
    for carrier, pattern in CARRIER_PATTERNS.items():
        if re.match(pattern, tracking_number):
            return carrier
    return "Unknown"
```

**Implementation:** Add to utils.py, use in amazon_scraper.py to validate parsed carrier matches tracking number format (P2 priority).

## Competitor Feature Analysis

| Feature | Amazon API Scrapers (SerpAPI, Oxylabs) | Custom Playwright Scripts | Our Approach (browser-use + Claude) |
|---------|--------------|--------------|--------------|
| **Extraction Method** | Pre-built API endpoints, return JSON | CSS selectors, custom parsers | AI vision + structured prompts |
| **Maintenance** | Zero (vendor maintains) | High (breaks on UI changes) | Low (AI adapts to changes) |
| **Success Rate** | 99%+ (vendor SLA) | 70-85% (selector brittleness) | 89-95% (AI benchmark + tuning) |
| **Cost** | $50-500/month (pay per request) | Free (DIY) | $5-15/month (Claude API) |
| **Session Handling** | Built-in (vendor proxies) | Manual (cookie persistence) | Manual (browser profile) |
| **Rate Limiting** | Built-in (vendor manages) | Manual (sleep timers) | Manual (cooldown logic) |
| **ToS Compliance** | Vendor risk (many violate ToS) | User risk (Amazon bans) | User risk (mitigated by stealth) |
| **Customization** | Limited (API endpoints only) | Full (any scraping logic) | Full (custom prompts + tasks) |

**Our Recommendation:** Hybrid approach chosen - browser-use (AI adaptability) + manual session handling (control) + rate limiting (safety). Best balance of cost, reliability, and customization for this use case.

## Sources

### E-commerce Data Extraction Best Practices
- [eCommerce Data Scraping in 2026: The Ultimate Strategic Guide](https://groupbwt.com/blog/ecommerce-data-scraping/)
- [How AI-Powered Extraction Unlocks Amazon, Walmart, eBay Data](https://forage.ai/blog/master-ecommerce-data-extraction/)
- [Unified Platforms and Agentic AI Will Define E-Commerce in 2026](https://www.ecommercetimes.com/story/unified-platforms-and-agentic-ai-will-define-e-commerce-in-2026-178463.html)

### Amazon Scraping Patterns
- [Complete 2026 Amazon Scraping Guide: Product Data, Prices, Sellers, and More | Scrape.do](https://scrape.do/blog/amazon-scraping/)
- [How to Scrape Amazon Product Data: 2026 Guide (Python + API)](https://brightdata.com/blog/how-tos/how-to-scrape-amazon)
- [Best Amazon Scraper APIs for 2026: Top Picks Compared](https://oxylabs.io/blog/best-amazon-scraper-api)

### Browser Automation and Error Handling
- [Building a Robust Web Scraper with Error Handling and Retry Logic](https://medium.com/techtrends-digest/building-a-robust-web-scraper-with-error-handling-and-retry-logic-3e7b6541bbbc)
- [How to Fix Common Web Scraping Errors in 2026](https://www.capsolver.com/blog/web-scraping/how-to-fix-common-web-scraping-errors-in-2026)
- [2026 Outlook: AI-Driven Browser Automation](https://www.browserless.io/blog/state-of-ai-browser-automation-2026)

### AI Agent Web Scraping and Validation
- [How AI Is Changing Web Scraping in 2026 · Kadoa](https://www.kadoa.com/blog/how-ai-is-changing-web-scraping-2026)
- [AI Agent Web Scraping: Revolutionizing Data Collection and Analysis | ScrapeGraphAI](https://scrapegraphai.com/blog/ai-agent-webscraping)
- [Best 12+ AI Web Scraping Agents for 2026 (Free & Paid)](https://research.aimultiple.com/ai-web-scraping/)

### Data Normalization and Structured Output
- [LLM-Powered Data Normalization - Cleaning Scraped Data Without Regex Hell | ScrapingAnt](https://scrapingant.com/blog/llm-powered-data-normalization-cleaning-scraped-data)
- [The guide to structured outputs and function calling with LLMs](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
- [Structured Outputs: Reliable Schema-Validated Data Extraction from Language Models](https://mbrenndoerfer.com/writing/structured-outputs-schema-validated-data-extraction-language-models)

### Session Persistence and Cookie Management
- [Browser Automation Session Management Guide October 2025](https://www.skyvern.com/blog/browser-automation-session-management/)
- [Mastering Browser Sessions with browser-use: The Backbone of Reliable AI Automations](https://sahilkumar1210.medium.com/mastering-browser-sessions-with-browser-use-the-backbone-of-reliable-ai-automations-f285e449f661)
- [Managing Cookies using Playwright | BrowserStack](https://www.browserstack.com/guide/playwright-cookies)

### Multi-Step Workflow Orchestration
- [Temporal: Workflow Orchestration That Survives the Apocalypse](https://james-carr.org/posts/2026-01-29-temporal-workflow-orchestration/)
- [Automating data workflows with orchestration tools](https://medium.com/@trm5073/automating-data-workflows-with-orchestration-tools-eec9a61d5521)

### Data Quality and Validation
- [How to Fix Inaccurate Web Scraping Data: 2026 Best Practices](https://brightdata.com/blog/web-data/fix-inaccurate-web-scraping-data)
- [How to Validate Data in Web Scraping: 5 Essential Strategies for Quality Assurance](https://scrapingpros.com/blog/web-scraping-data-validation/)
- [State of Web Scraping 2026: Trends, Challenges & What's Next](https://www.browserless.io/blog/state-of-web-scraping-2026)

### Browser-Use Library and AI Agent Patterns
- [GitHub - browser-use/browser-use: Make websites accessible for AI agents](https://github.com/browser-use/browser-use)
- [Top 10 Browser Use Agents: Full Review 2026](https://o-mega.ai/articles/top-10-browser-use-agents-full-review-2026)
- [Best 30+ Open Source Web Agents in 2026](https://aimultiple.com/open-source-web-agents)

### Invoice and Tracking Data Extraction
- [Invoice Data Extraction: Automate AP with AI (2026 Guide)](https://www.docupipe.ai/blog/invoice-data-extraction)
- [Extract Data from Invoices Automatically: 2 Main Methods in 2026](https://www.goautoma.com/blog/how-to-extract-data-from-invoices-automatically)
- [Detect carrier by tracking number - TrackingMore](https://www.trackingmore.com/api-carriers-detect-carrier.html)

### Schema Validation and JSON Output
- [Structured model outputs | OpenAI API](https://platform.openai.com/docs/guides/structured-outputs)
- [Structured outputs | Gemini API](https://ai.google.dev/gemini-api/docs/structured-output)
- [Structured outputs on Amazon Bedrock: Schema-compliant AI responses](https://aws.amazon.com/blogs/machine-learning/structured-outputs-on-amazon-bedrock-schema-compliant-ai-responses/)

---
*Feature research for: Amazon email automation data extraction*
*Researched: 2026-02-12*
*Overall confidence: HIGH (verified with multiple authoritative sources, aligned with project implementation)*
