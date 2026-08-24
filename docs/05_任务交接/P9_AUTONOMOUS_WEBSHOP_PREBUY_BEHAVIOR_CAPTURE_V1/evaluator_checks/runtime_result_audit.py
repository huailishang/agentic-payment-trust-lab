from __future__ import print_function

import argparse
import json
import pathlib
import re


EXPECTED_POLICY_FIELDS = [
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
]
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--expected-asin", required=True)
    parser.add_argument("--expected-option", required=True)
    parser.add_argument("--expected-price", required=True, type=float)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = json.loads(pathlib.Path(args.result).read_text(encoding="utf-8"))

    require(payload.get("schema") == "webshop-autonomous-prebuy-behavior/v1", "wrong schema")
    require(payload.get("overall_pass") is True, "overall_pass is not true")
    require(payload.get("trace_type") == "AUTONOMOUS_AGENT", "wrong trace type")
    require(payload.get("policy_type") == "DETERMINISTIC_LOCAL_POLICY", "wrong policy type")
    require(payload.get("no_llm") is True, "no_llm must be true")
    require(payload.get("goal_index") == 10, "wrong frozen goal index")
    require(payload.get("policy_input_fields") == EXPECTED_POLICY_FIELDS, "policy input declaration differs")
    require(not payload.get("hidden_truth_exposed_to_policy"), "hidden truth was exposed to policy")

    score = payload.get("score", {})
    require(str(score.get("selected_asin", "")).upper() == args.expected_asin.upper(), "target ASIN mismatch")
    options = [str(value).lower() for value in score.get("selected_option_values", [])]
    require(args.expected_option.lower() in options, "required option mismatch")
    require(abs(float(score.get("selected_price")) - args.expected_price) < 0.0001, "price mismatch")
    require(score.get("target_match") is True, "target_match is not true")
    require(score.get("required_option_match") is True, "required_option_match is not true")

    runs = payload.get("runs", [])
    require(len(runs) == 3, "exactly three fresh runs are required")
    normalized_hashes = []
    for index, run in enumerate(runs):
        steps = run.get("steps", [])
        require(steps, "run {} has no real steps".format(index))
        actions = [str(step.get("chosen_action", "")) for step in steps]
        require(any(action.lower().startswith("search[") for action in actions), "run lacks search action")
        require(any(action.lower().startswith("click[") for action in actions), "run lacks click action")
        require(not any(action.lower() == "click[buy now]" for action in actions), "Buy Now was executed")
        require(run.get("buy_now_available") is True, "Buy Now was not reached")
        require(run.get("buy_now_executed") is False, "Buy Now execution flag is true")
        require(run.get("purchase_count") == 0, "purchase side effect observed")
        digest = str(run.get("normalized_trace_sha256", ""))
        require(SHA256.match(digest) is not None, "invalid normalized trace SHA-256")
        normalized_hashes.append(digest)
        for sequence, step in enumerate(steps):
            require(step.get("sequence") == sequence, "non-contiguous step sequence")
            require(SHA256.match(str(step.get("observation_sha256", ""))) is not None, "invalid observation SHA-256")
            require(isinstance(step.get("available_actions"), dict), "available actions are missing")
            require(bool(step.get("reason_summary")), "reason summary is missing")
            require("reward" in step and "done" in step and "source" in step, "step evidence is incomplete")

    require(len(set(normalized_hashes)) == 1, "repeat=3 normalized traces differ")
    require(payload.get("repeat_identical") is True, "repeat_identical is not true")
    require(payload.get("payment_order_network_side_effect_count") == 0, "external side effect observed")

    print("PASS: independent autonomous runtime result audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
