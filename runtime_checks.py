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
            "compatibility warnings on Python 3.14+ in some environments. "
            "Python 3.13 is the preferred interpreter for this repository. "
            "Continuing on 3.14+, but if you see repeated step failures "
            "(for example 'items'), run with DEBUG logging to capture full traces.",
            ".".join(map(str, sys.version_info[:3])),
        )

    _WARNED_ONCE = True
