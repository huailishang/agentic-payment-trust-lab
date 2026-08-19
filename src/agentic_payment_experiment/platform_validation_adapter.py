"""Map payment-domain validation judgments to Platform validation-result-v0.1.

The adapter does not re-run payment policy. It only translates the native
ValidationResult into the stable cross-repository result envelope.
"""
from __future__ import annotations

from typing import Any

from .models import Decision, ValidationResult


PLATFORM_VALIDATION_SCHEMA_VERSION = "validation-result-v0.1"
VALIDATOR_ID = "payment.validator"


def adapt_validation_result_to_platform(result: ValidationResult) -> dict[str, Any]:
    """Translate one native payment ValidationResult without changing its meaning."""

    verdict = {
        Decision.ALLOW: "PASS",
        Decision.DENY: "FAIL",
        Decision.CONFIRMATION_REQUIRED: "BLOCKED",
        Decision.INDETERMINATE: "INDETERMINATE",
    }[result.decision]

    evidence_by_code: dict[str, list[dict[str, str | None]]] = {}
    top_level_refs: list[dict[str, str | None]] = []
    seen_refs: set[tuple[str, str, str | None]] = set()

    for item in result.evidence:
        ref = {
            "ref_type": "payment_validation",
            "ref": item.field_path,
            "locator": item.code,
        }
        evidence_by_code.setdefault(item.code, []).append(ref)
        key = (str(ref["ref_type"]), str(ref["ref"]), ref.get("locator"))
        if key not in seen_refs:
            seen_refs.add(key)
            top_level_refs.append(ref)

    findings = [
        {
            "code": issue.code,
            "message": issue.message,
            "severity": None,
            "evidence_refs": evidence_by_code.get(issue.code, []),
        }
        for issue in result.issues
    ]

    return {
        "schema_version": PLATFORM_VALIDATION_SCHEMA_VERSION,
        "verdict": verdict,
        "validator_id": VALIDATOR_ID,
        "validator_version": result.rule_version,
        "findings": findings,
        "evidence_refs": top_level_refs,
        "limitations": list(result.limitations),
    }
