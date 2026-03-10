"""Static contract checks for strict Amazon order-details item extraction scope."""

from pathlib import Path
import re


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = Path("amazon_scraper.py").read_text(encoding="utf-8")

    _assert(
        "ORDER_DETAILS_ITEM_TITLE_SELECTOR_TEMPLATES" in source
        and "ORDER_DETAILS_ITEM_QUANTITY_SELECTOR_TEMPLATES" in source
        and "ORDER_DETAILS_ROW_LOCAL_QUANTITY_SELECTORS" in source,
        "Strict order-details selector templates must be defined.",
    )
    _assert(
        "strict-order-details-rows" in source,
        "Strict item extraction mode label must be present.",
    )
    _assert(
        "Strict item extraction found no order-details rows; refusing broad fallback." in source,
        "Shipping fallback must fail closed when strict row extraction yields no items.",
    )

    fn_match = re.search(
        r"async def _extract_items_from_order_page[\s\S]*?^\s*async def _scrape_shipping_fallback",
        source,
        flags=re.MULTILINE,
    )
    _assert(fn_match is not None, "Could not locate _extract_items_from_order_page function body.")
    fn_src = fn_match.group(0)

    _assert(
        "a[href*='/dp/']" not in fn_src
        and "global-fallback" not in fn_src
        and "rowLocalQuantitySelectors" in fn_src
        and "findRowLocalQuantity" in fn_src,
        "Item extraction must not include global product-link fallback scans.",
    )

    print("PASS: amazon item scope contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
