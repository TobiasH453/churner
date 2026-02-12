# Architecture Research: Browser Automation Error Handling

**Domain:** AI-driven browser automation for email processing workflows
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Browser automation agents require multi-layered error handling architecture that distinguishes recoverable failures from fatal errors, propagates meaningful context across async boundaries, and provides observability into agent behavior before crashes occur. The current project architecture masks root causes through broad exception handling, returns placeholder data on failures, and lacks visibility into what the browser-use agent is doing when it fails.

This research synthesizes production patterns from Skyvern, agent-browser (Vercel), Microsoft Azure AI, and n8n production deployments to recommend a three-tier error handling architecture with structured logging, retry strategies, and state persistence.

## Current Architecture Analysis

### Existing System Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      n8n Workflow Layer                      │
│  (Orchestration, Email Trigger, Google Sheets, Telegram)    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP POST
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Server (main.py)                   │
│                   Port 8080 Webhook Receiver                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              BrowserAgent (browser_agent.py)                 │
│              Routes order vs shipping workflows              │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
               ↓                        ↓
┌──────────────────────┐    ┌──────────────────────────────┐
│  AmazonScraper       │    │  ElectronicsBuyerAgent       │
│  (amazon_scraper.py) │    │  (electronics_buyer.py)      │
│  Uses browser-use    │    │  Uses browser-use            │
└──────────────────────┘    └──────────────────────────────┘
```

### Critical Issues Identified

1. **Silent Failures with Placeholder Data**
   - Agent crashes return `OrderDetails(items=[{"name": "NEEDS_PARSING"}])`
   - Downstream systems (Google Sheets) receive invalid data
   - No distinction between "parsing in progress" vs "parsing failed"

2. **Broad Exception Masking**
   ```python
   except Exception as e:
       logger.warning(f"Could not extract content: {e}")
   ```
   - Hides browser crashes, network timeouts, API errors equally
   - No retry logic for transient failures
   - No alerting on fatal errors

3. **No Agent Observability**
   - Can't see what browser-use agent is doing before crash
   - No logs of navigation steps, clicks, or element searches
   - No distinction between "element not found" vs "page didn't load"

4. **Async Context Loss**
   - Request IDs don't propagate through async calls
   - Can't correlate logs across Amazon scraper → EB agent
   - No tracing of multi-step workflows

## Recommended Architecture

### Three-Tier Error Handling Model

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 1: n8n Workflow                      │
│  Responsibility: Retry transient failures, route to DLQ      │
├─────────────────────────────────────────────────────────────┤
│  • Exponential backoff (1s, 2s, 4s, 8s, 16s)                │
│  • Max 5 retries for HTTP timeout errors                     │
│  • Circuit breaker if FastAPI down (5 consecutive failures)  │
│  • Dead letter queue for non-retryable errors                │
│  • Slack alerts with execution links                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  TIER 2: FastAPI Server                      │
│  Responsibility: Classify errors, set HTTP status codes      │
├─────────────────────────────────────────────────────────────┤
│  • Timeout middleware (10min max for browser operations)     │
│  • Custom exception types (RetryableError, FatalError)       │
│  • Structured error responses with classification            │
│  • Request ID injection for distributed tracing              │
│  • Health check endpoints for circuit breaker                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TIER 3: Browser Agent & Scrapers                  │
│  Responsibility: Detailed error context, agent observability │
├─────────────────────────────────────────────────────────────┤
│  • Specific exception types per failure mode                 │
│  • Agent action logging (navigation, clicks, extractions)    │
│  • Retry logic for element waits (3 attempts, 5s delay)      │
│  • Screenshot capture on failure for debugging               │
│  • Structured extraction validation (not placeholder data)   │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Tier 1: n8n Workflow Layer

| Component | Responsibility | Error Handling Strategy |
|-----------|----------------|------------------------|
| Gmail Trigger | Detect Amazon emails | Log missing emails, alert if no emails >24h |
| HTTP Request Node | Call FastAPI webhook | Retry 5xx errors, fail fast on 4xx, timeout 10min |
| Error Workflow | Handle execution failures | Route to DLQ, send Slack alert, log to Airtable |
| Circuit Breaker | Detect FastAPI downtime | Open after 5 consecutive failures, test every 60s |
| Dead Letter Queue | Store failed emails | Persist payload, track retry count, manual replay |

**Implementation:**
- Use n8n's built-in "Continue On Fail" + "IF Error" nodes
- Exponential backoff via Loop + Wait nodes (1s → 2s → 4s → 8s → 16s)
- DLQ writes to Google Sheet tab "Failed Emails" with full payload
- Circuit breaker uses n8n's "Workflow Settings" → "Error Workflow"

### Tier 2: FastAPI Server Layer

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Timeout Middleware | Prevent hung requests | `asyncio.wait_for(request, timeout=600)` → 504 |
| Exception Middleware | Classify error types | `RetryableError` → 503, `FatalError` → 500 |
| Request ID Middleware | Inject trace IDs | Generate UUID, add to headers, contextvars |
| Health Check Endpoint | Circuit breaker probe | `/health` returns service status, dependency checks |
| Structured Logging | JSON logs for parsing | Structlog with ContextVars for async propagation |

**Custom Exception Hierarchy:**
```python
class AutomationError(Exception):
    """Base exception for all automation errors"""
    pass

class RetryableError(AutomationError):
    """Transient failures that should be retried"""
    # Examples: network timeout, element not found yet, API rate limit
    pass

class FatalError(AutomationError):
    """Permanent failures that should not retry"""
    # Examples: invalid order number, account suspended, missing credentials
    pass

class ValidationError(FatalError):
    """Data extraction validation failed"""
    pass
```

### Tier 3: Browser Agent & Scrapers Layer

| Component | Responsibility | Error Handling Strategy |
|-----------|----------------|------------------------|
| BrowserAgent | Orchestrate multi-step workflow | Catch specific exceptions, enrich context, propagate |
| AmazonScraper | Navigate Amazon, extract data | Retry element waits, validate extracted data, screenshot on fail |
| ElectronicsBuyerAgent | Submit deals/tracking | Login detection, form validation, confirmation detection |
| browser-use Agent | Execute LLM-driven actions | Log each action before execution, capture final state |

**Specific Error Types:**

```python
# Amazon scraping errors
class AmazonLoginRequiredError(RetryableError):
    """Session expired, need to re-authenticate"""
    pass

class AmazonInvoiceNotFoundError(FatalError):
    """Order number invalid or invoice not accessible"""
    pass

class AmazonElementNotFoundError(RetryableError):
    """Expected element missing, may appear after wait"""
    pass

# ElectronicsBuyer errors
class EBLoginFailedError(FatalError):
    """Credentials invalid or account suspended"""
    pass

class EBDealNotFoundError(RetryableError):
    """Product not currently in deals, may appear later"""
    pass

# Data extraction errors
class ExtractionValidationError(FatalError):
    """Extracted data failed validation, likely parsing bug"""
    pass
```

## Data Flow: Error Propagation

### Request Flow (Success Case)

```
n8n Email Trigger
    ↓ (EmailData JSON)
FastAPI /process-order
    ↓ (inject request_id in contextvars)
BrowserAgent.process_email()
    ↓ (route by email_type)
AmazonScraper.scrape_order_confirmation()
    ↓ (browser-use agent navigation)
Extract OrderDetails
    ↓ (validate extracted data)
ElectronicsBuyerAgent.submit_deal()
    ↓ (browser-use agent form submission)
Return AgentResponse(success=True)
    ↓ (JSON response)
n8n Google Sheets node
    ↓ (append row)
n8n Telegram node (success notification)
```

### Error Flow (Recoverable Failure)

```
AmazonScraper: Element not found (button#invoice-details)
    ↓ (raise AmazonElementNotFoundError)
BrowserAgent: Catch, check retry count
    ↓ (attempt 1 of 3, wait 5s)
AmazonScraper: Retry navigation
    ↓ (element found on retry)
Continue normal flow...
```

### Error Flow (Fatal Failure)

```
AmazonScraper: Order number returns 404
    ↓ (raise AmazonInvoiceNotFoundError)
BrowserAgent: Catch FatalError
    ↓ (no retry, capture context)
Return AgentResponse(success=False, errors=["Invoice not found: 111-222-333"])
    ↓ (HTTP 500 with error classification)
FastAPI: Log structured error with request_id
    ↓ (return 500 response)
n8n: Detect 500 error
    ↓ (trigger Error Workflow, no retry)
Dead Letter Queue: Store payload
    ↓ (write to Google Sheet "Failed Emails")
Slack Alert: Send notification with error details
```

## Observability Strategies

### Structured Logging with ContextVars

**Problem:** Request IDs disappear across async boundaries in Python
**Solution:** Use structlog + ContextVars for automatic propagation

```python
import structlog
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='no-request-id')

# Configure structlog with ContextVars processor
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # AUTO-INJECT request_id
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
```

**Middleware to inject request_id:**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Result:** Every log line automatically includes request_id without manual passing.

### Agent Action Logging

**Problem:** Can't see what browser-use agent is doing before crash
**Solution:** Log each agent action with structured context

```python
# Before agent execution
logger.info("browser_agent.start",
    task_type="scrape_order_confirmation",
    order_number=order_number,
    url=invoice_url
)

# During agent execution (would require browser-use modification)
# Log each action step: navigate, click, extract
# (Current browser-use library doesn't expose this)

# After agent execution
logger.info("browser_agent.complete",
    task_type="scrape_order_confirmation",
    order_number=order_number,
    extracted_fields=["items", "total", "delivery_date"],
    duration_seconds=12.3
)
```

### Screenshot Capture on Failure

**Pattern:** Save browser state when extraction fails for debugging

```python
async def scrape_with_error_context(self, order_number: str):
    try:
        result = await agent.run()
        # Validate extraction succeeded
        if not self._validate_extraction(result):
            # Capture screenshot before raising error
            screenshot_path = f"logs/failed_{order_number}_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            raise ExtractionValidationError(f"Validation failed, see {screenshot_path}")
    except Exception as e:
        logger.error("scrape_failed",
            order_number=order_number,
            error_type=type(e).__name__,
            error_message=str(e),
            screenshot_path=screenshot_path if 'screenshot_path' in locals() else None
        )
        raise
```

### Metrics to Track

| Metric | Purpose | Alert Threshold |
|--------|---------|----------------|
| `automation.email.processed.total` | Count by email_type | - |
| `automation.email.success_rate` | Percentage by email_type | <90% over 1 hour |
| `automation.execution_time_seconds` | Latency percentiles (p50, p95, p99) | p95 >300s |
| `automation.error.rate` | Errors by error_type | >5 errors/hour for FatalError |
| `automation.retry.count` | Retry attempts by operation | >10 retries/hour |
| `browser_agent.action.duration` | Time per agent action | p99 >60s |
| `api.cost.tokens` | Claude API token usage | >$20/day |

## Retry Strategies

### Exponential Backoff Pattern

**Use for:** Network timeouts, rate limits, transient API errors

```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """Retry with exponential backoff and optional jitter"""
    for attempt in range(max_retries):
        try:
            return await func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, propagate error

            # Calculate delay: 1s, 2s, 4s, 8s, 16s
            delay = min(initial_delay * (2 ** attempt), max_delay)

            # Add jitter ±20% to prevent thundering herd
            if jitter:
                delay *= (0.8 + 0.4 * random.random())

            logger.warning("retry_scheduled",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay,
                error=str(e)
            )
            await asyncio.sleep(delay)
```

### Element Wait Retry Pattern

**Use for:** Playwright element not found errors

```python
async def wait_for_element_with_retry(
    page: Page,
    selector: str,
    max_attempts: int = 3,
    wait_timeout: int = 5000  # 5 seconds
):
    """Retry element wait with increasing timeouts"""
    for attempt in range(max_attempts):
        try:
            return await page.wait_for_selector(
                selector,
                timeout=wait_timeout * (attempt + 1)  # 5s, 10s, 15s
            )
        except PlaywrightTimeoutError:
            if attempt == max_attempts - 1:
                # Last attempt failed, capture context
                screenshot_path = f"logs/element_not_found_{timestamp}.png"
                await page.screenshot(path=screenshot_path)
                raise AmazonElementNotFoundError(
                    f"Element '{selector}' not found after {max_attempts} attempts. "
                    f"Screenshot: {screenshot_path}"
                )
            logger.warning("element_wait_retry",
                selector=selector,
                attempt=attempt + 1,
                next_timeout_ms=wait_timeout * (attempt + 2)
            )
```

### Login Session Retry Pattern

**Use for:** Cookie expiration, session timeouts

```python
async def scrape_with_session_retry(self, order_number: str):
    """Retry scraping with session refresh on auth failure"""
    try:
        return await self._scrape_order_internal(order_number)
    except AmazonLoginRequiredError:
        logger.warning("session_expired", order_number=order_number)

        # Refresh session by reloading cookies or re-authenticating
        await self._refresh_session()

        # Single retry after session refresh
        return await self._scrape_order_internal(order_number)
```

## State Management for Multi-Step Workflows

### Session Persistence with agent-browser Pattern

**Pattern:** Persist browser state between commands for speed and reliability

```python
# Save state after successful Amazon login
async def save_browser_state(page: Page, state_name: str):
    """Save cookies, localStorage, sessionStorage"""
    state = {
        "cookies": await page.context.cookies(),
        "localStorage": await page.evaluate("() => Object.entries(localStorage)"),
        "sessionStorage": await page.evaluate("() => Object.entries(sessionStorage)"),
        "timestamp": datetime.utcnow().isoformat()
    }

    state_path = f"data/browser-state/{state_name}.json"
    with open(state_path, 'w') as f:
        json.dump(state, f)

    logger.info("browser_state_saved",
        state_name=state_name,
        cookie_count=len(state['cookies'])
    )

# Load state before scraping
async def load_browser_state(page: Page, state_name: str):
    """Restore browser state from saved snapshot"""
    state_path = f"data/browser-state/{state_name}.json"
    if not Path(state_path).exists():
        raise FatalError(f"Browser state '{state_name}' not found")

    with open(state_path) as f:
        state = json.load(f)

    # Restore cookies
    await page.context.add_cookies(state['cookies'])

    # Restore localStorage
    for key, value in state['localStorage']:
        await page.evaluate(f"localStorage.setItem('{key}', '{value}')")

    logger.info("browser_state_loaded",
        state_name=state_name,
        state_age_hours=(datetime.utcnow() - datetime.fromisoformat(state['timestamp'])).total_seconds() / 3600
    )
```

### Workflow State Tracking

**Pattern:** Track progress through multi-step workflows for resume/retry

```python
class WorkflowState(BaseModel):
    """Track progress through order processing workflow"""
    order_number: str
    email_type: str
    request_id: str
    started_at: datetime

    # Checkpoints
    amazon_scrape_complete: bool = False
    amazon_data: Optional[OrderDetails] = None

    eb_submission_complete: bool = False
    eb_result: Optional[EBDealResult] = None

    # Error tracking
    retry_count: int = 0
    last_error: Optional[str] = None
    last_error_timestamp: Optional[datetime] = None

# Save checkpoint after each major step
async def process_with_checkpoints(self, email_data: EmailData):
    state = WorkflowState(
        order_number=email_data.order_number,
        email_type=email_data.email_type,
        request_id=request_id_var.get(),
        started_at=datetime.utcnow()
    )

    try:
        # Step 1: Amazon scraping
        amazon_data = await self.amazon_scraper.scrape_order_confirmation(
            email_data.order_number
        )
        state.amazon_scrape_complete = True
        state.amazon_data = amazon_data
        save_workflow_state(state)  # CHECKPOINT

        # Step 2: EB submission
        eb_result = await self.eb_agent.submit_deal(
            items=[item['name'] for item in amazon_data.items],
            quantities={item['name']: item['quantity'] for item in amazon_data.items}
        )
        state.eb_submission_complete = True
        state.eb_result = eb_result
        save_workflow_state(state)  # CHECKPOINT

        return AgentResponse(success=True, ...)

    except Exception as e:
        state.retry_count += 1
        state.last_error = str(e)
        state.last_error_timestamp = datetime.utcnow()
        save_workflow_state(state)
        raise
```

## Architectural Patterns

### Pattern 1: Error Classification at Boundary

**What:** Classify errors into retryable vs fatal at the layer where they occur

**When to use:** At each architectural boundary (n8n ↔ FastAPI, FastAPI ↔ browser agents)

**Trade-offs:**
- Pro: Clear retry semantics, prevents unnecessary retries
- Con: Requires upfront classification of all error types

**Example:**
```python
# In amazon_scraper.py
try:
    invoice_element = await page.wait_for_selector("#invoice", timeout=10000)
except PlaywrightTimeoutError:
    # CLASSIFY: This is retryable (page might load slowly)
    raise AmazonElementNotFoundError("Invoice element not found") from e

try:
    response = await page.goto(invoice_url)
    if response.status == 404:
        # CLASSIFY: This is fatal (order number invalid)
        raise AmazonInvoiceNotFoundError(f"Order {order_number} not found")
except Exception as e:
    # CLASSIFY: Unknown error, treat as fatal to avoid infinite retry
    raise FatalError(f"Unexpected error navigating to invoice: {e}") from e
```

### Pattern 2: Enrich Context on Propagation

**What:** Add contextual information as errors bubble up through layers

**When to use:** When errors cross component boundaries (scraper → agent → server)

**Trade-offs:**
- Pro: Rich debugging context in final error
- Con: More verbose error handling code

**Example:**
```python
# Layer 3: Scraper (initial error)
raise AmazonElementNotFoundError("Invoice button not found")

# Layer 2: Agent (enrich with workflow context)
try:
    amazon_data = await self.amazon_scraper.scrape_order_confirmation(order_number)
except AmazonElementNotFoundError as e:
    raise AmazonElementNotFoundError(
        f"Failed to scrape order {order_number}: {e}"
    ) from e

# Layer 1: Server (enrich with request context)
try:
    result = await agent.process_email(email_data)
except AmazonElementNotFoundError as e:
    logger.error("scraping_failed",
        request_id=request_id_var.get(),
        order_number=email_data.order_number,
        email_type=email_data.email_type,
        error_chain=[str(e), str(e.__cause__)]
    )
    raise HTTPException(
        status_code=503,  # Service Unavailable = retryable
        detail={
            "error_type": "AmazonElementNotFoundError",
            "retryable": True,
            "message": str(e)
        }
    )
```

### Pattern 3: Circuit Breaker for Downstream Dependencies

**What:** Stop sending requests to failing services, test periodically for recovery

**When to use:** When calling external APIs (Amazon, ElectronicsBuyer, Claude API)

**Trade-offs:**
- Pro: Prevents cascading failures, reduces error log noise
- Con: Adds latency during recovery detection

**Example (at n8n workflow level):**
```
[HTTP Request to FastAPI]
    ↓ (on error)
[Function: Increment failure counter in workflow memory]
    ↓
[IF: failure_count >= 5]
    → YES: [Set variable: circuit_open = true, last_check = now]
           [Slack: "Circuit breaker opened for FastAPI"]
           [End workflow with error]
    → NO: [Continue to retry logic]

[Separate Scheduled Workflow: every 60s]
    ↓
[IF: circuit_open == true AND (now - last_check) > 60s]
    → YES: [HTTP Request: GET /health]
           ↓ (on success)
           [Set variable: circuit_open = false, failure_count = 0]
           [Slack: "Circuit breaker closed, FastAPI recovered"]
```

### Pattern 4: Dead Letter Queue with Replay

**What:** Store failed messages in durable storage for manual inspection and replay

**When to use:** For non-retryable errors that may require human intervention

**Trade-offs:**
- Pro: No data loss, supports manual replay, audit trail
- Con: Requires manual intervention, storage overhead

**Example (at n8n workflow level):**
```
[HTTP Request to FastAPI]
    ↓ (on 500 error with retryable=false)
[Error Workflow Trigger]
    ↓
[Google Sheets: Append to "Dead Letter Queue" tab]
    Columns: timestamp, order_number, email_type, error_message, raw_payload
    ↓
[Airtable: Create record in "Failed Automations" base]
    Fields: Request ID, Error Type, Retry Count, Status="Needs Review"
    ↓
[Slack: Send alert with link to Airtable record]
    Message: "Order 111-222-333 failed (AmazonInvoiceNotFoundError). Review: [link]"

[Manual Replay Process]
    1. Human reviews Airtable record, fixes root cause
    2. Updates Status field to "Ready for Replay"
    3. Separate n8n workflow polls Airtable for "Ready for Replay"
    4. Fetches raw_payload, calls FastAPI endpoint
    5. Updates Status to "Replayed Successfully" or "Replay Failed"
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Returning Placeholder Data on Failure

**What people do:**
```python
except Exception as e:
    logger.warning(f"Could not extract content: {e}")
    return OrderDetails(
        items=[{"name": "NEEDS_PARSING", "quantity": 1}],
        total_before_cashback="$0.00",
        ...
    )
```

**Why it's wrong:**
- Downstream systems (Google Sheets) receive invalid data
- Masks the real error from n8n retry logic
- No way to distinguish "in progress" from "permanently failed"
- Creates data quality issues that require manual cleanup

**Do this instead:**
```python
except Exception as e:
    logger.error("extraction_failed",
        order_number=order_number,
        error_type=type(e).__name__,
        error_message=str(e)
    )
    raise ExtractionValidationError(f"Failed to extract order details: {e}") from e
```

### Anti-Pattern 2: Broad Exception Catching Without Classification

**What people do:**
```python
try:
    result = await agent.run()
except Exception as e:
    return AgentResponse(success=False, errors=[str(e)])
```

**Why it's wrong:**
- Treats all errors equally (retryable network timeout = fatal invalid credentials)
- No retry guidance for n8n layer
- Loses error type information
- Can't set appropriate HTTP status codes

**Do this instead:**
```python
try:
    result = await agent.run()
except PlaywrightTimeoutError as e:
    raise AmazonElementNotFoundError("Element not found, retry may succeed") from e
except HTTPError as e:
    if e.status == 404:
        raise AmazonInvoiceNotFoundError("Order not found, do not retry") from e
    else:
        raise RetryableError(f"HTTP error {e.status}, may be transient") from e
except Exception as e:
    # Truly unknown error, log full context and treat as fatal
    logger.error("unexpected_error", error_type=type(e).__name__, traceback=traceback.format_exc())
    raise FatalError(f"Unexpected error: {e}") from e
```

### Anti-Pattern 3: No Logging Before Async Calls

**What people do:**
```python
async def process_email(self, email_data: EmailData):
    amazon_data = await self.amazon_scraper.scrape_order_confirmation(...)
```

**Why it's wrong:**
- If scraper crashes immediately, no log entry shows the attempt started
- Can't determine if function was called or if it's still running
- No timestamp for latency analysis

**Do this instead:**
```python
async def process_email(self, email_data: EmailData):
    logger.info("scraping_started",
        order_number=email_data.order_number,
        email_type=email_data.email_type
    )

    start_time = time.time()
    amazon_data = await self.amazon_scraper.scrape_order_confirmation(...)

    logger.info("scraping_completed",
        order_number=email_data.order_number,
        duration_seconds=time.time() - start_time,
        items_extracted=len(amazon_data.items)
    )
```

### Anti-Pattern 4: Fixed Retry Delays

**What people do:**
```python
for attempt in range(5):
    try:
        return await func()
    except Exception:
        await asyncio.sleep(5)  # Always 5 seconds
```

**Why it's wrong:**
- No backoff means hammering failing service at constant rate
- No jitter means synchronized retries from multiple instances
- Fixed delay may be too short for slow recovery or too long for quick recovery

**Do this instead:**
Use exponential backoff with jitter (see "Retry Strategies" section above).

## Scaling Considerations

### Current Scale: Single User, ~5 Emails/Day

**Architecture:** Monolithic FastAPI server on MacBook, visible browser

**Bottlenecks:** None at current scale

**Recommendations:**
- Focus on reliability over performance
- Visible browser acceptable (user wants to supervise)
- Single-threaded execution sufficient

### Future Scale: ~50 Emails/Day

**Bottlenecks:**
- Browser session conflicts (can't run multiple browser-use agents simultaneously)
- Long-running operations block webhook endpoint

**Adjustments:**
1. **Add job queue** (Redis + Celery or database-backed queue)
   - FastAPI endpoint immediately returns 202 Accepted
   - Worker processes pick up jobs from queue
   - n8n polls status endpoint for completion

2. **Connection pooling** for browser contexts
   - Pre-launch browser instance, reuse contexts
   - Reduces startup latency from ~5s to <1s

3. **Parallel execution** for independent operations
   - Run Amazon scraping + EB deal lookup concurrently
   - Use `asyncio.gather()` to parallelize

### Future Scale: Multiple Users, >100 Emails/Day

**Bottlenecks:**
- Claude API rate limits (50 requests/min for Sonnet)
- Google Sheets write quota (100 requests/100s per user)
- Single MacBook can't handle load

**Adjustments:**
1. **Headless browser in cloud** (AWS EC2, Render, Railway)
   - Multiple instances behind load balancer
   - Shared Redis for state/session management

2. **API rate limit handling**
   - Queue Claude API calls with rate limiter
   - Batch Google Sheets writes (update every 5min instead of per email)

3. **Horizontal scaling**
   - Multiple n8n instances with shared database
   - Multiple FastAPI workers with load balancer

## Integration Points

### n8n ↔ FastAPI Server

| Integration | Pattern | Error Handling |
|-------------|---------|----------------|
| Webhook Call | HTTP POST to `http://localhost:8080/process-order` | Retry 503 errors, fail on 500, timeout 10min |
| Authentication | None (localhost only) | Consider API key if exposing publicly |
| Payload Format | JSON with `EmailData` schema | Validate in FastAPI, return 422 on invalid |
| Response Format | JSON with `AgentResponse` schema | Parse `success` field, check `errors` array |

### FastAPI ↔ browser-use Agents

| Integration | Pattern | Error Handling |
|-------------|---------|----------------|
| Browser Launch | Persistent profile in `./data/browser-profile` | Retry launch failures up to 3 times |
| Session Management | Load/save cookies per scraper | Refresh session on auth errors |
| Agent Task Definition | String prompt with step-by-step instructions | Validate extracted data structure |
| Result Extraction | Parse `result.extracted_content()` | Raise `ExtractionValidationError` if invalid |

### Browser Agents ↔ External Sites

| Service | Communication | Failure Modes | Recovery Strategy |
|---------|---------------|---------------|-------------------|
| Amazon | HTTPS via Playwright | Rate limiting, CAPTCHA, session expiry | Retry with backoff, manual CAPTCHA solve, session refresh |
| ElectronicsBuyer.gg | HTTPS via Playwright | Login failures, deal not found, downtime | Retry login, defer if deal missing, circuit breaker |
| Claude API | HTTPS via LangChain | Rate limits, timeouts, quota exceeded | Retry with backoff, queue requests, alert on quota |

## Build Order Implications

Based on error handling architecture research, suggested implementation phases:

### Phase 1: Foundation (Error Classification)
1. Define custom exception hierarchy (`RetryableError`, `FatalError`, etc.)
2. Add specific exception types for Amazon/EB failure modes
3. Update scrapers to raise classified exceptions (not generic `Exception`)
4. Validate this works with test cases for each error type

**Why first:** All other error handling depends on proper classification

### Phase 2: Server Layer (Structured Responses)
1. Add FastAPI exception middleware to catch classified errors
2. Set HTTP status codes based on error type (503 for retryable, 500 for fatal)
3. Return structured JSON with `error_type`, `retryable`, `message` fields
4. Add timeout middleware (10min max)

**Why second:** Enables n8n retry logic to work correctly

### Phase 3: Observability (Logging & Tracing)
1. Replace `logging` with `structlog` + ContextVars
2. Add request ID middleware to FastAPI
3. Log structured events before/after async calls
4. Add screenshot capture on extraction failures

**Why third:** Can debug failures from Phases 1-2 with rich context

### Phase 4: Workflow Layer (n8n Retry & DLQ)
1. Add exponential backoff retry logic to n8n HTTP node
2. Create Error Workflow for Dead Letter Queue
3. Add circuit breaker logic (failure counter + conditional)
4. Connect Slack alerts for fatal errors

**Why fourth:** Completes end-to-end error handling with recovery

### Phase 5: State Management (Resume/Replay)
1. Add workflow state checkpoints after each major step
2. Implement browser state save/load for session persistence
3. Build manual replay workflow for DLQ entries

**Why last:** Optional optimization, not required for initial reliability

## Sources

### High Confidence (Official Documentation & Technical Articles)

- [Error Handling in Browser Automation - Skyvern](https://www.skyvern.com/blog/error-handling-in-browser-automation/) - Error classification patterns, recoverable vs fatal taxonomy
- [Browser Automation Agents: Architecture, Applications, Challenges - Atoms.dev](https://atoms.dev/insights/browser-automation-agents-architecture-applications-challenges-and-future-trends/138768f2d19549faa410f3a280faee57) - Multi-layer architecture, state management, self-healing mechanisms
- [AI Agent Monitoring Best Practices - UptimeRobot](https://uptimerobot.com/knowledge-hub/monitoring/ai-agent-monitoring-best-practices-tools-and-metrics/) - Logging requirements, alert triggers, metrics tracking
- [Agent Factory: Top 5 Agent Observability Best Practices - Microsoft Azure Blog](https://azure.microsoft.com/en-us/blog/agent-factory-top-5-agent-observability-best-practices-for-reliable-ai/) - CI/CD integration, tracing, production monitoring
- [n8n Error Handling Patterns - PageLines](https://www.pagelines.com/blog/n8n-error-handling-patterns) - Exponential backoff, dead letter queue, circuit breaker implementations
- [FastAPI Error Handling Patterns - Better Stack](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/) - Middleware patterns, exception handlers, HTTP status codes
- [Structlog ContextVars: Python Async Logging 2026](https://johal.in/structlog-contextvars-python-async-logging-2026/) - Context propagation in async Python, ContextVars usage

### Medium Confidence (Community Articles & Documentation)

- [The Green Report: Enhancing Automation Reliability with Retry Patterns](https://www.thegreenreport.blog/articles/enhancing-automation-reliability-with-retry-patterns/enhancing-automation-reliability-with-retry-patterns.html) - Retry strategy patterns
- [API Error Handling & Retry Strategies: Python Guide 2026](https://easyparser.com/blog/api-error-handling-retry-strategies-python-guide) - Exponential backoff implementation
- [How to Implement Dead Letter Queue Patterns](https://oneuptime.com/blog/post/2026-02-09-dead-letter-queue-patterns/view) - DLQ design patterns
- [Vercel agent-browser: AI-First Browser Automation - Zylos Research](https://zylos.ai/research/2026-01-14-vercel-agent-browser) - State persistence patterns
- [Python Logging with Structlog - Better Stack](https://betterstack.com/community/guides/logging/structlog/) - Structured logging implementation
- [Effective Error Handling and Retries in Playwright Tests - Neova Solutions](https://www.neovasolutions.com/2024/08/15/effective-error-handling-and-retries-in-playwright-tests/) - Playwright-specific error patterns

### Additional Resources (Referenced but not directly fetched)

- [n8n Official Error Handling Docs](https://docs.n8n.io/flow-logic/error-handling/)
- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Python Exception Handling Patterns - Jerry Ng](https://jerrynsh.com/python-exception-handling-patterns-and-best-practices/)

---

*Architecture research for: Amazon Email Automation Browser Agents*
*Researched: 2026-02-12*
*Next: Write PITFALLS.md documenting critical failure modes to avoid*
