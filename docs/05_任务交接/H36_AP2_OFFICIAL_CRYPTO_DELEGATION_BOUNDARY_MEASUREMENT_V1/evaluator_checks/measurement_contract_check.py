from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
EVIDENCE = TASK / "evidence"
MATRIX = EVIDENCE / "H36_OFFICIAL_BOUNDARY_MATRIX.json"
DEPS = EVIDENCE / "H36_MINIMUM_DEPENDENCIES.json"
REPORT = TASK / "REPORT.md"

EXPECTED_SURFACES = [
    "mandate_facade_verify",
    "sdjwt_chain_verify",
    "root_issuer_signature",
    "key_provider_and_cnf_delegation",
    "kb_aud_nonce_holder_proof",
    "checkout_chain_semantics",
    "payment_chain_semantics",
    "receipt_verification",
    "local_generic_es256_reuse",
    "first_executable_slice",
]
STATUSES = {"OBSERVED", "PARTIAL", "NOT_PRESENT", "BLOCKED_BY_DEPENDENCY"}
REUSE = {
    "REUSE_DIRECT",
    "REUSE_PRIMITIVE_ONLY",
    "AP2_SPECIFIC_GLUE_REQUIRED",
    "NOT_COMPARABLE",
}
DECISIONS = {
    "BOUNDED_REUSE_SLICE",
    "AP2_SPECIFIC_CRYPTO_ADAPTER",
    "DEPENDENCY_BLOCKED",
    "NO_JUSTIFIED_NEXT_SLICE",
}
REQUIRED_PACKAGES = {"pydantic", "jwcrypto", "cryptography"}


def fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def load(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    try:
        matrix = load(MATRIX)
        deps = load(DEPS)
    except Exception as exc:
        return fail(f"missing/invalid H36 evidence: {exc}")

    rows = matrix.get("surfaces") if isinstance(matrix, dict) else None
    if not isinstance(rows, list):
        return fail("matrix.surfaces must be a list")
    names = [row.get("surface") for row in rows if isinstance(row, dict)]
    if names != EXPECTED_SURFACES:
        return fail(f"surfaces must exactly match frozen order: {EXPECTED_SURFACES}; got {names}")

    for row in rows:
        if row.get("status") not in STATUSES:
            return fail(f"invalid status for {row.get('surface')}: {row.get('status')}")
        if row.get("reuse_classification") not in REUSE:
            return fail(f"invalid reuse classification for {row.get('surface')}")
        official = row.get("official_evidence")
        if not isinstance(official, list) or not official:
            return fail(f"official_evidence required for {row.get('surface')}")
        for item in official:
            if not isinstance(item, dict) or not all(item.get(k) for k in ("path", "symbol", "fact")):
                return fail(f"incomplete official evidence for {row.get('surface')}")
        if not isinstance(row.get("implementation_needed"), bool):
            return fail(f"implementation_needed must be bool for {row.get('surface')}")
        if not str(row.get("first_executable_boundary", "")).strip():
            return fail(f"first_executable_boundary required for {row.get('surface')}")

    dep_rows = deps.get("dependencies") if isinstance(deps, dict) else None
    if not isinstance(dep_rows, list) or not dep_rows:
        return fail("dependencies list required")
    package_names = {str(x.get("package", "")).lower() for x in dep_rows if isinstance(x, dict)}
    missing = REQUIRED_PACKAGES - package_names
    if missing:
        return fail(f"required dependency rows missing: {sorted(missing)}")
    if not any(name in package_names for name in {"sd-jwt", "sd_jwt", "py-sd-jwt"}):
        return fail("sd-jwt dependency row missing")

    for row in dep_rows:
        if not isinstance(row, dict):
            return fail("dependency row must be object")
        for key in (
            "package",
            "required_for_surface",
            "source_evidence",
            "already_present",
            "install_required_for_next_experiment",
            "pin_source",
            "notes",
        ):
            if key not in row:
                return fail(f"dependency field missing: {key}")

    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    status_line = next(
        (line.strip() for line in text.splitlines() if line.startswith("Executor status:")),
        "",
    )
    if status_line != "Executor status: `SUBMITTED_FOR_REVIEW`":
        return fail(f"REPORT status must be SUBMITTED_FOR_REVIEW; got {status_line!r}")

    class_line = next(
        (line.strip() for line in text.splitlines() if line.startswith("Overall classification:")),
        "",
    )
    chosen = class_line.replace("Overall classification:", "").strip().strip("`")
    if chosen not in DECISIONS:
        return fail(f"REPORT final classification invalid: {chosen!r}")

    forbidden_claims = [
        "完整 AP2 conformance 已验证",
        "real payment 已验证",
        "Sandbox 已验证",
    ]
    for phrase in forbidden_claims:
        if phrase in text:
            return fail(f"forbidden overclaim in REPORT: {phrase}")

    print("OK")
    print(f"surfaces={len(rows)}")
    print(f"dependencies={len(dep_rows)}")
    print(f"classification={chosen}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
