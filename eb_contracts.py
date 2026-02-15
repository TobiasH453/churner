"""Contract helpers for ElectronicsBuyer deal/tracking result normalization."""

from __future__ import annotations

from typing import Iterable

from models import EBDealResult

FLAG_UNMATCHED_ITEMS = "FLAG_UNMATCHED_ITEMS"
FLAG_DEAL_PAYOUT_INCOMPLETE = "FLAG_DEAL_PAYOUT_INCOMPLETE"
FLAG_DEAL_NO_SUBMISSIONS = "FLAG_DEAL_NO_SUBMISSIONS"
FLAG_DEAL_TIMEOUT = "FLAG_DEAL_TIMEOUT"


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _normalize_items(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            normalized.append(value)
    return _unique_preserve_order(normalized)


def _normalize_quantities(quantities: dict) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for raw_name, raw_qty in (quantities or {}).items():
        if not isinstance(raw_name, str):
            continue
        name = raw_name.strip()
        if not name:
            continue
        try:
            qty = int(raw_qty)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        normalized[name] = qty
    return normalized


def _flagged_error(flag: str, message: str) -> str:
    return f"{flag}: {message}"


def enforce_deal_contract(result: EBDealResult, quantities: dict) -> EBDealResult:
    """Apply strict deal success semantics with explicit unmatched/payout flags."""
    normalized_quantities = _normalize_quantities(quantities)
    requested_items = _unique_preserve_order(normalized_quantities.keys())
    submitted_items = _normalize_items(result.submitted_items)
    payout_items = _normalize_items(result.payout_captured_items)
    unmatched_items = _normalize_items(result.unmatched_items)
    warnings = _normalize_items(result.warnings)

    inferred_unmatched = [
        item for item in requested_items if item not in submitted_items and item not in unmatched_items
    ]
    if inferred_unmatched:
        unmatched_items = _unique_preserve_order(unmatched_items + inferred_unmatched)

    if unmatched_items and FLAG_UNMATCHED_ITEMS not in warnings:
        warnings.append(FLAG_UNMATCHED_ITEMS)

    missing_payout_items = [item for item in submitted_items if item not in payout_items]
    warning_set = _unique_preserve_order(warnings)

    if result.success and not submitted_items:
        return result.model_copy(
            update={
                "success": False,
                "error_message": _flagged_error(
                    FLAG_DEAL_NO_SUBMISSIONS,
                    "Deal reported success but did not include submitted_items.",
                ),
                "warnings": _unique_preserve_order(warning_set + [FLAG_DEAL_NO_SUBMISSIONS]),
                "unmatched_items": unmatched_items,
                "submitted_items": submitted_items,
                "payout_captured_items": payout_items,
            }
        )

    if result.success and (missing_payout_items or result.payout_value <= 0):
        detail = (
            f"Missing payout capture for submitted items: {missing_payout_items}"
            if missing_payout_items
            else "Deal reported success with non-positive payout value."
        )
        return result.model_copy(
            update={
                "success": False,
                "error_message": _flagged_error(FLAG_DEAL_PAYOUT_INCOMPLETE, detail),
                "warnings": _unique_preserve_order(warning_set + [FLAG_DEAL_PAYOUT_INCOMPLETE]),
                "unmatched_items": unmatched_items,
                "submitted_items": submitted_items,
                "payout_captured_items": payout_items,
            }
        )

    if missing_payout_items and FLAG_DEAL_PAYOUT_INCOMPLETE not in warning_set:
        warning_set.append(FLAG_DEAL_PAYOUT_INCOMPLETE)

    if not result.success and not result.error_message and missing_payout_items:
        error_message = _flagged_error(
            FLAG_DEAL_PAYOUT_INCOMPLETE,
            f"Missing payout capture for submitted items: {missing_payout_items}",
        )
    else:
        error_message = result.error_message

    return result.model_copy(
        update={
            "warnings": _unique_preserve_order(warning_set),
            "unmatched_items": unmatched_items,
            "submitted_items": submitted_items,
            "payout_captured_items": payout_items,
            "error_message": error_message,
        }
    )
