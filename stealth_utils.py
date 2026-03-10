"""
Stealth utilities for human-like browser automation
"""
import random
import os
import glob
import shutil
import tempfile
import time
from pathlib import Path
from browser_use.browser.profile import BrowserProfile

STEALTH_BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-first-run',
    '--no-default-browser-check',
]

STEALTH_IGNORE_DEFAULT_ARGS = ['--enable-automation']

_VOLATILE_PROFILE_DIR_NAMES = {
    "cache",
    "cache_data",
    "code cache",
    "gpucache",
    "grshadercache",
    "dawngraphitecache",
    "blob_storage",
    "service worker",
    "shadercache",
    "crashpad",
}
_PROFILE_SNAPSHOT_ROOT_PREFIX = "browser-profile-snapshot-"
_PROFILE_SNAPSHOT_TTL_SECONDS = 6 * 60 * 60

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


def _is_volatile_component(path_component: str) -> bool:
    return path_component.strip().lower() in _VOLATILE_PROFILE_DIR_NAMES


def _copy_profile_best_effort(src_root: Path, dst_root: Path) -> None:
    for current_root, dirnames, filenames in os.walk(src_root):
        current_path = Path(current_root)
        rel = current_path.relative_to(src_root)
        rel_parts = rel.parts
        if any(_is_volatile_component(part) for part in rel_parts):
            dirnames[:] = []
            continue

        # Skip volatile directories before os.walk enters them.
        dirnames[:] = [name for name in dirnames if not _is_volatile_component(name)]

        target_dir = dst_root / rel
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            source_file = current_path / filename
            target_file = target_dir / filename
            try:
                shutil.copy2(source_file, target_file)
            except (FileNotFoundError, PermissionError, OSError):
                # Chromium mutates profile files while active; ignore transient misses.
                continue


def _prune_old_profile_snapshots(tmp_root: Path) -> None:
    now = time.time()
    for child in tmp_root.iterdir():
        if not child.is_dir() or not child.name.startswith(_PROFILE_SNAPSHOT_ROOT_PREFIX):
            continue
        try:
            age_seconds = now - child.stat().st_mtime
            if age_seconds > _PROFILE_SNAPSHOT_TTL_SECONDS:
                shutil.rmtree(child, ignore_errors=True)
        except OSError:
            continue


def _create_profile_snapshot(user_data_dir: str) -> str:
    source = Path(user_data_dir).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        return user_data_dir

    tmp_root = Path(tempfile.gettempdir())
    _prune_old_profile_snapshots(tmp_root)
    snapshot_dir = Path(
        tempfile.mkdtemp(prefix=_PROFILE_SNAPSHOT_ROOT_PREFIX, dir=str(tmp_root))
    )
    _copy_profile_best_effort(source, snapshot_dir)
    return str(snapshot_dir)

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

    safe_user_data_dir = _create_profile_snapshot(user_data_dir)

    return BrowserProfile(
        user_data_dir=safe_user_data_dir,
        headless=False,
        executable_path=chromium_path,  # Point to Playwright's Chromium
        wait_between_actions=random_delay,
        minimum_wait_page_load_time=0.5,
        wait_for_network_idle_page_load_time=1.0,
        # CRITICAL: Anti-detection arguments matching manual_login.py
        args=STEALTH_BROWSER_ARGS,
        ignore_default_args=STEALTH_IGNORE_DEFAULT_ARGS,
    )
