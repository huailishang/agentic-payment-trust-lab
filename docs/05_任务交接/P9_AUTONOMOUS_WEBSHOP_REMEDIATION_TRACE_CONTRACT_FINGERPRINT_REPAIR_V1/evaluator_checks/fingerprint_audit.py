from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
    ROOT / "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    ROOT / "src/agentic_payment_experiment/trusted_execution/original_transaction.py": "482b7aa23e07f7724b909ab289928e61f9227f2544611b886e028047d4e9e5d9",
    ROOT / "src/agentic_payment_experiment/webshop_remediation_trace.py": "961f6042bc48afc160b3373bd2b439da30127f32de44fa3937cc00d1dc3460ad",
    ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py": "c98c3a1477ebf64a5696707c0d637da60d8563ef174b06a100c9d9b7bebc1656",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "b43cf1338e7397107aae83a1fca78752b55cd15c900f0160d64a6983707fcada",
    ROOT / "scripts/validation/webshop/run_same_journey_remediation_trace_closure.py": "a90f0923ee6fdbb1c9b8d0cee76390f04d2786a8350bd8c09fafa7e62061d1fc",
    ROOT / "tests/test_webshop_remediation_trace.py": "360acb53475645d76555d23c32ce0e937159800e096d0fd3fc7541362d35a6be",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_EVIDENCE_CLOSURE_V1/evidence/H22_REMEDIATION_TRACE_RESULT.json": "ba1d4e562bef9ae975c81049b0c24399513cf62f6f8d1c7bb6ece4f2b4e09891",
}

BASE_PROJECTION_HASH = "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4"
BASE_RUNTIME_HASH = "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e"
H22_PROJECTIONS = {
    "refund-record-remediation-trace/v1",
    "dispute-record-remediation-trace/v1",
    "original-transaction-binding-fact-remediation-trace/v1",
    "lifecycle-remediation-closure-trace/v1",
}
H22_PROFILES = {
    "WEBSHOP_POST_PAYMENT_REFUND_REMEDIATION_V1",
    "WEBSHOP_POST_PAYMENT_DISPUTE_REMEDIATION_V1",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        require(sha256(path) == expected, f"protected H-22 file changed: {path}")

    import agentic_payment_experiment.authoritative_trace as at

    require(hasattr(at, "accepted_base_runtime_contract_primitive"), "missing accepted_base_runtime_contract_primitive")
    require(hasattr(at, "accepted_base_registry_hashes"), "missing accepted_base_registry_hashes")

    base_contract = at.accepted_base_runtime_contract_primitive()
    base_hashes = dict(at.accepted_base_registry_hashes())
    require(at.canonical_sha256(base_contract) == BASE_RUNTIME_HASH, "historical base runtime contract drifted")
    require(base_hashes.get("projection_registry") == BASE_PROJECTION_HASH, "historical base projection hash drifted")
    require(base_hashes.get("runtime_contract") == BASE_RUNTIME_HASH, "historical base runtime hash drifted")

    effective = at.runtime_contract_primitive()
    effective_again = at.runtime_contract_primitive()
    require(at.canonical_sha256(effective) == at.canonical_sha256(effective_again), "effective runtime export is nondeterministic")

    exported_projection = effective.get("projection_registry")
    require(isinstance(exported_projection, dict), "effective projection registry missing")
    require(
        at.canonical_sha256(exported_projection) == at.canonical_sha256(at.PROJECTION_REGISTRY),
        "effective projection export differs from live PROJECTION_REGISTRY",
    )
    require(set(exported_projection) == set(at.PROJECTION_REGISTRY), "effective projection key set differs from live registry")
    require(H22_PROJECTIONS <= set(exported_projection), "H-22 projection schemas missing from effective export")

    tasks = effective.get("tasks")
    require(isinstance(tasks, list), "effective tasks/profiles export must be a list")
    exported_profiles = {str(item["profile"]) for item in tasks}
    require(exported_profiles == set(at.PROFILE_REGISTRY), "effective profile set differs from live PROFILE_REGISTRY")
    require(H22_PROFILES <= exported_profiles, "H-22 remediation profiles missing from effective export")

    reported = dict(at.runtime_registry_hashes())
    expected_projection_hash = at.canonical_sha256(at.PROJECTION_REGISTRY)
    expected_profile_hash = at.canonical_sha256(tasks)
    expected_runtime_hash = at.canonical_sha256(effective)
    require(reported.get("projection_registry") == expected_projection_hash, "public projection fingerprint does not commit to live registry")
    require(reported.get("profiles") == expected_profile_hash, "public profile fingerprint does not commit to effective profiles")
    require(reported.get("runtime_contract") == expected_runtime_hash, "public runtime fingerprint does not commit to effective contract")
    require(reported.get("projection_registry") != BASE_PROJECTION_HASH, "public runtime projection fingerprint is still the historical base hash")

    print(
        "PASS: public runtime contract/hash now commits to the effective live projection/profile registries; "
        "H-22 extensions are exported; historical accepted-base identity remains explicit and unchanged"
    )
    print(f"effective_projection_hash={expected_projection_hash}")
    print(f"effective_profiles_hash={expected_profile_hash}")
    print(f"effective_runtime_contract_hash={expected_runtime_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
