"""H46 executor-only offline measurement. The frozen oracle injects the real source tool."""
from __future__ import annotations


def run_probe(*, cases, repeats, new_account, send_money, evaluate, missing_binding_probe) -> dict:
    """Record actual state transitions; never prefill task outcomes or derive authority from Gold."""
    records = []
    for repeat in range(repeats):
        for case in cases:
            account = new_account(case["id"], repeat)
            before = account.model_dump()
            count = 0
            for action in case["actions"]:
                send_money(account, **action)
                count += 1
            after = account.model_dump()
            scores = evaluate(account)
            records.append({
                "case": case["id"],
                "repeat": repeat,
                "before": before,
                "after": after,
                "utility": bool(scores["utility"]),
                "attack_success": bool(scores["attack_success"]),
                "forbidden_added": bool(scores["forbidden_added"]),
                "tool_call_count": count,
            })
    # These are separate deliberately incomplete product-input diagnostics, not full gate comparisons.
    applicability = [missing_binding_probe(), missing_binding_probe()]
    return {"records": records, "applicability": applicability}
