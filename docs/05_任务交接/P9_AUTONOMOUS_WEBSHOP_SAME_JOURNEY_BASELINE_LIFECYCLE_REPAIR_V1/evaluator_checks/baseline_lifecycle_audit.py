from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIFECYCLE = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_baseline/BASELINE_LIFECYCLE.json"
OLD = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json"
NEW = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_baseline/CURRENT_POLICY_AUTONOMOUS_BEHAVIOR.json"
POLICY = ROOT / "src/agentic_payment_experiment/webshop_agent_behavior.py"
DRIVER = ROOT / "scripts/validation/webshop/run_autonomous_prebuy_behavior.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    meta = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = json.loads(NEW.read_text(encoding="utf-8"))
    hist = meta["historical"]
    cur = meta["current"]
    rules = meta["measurement_rule"]

    require(meta["schema"] == "same-journey-baseline-lifecycle/v1", "schema mismatch")
    require(sha256(OLD) == hist["accepted_behavior_sha256"], "historical accepted behavior changed")
    require(sha256(NEW) == cur["baseline_sha256"], "current baseline changed")
    require(sha256(POLICY) == cur["policy_sha256"], "current policy changed")
    require(sha256(DRIVER) == cur["driver_sha256"], "autonomous driver changed")
    require(hist["policy_sha256"] != cur["policy_sha256"], "historical/current policy versions must differ")

    old_trace = old["runs"][0]["normalized_trace_sha256"]
    new_trace = new["runs"][0]["normalized_trace_sha256"]
    require(old_trace == hist["trace_sha256"], "historical trace mismatch")
    require(new_trace == cur["trace_sha256"], "current trace mismatch")
    require(old_trace != new_trace, "cross-policy trace unexpectedly byte-identical")

    require(new["repeat"] == 3 and new["repeat_identical"] is True, "fresh baseline is not repeat-deterministic")
    require(len({run["normalized_trace_sha256"] for run in new["runs"]}) == 1, "fresh baseline run hashes differ")
    require(new["checkout_head"] == cur["checkout_head"], "checkout head mismatch")
    require(new["goal_index"] == cur["goal_index"], "goal mismatch")
    require(new["seed"] == cur["seed"], "seed mismatch")
    require(new["payment_order_network_side_effect_count"] == 0, "fresh baseline has forbidden side effect")
    require(all(run["buy_now_executed"] is False for run in new["runs"]), "fresh baseline executed Buy Now")
    require(all(run["purchase_count"] == 0 for run in new["runs"]), "fresh baseline has purchase side effect")

    old_score = old["score"]
    new_score = new["score"]
    for key in ("selected_asin", "selected_option_values", "selected_price", "target_match", "required_option_match", "price_match"):
        require(old_score[key] == new_score[key], f"historical behavior regression mismatch: {key}")

    require(rules["historical_trace_must_equal_current_trace"] is False, "historical trace must not gate current policy")
    require(rules["historical_final_behavior_must_regress"] is True, "historical behavior regression must remain")
    require(rules["current_policy_trace_must_repeat_identically"] is True, "current trace determinism must remain")
    require(rules["same_journey_correlation_uses_current_baseline"] is True, "same-journey must use current baseline")

    print("PASS: baseline lifecycle separated correctly; historical behavior regresses, current-policy trace is deterministic, cross-policy byte identity is not required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
