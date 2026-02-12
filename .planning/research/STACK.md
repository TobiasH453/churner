# Stack Research: Browser Automation Debugging

**Domain:** Browser automation for Amazon scraping with AI agents
**Researched:** 2026-02-12
**Confidence:** HIGH

## Current Stack Analysis

### Installed Versions (Verified)

| Technology | Version | Status | Notes |
|------------|---------|--------|-------|
| browser-use | 0.11.9 | **Current** | Latest stable version (verified from logs) |
| Playwright | 1.58.0 | **Current** | Latest stable release |
| Anthropic | 0.79.0 | **Current** | Claude 3.5 Sonnet support |
| langchain | 1.2.10 | **Current** | Compatible with browser-use |
| langchain-anthropic | 1.3.3 | **Current** | Anthropic integration |
| Python | 3.14 | **Warning** | Pydantic v1 compatibility issues noted in logs |

**Confidence:** HIGH - Verified from actual installed packages and server logs

## Root Cause Analysis

### Issue Pattern Identified

From server logs (lines 43-56):
```
📍 Step 1:
❌ Result failed 1/4 times: items
📍 Step 2:
❌ Result failed 2/4 times: items
📍 Step 3:
❌ Result failed 3/4 times: items
📍 Step 4:
❌ Result failed 4/4 times: items
❌ Stopping due to 3 consecutive failures
```

**Root Cause:** Structured output validation failure for DoneAction's "items" field. The agent is completing steps but failing Pydantic validation when attempting to return results.

**Confidence:** HIGH - Pattern matches documented browser-use issues #2994, #2582, #3293

### Why This Happens

1. **Missing output_model_schema**: Current code does not provide a Pydantic BaseModel schema to browser-use Agent
2. **Default validation expects "items" field**: browser-use's internal DoneAction expects specific fields that aren't being populated
3. **extracted_content returns empty list**: Log line 64 shows `extracted_content: []` indicating no data extraction occurred
4. **Task prompt doesn't specify extraction format**: Multi-step natural language tasks don't define return structure

**Confidence:** HIGH - Corroborated by official docs and GitHub issues

## Recommended Solutions

### Solution 1: Add output_model_schema (Recommended)

**What:** Define Pydantic models for structured output validation

**Implementation:**
```python
from pydantic import BaseModel, Field
from typing import List

class AmazonOrderItem(BaseModel):
    name: str = Field(description="Item name")
    quantity: int = Field(description="Quantity ordered")
    price: str = Field(description="Price per item")

class AmazonOrderExtraction(BaseModel):
    items: List[AmazonOrderItem] = Field(description="All items in order")
    total_before_cashback: str = Field(description="Subtotal before discounts")
    grand_total: str = Field(description="Final amount charged")
    cashback_percent: float = Field(description="Cashback percentage")
    arrival_date: str = Field(description="Estimated delivery date")

# In amazon_scraper.py
agent = Agent(
    task=task,
    llm=self.llm,
    use_vision='auto',
    max_actions_per_step=3,
    browser_profile=browser_profile,
    output_model_schema=AmazonOrderExtraction  # Add this
)
```

**Why this works:**
- Forces Claude to return structured JSON matching schema
- Enables Pydantic validation at output stage
- Browser-use automatically validates against schema
- Falls back gracefully if extraction fails

**Trade-offs:**
- More rigid task structure
- Requires schema maintenance as requirements change
- May reduce agent flexibility for edge cases

**When to use:** When you need reliable structured data extraction (Amazon scraping, form data)

**Confidence:** HIGH - Official browser-use parameter, documented in [All Parameters](https://docs.browser-use.com/customize/agent/all-parameters)

---

### Solution 2: Simplify Task Prompt (Quick Fix)

**What:** Remove multi-step complexity and focus on single extraction goal

**Before:**
```python
task = """
Step 1: Go to https://www.amazon.com/ap/signin
Step 2: Find the email input box...
[11 detailed steps]
"""
```

**After:**
```python
task = f"""
Go to {invoice_url} and extract this data as JSON:
- items (array with name, quantity, price)
- total_before_cashback (string)
- grand_total (string)
- cashback_percent (number, usually 5 or 6)
- arrival_date (string)

Return the data in a structured JSON format.
"""
```

**Why this works:**
- Reduces action chain complexity (fewer validation checkpoints)
- Direct navigation skips authentication steps
- JSON format hint guides LLM output structure
- Shorter task = faster execution = fewer failure points

**Trade-offs:**
- Assumes user is already logged in (requires persistent session)
- Less explicit about where to find data
- May miss edge cases that detailed steps would catch

**When to use:** When you have persistent sessions and need quick fixes without code restructuring

**Confidence:** MEDIUM - Addresses symptom not cause, but commonly recommended in community

---

### Solution 3: Increase max_failures and Enable Retries

**What:** Give agent more attempts to succeed

**Implementation:**
```python
agent = Agent(
    task=task,
    llm=self.llm,
    use_vision='auto',
    max_actions_per_step=3,
    browser_profile=browser_profile,
    max_failures=6,  # Increase from default 3
    final_response_after_failure=True,  # Ensure graceful fallback
    step_timeout=180,  # Increase timeout for slower pages
)
```

**Why this works:**
- Allows agent to recover from transient failures
- final_response_after_failure attempts one last extraction
- Longer timeout prevents premature failure on slow pages

**Trade-offs:**
- Does NOT fix underlying validation issue
- Increases execution time (2x more retries = 2x longer)
- May mask deeper problems
- Still returns empty extracted_content if validation fails

**When to use:** As a temporary measure while implementing Solution 1 or 2

**Confidence:** MEDIUM - Documented parameter, but doesn't solve root cause

---

### Solution 4: Use extract_structured_data Action Explicitly

**What:** Use browser-use's built-in structured extraction action

**Implementation:**
```python
from browser_use.agent.service import Agent
from browser_use.browser.views import BrowserSession
from browser_use.controller.service import Controller

task = f"""
1. Navigate to {invoice_url}
2. Use extract_structured_data action to get:
   - All item names and quantities
   - Subtotal and grand total amounts
   - Cashback percentage
   - Delivery date
3. Return the extracted data
"""
```

**Why this works:**
- Leverages browser-use's optimized extraction logic
- Handles pagination and partial content automatically
- Designed specifically for data scraping tasks

**Trade-offs:**
- Less documented than other approaches
- Requires understanding browser-use's action system
- May not work with all page layouts

**When to use:** When basic task prompts fail but you want to stay within browser-use framework

**Confidence:** LOW - Mentioned in GitHub issues but sparse documentation

---

## Alternative Approaches (If browser-use Remains Problematic)

### Alternative 1: LangChain PlayWright Toolkit

**What:** Use LangChain's native Playwright integration instead of browser-use

**Stack:**
```python
from langchain_community.agent_toolkits.playwright.toolkit import PlayWrightBrowserToolkit
from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
from playwright.async_api import async_playwright

# Create toolkit
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()

    toolkit = PlayWrightBrowserToolkit.from_browser_context(context)
    tools = toolkit.get_tools()

    # Create agent
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # Execute
    result = await agent.arun(f"Navigate to {invoice_url} and extract order data")
```

**Advantages:**
- More mature integration (part of LangChain core)
- Better structured output support with LangChain's parsers
- Extensive documentation and examples
- Works with multiple LLMs

**Disadvantages:**
- Requires code rewrite
- More boilerplate than browser-use
- Less AI-native (more tool-oriented)
- Steeper learning curve

**When to use:** If browser-use validation issues persist after trying Solutions 1-3

**Confidence:** HIGH - Well-documented alternative, [LangChain Playwright Toolkit](https://python.langchain.com/docs/integrations/tools/playwright/)

---

### Alternative 2: AgentQL + LangChain

**What:** Use AgentQL for deterministic element selection with AI fallback

**Stack:**
```python
from langchain.tools import Tool
from agentql import ExtractWebDataTool, ExtractWebDataBrowserTool

# Create extraction tool
extract_tool = ExtractWebDataBrowserTool(
    playwright_browser=browser,
    query="""
    {
        items[] {
            name
            quantity
            price
        }
        totals {
            subtotal
            grand_total
        }
        cashback_percent
        arrival_date
    }
    """
)

# Wrap in LangChain agent
tools = [extract_tool]
agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS)
```

**Advantages:**
- Deterministic element selection (less AI variability)
- Structured query language specifically for data extraction
- Handles dynamic pages well
- Native LangChain integration

**Disadvantages:**
- Additional dependency (agentql library)
- Query syntax learning curve
- Requires knowing page structure upfront

**When to use:** When you need high reliability and can define extraction schemas

**Confidence:** MEDIUM - Newer tool, but [officially integrated with LangChain](https://docs.agentql.com/integrations/langchain)

---

### Alternative 3: Direct Playwright + Claude Structured Output

**What:** Bypass agent frameworks entirely, use Playwright directly + Claude API

**Stack:**
```python
from playwright.async_api import async_playwright
from anthropic import AsyncAnthropic
from pydantic import BaseModel
import json

async def scrape_amazon_order(order_number: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate
        await page.goto(f"https://www.amazon.com/gp/css/summary/print.html?orderID={order_number}")
        await page.wait_for_load_state('networkidle')

        # Get page content
        content = await page.content()
        screenshot = await page.screenshot()

        # Close browser
        await browser.close()

        # Use Claude with structured output
        client = AsyncAnthropic()
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64.b64encode(screenshot).decode()
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Extract order data from this Amazon invoice. Return as JSON matching this schema: {AmazonOrderExtraction.model_json_schema()}"
                    }
                ]
            }]
        )

        # Parse response
        extracted = json.loads(response.content[0].text)
        return AmazonOrderExtraction(**extracted)
```

**Advantages:**
- Full control over browser and API interactions
- No framework limitations or validation quirks
- Simplest to debug (no abstraction layers)
- Most cost-effective (single Claude API call per page)

**Disadvantages:**
- Requires manual error handling
- No automatic retries or recovery
- More code to maintain
- Loses agentic decision-making

**When to use:** When agent behavior is unpredictable and tasks are deterministic

**Confidence:** HIGH - Standard approach, maximum control

---

## Debugging Tools & Techniques

### 1. Enable browser-use GIF Recording

**What:** Visual debugging of agent actions

**Implementation:**
```python
agent = Agent(
    task=task,
    llm=self.llm,
    browser_profile=browser_profile,
    generate_gif="debug_agent.gif",  # Saves animated GIF of all actions
    save_conversation_path="conversation.json"  # Saves full LLM conversation
)
```

**Why useful:**
- See exactly what agent is doing at each step
- Identify where UI interaction fails
- Share debugging artifacts with others

**Confidence:** HIGH - Built-in browser-use feature

---

### 2. Increase Logging Verbosity

**What:** Get detailed browser-use internal logs

**Implementation:**
```python
import logging

# In utils.py or main.py
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("browser_use").setLevel(logging.DEBUG)
logging.getLogger("playwright").setLevel(logging.INFO)
```

**Why useful:**
- See all Playwright commands executed
- View LLM prompts and responses
- Catch errors hidden by try/catch blocks

**Confidence:** HIGH - Standard Python logging

---

### 3. Playwright Inspector Mode

**What:** Step through browser actions interactively

**Implementation:**
```python
# Set environment variable before running
PWDEBUG=1 python main.py

# Or programmatically
browser_profile = BrowserProfile(
    user_data_dir="./data/browser-profile",
    headless=False,
    executable_path=chromium_path,
    args=['--disable-blink-features=AutomationControlled'],
    slow_mo=1000,  # Slow down by 1 second per action
)
```

**Why useful:**
- Pause at each action
- Inspect element selectors
- Test alternative navigation paths
- Verify cookies and session state

**Confidence:** HIGH - [Official Playwright debugging tool](https://playwright.dev/docs/best-practices)

---

### 4. Capture Network Traffic

**What:** Log all HTTP requests/responses

**Implementation:**
```python
async def scrape_with_network_logging(order_number: str):
    # Add network listener before creating agent
    context = browser_context  # Access from browser_profile

    async def log_request(route, request):
        logger.info(f"→ {request.method} {request.url}")
        await route.continue_()

    async def log_response(response):
        logger.info(f"← {response.status} {response.url}")

    await context.route("**/*", log_request)
    context.on("response", log_response)

    # Now run agent
    result = await agent.run()
```

**Why useful:**
- Detect blocked requests (403/429 errors)
- Verify API calls Amazon makes
- Check for CAPTCHA challenges
- Monitor rate limiting

**Confidence:** MEDIUM - Requires accessing browser-use internals

---

### 5. Save Page State on Failure

**What:** Capture HTML/screenshots when agent fails

**Implementation:**
```python
try:
    result = await agent.run()
except Exception as e:
    # Save debugging artifacts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save HTML
    page_content = await page.content()
    with open(f"logs/error_page_{timestamp}.html", "w") as f:
        f.write(page_content)

    # Save screenshot
    await page.screenshot(path=f"logs/error_screenshot_{timestamp}.png")

    logger.error(f"Agent failed. Artifacts saved: error_page_{timestamp}.html")
    raise
```

**Why useful:**
- Reproduce failures without re-running
- Share exact error state with others
- Inspect DOM when selector fails

**Confidence:** HIGH - Standard debugging practice

---

## Configuration Best Practices

### Timeout Settings

**Current Issue:** Default timeouts too short for Amazon pages

**Recommended:**
```python
agent = Agent(
    task=task,
    llm=self.llm,
    browser_profile=browser_profile,
    llm_timeout=120,        # LLM response timeout (default: 90s)
    step_timeout=180,       # Per-step timeout (default: 120s)
    max_actions_per_step=5, # Increase from 3 for complex pages
)
```

**Rationale:**
- Amazon pages load slowly (lots of JS)
- Increase max_actions_per_step to fill forms in one step
- LLM needs time to process screenshots with vision

**Confidence:** HIGH - Documented parameters

---

### Session Persistence

**Current Issue:** Login required on every run (logs show signin steps)

**Recommended:**
```python
# In stealth_utils.py - ALREADY IMPLEMENTED
browser_profile = BrowserProfile(
    user_data_dir="./data/browser-profile",  # ✅ Persists cookies
    headless=False,
    # ... other args
)

# But also check cookies are actually saved:
async def verify_session():
    # Test if logged in
    page = await context.new_page()
    await page.goto("https://www.amazon.com/gp/css/order-history")

    # Check if redirected to login
    if "ap/signin" in page.url:
        logger.warning("Session expired - need to re-login")
        # Trigger manual_login.py
    else:
        logger.info("Session valid")
```

**Rationale:**
- Eliminates 8+ login steps per task
- Reduces Amazon bot detection risk
- Faster execution (skip authentication)

**Confidence:** HIGH - Current implementation looks correct

---

### Vision vs. DOM Selectors

**Current Setting:** `use_vision='auto'`

**Recommendation:** Test `use_vision=True` explicitly

**Rationale:**
- Amazon invoices are rendered PDFs (hard to extract via DOM)
- Screenshot + Claude vision may extract data better than DOM parsing
- Trade-off: slower (image processing) but more reliable

**Test:**
```python
# Try explicit vision mode
agent = Agent(
    task=task,
    llm=self.llm,
    use_vision=True,          # Force vision usage
    vision_detail_level='high', # Higher quality extraction
    browser_profile=browser_profile,
)
```

**Confidence:** MEDIUM - Worth testing but not guaranteed fix

---

## Python 3.14 Compatibility Warning

**Issue Noted in Logs:**
```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

**Impact:**
- LangChain uses Pydantic v1 internally (legacy support)
- Python 3.14 deprecates some v1 APIs
- May cause validation errors in browser-use

**Mitigation:**
```bash
# Option 1: Downgrade Python (safest)
pyenv install 3.11.8
pyenv local 3.11.8
python -m venv venv --clear

# Option 2: Force Pydantic v2 mode (experimental)
export PYDANTIC_V2=true
```

**Recommendation:** Use Python 3.11.x until LangChain fully migrates to Pydantic v2

**Confidence:** HIGH - Official warning in logs, known compatibility issue

---

## Prescriptive Roadmap

### Immediate Actions (Today)

1. **Add output_model_schema** (Solution 1) - 30 minutes
   - Define Pydantic models in models.py
   - Update amazon_scraper.py Agent instantiation
   - Test with single order

2. **Simplify task prompt** (Solution 2) - 15 minutes
   - Remove multi-step login instructions
   - Use direct URL navigation
   - Specify JSON return format

3. **Enable debug artifacts** - 10 minutes
   - Add `generate_gif=True`
   - Add `save_conversation_path`
   - Run test and review GIF

**Expected Outcome:** Either structured output works (Solution 1) OR you see exact failure point (debug artifacts)

---

### Short-Term Fixes (This Week)

4. **Add session validation** - 20 minutes
   - Check if logged in before running agent
   - Trigger manual_login.py if needed
   - Eliminate redundant login steps

5. **Increase timeouts** - 5 minutes
   - Bump step_timeout to 180s
   - Increase max_failures to 6

6. **Test vision mode** - 30 minutes
   - Try `use_vision=True` + `vision_detail_level='high'`
   - Compare extraction quality

**Expected Outcome:** Consistent 80%+ success rate on test orders

---

### Long-Term Options (Next Sprint)

7. **If validation issues persist:** Migrate to Alternative 1 (LangChain Playwright)
   - Week 1: Implement toolkit in parallel branch
   - Week 2: Test side-by-side
   - Week 3: Switch if better reliability

8. **If performance is slow:** Consider Alternative 3 (Direct Playwright)
   - Simplest code
   - Single Claude call per page
   - No agent unpredictability

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Extraction success rate | 0% (all fail validation) | 95% | Successful AgentResponse.amazon_data |
| Execution time | 3.67s (premature failure) | 30-60s | AgentResponse.execution_time_seconds |
| Empty extracted_content | 100% | <5% | Count `extracted_content: []` in logs |
| Login required per run | 100% | 0% (use session) | Grep logs for "ap/signin" |

---

## Sources

### High Confidence (Official Documentation)
- [Browser-Use All Parameters](https://docs.browser-use.com/customize/agent/all-parameters) - Configuration reference
- [Playwright Best Practices](https://playwright.dev/docs/best-practices) - Official debugging guide
- [Playwright Debugging Guide](https://www.browserstack.com/guide/playwright-debugging) - 2026 tutorial

### Medium Confidence (GitHub Issues)
- [Issue #2994: Structured Output Limitation](https://github.com/browser-use/browser-use/issues/2994) - Extraction truncation
- [Issue #2582: ActionResult Ignored](https://github.com/browser-use/browser-use/issues/2582) - extracted_content bug
- [Issue #3293: Pydantic Validation Error](https://github.com/browser-use/browser-use/issues/3293) - Validation failures
- [Issue #192: Result Failed Errors](https://github.com/browser-use/browser-use/issues/192) - Connection failures

### Alternative Approaches
- [LangChain Playwright Toolkit](https://python.langchain.com/docs/integrations/tools/playwright/) - Mature alternative
- [AgentQL LangChain Integration](https://docs.agentql.com/integrations/langchain) - Deterministic extraction
- [Playwright Web Scraping Tutorial](https://www.browserstack.com/guide/playwright-web-scraping) - 2026 guide

---

**Last Updated:** 2026-02-12
**Next Review:** After implementing Solutions 1 & 2
**Confidence:** HIGH for root cause, MEDIUM-HIGH for solutions
