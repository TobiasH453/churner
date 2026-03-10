"""Static contract checks for Amazon personal/business account routing."""

from pathlib import Path


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    models_src = Path("models.py").read_text(encoding="utf-8")
    browser_src = Path("browser_agent.py").read_text(encoding="utf-8")
    scraper_src = Path("amazon_scraper.py").read_text(encoding="utf-8")

    _assert(
        "account_type: Optional[str] = None" in models_src,
        "EmailData must include optional account_type routing field.",
    )

    _assert(
        "self.amazon_personal_scraper = AmazonScraper(account_type=\"amz_personal\")" in browser_src
        and "self.amazon_business_scraper = AmazonScraper(account_type=\"amz_business\")" in browser_src,
        "BrowserAgent must initialize separate personal and business Amazon scrapers.",
    )
    _assert(
        "def _select_amazon_scraper" in browser_src and "defaulting to personal scraper" in browser_src,
        "BrowserAgent must route by account_type and fallback to personal.",
    )

    _assert(
        "PERSONAL_USER_DATA_DIR" in scraper_src and "BUSINESS_USER_DATA_DIR" in scraper_src,
        "AmazonScraper must define separate persistent profile directories.",
    )
    _assert(
        "AMAZON_BUSINESS_EMAIL" in scraper_src
        and "AMAZON_BUSINESS_PASSWORD" in scraper_src
        and "AMAZON_BUSINESS_TOTP_SECRET" in scraper_src,
        "Amazon business credential env vars must be wired in scraper initialization.",
    )
    _assert(
        'if self.account_type == "amz_business":' in scraper_src
        and "https://www.amazon.com/your-orders/order-details" in scraper_src
        and "ab_ppx_yo_dt_b_fed_order_details" in scraper_src,
        "Business order confirmation must use the /your-orders/order-details URL.",
    )
    _assert(
        "https://www.amazon.com/gp/css/summary/print.html?ie=UTF8&orderID={order_number}" in scraper_src,
        "Personal order confirmation must retain legacy print URL behavior.",
    )

    print("PASS: amazon account routing contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
