from __future__ import print_function

import argparse
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = REPOSITORY_ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"
SCHEMA = "webshop-autonomous-prebuy-behavior/v1"
POLICY_INPUT_FIELDS = [
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--goal-index", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--expected-asin", required=True)
    parser.add_argument("--expected-option", required=True)
    parser.add_argument("--expected-price", required=True, type=float)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def load_policy_module():
    spec = importlib.util.spec_from_file_location("webshop_agent_behavior_runtime", str(POLICY_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load policy module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def setup_local_jvm():
    root = Path(sys.prefix) / "Library" / "lib" / "jvm"
    candidates = [root]
    if root.is_dir():
        candidates.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    java_home = None
    for candidate in candidates:
        if (candidate / "bin" / "java.exe").is_file() or (candidate / "bin" / "java").is_file():
            java_home = candidate
            break
    if java_home is None:
        raise RuntimeError("environment-local JVM not found under {}".format(root))
    os.environ["JAVA_HOME"] = str(java_home)
    os.environ["PATH"] = str(java_home / "bin") + os.pathsep + os.environ.get("PATH", "")
    return str(java_home)


def normalise_observation(value):
    if isinstance(value, tuple):
        value = value[0]
    return "" if value is None else str(value)


def normalise_actions(value):
    clickables = value.get("clickables", []) if isinstance(value, dict) else []
    return {
        "has_search_bar": bool(value.get("has_search_bar")) if isinstance(value, dict) else False,
        "clickables": [str(item) for item in clickables],
    }


def trace_hash(steps):
    material = json.dumps(steps, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def checkout_head(checkout):
    result = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def make_runtime(checkout, seed):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass

    os.chdir(str(checkout))
    if str(checkout) not in sys.path:
        sys.path.insert(0, str(checkout))

    import gym
    import web_agent_site.envs  # noqa: F401

    kwargs = {
        "observation_mode": "text",
        "num_products": 1000,
        "human_goals": True,
    }
    try:
        environment = gym.make("WebAgentTextEnv-v0", disable_env_checker=True, **kwargs)
    except TypeError:
        environment = gym.make("WebAgentTextEnv-v0", **kwargs)
    return environment.unwrapped


def score_after_stop(runtime, session_id, args):
    session = runtime.server.user_sessions[str(session_id)]
    selected_asin = session.get("asin")
    selected_options = session.get("options", {})
    option_values = [str(value) for value in selected_options.values()]
    selected_price = None
    if selected_asin is not None:
        raw_price = runtime.server.product_prices.get(str(selected_asin).upper())
        if raw_price is not None:
            selected_price = float(raw_price)

    return {
        "selected_asin": selected_asin,
        "selected_option_values": option_values,
        "selected_price": selected_price,
        "target_match": str(selected_asin or "").upper() == args.expected_asin.upper(),
        "required_option_match": args.expected_option.lower()
        in [value.lower() for value in option_values],
        "price_match": selected_price is not None
        and abs(float(selected_price) - float(args.expected_price)) < 0.0001,
    }


def run_once(policy, checkout, args):
    runtime = make_runtime(checkout, args.seed)
    initial = runtime.reset(session=args.goal_index)
    observation = normalise_observation(initial)
    instruction = str(runtime.instruction_text)
    previous_actions = []
    steps = []
    stopped = False

    for step_index in range(10):
        available = normalise_actions(runtime.get_available_actions())
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
            raise RuntimeError("policy returned neither action nor stop")
        if decision.action.strip().lower() == "click[buy now]":
            raise RuntimeError("policy attempted forbidden Buy Now action")

        observation_hash = hashlib.sha256(observation.encode("utf-8")).hexdigest()
        result = runtime.step(decision.action)
        if not isinstance(result, tuple) or len(result) != 4:
            raise RuntimeError("unexpected WebShop step result")
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
        observation = normalise_observation(next_observation)
        if done:
            raise RuntimeError("runtime ended before pre-purchase stop")

    if not stopped:
        raise RuntimeError("policy did not reach bounded stop condition")

    final_actions = normalise_actions(runtime.get_available_actions())
    buy_now_available = any(
        item.lower() == "buy now" for item in final_actions.get("clickables", [])
    )
    session = runtime.server.user_sessions[str(runtime.session)]
    purchase_count = int(session.get("actions", {}).get("purchase", 0))
    score = score_after_stop(runtime, runtime.session, args)

    run = {
        "steps": steps,
        "buy_now_available": buy_now_available,
        "buy_now_executed": False,
        "purchase_count": purchase_count,
        "score": score,
    }
    run["normalized_trace_sha256"] = trace_hash(
        {
            "steps": steps,
            "buy_now_available": buy_now_available,
            "buy_now_executed": False,
            "purchase_count": purchase_count,
            "score": score,
        }
    )
    return run


def main():
    args = parse_args()
    if args.repeat <= 0:
        raise ValueError("repeat must be positive")

    checkout = Path(args.checkout).resolve()
    output = Path(args.output).resolve()
    policy = load_policy_module()
    java_home = setup_local_jvm()
    source_head = checkout_head(checkout)

    runs = [run_once(policy, checkout, args) for _ in range(args.repeat)]
    digests = [run["normalized_trace_sha256"] for run in runs]
    repeat_identical = len(set(digests)) == 1
    first_score = runs[0]["score"] if runs else {}

    overall_pass = bool(
        runs
        and repeat_identical
        and all(run["buy_now_available"] for run in runs)
        and all(not run["buy_now_executed"] for run in runs)
        and all(run["purchase_count"] == 0 for run in runs)
        and first_score.get("target_match") is True
        and first_score.get("required_option_match") is True
        and first_score.get("price_match") is True
    )

    payload = {
        "schema": SCHEMA,
        "trace_type": "AUTONOMOUS_AGENT",
        "policy_type": "DETERMINISTIC_LOCAL_POLICY",
        "no_llm": True,
        "goal_index": args.goal_index,
        "seed": args.seed,
        "repeat": args.repeat,
        "policy_input_fields": POLICY_INPUT_FIELDS,
        "hidden_truth_exposed_to_policy": False,
        "checkout_head": source_head,
        "java_home_source": "sys.prefix/Library/lib/jvm",
        "java_home_resolved": java_home,
        "runs": runs,
        "score": first_score,
        "repeat_identical": repeat_identical,
        "payment_order_network_side_effect_count": 0,
        "overall_pass": overall_pass,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
