from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

PROBES = (
    "P01_P3_BOUND_NO_CREDENTIAL",
    "P02_P3_EXPECTED_CREDENTIAL_CURRENT_MISSING",
    "P03_P3_MATCHING_CREDENTIAL_REF_ONLY",
    "P04_AP2_HP_USER_AUTH_SIGNATURE_UNVERIFIED",
    "P05_AP2_HNP_INTENT_AUTH_SIGNATURE_UNVERIFIED",
    "P06_ACP_WEBHOOK_PAYEE_AUTHENTICITY_UNVERIFIED",
)
SURFACES = {
    "P3_IDENTITY_GATE",
    "AP2_HUMAN_PRESENT",
    "AP2_HUMAN_NOT_PRESENT",
    "ACP_CHECKOUT",
}
NOT_VERIFIED_CODES = {
    "ap2_user_authorization_signature_not_verified",
    "ap2_intent_authorization_signature_not_verified",
    "seller_identity_from_endpoint_context_not_verified",
    "payee_identity_not_verified",
    "order_webhook_signature_not_verified",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def subset_equal(expected: object, observed: object) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(observed, Mapping):
            return False
        return all(key in observed and subset_equal(value, observed[key]) for key, value in expected.items())
    if isinstance(expected, list):
        if not isinstance(observed, list):
            return False
        return all(item in observed for item in expected)
    return expected == observed


def main() -> int:
    require(len(sys.argv) == 3, "usage: h24_result_audit.py <result.json> <matrix.json>")
    result_path = Path(sys.argv[1])
    matrix_path = Path(sys.argv[2])
    require(result_path.is_file(), f"missing result: {result_path}")
    require(matrix_path.is_file(), f"missing matrix: {matrix_path}")

    data = json.loads(result_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    require(
        data.get("schema") == "actor-authenticity-signed-instruction-gap-measurement/v1",
        "wrong result schema",
    )
    require(data.get("repeat_per_probe") == 2, "repeat_per_probe must be 2")

    matrix_probes = matrix.get("probes")
    require(isinstance(matrix_probes, list) and len(matrix_probes) == 6, "matrix must contain six probes")
    expected_by_id = {item["probe_id"]: item for item in matrix_probes}
    require(tuple(expected_by_id) == PROBES, "matrix probe order/identity changed")

    probes = data.get("probes")
    require(isinstance(probes, list) and len(probes) == 6, "result must contain six probes")
    require(tuple(item.get("probe_id") for item in probes) == PROBES, "result probe order/identity changed")

    observed_surfaces: set[str] = set()
    product_codes: set[str] = set()
    verified_probe_ids: list[str] = []
    explicit_not_verified_ids: list[str] = []

    for item in probes:
        probe_id = item["probe_id"]
        expected_item = expected_by_id[probe_id]
        require(item.get("surface") == expected_item["surface"], f"{probe_id}: surface changed")
        observed_surfaces.add(str(item["surface"]))
        require(item.get("measurement_complete") is True, f"{probe_id}: incomplete")
        require(item.get("repeat_identical") is True, f"{probe_id}: non-deterministic")
        digests = item.get("run_digests")
        require(
            isinstance(digests, list) and len(digests) == 2 and digests[0] == digests[1],
            f"{probe_id}: repeat digests invalid",
        )
        observation = item.get("product_observation")
        diagnostics = item.get("measurement_diagnostics")
        require(isinstance(observation, dict), f"{probe_id}: product_observation missing")
        require(isinstance(diagnostics, dict), f"{probe_id}: measurement_diagnostics missing")
        require(
            item.get("expected_observation") == expected_item["expected"],
            f"{probe_id}: expected_observation differs from frozen matrix",
        )
        recomputed_match = subset_equal(expected_item["expected"], observation)
        require(
            item.get("expectation_match") is recomputed_match,
            f"{probe_id}: expectation_match is not mechanically recomputable",
        )

        reason_codes = observation.get("reason_codes") or []
        limitation_codes = observation.get("limitation_codes") or []
        require(isinstance(reason_codes, list), f"{probe_id}: reason_codes must be a list")
        require(isinstance(limitation_codes, list), f"{probe_id}: limitation_codes must be a list")
        product_codes.update(str(code) for code in reason_codes + limitation_codes)

        verified = bool(observation.get("verified_authenticity_observed", False))
        if observation.get("assurance_level") == "VERIFIED":
            verified = True
        if observation.get("cryptographic_signature_verified") is True:
            verified = True
        if verified:
            verified_probe_ids.append(probe_id)

        if any(str(code) in NOT_VERIFIED_CODES for code in limitation_codes):
            explicit_not_verified_ids.append(probe_id)

        # Measurement taxonomy may classify product observations, but it must not
        # claim a stronger verified state than the product output itself.
        require(
            diagnostics.get("verified_authenticity_inferred") not in {True, "true", "VERIFIED"},
            f"{probe_id}: diagnostics fabricated VERIFIED authenticity",
        )

    require(observed_surfaces == SURFACES, f"surface set mismatch: {sorted(observed_surfaces)}")

    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("probes_measured") == 6 and summary.get("probes_total") == 6, "summary must report 6/6")
    require(summary.get("surface_count_measured") == 4, "summary must report four measured surfaces")
    require(
        summary.get("probes_with_verified_authenticity") == verified_probe_ids,
        "verified-authenticity probe list not mechanically derived",
    )
    require(
        summary.get("probes_with_explicit_not_verified_boundary") == explicit_not_verified_ids,
        "explicit-not-verified probe list not mechanically derived",
    )
    require(
        set(summary.get("unique_limitation_reason_codes") or []) == product_codes,
        "unique product code ledger not mechanically derived",
    )

    families = summary.get("candidate_mechanism_families")
    require(isinstance(families, dict), "candidate_mechanism_families missing")
    for family, members in families.items():
        require(isinstance(family, str) and family, "mechanism family name invalid")
        require(isinstance(members, list) and members, f"{family}: member list missing")
        require(set(members) <= set(PROBES), f"{family}: unknown probe member")

    repeated = False
    for members in families.values():
        member_surfaces = {
            expected_by_id[probe_id]["surface"]
            for probe_id in members
            if probe_id in expected_by_id
        }
        if len(member_surfaces) >= 2:
            repeated = True
            break
    require(
        summary.get("cross_surface_repeated_mechanism") is repeated,
        "cross_surface_repeated_mechanism is not mechanically derived",
    )

    guardrails = data.get("guardrails")
    require(isinstance(guardrails, dict), "guardrails missing")
    for key in (
        "external_network_calls",
        "real_payment_execution_count",
        "real_credential_use_count",
        "real_key_use_count",
        "real_signature_operation_count",
    ):
        require(guardrails.get(key) == 0, f"guardrail violated: {key}")

    print(
        "PASS: H-24 six-probe authenticity measurement is complete, deterministic, "
        "product/diagnostic facts stay separated, and cross-surface grouping is mechanically auditable"
    )
    print(f"verified_probe_ids={verified_probe_ids}")
    print(f"explicit_not_verified_probe_ids={explicit_not_verified_ids}")
    print(f"cross_surface_repeated_mechanism={repeated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
