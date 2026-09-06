from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.webshop_agent_behavior import (  # noqa: E402
    AgentPolicyInput,
    choose_webshop_action,
)

TASK_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = TASK_DIR / "TRANSFORMATION_MATRIX.yaml"
POLICY_PATH = REPO / "src/agentic_payment_experiment/webshop_agent_behavior.py"
TEST_PATH = REPO / "tests/test_webshop_agent_behavior.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _option_from_action(action: str | None) -> str | None:
    if action is None:
        return None
    match = re.fullmatch(r"click\[(.+)\]", str(action).strip(), re.IGNORECASE)
    return match.group(1) if match else None


def _run_once(case: dict[str, Any], base_previous: list[str]) -> dict[str, Any]:
    previous = list(base_previous) + [str(x) for x in case.get("previous_actions", [])]
    clickables = [str(x) for x in case["clickables"]]
    new_actions: list[str] = []
    new_options: list[str] = []
    decisions: list[dict[str, Any]] = []
    observed_stop = False
    safety_guardrail_hit = False

    for _ in range(int(case.get("max_steps", 1))):
        decision = choose_webshop_action(
            AgentPolicyInput(
                instruction_text=str(case["instruction"]),
                observation="synthetic systematic option-grounding discovery state",
                available_actions={"clickables": clickables, "has_search_bar": False},
                step_index=len(previous),
                previous_actions=previous,
            )
        )
        decisions.append(asdict(decision))
        observed_stop = bool(decision.stop)
        if decision.action is None:
            break

        action = str(decision.action)
        option = _option_from_action(action)
        if option is not None and option.strip().lower() == "buy now":
            safety_guardrail_hit = True
        new_actions.append(action)
        if option is not None:
            new_options.append(option)
        previous.append(action)
        if decision.stop:
            break

    return {
        "new_actions": new_actions,
        "new_option_set": sorted(set(new_options)),
        "observed_stop": observed_stop,
        "decisions": decisions,
        "safety_guardrail_hit": safety_guardrail_hit,
    }


def _expected_relation(case: dict[str, Any]) -> str:
    return "new_option_set={} ; require_stop={}".format(
        sorted(str(x) for x in case.get("expected_new_option_set", [])),
        bool(case.get("require_stop", False)),
    )


def _matches(case: dict[str, Any], observation: dict[str, Any]) -> bool:
    expected = sorted(str(x) for x in case.get("expected_new_option_set", []))
    if observation["new_option_set"] != expected:
        return False
    if bool(case.get("require_stop", False)) and not observation["observed_stop"]:
        return False
    if observation["safety_guardrail_hit"]:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    matrix_path = args.matrix.resolve()
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    cases = list(matrix.get("cases", []))
    repeat_per_case = int(matrix.get("repeat_per_case", 2))
    base_previous = [str(x) for x in matrix.get("base_previous_actions", [])]

    policy_before = sha256(POLICY_PATH)
    tests_before = sha256(TEST_PATH)
    case_results: list[dict[str, Any]] = []
    evaluation_count = 0

    for case in cases:
        repeats = []
        for _ in range(repeat_per_case):
            repeats.append(_run_once(case, base_previous))
            evaluation_count += 1

        normalized = [
            {
                "new_actions": item["new_actions"],
                "new_option_set": item["new_option_set"],
                "observed_stop": item["observed_stop"],
                "safety_guardrail_hit": item["safety_guardrail_hit"],
            }
            for item in repeats
        ]
        reproducible = all(item == normalized[0] for item in normalized[1:])
        expectation_passed = all(_matches(case, item) for item in repeats)
        result = "PASS" if reproducible and expectation_passed else "FAIL"
        failure_family = "NONE" if result == "PASS" else str(
            case.get("failure_family", "UNCLASSIFIED_MEASUREMENT_FAILURE")
        )
        safety_hit = any(bool(item["safety_guardrail_hit"]) for item in repeats)

        case_results.append(
            {
                "case_id": str(case["case_id"]),
                "seed_id": str(case["seed_id"]),
                "invariant_id": str(case["invariant_id"]),
                "transformation_family": str(case["transformation_family"]),
                "expected_relation": _expected_relation(case),
                "observed_action_set": normalized[0]["new_option_set"],
                "observed_stop": normalized[0]["observed_stop"],
                "result": result,
                "failure_family": failure_family,
                "reproducible": reproducible,
                "safety_guardrail_hit": safety_hit,
                "routing_label": "NONE",
                "notes": "" if result == "PASS" else "frozen invariant expectation not satisfied",
                "repeats": repeats,
            }
        )

    failed_by_family: dict[str, set[str]] = {}
    for item in case_results:
        if item["result"] != "FAIL" or not item["reproducible"]:
            continue
        failed_by_family.setdefault(str(item["failure_family"]), set()).add(str(item["seed_id"]))

    for item in case_results:
        if item["result"] == "PASS":
            item["routing_label"] = "NONE"
        elif item["safety_guardrail_hit"]:
            item["routing_label"] = "SAFETY_ESCALATION"
        elif item["reproducible"] and len(failed_by_family.get(str(item["failure_family"]), set())) >= 2:
            item["routing_label"] = "REPEATED_FAMILY_CANDIDATE"
        else:
            item["routing_label"] = "OBSERVE_ONLY"

    family_summary = {}
    for family, seeds in sorted(failed_by_family.items()):
        family_cases = [x for x in case_results if x["failure_family"] == family and x["result"] == "FAIL"]
        family_summary[family] = {
            "failed_cases": len(family_cases),
            "independent_seed_count": len(seeds),
            "seed_ids": sorted(seeds),
            "routing_candidate": len(seeds) >= 2,
        }

    policy_after = sha256(POLICY_PATH)
    tests_after = sha256(TEST_PATH)
    safety_hits = sum(1 for item in case_results if item["safety_guardrail_hit"])
    payload = {
        "schema": "webshop-option-grounding-systematic-discovery-result/v1",
        "task_id": str(matrix["task_id"]),
        "matrix_sha256": sha256(matrix_path),
        "policy_sha256_before": policy_before,
        "policy_sha256_after": policy_after,
        "tests_sha256_before": tests_before,
        "tests_sha256_after": tests_after,
        "product_snapshot_unchanged": policy_before == policy_after and tests_before == tests_after,
        "case_count": len(case_results),
        "repeat_per_case": repeat_per_case,
        "evaluation_count": evaluation_count,
        "measurement_complete": len(case_results) == int(matrix.get("total_cases", -1)),
        "passed_cases": sum(1 for item in case_results if item["result"] == "PASS"),
        "failed_cases": sum(1 for item in case_results if item["result"] == "FAIL"),
        "all_reproducible": all(bool(item["reproducible"]) for item in case_results),
        "safety_guardrail_hits": safety_hits,
        "external_side_effect_count": 0,
        "family_summary": family_summary,
        "cases": case_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    preserved_existing_result = False
    if args.output.exists():
        existing = args.output.read_text(encoding="utf-8")
        if existing != rendered:
            mismatch = args.output.with_suffix(args.output.suffix + ".rerun-mismatch")
            mismatch.write_text(rendered, encoding="utf-8")
            print(f"ERROR: rerun result differs from preserved canonical result; wrote {mismatch}")
            return 3
        preserved_existing_result = True
    else:
        args.output.write_text(rendered, encoding="utf-8")

    summary = {
        "measurement_complete": payload["measurement_complete"],
        "case_count": payload["case_count"],
        "evaluation_count": payload["evaluation_count"],
        "passed_cases": payload["passed_cases"],
        "failed_cases": payload["failed_cases"],
        "all_reproducible": payload["all_reproducible"],
        "safety_guardrail_hits": payload["safety_guardrail_hits"],
        "family_summary": family_summary,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Discovery failures are observations, not execution failures. Non-zero is reserved
    # for an incomplete/invalid measurement envelope or unexpected product mutation.
    if not payload["measurement_complete"] or not payload["product_snapshot_unchanged"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
