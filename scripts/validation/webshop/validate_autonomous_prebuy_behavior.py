from __future__ import print_function

import argparse
import json
import pathlib
import re


SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_FIELDS = [
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = json.loads(pathlib.Path(args.result).read_text(encoding="utf-8"))

    require(payload.get("schema") == "webshop-autonomous-prebuy-behavior/v1", "wrong schema")
    require(payload.get("trace_type") == "AUTONOMOUS_AGENT", "wrong trace type")
    require(payload.get("policy_type") == "DETERMINISTIC_LOCAL_POLICY", "wrong policy type")
    require(payload.get("no_llm") is True, "no_llm must be true")
    require(payload.get("policy_input_fields") == EXPECTED_FIELDS, "policy fields differ")
    require(payload.get("hidden_truth_exposed_to_policy") is False, "truth boundary violated")
    require(payload.get("overall_pass") is True, "overall result did not pass")
    require(payload.get("repeat_identical") is True, "repeat result differs")
    require(payload.get("payment_order_network_side_effect_count") == 0, "side effect count is not zero")

    runs = payload.get("runs", [])
    require(len(runs) == payload.get("repeat"), "run count differs from repeat")
    require(len(runs) == 3, "frozen plan requires three runs")

    hashes = []
    for run in runs:
        require(run.get("buy_now_available") is True, "Buy Now was not reached")
        require(run.get("buy_now_executed") is False, "Buy Now was executed")
        require(run.get("purchase_count") == 0, "purchase side effect observed")
        digest = str(run.get("normalized_trace_sha256", ""))
        require(SHA256.fullmatch(digest) is not None, "invalid normalized trace digest")
        hashes.append(digest)

        steps = run.get("steps", [])
        require(bool(steps), "runtime trace is empty")
        actions = [str(step.get("chosen_action", "")) for step in steps]
        require(any(action.lower().startswith("search[") for action in actions), "search action missing")
        require(any(action.lower().startswith("click[") for action in actions), "click action missing")
        require(not any(action.lower() == "click[buy now]" for action in actions), "forbidden Buy Now action")
        for index, step in enumerate(steps):
            require(step.get("sequence") == index, "step sequence is not contiguous")
            require(
                SHA256.fullmatch(str(step.get("observation_sha256", ""))) is not None,
                "observation digest missing",
            )
            require(isinstance(step.get("available_actions"), dict), "available actions missing")
            require(bool(step.get("reason_summary")), "reason summary missing")
            require("reward" in step and "done" in step and "source" in step, "step evidence incomplete")

    require(len(set(hashes)) == 1, "normalized traces are not identical")
    score = payload.get("score", {})
    require(score.get("target_match") is True, "selected product does not match")
    require(score.get("required_option_match") is True, "required option does not match")
    require(score.get("price_match") is True, "selected price does not match")

    print(
        json.dumps(
            {
                "status": "PASS",
                "runs": len(runs),
                "normalized_trace_sha256": hashes[0],
                "selected_asin": score.get("selected_asin"),
                "selected_option_values": score.get("selected_option_values"),
                "selected_price": score.get("selected_price"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
