# Pitfalls Research

**Domain:** Browser Automation with browser-use + Playwright + Claude Agents
**Researched:** 2026-02-12
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Agent Thinks Task is Complete Too Early

**What goes wrong:**
The browser-use agent exits within seconds, returning placeholder data like "NEEDS_PARSING" without actually completing the scraping task. Browser opens, loads homepage, then immediately closes with no error messages.

**Why it happens:**
- **Vague task instructions**: Agent receives multi-step tasks but lacks clear completion criteria. Without explicit "you are done when X is extracted" instructions, Claude judges the task complete prematurely
- **result.extracted_content() returns empty**: The agent completes its run but `extracted_content` is an empty list `[]` or has no structured data, causing placeholder values to be returned
- **Missing validation schema**: Without a Pydantic schema or explicit output format, browser-use doesn't know what "done" looks like
- **"items" validation failures**: Logs show `❌ Result failed 1/4 times: items` then `❌ Stopping due to 3 consecutive failures` - the agent tries to validate output against an expected structure but fails repeatedly

**How to avoid:**
1. **Add explicit extraction schema**: Use browser-use's `output_model` parameter with Pydantic models to define exactly what data must be extracted
2. **Clear success criteria in prompt**: End task with "Your task is complete ONLY when you have extracted: [list fields]. Return the data in this exact JSON structure: {schema}"
3. **Increase max_failures**: Default `max_failures=3` causes early exits. Raise to 5-7 for complex scraping tasks
4. **Add validation logic**: Check if `result.extracted_content` is None/empty before returning, retry with clearer instructions if empty
5. **Break into atomic subtasks**: Instead of "navigate and extract", use separate agents for navigation vs. extraction with explicit checkpoints

**Warning signs:**
- Browser closes within 5-10 seconds of opening
- Logs show "Result failed N/4 times" followed by "Stopping due to 3 consecutive failures"
- `result.extracted_content` returns `[]` or `None`
- No Python traceback but function returns placeholder values
- Agent logs show task start but no intermediate steps (Step 1, 2, 3...)

**Phase to address:**
Phase 2 (Basic Scraper Implementation) - Add output schemas before testing navigation logic

---

### Pitfall 2: Browser Context Not Properly Managed (Async Cleanup)

**What goes wrong:**
Browser closes prematurely during task execution or hangs indefinitely, causing memory leaks. On macOS, multiple browser processes accumulate over time consuming 20GB+ memory each.

**Why it happens:**
- **Missing async context manager**: Not using `async with Agent(...)` causes browser context to close before `await agent.run()` completes
- **Unclosed browser contexts**: Playwright creates new contexts but never closes previous ones, accumulating in memory
- **Orphaned page objects**: References to pages persist after browser closes, preventing garbage collection
- **Stale WebSocket connections**: browser-use maintains WS connections to browser; if not properly closed, they leak
- **Python 3.14 Pydantic compatibility**: Logs show `Core Pydantic V1 functionality isn't compatible with Python 3.14`, which can cause async cleanup issues

**How to avoid:**
1. **Always use async context managers**: Wrap Agent instantiation in `async with Agent(...) as agent:`
2. **Explicit browser cleanup**: After each run, call `await browser.close()` and clear context references
3. **Use browser-use 0.11.9+ session manager**: Newer versions (like 0.11.9 in logs) have improved SessionManager with `reset()` method
4. **Downgrade Python if needed**: Python 3.14 has compatibility issues with Pydantic v1. Use Python 3.11 or 3.12 for stability
5. **Implement browser recycling**: Reuse browser contexts for sequential tasks instead of creating new ones each time
6. **Set timeout on agent.run()**: Add `asyncio.wait_for(agent.run(), timeout=300)` to force cleanup on hangs

**Warning signs:**
- Memory usage climbing steadily (check Activity Monitor on macOS)
- Browser processes persist after Python script ends
- Logs show "Browser session reset complete" multiple times for single task
- Error: "Target page, context or browser has been closed"
- System warnings: "CPU at 100%, Memory at 98.9%"

**Phase to address:**
Phase 2 (Basic Scraper Implementation) - Set up proper async patterns from the start

---

### Pitfall 3: Amazon Anti-Bot Detection Triggers

**What goes wrong:**
Amazon shows CAPTCHA, blocks requests, or logs out the session immediately after automated login. Browser gets flagged as bot within seconds of navigation.

**Why it happens:**
- **navigator.webdriver exposed**: Playwright sets `navigator.webdriver = true` by default, instant bot detection
- **Headless mode fingerprinting**: Even with `headless=false`, certain Chromium flags leak automation signals
- **Too-fast navigation**: Human users don't navigate to invoice URLs instantly; bots do
- **Missing browser profile**: Fresh browser session every time (no cookies, no history) is suspicious
- **User-Agent mismatches**: Chrome for Testing UA differs from regular Chrome
- **Canvas/WebGL fingerprinting**: Amazon checks canvas rendering and GPU info; Playwright's differ from real browsers

**How to avoid:**
1. **Mandatory stealth arguments**: Already in `stealth_utils.py` - verify these are applied:
   ```python
   '--disable-blink-features=AutomationControlled',
   '--disable-dev-shm-usage',
   ignore_default_args=['--enable-automation']
   ```
2. **Use persistent browser profile**: Save cookies/session to `user_data_dir` and reuse across runs (already configured)
3. **Add human-like delays**: Randomize `wait_between_actions` (0.3-0.8s) and use triangular distribution (already done)
4. **playwright-stealth plugin**: Install `playwright-stealth` Python package and apply patches before navigation
5. **Rate limit requests**: Wait 30-60 seconds between consecutive Amazon scrapes (use Redis to track timing)
6. **Randomize viewport**: Vary window size and device pixel ratio across runs
7. **Real browser executable**: Use actual Chrome instead of Chromium (requires different executable path)

**Warning signs:**
- CAPTCHA appears on Amazon pages
- Login succeeds but immediately logged out on next navigation
- Amazon shows "unusual activity" warning
- Browser redirected to `/errors/validateCaptcha`
- Session cookies expire within minutes instead of hours/days

**Phase to address:**
Phase 3 (Stealth Hardening) - After basic scraping works, add anti-detection layers

---

### Pitfall 4: Prompt Over-Engineering (Screenshot Waste)

**What goes wrong:**
Agent takes 10+ screenshots for a single page scrape, burning API costs and adding 30-60 seconds per task. Claude repeatedly says "Let me take another screenshot to see the current state."

**Why it happens:**
- **use_vision='auto' too aggressive**: Browser-use automatically takes screenshots at every step when vision is enabled
- **Verbose task prompts**: Long multi-step instructions cause agent to "think" more, requesting vision confirmation
- **Missing DOM context**: Agent relies on screenshots when it could read page structure directly
- **No extraction examples**: Without example output, agent takes screenshots to "figure out" what to extract

**How to avoid:**
1. **Use vision sparingly**: Set `use_vision=False` for pages with clean HTML structure; only enable for complex layouts
2. **Provide explicit selectors**: Include CSS selectors or XPath in prompts: "Extract text from div.order-total"
3. **Single-step extraction**: "Navigate to URL, then extract these fields: ..." instead of multi-step sequences
4. **Add structured output examples**: Show agent exactly what JSON structure to return
5. **Disable vision for price/text fields**: Screenshots not needed for reading text; only for clicking buttons

**How to avoid:**
Set `max_actions_per_step=3` for simple tasks (already configured for invoice scraping)

**Warning signs:**
- Logs show multiple screenshot-related messages
- High Anthropic API costs ($20+ for 10-20 emails)
- Task takes 3-5 minutes when it should take 30 seconds
- Agent repeatedly says "analyzing screenshot..." in logs

**Phase to address:**
Phase 4 (Cost Optimization) - After basic functionality proven, reduce API calls

---

### Pitfall 5: Consecutive Failure Threshold Too Low

**What goes wrong:**
Agent stops with "Stopping due to 3 consecutive failures" before completing task, even though the issue is transient (slow page load, element not immediately visible).

**Why it happens:**
- **Default max_failures=3**: Browser-use defaults to stopping after 3 consecutive validation failures
- **"items" key missing in output**: Logs show `❌ Result failed X/4 times: items` - agent returns data but missing required field
- **Async timing issues**: Page loads in 2 seconds but agent checks after 1 second, sees empty, marks as failure
- **Network timeouts**: Amazon throttles requests or CDN slow, causing legitimate delays interpreted as failures

**How to avoid:**
1. **Increase max_failures parameter**: Set `max_failures=5` or higher in Agent constructor
2. **Add retry logic**: Wrap `agent.run()` in try/except with exponential backoff (3 retries total)
3. **Longer wait_for_network_idle**: Increase from 1.0s to 2.0s in BrowserProfile for slow pages
4. **Validate output schema**: Ensure Pydantic models match what agent actually extracts (check logs for "items" field)
5. **Test with real network delays**: Run scraper on throttled connection to catch timing issues early

**Warning signs:**
- Error message: "Stopping due to 3 consecutive failures"
- Logs show "Result failed 1/4 times" then "2/4" then "3/4" in rapid succession
- Task fails on first attempt but succeeds when immediately retried
- Failure happens on pages with known slow load times (e.g., Amazon order history)

**Phase to address:**
Phase 2 (Basic Scraper Implementation) - Configure resilience settings before testing at scale

---

### Pitfall 6: Chromium Executable Path Mismatches

**What goes wrong:**
Browser fails to launch with cryptic errors about missing executables or "Chrome for Testing" not found. Automation works on dev machine but breaks in production/CI.

**Why it happens:**
- **Playwright installs Chrome for Testing**: Recent Playwright versions (1.57+) use Chrome for Testing (20GB/instance) instead of lightweight Chromium
- **macOS ARM64 vs Intel paths**: Executable location differs: `chrome-mac-arm64/` vs `chrome-mac/`
- **Multiple Playwright versions**: Global install uses one Chromium version, venv uses another, paths don't match
- **Playwright cache cleared**: Running `brew cleanup` or clearing cache removes downloaded browsers

**How to avoid:**
1. **Auto-detect executable**: Use `stealth_utils._find_chromium_executable()` helper (already implemented)
2. **Verify after Playwright install**: Run `python -m playwright install chromium` then check `~/Library/Caches/ms-playwright/`
3. **Pin Playwright version**: Lock to 1.48.x in requirements.txt (1.57+ has memory issues)
4. **Fallback to system Chrome**: If Playwright Chromium missing, fall back to `/Applications/Google Chrome.app/...`
5. **Test on clean environment**: Spin up Docker or VM to verify executable detection works without assumptions

**Warning signs:**
- Error: "Playwright Chromium not found in ~/Library/Caches/ms-playwright"
- Error: "Chromium executable not found in chromium-1XXX"
- Browser fails to launch with no visible error
- Works on one Mac but not another (ARM vs Intel)

**Phase to address:**
Phase 1 (Foundation Setup) - Verify browser installation before writing automation code

---

## Moderate Pitfalls

### Pitfall 7: Login Credentials in Task Prompts

**What goes wrong:**
Amazon password appears in Claude API request logs, visible in Anthropic console and potentially logged by browser-use telemetry.

**Prevention:**
- **Never pass credentials in task prompts**: Use cookies instead of automated login
- Save authenticated session with `manual_login.py` script
- Load cookies from `user_data_dir` in BrowserProfile (already configured)
- If login required, use environment variables and inject separately from task string

**Phase to address:**
Phase 2 (Basic Scraper) - Remove hardcoded login steps from task prompts immediately

---

### Pitfall 8: Direct URL Navigation Fails (Redirect Loops)

**What goes wrong:**
Navigating directly to `https://www.amazon.com/gp/css/summary/print.html?orderID=X` redirects to login, then back to homepage, never reaching invoice.

**Prevention:**
- **Check session validity first**: Navigate to `amazon.com/gp/css/order-history` before invoice
- If redirected to signin, session expired - trigger manual re-login
- **Cookies expire monthly**: Set up monitoring to alert when re-login needed
- Use `manual_login.py` to refresh cookies proactively every 25 days

**Phase to address:**
Phase 2 (Basic Scraper) - Add session validation check before task execution

---

### Pitfall 9: Race Condition in Async ElectronicsBuyer Submission

**What goes wrong:**
ElectronicsBuyer agent starts before Amazon agent finishes, uses placeholder "NEEDS_PARSING" data.

**Prevention:**
- **Await Amazon scraper fully**: Ensure `amazon_data = await self.amazon_scraper.scrape_order()` completes
- **Validate data before EB submission**: Check if `items != "NEEDS_PARSING"` before calling EB agent
- Add exponential backoff if Amazon scraper returns incomplete data
- Current code in `browser_agent.py` already uses proper await, but add validation

**Phase to address:**
Phase 5 (EB.gg Integration) - Add data validation before submission

---

### Pitfall 10: Google Sheets Duplicate Rows (Shipping Updates)

**What goes wrong:**
Shipping confirmation creates new row instead of updating existing order row, causing duplicate order numbers in sheet.

**Prevention:**
- **Match on Order Number (Column G)**: Search sheet for order number before deciding append vs. update
- n8n workflow needs IF node to route: `if row_exists(order_number) → Update else → Append`
- Keep SQLite local cache of order_number → sheet_row_id mappings for fast lookups
- Current architecture separates order vs. shipping, but n8n logic not yet implemented

**Phase to address:**
Phase 6 (Google Sheets Integration) - Implement find-or-create logic in n8n workflow

---

## Minor Pitfalls

### Pitfall 11: Log File Growth (Disk Space)

**What goes wrong:**
`logs/server.log` and `logs/agent.log` grow to GB sizes over weeks, filling disk.

**Prevention:**
- Install `pm2-logrotate`: `pm2 install pm2-logrotate`
- Configure max size: `pm2 set pm2-logrotate:max_size 10M`
- Set retention: `pm2 set pm2-logrotate:retain 7` (keep 7 days)

**Phase to address:**
Phase 8 (Production Hardening)

---

### Pitfall 12: n8n Polling Interval Too Aggressive

**What goes wrong:**
Gmail Trigger polls every 1 minute, hits API rate limits, gets throttled.

**Prevention:**
- Set polling to 15 minutes (requirement: <20min latency allows this)
- Use Gmail Push Notifications (Pub/Sub) instead of polling for instant triggers
- Current plan uses 15min polling - don't reduce below this

**Phase to address:**
Phase 6 (Google Sheets Integration) - Configure during n8n workflow setup

---

### Pitfall 13: Telegram Spam on Retries

**What goes wrong:**
If email processing fails and retries 3 times, Telegram sends 3 error notifications.

**Prevention:**
- Add deduplication: track `{order_number, email_type}` in SQLite with timestamp
- Only send Telegram alert if >5 minutes since last alert for same order
- Or: Only notify on final failure, not intermediate retries

**Phase to address:**
Phase 7 (Telegram Notifications)

---

### Pitfall 14: Cashback Percentage Parsing Ambiguity

**What goes wrong:**
Amazon invoice shows "5% back" but it's a promotional banner, not the actual cashback. Agent extracts wrong percentage.

**Prevention:**
- Provide specific CSS selectors for cashback field in prompt
- If ambiguous, default to 5% and log warning for manual review
- Add validation: if extracted CB% > 10%, likely wrong - flag for human check

**Phase to address:**
Phase 4 (Data Extraction Refinement) - After basic extraction works, add validation logic

---

### Pitfall 15: ElectronicsBuyer UI Changes Break Agent

**What goes wrong:**
EB.gg updates their form layout, agent can't find "Submit Tracking" button, all submissions fail.

**Prevention:**
- Use flexible selectors: `button:has-text("Submit")` instead of hardcoded class names
- Implement UI change detection: if agent fails 5x in row, send alert "EB.gg UI may have changed"
- Keep screenshots of failed attempts for debugging
- Test EB agent weekly with dummy data to catch UI changes early

**Phase to address:**
Phase 8 (Monitoring) - Set up change detection after initial implementation stable

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode login in task prompt | Fast prototyping | Password in logs, fails monthly when cookies expire | Never - use saved cookies from start |
| Skip output schema validation | Fewer lines of code | Agent returns garbage data silently | Never - add Pydantic models in Phase 2 |
| Use `use_vision='auto'` everywhere | Works for complex pages | 10x API costs, slow execution | Only for visually complex pages (login CAPTCHAs) |
| Single retry attempt | Fast failure feedback | 5% legitimate failures due to network glitches | MVP only - add 3x retries by Phase 3 |
| Append all emails to Sheet | Simple n8n workflow | Duplicate rows for shipping updates | MVP only - add find-or-create in Phase 6 |
| Global browser context (no cleanup) | Simpler code structure | Memory leaks, crashes after 20-30 runs | Never - use async context managers from Phase 1 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Amazon invoice URLs | Assume order number in URL is enough | Must be logged in first - check session cookies exist |
| Anthropic API | Send full email body in prompt | Truncate to order number only - full email wastes tokens |
| n8n → FastAPI webhook | Set 2min timeout (default) | Use 10min timeout - browser automation is slow |
| Google Sheets API | Update cells individually (A1, A2, A3...) | Batch update entire row - 10x faster, fewer API calls |
| Telegram notifications | Send HTML formatted messages | Use Markdown - HTML breaks on some Telegram clients |
| browser-use output | Expect JSON from `result.extracted_content` | Returns Pydantic model or dict - check type before accessing |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Creating new browser context per task | Memory climbs 1GB per 10 emails | Reuse browser context across tasks in same session | After 20-30 emails processed |
| Scraping all order history instead of single order | Takes 2-3 minutes per email | Navigate directly to invoice/tracking URL | Immediate (design flaw) |
| Synchronous processing (await each email) | Queue backs up during peak (5 emails/hour) | Add async task queue (Redis + Celery) | When >3 emails arrive within 15min |
| Taking screenshots for text extraction | 3-5 seconds per screenshot, high API costs | Use DOM parsing for structured text, vision only for buttons | Noticeable with >5 emails/day |
| Polling n8n Gmail every 1 minute | Gmail API quota exhausted | Use 15min polling or Push notifications | Gmail throttles after ~1000 polls/day |
| No browser-use max_steps limit | Agent loops forever on broken pages | Set `max_steps=20` for simple tasks | Agent hangs indefinitely on edge cases |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Commit `.env` file to git | Amazon credentials leaked publicly | Add `.env` to `.gitignore` immediately |
| Log full email body | Customer PII in logs | Redact all email content except order numbers |
| Store cookies in plaintext | Session hijacking if disk compromised | Encrypt cookies file with macOS FileVault or cryptography lib |
| Run FastAPI on 0.0.0.0 without auth | Anyone on network can trigger automation | Add API key header validation or use localhost only |
| No rate limiting on `/process-order` | Malicious actor floods endpoint, racks up API costs | Add rate limit: 10 requests/minute per IP |
| Trust email sender without validation | Spoofed emails trigger automation | Verify SPF/DKIM in n8n before processing |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication during 3-5min processing | User thinks system frozen | Send immediate Telegram "Processing order X..." then final result |
| Error messages like "Agent failed" without context | User doesn't know what to do | Include order number, error type, and next steps in notification |
| Telegram notifications at 3am | Sleep disruption | Add "quiet hours" (11pm-7am) - queue notifications, send batch at 7am |
| Browser window pops to front during automation | Interrupts user's work | Use `--disable-popup-blocking` and keep browser minimized |
| No way to manually retry failed orders | User must dig through logs, restart server | Add `/retry/{order_number}` endpoint to FastAPI |
| Google Sheet auto-calculates during update | Formulas broken by automation appending rows | Freeze formula rows (1-10), data starts row 11+ |

## "Looks Done But Isn't" Checklist

- [ ] **Amazon scraper:** Often missing session validation - verify cookies exist before navigation
- [ ] **Output parsing:** Often returns "NEEDS_PARSING" - verify `extracted_content` is not empty before returning
- [ ] **Error handling:** Often only catches Exception - verify specific error types (TimeoutError, ValidationError) handled separately
- [ ] **Telegram notifications:** Often only sends success messages - verify error alerts configured
- [ ] **Google Sheets updates:** Often only appends - verify shipping updates modify existing row, not append
- [ ] **Browser cleanup:** Often skips `await browser.close()` - verify async context manager used
- [ ] **API cost monitoring:** Often no budget alerts - verify Anthropic console has $20/month alert configured
- [ ] **Cookie expiration:** Often no monitoring - verify manual re-login reminder set (every 25 days)
- [ ] **ElectronicsBuyer login:** Often assumes logged in - verify login check before submission
- [ ] **n8n workflow error handling:** Often no error branch - verify Error Trigger workflow exists
- [ ] **Rate limiting:** Often no delays between tasks - verify 30s delay between Amazon scrapes
- [ ] **Log rotation:** Often logs grow forever - verify pm2-logrotate installed and configured

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Agent exits early (Pitfall 1) | LOW | 1. Add output_model Pydantic schema 2. Increase max_failures to 5 3. Add explicit success criteria to prompt 4. Test with single email |
| Browser context not cleaned (Pitfall 2) | MEDIUM | 1. Restart Python server 2. Add `async with Agent(...)` pattern 3. Check Activity Monitor, kill orphaned Chrome processes 4. Downgrade to Python 3.12 if on 3.14 |
| Amazon anti-bot detection (Pitfall 3) | HIGH | 1. Wait 24 hours (IP cooldown) 2. Delete cookies, run manual_login.py with fresh session 3. Add playwright-stealth 4. Increase wait_between_actions to 1-2s 5. Test on different network |
| Consecutive failures stop agent (Pitfall 5) | LOW | 1. Increase max_failures parameter 2. Add retry wrapper with exponential backoff 3. Check logs for validation errors 4. Fix Pydantic schema mismatches |
| Login credentials leaked (Pitfall 7) | CRITICAL | 1. Rotate Amazon password immediately 2. Remove from task prompts 3. Use cookie-based auth only 4. Audit Anthropic API logs for exposure 5. Enable 2FA on Amazon |
| Duplicate Sheet rows (Pitfall 10) | MEDIUM | 1. Manually deduplicate in Sheet (sort by order number) 2. Add IF node in n8n to check existing rows 3. Create SQLite cache for order→row mapping |
| EB.gg UI changed (Pitfall 15) | MEDIUM | 1. Check EB.gg manually, note new field names/layout 2. Update task prompt with new selectors 3. Test with dummy tracking number 4. Re-enable live submissions |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Agent exits early (Pitfall 1) | Phase 2 (Basic Scraper) | Test scraper returns full OrderDetails, not "NEEDS_PARSING" |
| Browser context cleanup (Pitfall 2) | Phase 1 (Foundation) | Run scraper 10x in loop, memory stays under 1GB |
| Amazon anti-bot detection (Pitfall 3) | Phase 3 (Stealth Hardening) | Scrape 5 orders in 5 minutes without CAPTCHA |
| Prompt over-engineering (Pitfall 4) | Phase 4 (Cost Optimization) | API costs <$0.50 per email processed |
| Consecutive failures (Pitfall 5) | Phase 2 (Basic Scraper) | Scraper succeeds on first slow page load (5s+) |
| Chromium executable path (Pitfall 6) | Phase 1 (Foundation) | Browser launches on fresh Mac without manual config |
| Login credentials in prompts (Pitfall 7) | Phase 2 (Basic Scraper) | Search code for "password" - no matches in task strings |
| Direct URL redirect loops (Pitfall 8) | Phase 2 (Basic Scraper) | Session validation check returns True before scraping |
| EB race condition (Pitfall 9) | Phase 5 (EB Integration) | EB agent never receives "NEEDS_PARSING" |
| Duplicate Sheet rows (Pitfall 10) | Phase 6 (Sheets Integration) | Process 2 emails for same order - only 1 row in Sheet |
| Log file growth (Pitfall 11) | Phase 8 (Production) | Logs stay under 50MB after 1 week of operation |
| n8n polling too aggressive (Pitfall 12) | Phase 6 (Sheets Integration) | Gmail API usage <50% of daily quota |
| Telegram notification spam (Pitfall 13) | Phase 7 (Telegram) | Failed retry sends only 1 notification, not 3 |
| Cashback parsing ambiguity (Pitfall 14) | Phase 4 (Data Refinement) | Manual review of 10 orders - CB% correct in all |
| EB.gg UI changes (Pitfall 15) | Phase 8 (Monitoring) | Weekly test detects UI changes within 7 days |

## Sources

### Browser-Use Specific Issues
- [Bug: Browser get killed and task restarts · Issue #2613](https://github.com/browser-use/browser-use/issues/2613)
- [Issue related to Patchright: Stopping due to 3 consecutive failures · Issue #582](https://github.com/browser-use/web-ui/issues/582)
- [agent stops after 3 consecutive failures · Issue #660](https://github.com/browser-use/web-ui/issues/660)
- [Bug: Agent run function is not stopping · Issue #3615](https://github.com/browser-use/browser-use/issues/3615)
- [Agent failed if we execute several tasks · Issue #1073](https://github.com/browser-use/browser-use/issues/1073)
- [Agent Settings - Browser Use Documentation](https://docs.browser-use.com/customize/agent-settings)

### Playwright Issues
- [Browser is closing automatically · Issue #34485](https://github.com/microsoft/playwright/issues/34485)
- [Bug: Memory Consumption Issue with Playwright 1.44.1 · Issue #32459](https://github.com/microsoft/playwright/issues/32459)
- [Bug: Playwright 1.57 high memory usage (20GB+ per instance) · Issue #38489](https://github.com/microsoft/playwright/issues/38489)
- [How to Fix "Target Closed" Error in Playwright](https://www.checklyhq.com/docs/learn/playwright/error-target-closed/)

### Claude Agent Architecture
- [Tracing Claude Code's LLM Traffic: Agentic loop](https://medium.com/@georgesung/tracing-claude-codes-llm-traffic-agentic-loop-sub-agents-tool-use-prompts-7796941806f5)
- [Claude Code's Tasks update prevents hallucinated completion](https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across)

### Anti-Bot Detection
- [How to Avoid Bot Detection with Playwright](https://www.browserstack.com/guide/playwright-bot-detection)
- [Avoid Bot Detection With Playwright Stealth](https://www.scrapeless.com/en/blog/avoid-bot-detection-with-playwright-stealth)
- [How to Bypass Amazon CAPTCHA for Web Scraping](https://brightdata.com/blog/web-data/bypass-amazon-captcha)
- [Making Playwright scrapers undetected](https://substack.thewebscraping.club/p/playwright-scrapers-undetected)

### Browser Automation Performance
- [Why less is more: The Playwright proliferation problem with MCP](https://www.speakeasy.com/blog/playwright-tool-proliferation)
- [How to Fix Playwright MCP 2.0 Memory Leaks](https://markaicode.com/playwright-mcp-memory-leak-fixes-2025/)

### Project-Specific Analysis
- Local logs: `/Users/pinkpanther/Desktop/amazon-email-automation/logs/server.log`
- Code review: `amazon_scraper.py`, `browser_agent.py`, `stealth_utils.py`, `main.py`

---

*Pitfalls research for: Amazon Email Automation Browser Agent*
*Researched: 2026-02-12*
*Next: Use these pitfalls to inform debugging roadmap and stabilization phase*
