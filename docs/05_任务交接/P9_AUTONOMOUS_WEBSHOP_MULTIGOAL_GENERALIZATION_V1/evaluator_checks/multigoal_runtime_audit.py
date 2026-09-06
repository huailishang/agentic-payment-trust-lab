from __future__ import print_function

import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[4]
DRIVER = ROOT / "scripts" / "validation" / "webshop" / "run_autonomous_prebuy_behavior.py"
CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"

SEED = 20260823
REPEAT = 2

CASES = [
    {
        "goal_index": 0,
        "expected_asin": "B09MW563KN",
        "required_options": ["blue"],
        "expected_price": 22.9,
    },
    {
        "goal_index": 2,
        "expected_asin": "B07S7HDC88",
        "required_options": ["black1901", "10.5"],
        "expected_price": 35.421970457880775,
    },
    {
        "goal_index": 7,
        "expected_asin": "B09HX5CD2D",
        "required_options": ["heather charcoal", "small"],
        "expected_price": 39.95,
    },
    {
        "goal_index": 9,
        "expected_asin": "B09KP78G37",
        "required_options": ["red", "x-large"],
        "expected_price": 55.69454800459104,
    },
    {
        "goal_index": 10,
        "expected_asin": "B099231V35",
        "required_options": ["orange"],
        "expected_price": 16.79,
    },
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def lower_values(values):
    return [str(value).strip().lower() for value in values]


def run_case(case, output):
    command = [
        sys.executable,
        str(DRIVER),
        "--checkout",
        str(CHECKOUT),
        "--goal-index",
        str(case["goal_index"]),
        "--seed",
        str(SEED),
        "--repeat",
        str(REPEAT),
        "--expected-asin",
        case["expected_asin"],
        "--expected-option",
        case["required_options"][0],
        "--expected-price",
        str(case["expected_price"]),
        "--output",
        str(output),
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if not output.is_file():
        raise AssertionError(
            "goal {} produced no result; exit={} stderr={}".format(
                case["goal_index"], completed.returncode, completed.stderr[-1000:]
            )
        )
    payload = json.loads(output.read_text(encoding="utf-8"))
    return completed, payload


def validate_case(case, completed, payload):
    goal = case["goal_index"]
    require(completed.returncode == 0, "goal {} driver exit {}".format(goal, completed.returncode))
    require(payload.get("schema") == "webshop-autonomous-prebuy-behavior/v1", "goal {} wrong schema".format(goal))
    require(payload.get("trace_type") == "AUTONOMOUS_AGENT", "goal {} wrong trace type".format(goal))
    require(payload.get("policy_type") == "DETERMINISTIC_LOCAL_POLICY", "goal {} wrong policy type".format(goal))
    require(payload.get("no_llm") is True, "goal {} no_llm is not true".format(goal))
    require(payload.get("hidden_truth_exposed_to_policy") is False, "goal {} hidden truth exposed".format(goal))
    require(payload.get("goal_index") == goal, "goal {} result index mismatch".format(goal))
    require(payload.get("repeat") == REPEAT, "goal {} repeat mismatch".format(goal))
    require(payload.get("repeat_identical") is True, "goal {} repeat not deterministic".format(goal))
    require(payload.get("payment_order_network_side_effect_count") == 0, "goal {} external side effect".format(goal))

    score = payload.get("score", {})
    require(
        str(score.get("selected_asin", "")).upper() == case["expected_asin"].upper(),
        "goal {} target ASIN mismatch: {}".format(goal, score.get("selected_asin")),
    )
    selected_options = lower_values(score.get("selected_option_values", []))
    for option in lower_values(case["required_options"]):
        require(option in selected_options, "goal {} missing required option {}".format(goal, option))
    selected_price = float(score.get("selected_price"))
    require(
        abs(selected_price - float(case["expected_price"])) < 0.0001,
        "goal {} price mismatch: {}".format(goal, selected_price),
    )

    runs = payload.get("runs", [])
    require(len(runs) == REPEAT, "goal {} run count mismatch".format(goal))
    hashes = []
    for run_index, run in enumerate(runs):
        require(run.get("buy_now_available") is True, "goal {} run {} did not reach Buy Now".format(goal, run_index))
        require(run.get("buy_now_executed") is False, "goal {} run {} executed Buy Now".format(goal, run_index))
        require(run.get("purchase_count") == 0, "goal {} run {} purchase side effect".format(goal, run_index))
        actions = [str(step.get("chosen_action", "")) for step in run.get("steps", [])]
        require(actions, "goal {} run {} has no actions".format(goal, run_index))
        require(any(action.lower().startswith("search[") for action in actions), "goal {} run {} lacks search".format(goal, run_index))
        require(any(action.lower() == "click[{}]".format(case["expected_asin"]).lower() for action in actions), "goal {} run {} lacks target product click".format(goal, run_index))
        require(not any(action.lower() == "click[buy now]" for action in actions), "goal {} run {} executed Buy Now action".format(goal, run_index))
        run_options = lower_values(run.get("score", {}).get("selected_option_values", []))
        for option in lower_values(case["required_options"]):
            require(option in run_options, "goal {} run {} missing option {}".format(goal, run_index, option))
        hashes.append(str(run.get("normalized_trace_sha256", "")))
    require(len(set(hashes)) == 1, "goal {} normalized traces differ".format(goal))

    return {
        "goal_index": goal,
        "selected_asin": score.get("selected_asin"),
        "selected_options": score.get("selected_option_values", []),
        "selected_price": score.get("selected_price"),
        "normalized_trace_sha256": hashes[0],
        "pass": True,
    }


def main():
    require(DRIVER.is_file(), "runtime driver is missing")
    require(CHECKOUT.is_dir(), "WebShop checkout is missing")

    summaries = []
    with tempfile.TemporaryDirectory(prefix="webshop-multigoal-") as tmp:
        tmp_root = pathlib.Path(tmp)
        for case in CASES:
            output = tmp_root / "goal-{}.json".format(case["goal_index"])
            completed, payload = run_case(case, output)
            try:
                summary = validate_case(case, completed, payload)
            except Exception as exc:
                score = payload.get("score", {}) if isinstance(payload, dict) else {}
                summary = {
                    "goal_index": case["goal_index"],
                    "selected_asin": score.get("selected_asin"),
                    "selected_options": score.get("selected_option_values", []),
                    "selected_price": score.get("selected_price"),
                    "driver_exit": completed.returncode,
                    "pass": False,
                    "failure": str(exc),
                }
            summaries.append(summary)

    result = {
        "schema": "webshop-autonomous-multigoal-audit/v1",
        "seed": SEED,
        "repeat_per_goal": REPEAT,
        "goal_count": len(CASES),
        "passed": sum(1 for item in summaries if item["pass"]),
        "target": len(CASES),
        "cases": summaries,
        "buy_now_executed": False,
        "external_side_effect_count": 0,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if result["passed"] != result["target"]:
        print("FAIL: multi-goal target {}/{} not met".format(result["passed"], result["target"]))
        return 1
    print("PASS: five-goal autonomous WebShop generalization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
