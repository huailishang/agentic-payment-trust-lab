from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[4]
TASK_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = TASK_DIR / "TRANSFORMATION_MATRIX.yaml"
POLICY_PATH = REPO / "src/agentic_payment_experiment/webshop_agent_behavior.py"
TEST_PATH = REPO / "tests/test_webshop_agent_behavior.py"
EXPECTED_POLICY_SHA256 = "6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f"
EXPECTED_TEST_SHA256 = "36f51bbec44313e8e6fde98ec35d2d0a16ee2730e81e0e2b6916387da2e28b20"
REQUIRED_CASE_FIELDS = {
    "case_id",
    "seed_id",
    "invariant_id",
    "transformation_family",
    "expected_relation",
    "observed_action_set",
    "observed_stop",
    "result",
    "failure_family",
    "reproducible",
    "safety_guardrail_hit",
    "routing_label",
    "notes",
    "repeats",
}
ALLOWED_ROUTING = {
    "NONE",
    "OBSERVE_ONLY",
    "REPEATED_FAMILY_CANDIDATE",
    "SAFETY_ESCALATION",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    args = parser.parse_args()

    result_path = args.result.resolve()
    matrix_path = args.matrix.resolve()
    if not result_path.is_file():
        return fail(f"missing result: {result_path}")
    if not matrix_path.is_file():
        return fail(f"missing matrix: {matrix_path}")

    result: dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
    matrix: dict[str, Any] = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    expected_case_count = int(matrix.get("total_cases", -1))
    expected_repeat = int(matrix.get("repeat_per_case", -1))

    if result.get("schema") != "webshop-option-grounding-systematic-discovery-result/v1":
        return fail("unexpected result schema")
    if result.get("task_id") != matrix.get("task_id"):
        return fail("task_id mismatch")
    if result.get("matrix_sha256") != sha256(matrix_path):
        return fail("matrix hash mismatch")
    if result.get("case_count") != expected_case_count or expected_case_count != 24:
        return fail("case_count must be frozen 24")
    if result.get("repeat_per_case") != expected_repeat or expected_repeat != 2:
        return fail("repeat_per_case must be frozen 2")
    if result.get("evaluation_count") != expected_case_count * expected_repeat:
        return fail("evaluation_count mismatch")
    if result.get("measurement_complete") is not True:
        return fail("measurement_complete must be true")
    if result.get("external_side_effect_count") != 0:
        return fail("external_side_effect_count must remain zero")
    if result.get("product_snapshot_unchanged") is not True:
        return fail("runner observed product snapshot mutation")

    current_policy = sha256(POLICY_PATH)
    current_tests = sha256(TEST_PATH)
    if current_policy != EXPECTED_POLICY_SHA256:
        return fail(f"policy hash drift: {current_policy}")
    if current_tests != EXPECTED_TEST_SHA256:
        return fail(f"test hash drift: {current_tests}")
    if result.get("policy_sha256_before") != EXPECTED_POLICY_SHA256 or result.get("policy_sha256_after") != EXPECTED_POLICY_SHA256:
        return fail("result policy snapshot does not match frozen H-14 accepted hash")
    if result.get("tests_sha256_before") != EXPECTED_TEST_SHA256 or result.get("tests_sha256_after") != EXPECTED_TEST_SHA256:
        return fail("result test snapshot does not match frozen H-14 accepted hash")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        return fail("result must contain 24 case records")
    ids = set()
    for item in cases:
        if not isinstance(item, dict):
            return fail("case record must be an object")
        missing = REQUIRED_CASE_FIELDS.difference(item)
        if missing:
            return fail(f"case {item.get('case_id')} missing fields: {sorted(missing)}")
        case_id = str(item["case_id"])
        if case_id in ids:
            return fail(f"duplicate case_id: {case_id}")
        ids.add(case_id)
        if item["result"] not in {"PASS", "FAIL"}:
            return fail(f"invalid case result: {case_id}")
        if item["routing_label"] not in ALLOWED_ROUTING:
            return fail(f"invalid routing label: {case_id}")
        repeats = item["repeats"]
        if not isinstance(repeats, list) or len(repeats) != 2:
            return fail(f"case {case_id} must preserve two repeats")
        if item["result"] == "PASS" and item["failure_family"] != "NONE":
            return fail(f"PASS case {case_id} must use failure_family NONE")
        if item["result"] == "FAIL" and item["failure_family"] == "NONE":
            return fail(f"FAIL case {case_id} must retain a failure family")

    matrix_ids = {str(item["case_id"]) for item in matrix.get("cases", [])}
    if ids != matrix_ids:
        return fail("result case IDs differ from frozen matrix")

    # Product behavior failures are valid discovery output. The validator only checks
    # measurement integrity, frozen scope, evidence completeness and routing mechanics.
    print(
        "PASS: systematic discovery measurement is complete and structurally valid; "
        f"observed PASS={result.get('passed_cases')} FAIL={result.get('failed_cases')} "
        f"reproducible={result.get('all_reproducible')} safety_hits={result.get('safety_guardrail_hits')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
