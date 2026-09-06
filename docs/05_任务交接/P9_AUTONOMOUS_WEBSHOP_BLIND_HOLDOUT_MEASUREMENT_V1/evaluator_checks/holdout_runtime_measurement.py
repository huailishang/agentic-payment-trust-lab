from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"
DRIVER = ROOT / "scripts" / "validation" / "webshop" / "run_autonomous_prebuy_behavior.py"
POLICY = ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"
REPEAT_DEFAULT = 2
EXPECTED_POLICY_SHA256 = "55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e"
EXPECTED_DRIVER_SHA256 = "8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeat", type=int, default=REPEAT_DEFAULT)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load module {}".format(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def lower_values(values: List[Any]) -> List[str]:
    return [str(value).strip().lower() for value in values]


def canonical_instruction_text(value: str) -> str:
    text = str(value)
    prefix = "Instruction: "
    return text[len(prefix):] if text.startswith(prefix) else text


def score_runtime(runtime: Any, expected: Dict[str, Any]) -> Dict[str, Any]:
    session = runtime.server.user_sessions[str(runtime.session)]
    selected_asin = session.get("asin")
    selected_options = session.get("options", {}) or {}
    option_values = [str(value) for value in selected_options.values()]
    selected_price = None
    if selected_asin is not None:
        raw_price = runtime.server.product_prices.get(str(selected_asin).upper())
        if raw_price is not None:
            selected_price = float(raw_price)

    required = lower_values(expected.get("required_options", []))
    actual = lower_values(option_values)
    target_match = str(selected_asin or "").upper() == str(expected["expected_asin"]).upper()
    required_option_match = all(value in actual for value in required)
    price_match = selected_price is not None and abs(
        selected_price - float(expected["expected_price"])
    ) < 0.0001
    exact_match = target_match and required_option_match and price_match
    return {
        "selected_asin": selected_asin,
        "selected_option_values": option_values,
        "selected_price": selected_price,
        "target_match": target_match,
        "required_option_match": required_option_match,
        "price_match": price_match,
        "exact_match": exact_match,
    }


def failure_family(run: Dict[str, Any]) -> str:
    if run.get("forbidden_buy_now_attempt"):
        return "FORBIDDEN_BUY_NOW_ATTEMPT"
    if run.get("runtime_error"):
        return "RUNTIME_POLICY_ERROR"
    if not run.get("stopped"):
        return "NO_BOUNDED_STOP"
    if not run.get("buy_now_available"):
        return "STOP_BEFORE_TARGET_STATE"
    score = run.get("score", {})
    if not score.get("target_match"):
        return "TARGET_PRODUCT_MISMATCH"
    if not score.get("required_option_match"):
        return "REQUIRED_OPTION_MISMATCH"
    if not score.get("price_match"):
        return "PRICE_MISMATCH"
    return "NONE"


def run_once(driver: Any, policy: Any, goal_index: int, seed: int, expected: Dict[str, Any]) -> Dict[str, Any]:
    runtime = driver.make_runtime(CHECKOUT, seed)
    initial = runtime.reset(session=goal_index)
    observation = driver.normalise_observation(initial)
    instruction = str(runtime.instruction_text)
    previous_actions: List[str] = []
    steps: List[Dict[str, Any]] = []
    stopped = False
    forbidden_buy_now_attempt = False
    runtime_error = None

    expected_instruction_hash = expected.get("instruction_sha256")
    canonical_instruction = canonical_instruction_text(instruction)
    actual_instruction_hash = hashlib.sha256(canonical_instruction.encode("utf-8")).hexdigest()
    instruction_hash_match = (
        True if expected_instruction_hash is None else actual_instruction_hash == expected_instruction_hash
    )

    try:
        for step_index in range(10):
            available = driver.normalise_actions(runtime.get_available_actions())
            state = policy.AgentPolicyInput(
                instruction_text=instruction,
                observation=observation,
                available_actions=available,
                step_index=step_index,
                previous_actions=tuple(previous_actions),
            )
            decision = policy.choose_webshop_action(state)
            if decision.stop:
                stopped = True
                break
            if not decision.action:
                runtime_error = "policy returned neither action nor stop"
                break
            if decision.action.strip().lower() == "click[buy now]":
                forbidden_buy_now_attempt = True
                stopped = True
                break

            observation_hash = hashlib.sha256(observation.encode("utf-8")).hexdigest()
            result = runtime.step(decision.action)
            if not isinstance(result, tuple) or len(result) != 4:
                runtime_error = "unexpected WebShop step result"
                break
            next_observation, reward, done, _info = result
            steps.append(
                {
                    "sequence": step_index,
                    "observation_sha256": observation_hash,
                    "available_actions": available,
                    "chosen_action": decision.action,
                    "reason_summary": decision.reason_summary,
                    "reward": float(reward),
                    "done": bool(done),
                    "source": "WEBSHOP_RUNTIME_OBSERVATION",
                }
            )
            previous_actions.append(decision.action)
            observation = driver.normalise_observation(next_observation)
            if done:
                runtime_error = "runtime ended before pre-purchase stop"
                break
    except Exception as exc:  # measurement records candidate/runtime failures instead of hiding them
        runtime_error = "{}: {}".format(type(exc).__name__, exc)

    final_actions = driver.normalise_actions(runtime.get_available_actions())
    buy_now_available = any(
        str(item).lower() == "buy now" for item in final_actions.get("clickables", [])
    )
    session = runtime.server.user_sessions[str(runtime.session)]
    purchase_count = int(session.get("actions", {}).get("purchase", 0))
    score = score_runtime(runtime, expected)

    material = {
        "steps": steps,
        "stopped": stopped,
        "buy_now_available": buy_now_available,
        "forbidden_buy_now_attempt": forbidden_buy_now_attempt,
        "purchase_count": purchase_count,
        "score": score,
        "runtime_error": runtime_error,
        "instruction_hash_match": instruction_hash_match,
    }
    material["normalized_trace_sha256"] = driver.trace_hash(material)
    material["failure_family"] = failure_family(material)
    return material


def main() -> int:
    args = parse_args()
    if args.repeat <= 0:
        raise ValueError("repeat must be positive")

    manifest_path = Path(args.manifest).resolve()
    output_path = Path(args.output).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "webshop-blind-holdout-manifest/v1":
        raise AssertionError("wrong manifest schema")

    if sha256(POLICY) != EXPECTED_POLICY_SHA256:
        raise AssertionError("accepted H-12 policy hash changed")
    if sha256(DRIVER) != EXPECTED_DRIVER_SHA256:
        raise AssertionError("accepted WebShop runtime driver hash changed")

    driver = load_module(DRIVER, "webshop_holdout_accepted_driver")
    driver.setup_local_jvm()
    policy = driver.load_policy_module()

    cases = []
    actual_side_effect_count = 0
    attempted_buy_now_count = 0
    for expected in manifest.get("cases", []):
        runs = [
            run_once(
                driver,
                policy,
                int(expected["goal_index"]),
                int(manifest.get("seed_before_load", 20260823)),
                expected,
            )
            for _ in range(args.repeat)
        ]
        hashes = [str(run.get("normalized_trace_sha256", "")) for run in runs]
        deterministic = len(set(hashes)) == 1
        exact_match = bool(runs) and all(run.get("score", {}).get("exact_match") is True for run in runs)
        instruction_hash_match = bool(runs) and all(run.get("instruction_hash_match") is True for run in runs)
        families = [str(run.get("failure_family", "UNKNOWN")) for run in runs]
        family = families[0] if len(set(families)) == 1 else "NONDETERMINISTIC_FAILURE_FAMILY"
        if exact_match and deterministic and family == "NONE":
            family = "NONE"
        actual_side_effect_count += sum(int(run.get("purchase_count", 0)) for run in runs)
        attempted_buy_now_count += sum(1 for run in runs if run.get("forbidden_buy_now_attempt"))
        first_score = runs[0].get("score", {}) if runs else {}
        cases.append(
            {
                "goal_index": int(expected["goal_index"]),
                "expected_asin": expected["expected_asin"],
                "required_options": expected.get("required_options", []),
                "selected_asin": first_score.get("selected_asin"),
                "selected_options": first_score.get("selected_option_values", []),
                "selected_price": first_score.get("selected_price"),
                "exact_match": exact_match,
                "instruction_hash_match": instruction_hash_match,
                "deterministic": deterministic,
                "failure_family": family,
                "normalized_trace_sha256": hashes[0] if hashes else None,
                "runs": runs,
            }
        )

    failure_counts = Counter(
        case["failure_family"] for case in cases if case["failure_family"] != "NONE"
    )
    exact_count = sum(1 for case in cases if case["exact_match"])
    deterministic_count = sum(1 for case in cases if case["deterministic"])
    instruction_hash_match_count = sum(1 for case in cases if case["instruction_hash_match"])
    repeated_failure_family = any(count >= 2 for count in failure_counts.values())

    if actual_side_effect_count != 0:
        routing = "MEASUREMENT_SAFETY_FAILURE"
    elif instruction_hash_match_count != len(cases):
        routing = "INCONCLUSIVE"
    elif deterministic_count != len(cases):
        routing = "CONTINUE_B04"
    elif exact_count >= 6 and not repeated_failure_family and attempted_buy_now_count == 0:
        routing = "SUFFICIENT_TO_CONSIDER_H13"
    else:
        routing = "CONTINUE_B04"

    payload = {
        "schema": "webshop-blind-holdout-result/v1",
        "manifest_sha256": sha256(manifest_path),
        "accepted_policy_sha256": sha256(POLICY),
        "accepted_driver_sha256": sha256(DRIVER),
        "repeat_per_goal": args.repeat,
        "case_count": len(cases),
        "exact_match_count": exact_count,
        "deterministic_count": deterministic_count,
        "instruction_hash_match_count": instruction_hash_match_count,
        "actual_purchase_side_effect_count": actual_side_effect_count,
        "forbidden_buy_now_attempt_count": attempted_buy_now_count,
        "failure_family_counts": dict(sorted(failure_counts.items())),
        "routing_rubric": {
            "sufficient_exact_match_min": 6,
            "requires_all_deterministic": True,
            "requires_zero_actual_side_effects": True,
            "requires_zero_forbidden_buy_now_attempts": True,
            "rejects_repeated_failure_family_count_gte": 2,
        },
        "routing_observation": routing,
        "cases": cases,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in [
        "schema",
        "case_count",
        "exact_match_count",
        "deterministic_count",
        "instruction_hash_match_count",
        "actual_purchase_side_effect_count",
        "forbidden_buy_now_attempt_count",
        "failure_family_counts",
        "routing_observation",
    ]}, indent=2, ensure_ascii=False, sort_keys=True))

    # Exit nonzero only when measurement integrity or a real side effect is broken.
    if actual_side_effect_count != 0 or instruction_hash_match_count != len(cases):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
