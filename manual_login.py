#!/usr/bin/env python3
"""
Manual login script - Run this to log into Amazon and ElectronicsBuyer.gg
The browser profile will be saved for future automation runs
"""
import asyncio
from playwright.async_api import async_playwright
import os
import sys

PROFILE_DIRS = {
    "personal": "./data/browser-profile-personal",
    "business": "./data/browser-profile-business",
}

async def manual_login(account_mode: str = "personal"):
    """
    Opens Chrome with SAME configuration as automation
    """
    user_data_dir = PROFILE_DIRS.get(account_mode, PROFILE_DIRS["personal"])

    print("🌐 Opening Chrome browser for manual Amazon login...")
    print("📝 Instructions:")
    print("   1. Browser will open to Amazon")
    print(f"   2. Log in to the Amazon {account_mode} account")
    print("   3. Press Ctrl+C in this terminal when done\n")

    # Ensure user_data_dir exists
    os.makedirs(user_data_dir, exist_ok=True)

    async with async_playwright() as p:
        # Launch with same args as browser-use automation
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check',
            ],
            ignore_default_args=['--enable-automation'],
        )

        page = await browser.new_page()
        await page.goto('https://www.amazon.com')

        print(f"✅ Browser opened! Log in to Amazon ({account_mode}) profile.")
        print(f"   🔹 Profile path: {user_data_dir}")
        print("   🔹 Press Ctrl+C here when login is complete\n")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n✅ Session saved to {user_data_dir}")
            print("✅ Amazon automation will now stay logged in for this profile.")
        finally:
            await browser.close()

if __name__ == "__main__":
    mode = "personal"
    if len(sys.argv) > 1:
        mode = str(sys.argv[1]).strip().lower()
    if mode not in PROFILE_DIRS:
        print("Usage: python manual_login.py [personal|business]")
        raise SystemExit(1)
    asyncio.run(manual_login(mode))
