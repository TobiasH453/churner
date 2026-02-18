"""Static contract checks for n8n /process-order workflow payload mapping."""

from __future__ import annotations

import json
from pathlib import Path


WORKFLOW_PATH = Path("n8n-workflows/03-process-order-v1.0.0.json")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load_workflow() -> dict:
    _assert(WORKFLOW_PATH.exists(), f"Missing workflow artifact: {WORKFLOW_PATH}")
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _node_by_name(nodes: list[dict], name: str) -> dict:
    for node in nodes:
        if node.get("name") == name:
            return node
    raise AssertionError(f"Missing node in workflow: {name}")


def _collect_set_fields(set_node: dict) -> dict[str, str]:
    string_values = (
        set_node.get("parameters", {})
        .get("values", {})
        .get("string", [])
    )
    mapping: dict[str, str] = {}
    for item in string_values:
        key = item.get("name")
        val = item.get("value")
        if isinstance(key, str) and isinstance(val, str):
            mapping[key] = val
    return mapping


def main() -> int:
    workflow = _load_workflow()
    nodes = workflow.get("nodes", [])
    _assert(isinstance(nodes, list) and nodes, "Workflow must contain nodes.")

    set_node = _node_by_name(nodes, "Canonical Payload")
    warn_node = _node_by_name(nodes, "Annotate Contract Warnings")
    required_node = _node_by_name(nodes, "Required Fields Present")
    request_node = _node_by_name(nodes, "POST /process-order")

    _assert(
        set_node.get("type") == "n8n-nodes-base.set",
        "Canonical Payload must be a Set node.",
    )
    set_fields = _collect_set_fields(set_node)
    _assert("email_type" in set_fields, "Set node must map email_type.")
    _assert("order_number" in set_fields, "Set node must map order_number.")
    _assert("account_type" in set_fields, "Set node must map account_type.")
    _assert(
        "amz_personal" in set_fields["account_type"],
        "account_type must default to amz_personal when missing.",
    )

    code_body = warn_node.get("parameters", {}).get("jsCode", "")
    _assert(isinstance(code_body, str), "Contract warning node must define jsCode.")
    _assert(
        "unknown_fields_accepted" in code_body,
        "Warning node must flag unknown_fields_accepted.",
    )
    _assert(
        "compatibility_mode_minor_variant" in code_body,
        "Warning node must flag compatibility_mode_minor_variant.",
    )

    req_params = required_node.get("parameters", {})
    req_serialized = json.dumps(req_params)
    _assert("email_type" in req_serialized, "Required-field guard must check email_type.")
    _assert("order_number" in req_serialized, "Required-field guard must check order_number.")

    req_url = request_node.get("parameters", {}).get("url", "")
    _assert("/process-order" in str(req_url), "Request node must target /process-order.")

    body_json = request_node.get("parameters", {}).get("bodyParametersJson", "")
    _assert("email_type" in str(body_json), "Request body must include email_type.")
    _assert("order_number" in str(body_json), "Request body must include order_number.")
    _assert("account_type" in str(body_json), "Request body must include account_type.")

    models_src = Path("models.py").read_text(encoding="utf-8")
    _assert(
        'email_type: Literal["order_confirmation", "shipping_confirmation"]' in models_src,
        "EmailData must keep constrained email_type literals.",
    )
    _assert("order_number: str" in models_src, "EmailData must require order_number.")
    _assert(
        "account_type: Optional[str] = None" in models_src,
        "EmailData must keep optional account_type field.",
    )

    print("PASS: n8n process-order contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
