"""
Stealth utilities for human-like browser automation
"""
import random
import os
import glob
from browser_use.browser.profile import BrowserProfile

STEALTH_BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-first-run',
    '--no-default-browser-check',
]

STEALTH_IGNORE_DEFAULT_ARGS = ['--enable-automation']

def _find_chromium_executable() -> str:
    """Find Playwright's Chromium executable"""
    # Playwright installs Chromium to cache directory
    playwright_cache = os.path.expanduser("~/Library/Caches/ms-playwright")

    # Find the chromium directory (e.g., chromium-1208)
    chromium_dirs = glob.glob(f"{playwright_cache}/chromium-*")
    if not chromium_dirs:
        raise FileNotFoundError(f"Playwright Chromium not found in {playwright_cache}. Run: python -m playwright install chromium")

    # Use the newest version (highest number)
    chromium_dir = sorted(chromium_dirs)[-1]

    # Try different possible paths (ARM64 vs Intel, different app names)
    possible_paths = [
        f"{chromium_dir}/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        f"{chromium_dir}/chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium",
        f"{chromium_dir}/chrome-mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        f"{chromium_dir}/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    ]

    for executable_path in possible_paths:
        if os.path.exists(executable_path):
            return executable_path

    raise FileNotFoundError(f"Chromium executable not found in {chromium_dir}. Checked: {possible_paths}")

    return executable_path

def get_chromium_executable() -> str:
    """Public helper for callers that need Playwright launch parity."""
    return _find_chromium_executable()

def create_stealth_profile(user_data_dir: str = "./data/browser-profile") -> BrowserProfile:
    """
    Create BrowserProfile with randomized human-like timing

    Args:
        user_data_dir: Path to persistent browser profile directory

    Returns:
        BrowserProfile configured for stealth
    """
    # Randomize delay between 0.3-0.8 seconds (triangular distribution peaks at 0.55s)
    random_delay = random.triangular(0.3, 0.8, 0.55)

    # Find Playwright's Chromium executable
    chromium_path = _find_chromium_executable()

    return BrowserProfile(
        user_data_dir=user_data_dir,
        headless=False,
        executable_path=chromium_path,  # Point to Playwright's Chromium
        wait_between_actions=random_delay,
        minimum_wait_page_load_time=0.5,
        wait_for_network_idle_page_load_time=1.0,
        # CRITICAL: Anti-detection arguments matching manual_login.py
        args=STEALTH_BROWSER_ARGS,
        ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
    )
