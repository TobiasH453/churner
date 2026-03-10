"""Fast checks for Amazon tracking number extraction robustness."""

import ast
import copy
from pathlib import Path


class _StripAnnotations(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.returns = None
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            arg.annotation = None
        if node.args.vararg is not None:
            node.args.vararg.annotation = None
        if node.args.kwarg is not None:
            node.args.kwarg.annotation = None
        return self.generic_visit(node)


def _load_extractor():
    source = Path("amazon_scraper.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="amazon_scraper.py")

    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "AmazonScraper":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_extract_tracking_number":
                    fn_node = item
                    break
            break

    if fn_node is None:
        raise AssertionError("Could not find AmazonScraper._extract_tracking_number in amazon_scraper.py")

    fn_node = copy.deepcopy(fn_node)
    fn_node = _StripAnnotations().visit(fn_node)

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
    exec(compile(module, filename="<tracking_test>", mode="exec"), {"re": __import__("re")}, namespace)
    return namespace["ScratchAmazonScraper"]._extract_tracking_number


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    extract = _load_extractor()
    source = Path("amazon_scraper.py").read_text(encoding="utf-8")

    _assert(
        extract("Tracking number: 1Z999AA10123456784") == "1Z999AA10123456784",
        "UPS-style tracking IDs should be extracted.",
    )
    _assert(
        extract("Your package is on the way. Tracking ID TBA 1234-5678-9012") == "TBA123456789012",
        "Amazon TBA IDs should normalize spaces/hyphens.",
    )
    _assert(
        extract("Shipment details: tracking # 9400111899223000123456") == "9400111899223000123456",
        "USPS-style numeric tracking IDs should be extracted.",
    )
    _assert(
        extract("No tracking information available yet.") is None,
        "Missing tracking text should return None.",
    )
    _assert(
        "multi-source extraction" in source,
        "Shipping fallback should retain the multi-source tracking recovery path.",
    )
    _assert(
        "matched order number" in source and "_extract_tracking_from_progress_tracker_card" in source,
        "Shipping fallback must reject order-number matches and use progress-tracker-card extraction.",
    )

    print("PASS: amazon tracking number extraction checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
