from __future__ import annotations

import json
import sys
from pathlib import Path

CASES = (
    "R01_FULL_REFUND",
    "R02_PARTIAL_REFUND",
    "R03_DISPUTE_OPEN",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH",
)
ORDER = (
    "AUTHORITATIVE_TRACE_VALID",
    "CONSUMER_ACCEPTED",
    "READ_MODEL_EVENT_PARITY",
    "SOURCE_BINDING_PARITY",
    "REMEDIATION_ROLES_VISIBLE",
    "BINDING_STATUS_EXPECTATION_VISIBLE",
    "CLOSURE_STATE_VISIBLE",
    "ACTION_ORIGIN_PROJECTABLE",
    "PLAYER_PAYLOAD_ACCEPTED",
    "PLAYER_RENDER_DETERMINISTIC",
)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    require(len(sys.argv) == 2, "usage: h23_result_audit.py <result.json>")
    path = Path(sys.argv[1])
    require(path.is_file(), f"missing result: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema") == "remediation-accountability-consumption-measurement/v1", "wrong schema")
    require(data.get("repeat_per_case") == 2, "repeat_per_case must be 2")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 5, "expected five cases")
    require(tuple(item.get("case_id") for item in cases) == CASES, "case order/identity changed")

    for item in cases:
        cid = item["case_id"]
        require(item.get("measurement_complete") is True, f"{cid}: incomplete")
        require(item.get("repeat_identical") is True, f"{cid}: non-deterministic")
        digests = item.get("run_digests")
        require(isinstance(digests, list) and len(digests) == 2 and digests[0] == digests[1], f"{cid}: bad repeat digests")
        continuity = item.get("continuity")
        require(isinstance(continuity, dict) and tuple(continuity.keys()) == ORDER, f"{cid}: continuity order changed")
        recomputed_pass = all(bool(continuity[name]) for name in ORDER)
        recomputed_first = next((name for name in ORDER if not bool(continuity[name])), None)
        require(item.get("continuity_pass") is recomputed_pass, f"{cid}: continuity_pass not mechanical")
        require(item.get("first_breakpoint") == recomputed_first, f"{cid}: first_breakpoint not mechanical")
        require(isinstance(item.get("consumer"), dict), f"{cid}: consumer observation missing")
        require(isinstance(item.get("player"), dict), f"{cid}: player observation missing")
        require(isinstance(item.get("action_origin"), dict), f"{cid}: action-origin observation missing")
        require(isinstance(item.get("closure"), dict), f"{cid}: closure observation missing")

    r05 = cases[-1]
    neg = r05.get("negative_control") or {}
    require(neg.get("binding_status") == "INVALID", "R05 must remain INVALID")
    require("original_transaction_payment_ref_mismatch" in (neg.get("reason_codes") or []), "R05 mismatch reason missing")
    require(neg.get("false_original_payment_relation_absent") is True, "R05 false payment relation appeared")
    require(neg.get("normalized_to_valid") is False, "R05 was normalized to VALID")

    summary = data.get("summary") or {}
    require(summary.get("cases_measured") == 5 and summary.get("cases_total") == 5, "summary must measure 5/5")
    distribution = summary.get("first_breakpoint_distribution")
    require(isinstance(distribution, dict), "first-breakpoint distribution missing")
    guardrails = data.get("guardrails") or {}
    for key in ("real_payment_execution_count", "real_refund_execution_count", "real_dispute_execution_count", "external_network_calls"):
        require(guardrails.get(key) == 0, f"guardrail violated: {key}")

    print("PASS: H-23 five-branch consumption measurement is complete, deterministic, mechanically auditable, and preserves the R05 negative control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
