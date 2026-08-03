from __future__ import annotations

import json
from pathlib import Path

matrix_path = Path(
    "docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/"
    "evidence/EV-02.runtime_mismatch_matrix.json"
)
matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
by_case = {item["case"]: item for item in matrix["cases"]}
findings: list[dict[str, object]] = []
for case_name in ("p4_stale_wrong_action", "p4_value_digest_mismatch"):
    item = by_case[case_name]
    assert item["decision"] == "INDETERMINATE"
    assert item["callback_count"] == 0
    assert item["checkout_executed"] is False
    diagnostic_codes = [
        code
        for code in item["reason_codes"]
        if "mismatch" in code
        or "stale" in code
        or "wrong_action" in code
        or "coverage" in code
        or "digest" in code
    ]
    findings.append(
        {
            "case": case_name,
            "decision": item["decision"],
            "callback_count": item["callback_count"],
            "context_policy_status": item["context_policy_status"],
            "context_policy_reason_codes": item["context_policy_reason_codes"],
            "outcome_reason_codes": item["reason_codes"],
            "causal_diagnostic_codes": diagnostic_codes,
            "causal_reason_exposed": bool(diagnostic_codes),
        }
    )

assert all(item["causal_reason_exposed"] is False for item in findings)
print(
    json.dumps(
        {
            "finding": "P4 runtime contract mismatch blocks safely but exposes no causal reason",
            "cases": findings,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
