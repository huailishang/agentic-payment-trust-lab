from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.adapters.x402 import (  # noqa: E402
    X402AdaptationStatus,
    adapt_x402_fixture,
    compute_requirement_digest,
)

FIXTURE_PATH = ROOT / "samples" / "protocols" / "x402" / "x402_offline_cases_v1.json"
document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
by_id = {item["case_id"]: item for item in document["cases"]}


def fixture(case_id: str = "X402-C01-BINDING-MATCH") -> dict[str, Any]:
    value = copy.deepcopy(by_id[case_id])
    value.setdefault("fixture_version", document["fixture_version"])
    return value


def set_path(value: dict[str, Any], path: str, malformed: Any) -> None:
    if path in {"case_id", "fixture_version"}:
        value[path] = malformed
        return
    section, field = path.split(".", 1)
    value[section][field] = malformed


required_text_paths = [
    "case_id",
    "fixture_version",
    "http_request.method",
    "http_request.resource_ref",
    "http_request.request_ref",
    "payment_requirement.requirement_id",
    "payment_requirement.requirement_digest",
    "payment_requirement.resource_ref",
    "payment_requirement.scheme",
    "payment_requirement.network",
    "payment_requirement.asset",
    "payment_requirement.payee",
    "payment_proof.proof_ref",
    "payment_proof.requirement_ref",
    "payment_proof.requirement_digest",
    "payment_proof.request_ref",
    "payment_proof.resource_ref",
    "payment_proof.scheme",
    "payment_proof.network",
    "payment_proof.asset",
    "payment_proof.payee",
    "payment_proof.original_transaction_ref",
    "facilitator_verification.status",
    "facilitator_verification.proof_ref",
    "facilitator_verification.requirement_ref",
    "facilitator_settlement.status",
    "facilitator_settlement.proof_ref",
    "facilitator_settlement.payment_ref",
    "facilitator_settlement.original_transaction_ref",
    "facilitator_settlement.provider_ref",
    "facilitator_async_observation.status",
    "facilitator_async_observation.payment_ref",
    "facilitator_async_observation.original_transaction_ref",
    "facilitator_async_observation.provider_ref",
    "resource_delivery.status",
    "resource_delivery.request_ref",
    "resource_delivery.resource_ref",
    "resource_delivery.proof_ref",
    "resource_delivery.delivery_ref",
    "project_context.user_ref",
    "project_context.agent_ref",
    "project_context.authority_ref",
    "project_context.authority_version",
    "project_context.merchant_ref",
    "project_context.category",
]

failures: list[str] = []
for index, path in enumerate(required_text_paths):
    sample = fixture()
    malformed: Any = ["not-text"] if index % 2 == 0 else {"not": "text"}
    set_path(sample, path, malformed)
    result = adapt_x402_fixture(sample)
    expected_reason = f"x402_string_invalid:{path}"
    if result.status is not X402AdaptationStatus.INVALID:
        failures.append(f"{path}: status={result.status.value}")
    if expected_reason not in result.reason_codes:
        failures.append(f"{path}: missing_reason={expected_reason}")
    neutral_values = (
        result.mandate,
        result.order,
        result.request,
        result.payment,
        result.settlement_observation,
        result.async_observation,
        result.resource_delivery,
    )
    if any(item is not None for item in neutral_values) or result.delivery_attempts:
        failures.append(f"{path}: neutral_models_constructed")

# Optional failure_code must also be strict when present.
failure_code = fixture("X402-C06-SETTLEMENT-DELIVERY-CONFLICT")
failure_code["resource_delivery"]["failure_code"] = ["not-text"]
result = adapt_x402_fixture(failure_code)
if result.status is not X402AdaptationStatus.INVALID:
    failures.append(f"resource_delivery.failure_code: status={result.status.value}")
if "x402_string_invalid:resource_delivery.failure_code" not in result.reason_codes:
    failures.append("resource_delivery.failure_code: missing_reason")

# Delivery-attempt textual fields use the duplicate fixture.
for field in ("execution_id", "request_ref", "resource_ref", "proof_ref", "status"):
    sample = fixture("X402-C05-DUPLICATE-CONCURRENT-REUSE")
    sample["delivery_attempts"][0][field] = ["not-text"]
    result = adapt_x402_fixture(sample)
    expected_reason = f"x402_string_invalid:delivery_attempts[0].{field}"
    if result.status is not X402AdaptationStatus.INVALID:
        failures.append(f"delivery_attempts[0].{field}: status={result.status.value}")
    if expected_reason not in result.reason_codes:
        failures.append(f"delivery_attempts[0].{field}: missing_reason={expected_reason}")
    if any(
        item is not None
        for item in (
            result.mandate,
            result.order,
            result.request,
            result.payment,
            result.settlement_observation,
            result.async_observation,
            result.resource_delivery,
        )
    ) or result.delivery_attempts:
        failures.append(f"delivery_attempts[0].{field}: neutral_models_constructed")

# Exact rejected linked-reference counterexample.
linked = fixture()
malformed_ref = ["proof-as-list"]
linked["payment_proof"]["proof_ref"] = malformed_ref
linked["facilitator_verification"]["proof_ref"] = malformed_ref
linked["facilitator_settlement"]["proof_ref"] = malformed_ref
linked["facilitator_settlement"]["payment_ref"] = malformed_ref
linked["facilitator_async_observation"]["payment_ref"] = malformed_ref
linked["resource_delivery"]["proof_ref"] = malformed_ref
linked_result = adapt_x402_fixture(linked)
if linked_result.status is not X402AdaptationStatus.INVALID:
    failures.append(f"linked-proof-counterexample: status={linked_result.status.value}")
if "x402_string_invalid:payment_proof.proof_ref" not in linked_result.reason_codes:
    failures.append("linked-proof-counterexample: missing path reason")
if linked_result.payment is not None:
    failures.append("linked-proof-counterexample: payment constructed")

# Blank string remains missing, not malformed.
blank = fixture()
blank["payment_proof"]["proof_ref"] = "   "
blank_result = adapt_x402_fixture(blank)
if blank_result.status is not X402AdaptationStatus.INVALID:
    failures.append(f"blank-proof: status={blank_result.status.value}")
if "x402_required_field_missing:payment_proof.proof_ref" not in blank_result.reason_codes:
    failures.append("blank-proof: missing required-field reason")

# Valid unsupported strings preserve UNSUPPORTED semantics.
for section, field, value, expected_reason in (
    ("payment_requirement", "scheme", "future-scheme", "x402_scheme_unsupported:future-scheme"),
    ("payment_requirement", "network", "future-network", "x402_network_unsupported:future-network"),
):
    sample = fixture()
    sample[section][field] = value
    sample["payment_proof"][field] = value
    result = adapt_x402_fixture(sample)
    if result.status is not X402AdaptationStatus.UNSUPPORTED:
        failures.append(f"unsupported-{field}: status={result.status.value}")
    if expected_reason not in result.reason_codes:
        failures.append(f"unsupported-{field}: missing_reason={expected_reason}")

# Direct digest API rejects malformed text before hashing.
digest_sample = fixture()
digest_sample["http_request"]["method"] = ["GET"]
try:
    compute_requirement_digest(
        digest_sample["http_request"],
        digest_sample["payment_requirement"],
    )
except ValueError as exc:
    if "x402_string_invalid:http_request.method" not in str(exc):
        failures.append(f"digest-api: wrong_error={exc}")
else:
    failures.append("digest-api: malformed method accepted")

# All six valid fixtures remain ready.
valid_statuses = [adapt_x402_fixture(fixture(item["case_id"])).status.value for item in document["cases"]]
if valid_statuses != ["READY"] * 6:
    failures.append(f"valid-fixtures={valid_statuses}")

print(f"required_text_paths_checked={len(required_text_paths)}")
print("optional_failure_code_checked=true")
print("delivery_attempt_text_paths_checked=5")
print(f"linked_counterexample_status={linked_result.status.value}")
print(f"blank_counterexample_status={blank_result.status.value}")
print(f"valid_fixture_statuses={valid_statuses}")
print(f"failure_count={len(failures)}")
for item in failures:
    print(f"FAILURE={item}")

if failures:
    raise SystemExit(1)
print("RESULT=PASS")
