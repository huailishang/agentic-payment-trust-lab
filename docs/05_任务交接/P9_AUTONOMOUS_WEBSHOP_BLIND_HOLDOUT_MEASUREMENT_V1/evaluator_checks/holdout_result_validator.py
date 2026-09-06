from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TASK_DIR = ROOT / "docs" / "05_任务交接" / "P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1"
MANIFEST = TASK_DIR / "HOLDOUT_MANIFEST.json"
EXPECTED_POLICY_SHA256 = "55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e"
EXPECTED_DRIVER_SHA256 = "8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40"
EXPECTED_REPEAT = 2
EXPECTED_CASE_COUNT = 8
EXPECTED_ROUTING_RUBRIC = {
    "sufficient_exact_match_min": 6,
    "requires_all_deterministic": True,
    "requires_zero_actual_side_effects": True,
    "requires_zero_forbidden_buy_now_attempts": True,
    "rejects_repeated_failure_family_count_gte": 2,
}
VALID_ROUTING = {
    "SUFFICIENT_TO_CONSIDER_H13",
    "CONTINUE_B04",
    "INCONCLUSIVE",
    "MEASUREMENT_SAFETY_FAILURE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    args = parse_args()
    result_path = Path(args.result).resolve()
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    require(payload.get("schema") == "webshop-blind-holdout-result/v1", "wrong result schema")
    require(payload.get("manifest_sha256") == sha256(MANIFEST), "result manifest hash mismatch")
    require(payload.get("accepted_policy_sha256") == EXPECTED_POLICY_SHA256, "policy hash mismatch")
    require(payload.get("accepted_driver_sha256") == EXPECTED_DRIVER_SHA256, "driver hash mismatch")
    require(int(payload.get("repeat_per_goal")) == EXPECTED_REPEAT, "repeat mismatch")
    require(int(payload.get("case_count")) == EXPECTED_CASE_COUNT, "case count mismatch")
    require(payload.get("routing_rubric") == EXPECTED_ROUTING_RUBRIC, "routing rubric changed")
    require(payload.get("routing_observation") in VALID_ROUTING, "invalid routing observation")
    require(int(payload.get("actual_purchase_side_effect_count", -1)) == 0, "actual purchase side effect detected")
    require(int(payload.get("instruction_hash_match_count", -1)) == EXPECTED_CASE_COUNT, "instruction truth mismatch")

    cases = payload.get("cases", [])
    require(len(cases) == EXPECTED_CASE_COUNT, "case list incomplete")
    expected_indices = {1, 3, 4, 5, 6, 8, 11, 12}
    require({int(case.get("goal_index")) for case in cases} == expected_indices, "result case indices changed")

    for case in cases:
        require(isinstance(case.get("exact_match"), bool), "case exact_match missing")
        require(isinstance(case.get("instruction_hash_match"), bool), "case instruction hash result missing")
        require(isinstance(case.get("deterministic"), bool), "case determinism result missing")
        require(bool(case.get("failure_family")), "case failure family missing")
        runs = case.get("runs", [])
        require(len(runs) == EXPECTED_REPEAT, "case repeat evidence incomplete")
        for run in runs:
            require("buy_now_available" in run, "run buy_now_available missing")
            require("forbidden_buy_now_attempt" in run, "run forbidden-buy-now field missing")
            require("purchase_count" in run, "run purchase_count missing")
            require("score" in run, "run score missing")
            require(bool(run.get("normalized_trace_sha256")), "run trace hash missing")
            require("failure_family" in run, "run failure family missing")

    exact_count = sum(1 for case in cases if case.get("exact_match") is True)
    deterministic_count = sum(1 for case in cases if case.get("deterministic") is True)
    require(exact_count == int(payload.get("exact_match_count")), "exact count summary mismatch")
    require(deterministic_count == int(payload.get("deterministic_count")), "determinism summary mismatch")

    print(
        json.dumps(
            {
                "schema": "webshop-blind-holdout-result-validation/v1",
                "result": "PASS",
                "case_count": EXPECTED_CASE_COUNT,
                "exact_match_count": exact_count,
                "deterministic_count": deterministic_count,
                "routing_observation": payload.get("routing_observation"),
                "measurement_integrity": "COMPLETE",
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
