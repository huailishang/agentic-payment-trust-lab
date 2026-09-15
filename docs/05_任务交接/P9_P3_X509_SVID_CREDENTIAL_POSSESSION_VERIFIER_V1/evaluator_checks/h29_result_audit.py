from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED = {
    "V01_VALID_BOUND_TO_VERIFIED": ("VALID", "VALID", "VERIFIED", "credential_possession_verified"),
    "N01_WRONG_TRUST_BUNDLE": ("INVALID", "VALID", "BOUND", "credential_trust_invalid"),
    "N02_WRONG_SPIFFE_SUBJECT": ("INVALID", "VALID", "BOUND", "credential_subject_binding_mismatch"),
    "N03_NO_POSSESSION_PROOF": ("MISSING_EVIDENCE", "VALID", "BOUND", "credential_possession_proof_missing"),
    "N04_BAD_POSSESSION_PROOF": ("INVALID", "VALID", "BOUND", "credential_possession_signature_invalid"),
    "N05_REPLAYED_NONCE": ("INVALID", "VALID", "BOUND", "credential_possession_replay_detected"),
    "N06_STALE_CHALLENGE": ("INVALID", "VALID", "BOUND", "credential_possession_challenge_stale"),
}


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: h29_result_audit.py RESULT.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if data.get("schema") != "p3-x509-svid-credential-possession-capability/v1":
        raise AssertionError(f"unexpected schema: {data.get('schema')!r}")

    cases = {item["case_id"]: item for item in data.get("cases", [])}
    if set(cases) != set(EXPECTED):
        raise AssertionError(f"unexpected case ids: {sorted(cases)}")

    verified = 0
    for case_id, (credential_status, identity_status, assurance, reason) in EXPECTED.items():
        item = cases[case_id]
        if item.get("credential_status") != credential_status:
            raise AssertionError(f"{case_id}: credential_status {item.get('credential_status')} != {credential_status}")
        if item.get("identity_status") != identity_status:
            raise AssertionError(f"{case_id}: identity_status {item.get('identity_status')} != {identity_status}")
        if item.get("assurance_level") != assurance:
            raise AssertionError(f"{case_id}: assurance {item.get('assurance_level')} != {assurance}")
        if reason not in item.get("reason_codes", []):
            raise AssertionError(f"{case_id}: missing reason {reason}")
        if assurance == "VERIFIED":
            verified += 1
            flags = item.get("four_condition_flags", {})
            if flags != {
                "credential_valid": True,
                "subject_binding_valid": True,
                "proof_of_possession_valid": True,
                "freshness_valid": True,
                "replay_detected": False,
            }:
                raise AssertionError(f"{case_id}: invalid four-condition flags: {flags!r}")

    if verified != 1:
        raise AssertionError(f"expected exactly one VERIFIED case, got {verified}")
    if data.get("verified_cases_before") != 0 or data.get("verified_cases_after") != 1:
        raise AssertionError("missing 0→1 VERIFIED project movement")
    if data.get("legacy_credential_ref_only_assurance") != "BOUND":
        raise AssertionError("legacy credential_ref-only path no longer BOUND")

    guard = data.get("guardrails", {})
    for key in ("network_calls", "real_payment", "production_credentials", "persisted_private_keys"):
        if guard.get(key) != 0:
            raise AssertionError(f"guardrail {key} must be 0, got {guard.get(key)!r}")

    residual = " ".join(data.get("residual_risks", [])).lower()
    required_terms = ("bounded", "synthetic", "not full", "production")
    if not all(term in residual for term in required_terms):
        raise AssertionError("residual-risk text must state bounded/synthetic/not-full/production limitations")

    print("PASS: H-29 result matches seven credential outcomes; base identity stays VALID/BOUND on failed optional stronger evidence; exactly one VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
