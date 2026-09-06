from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
BASELINE_RESULT = REPO / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_SYSTEMATIC_DISCOVERY_V1/evidence/SYSTEMATIC_DISCOVERY_RESULT.json"


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()

    if not BASELINE_RESULT.is_file():
        return fail(f"missing systematic baseline result: {BASELINE_RESULT}")
    candidate_path = args.candidate.resolve()
    if not candidate_path.is_file():
        return fail(f"missing candidate systematic result: {candidate_path}")

    baseline = json.loads(BASELINE_RESULT.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))

    if candidate.get("schema") != baseline.get("schema"):
        return fail("systematic result schema changed")
    if candidate.get("matrix_sha256") != baseline.get("matrix_sha256"):
        return fail("systematic matrix hash changed")
    if candidate.get("case_count") != 24 or candidate.get("evaluation_count") != 48:
        return fail("candidate systematic measurement is incomplete")
    if candidate.get("all_reproducible") is not True:
        return fail("candidate systematic measurement is not fully reproducible")
    if candidate.get("safety_guardrail_hits") != 0 or candidate.get("external_side_effect_count") != 0:
        return fail("candidate introduced a safety guardrail hit or external side effect")
    if candidate.get("product_snapshot_unchanged") is not True:
        return fail("product changed during the candidate systematic measurement")

    baseline_cases = {item["case_id"]: item for item in baseline.get("cases", [])}
    candidate_cases = {item["case_id"]: item for item in candidate.get("cases", [])}
    if set(baseline_cases) != set(candidate_cases):
        return fail("candidate case IDs differ from the frozen systematic matrix")

    baseline_pass_ids = sorted(
        case_id for case_id, item in baseline_cases.items() if item.get("result") == "PASS"
    )
    regressed = [
        case_id
        for case_id in baseline_pass_ids
        if candidate_cases[case_id].get("result") != "PASS"
    ]
    if regressed:
        return fail(f"previously passing systematic cases regressed: {regressed}")

    improved = sorted(
        case_id
        for case_id, item in baseline_cases.items()
        if item.get("result") == "FAIL" and candidate_cases[case_id].get("result") == "PASS"
    )
    remaining = sorted(
        case_id
        for case_id, item in baseline_cases.items()
        if item.get("result") == "FAIL" and candidate_cases[case_id].get("result") == "FAIL"
    )

    print(
        "PASS: all 19 previously passing systematic cases remain PASS; "
        f"candidate_passed={candidate.get('passed_cases')} candidate_failed={candidate.get('failed_cases')} "
        f"improved_revealed_cases={improved} remaining_revealed_failures={remaining}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
