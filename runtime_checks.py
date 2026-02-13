import logging
import sys

logger = logging.getLogger(__name__)

_WARNED_ONCE = False


def ensure_browser_runtime_compatibility() -> None:
    """
    Warn once when running on Python versions known to be unstable with
    the current browser-use/langchain stack.
    """
    global _WARNED_ONCE
    if _WARNED_ONCE:
        return

    if sys.version_info >= (3, 14):
        logger.warning(
            "Python %s detected. browser-use + langchain-core currently emit "
            "compatibility warnings on Python 3.14+, which can surface as "
            "agent step failures (for example repeated 'items' errors). "
            "Recommended runtime: Python 3.9-3.13.",
            ".".join(map(str, sys.version_info[:3])),
        )

    _WARNED_ONCE = True
