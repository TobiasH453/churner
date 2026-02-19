#!/usr/bin/env python3
"""Validate smoke response JSON against AgentResponse contract expectations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate /process-order smoke response structure and invariants.",
    )
    parser.add_argument(
        "--expected-email-type",
        required=True,
        choices=["order_confirmation", "shipping_confirmation"],
        help="Expected email_type in the response payload.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()

    try:
        from pydantic import ValidationError
    except ModuleNotFoundError:
        return fail(
            "Missing dependency: pydantic. Install project dependencies before running smoke validation."
        )

    try:
        from models import AgentResponse  # noqa: WPS433
    except Exception as exc:
        return fail(f"Unable to load project response model: {exc}")

    raw = sys.stdin.read().strip()
    if not raw:
        return fail("empty response body")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return fail(f"invalid JSON response: {exc}")

    try:
        response = AgentResponse.model_validate(payload)
    except ValidationError as exc:
        return fail(f"response did not satisfy AgentResponse contract: {exc}")

    if response.email_type != args.expected_email_type:
        return fail(
            f"email_type mismatch: expected {args.expected_email_type}, got {response.email_type}"
        )
    if not response.order_number:
        return fail("missing or empty order_number in response")
    if response.execution_time_seconds < 0:
        return fail("execution_time_seconds cannot be negative")

    print(f"PASS: response contract valid ({args.expected_email_type})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
