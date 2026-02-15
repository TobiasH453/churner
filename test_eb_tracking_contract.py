"""Fast static contract checks for ElectronicsBuyer tracking outcome flags."""

from pathlib import Path
import re


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = Path("electronics_buyer.py").read_text(encoding="utf-8")

    # Missing-field scenario contract.
    _assert(
        "FLAG_REQUIRED_FIELD_MISSING" in source,
        "Missing-field flag constant must be defined.",
    )
    _assert(
        re.search(r"_fill_required_tracking_field[\s\S]*FLAG_REQUIRED_FIELD_MISSING", source) is not None,
        "Required field validator must emit FLAG_REQUIRED_FIELD_MISSING.",
    )

    # Duplicate scenario contract.
    _assert(
        "FLAG_DUPLICATE_TRACKING" in source,
        "Duplicate flag constant must be defined.",
    )
    _assert(
        "TRACKING_DUPLICATE_TEXT_HINTS" in source and "_classify_tracking_page_failure" in source,
        "Duplicate classification helper must exist.",
    )
    _assert(
        re.search(r"_classify_tracking_page_failure[\s\S]*FLAG_DUPLICATE_TRACKING", source) is not None,
        "Duplicate classification must return FLAG_DUPLICATE_TRACKING.",
    )

    # Ambiguous/no-signal contract.
    _assert(
        "FLAG_NO_SUCCESS_SIGNAL" in source,
        "No-success-signal flag must be defined.",
    )
    _assert(
        "Deterministic tracking submission failed after 2 attempts" in source,
        "Two-attempt bounded retry path must remain in place.",
    )

    print("PASS: tracking contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
