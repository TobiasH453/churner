"""Fast checks for Amazon shipping delivery date normalization semantics."""

import ast
import copy
from pathlib import Path


def _load_normalizer():
    source = Path("amazon_scraper.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="amazon_scraper.py")

    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "AmazonScraper":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_normalize_shipping_delivery_date":
                    fn_node = item
                    break
            break

    if fn_node is None:
        raise AssertionError("Could not find AmazonScraper._normalize_shipping_delivery_date in amazon_scraper.py")

    fn_node = copy.deepcopy(fn_node)
    fn_node.returns = None
    for arg in fn_node.args.posonlyargs + fn_node.args.args + fn_node.args.kwonlyargs:
        arg.annotation = None
    if fn_node.args.vararg is not None:
        fn_node.args.vararg.annotation = None
    if fn_node.args.kwarg is not None:
        fn_node.args.kwarg.annotation = None

    scratch_class = ast.ClassDef(
        name="ScratchAmazonScraper",
        bases=[],
        keywords=[],
        body=[fn_node],
        decorator_list=[],
    )
    module = ast.Module(body=[scratch_class], type_ignores=[])
    ast.fix_missing_locations(module)

    namespace: dict = {}
    exec(compile(module, filename="<normalize_test>", mode="exec"), {"re": __import__("re")}, namespace)
    return namespace["ScratchAmazonScraper"]._normalize_shipping_delivery_date


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    normalize = _load_normalizer()
    source = Path("amazon_scraper.py").read_text(encoding="utf-8")

    _assert(
        normalize("Wednesday 3") == "Wednesday",
        "Weekday + number must normalize to weekday only.",
    )
    _assert(
        normalize("Wed, 3") == "Wed",
        "Abbreviated weekday + number must normalize to weekday only.",
    )
    _assert(
        normalize("Arriving March 4") == "March 4",
        "Leading arrival label should be stripped from month-day formats.",
    )
    _assert(
        normalize("March 4, 2026") == "March 4",
        "Month-day-year should normalize to month-day.",
    )
    _assert(
        normalize("Tomorrow by 10 PM") == "Tomorrow by 10 PM",
        "Unmatched formats should be preserved as cleaned plaintext.",
    )
    _assert(
        normalize(None) is None,
        "None input should remain None.",
    )
    _assert(
        "_normalize_shipping_delivery_date(" in source and "_extract_delivery_date(body_text)" in source,
        "Shipping fallback must apply shipping-specific delivery date normalization.",
    )

    print("PASS: amazon shipping date normalization checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
