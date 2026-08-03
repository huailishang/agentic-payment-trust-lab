from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from scripts.validation.webshop.verify_webshop_small_assets import (
    EXPECTED_COMMIT,
    WebShopSmallContractError,
    derive_search_keyword,
    validate_assets,
    validate_execution_plan,
    validate_small_data,
)


def _summary(observation: Any) -> Dict[str, Any]:
    text = observation[0] if isinstance(observation, tuple) else observation
    rendered = "" if text is None else str(text)
    return {
        "length": len(rendered),
        "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "preview": rendered[:240],
    }


def _step(runtime: Any, action: str) -> Tuple[Any, float, bool, Any]:
    result = runtime.step(action)
    if not isinstance(result, tuple) or len(result) != 4:
        raise WebShopSmallContractError("unexpected WebShop step result")
    observation, reward, done, info = result
    return observation, float(reward), bool(done), info


def _version(module_name: str) -> str:
    module = importlib.import_module(module_name)
    return str(getattr(module, "__version__", "unknown"))


def run_smoke(checkout: Path, expected_commit: str = EXPECTED_COMMIT) -> Dict[str, Any]:
    checkout = checkout.resolve()
    asset_report = validate_assets(
        checkout,
        require_index=True,
        expected_commit=expected_commit,
    )
    data_report = validate_small_data(checkout)
    keyword = derive_search_keyword(data_report["products"])

    os.chdir(str(checkout))
    sys.path.insert(0, str(checkout))

    import gym
    import pyserini
    import spacy
    import web_agent_site.envs  # noqa: F401 - registration side effect is required
    from pyserini.search.lucene import LuceneSearcher

    spec = gym.spec("WebAgentTextEnv-v0")
    if spec is None:
        raise WebShopSmallContractError("WebAgentTextEnv-v0 is not registered")

    index_path = checkout / "search_engine" / "indexes_1k"
    direct_searcher = LuceneSearcher(str(index_path))
    direct_hits = direct_searcher.search(keyword, k=10)
    if not direct_hits:
        raise WebShopSmallContractError(
            "direct Lucene query returned no result for {!r}".format(keyword)
        )
    direct_result_ids = [str(hit.docid) for hit in direct_hits]

    make_kwargs = {
        "observation_mode": "text",
        "num_products": 1000,
        "human_goals": True,
    }
    try:
        environment = gym.make(
            "WebAgentTextEnv-v0",
            disable_env_checker=True,
            **make_kwargs
        )
    except TypeError:
        environment = gym.make("WebAgentTextEnv-v0", **make_kwargs)
    runtime = environment.unwrapped

    actions: List[str] = []
    events: List[Dict[str, Any]] = []

    first_observation = runtime.reset()
    if _summary(first_observation)["length"] == 0:
        raise WebShopSmallContractError("first reset returned an empty observation")
    first_session = str(runtime.session)
    initial_actions = runtime.get_available_actions()
    if not initial_actions.get("has_search_bar"):
        raise WebShopSmallContractError("initial state does not expose a search bar")
    events.append(
        {
            "event": "reset_1",
            "session": first_session,
            "observation": _summary(first_observation),
            "available_actions": initial_actions,
        }
    )

    search_action = "search[{}]".format(keyword)
    actions.append(search_action)
    search_observation, search_reward, search_done, search_info = _step(
        runtime, search_action
    )
    if _summary(search_observation)["length"] == 0 or search_done:
        raise WebShopSmallContractError("search did not return a live non-empty state")
    result_actions = runtime.get_available_actions()
    clickables = list(result_actions.get("clickables", []))
    result_id_lookup = {item.lower(): item for item in direct_result_ids}
    chosen_clickable = next(
        (item for item in clickables if item.lower() in result_id_lookup),
        None,
    )
    if chosen_clickable is None:
        chosen_clickable = next(
            (
                item
                for item in clickables
                if re.fullmatch(r"[a-z0-9]{10}", item.lower())
            ),
            None,
        )
    if chosen_clickable is None:
        raise WebShopSmallContractError("search results contain no clickable product ASIN")
    chosen_asin = result_id_lookup.get(chosen_clickable.lower(), chosen_clickable.upper())
    events.append(
        {
            "event": "search",
            "action": search_action,
            "keyword": keyword,
            "reward": search_reward,
            "done": search_done,
            "info": search_info,
            "observation": _summary(search_observation),
            "clickables": clickables,
            "direct_lucene_result_ids": direct_result_ids,
        }
    )

    product_action = "click[{}]".format(chosen_clickable)
    actions.append(product_action)
    product_observation, product_reward, product_done, product_info = _step(
        runtime, product_action
    )
    if _summary(product_observation)["length"] == 0 or product_done:
        raise WebShopSmallContractError("product click did not return a live detail state")
    events.append(
        {
            "event": "product_click",
            "action": product_action,
            "chosen_product": chosen_asin,
            "reward": product_reward,
            "done": product_done,
            "info": product_info,
            "observation": _summary(product_observation),
        }
    )

    product = runtime.server.product_item_dict[str(chosen_asin).upper()]
    selected_options: Dict[str, str] = {}
    options = product.get("options", {})
    if isinstance(options, dict):
        for option_name in sorted(options):
            values = options.get(option_name)
            if not isinstance(values, list) or not values:
                continue
            option_value = str(values[0])
            current = runtime.get_available_actions().get("clickables", [])
            matching = next(
                (item for item in current if str(item).lower() == option_value.lower()),
                None,
            )
            if matching is None:
                raise WebShopSmallContractError(
                    "required option {!r} is not clickable".format(option_value)
                )
            option_action = "click[{}]".format(matching)
            actions.append(option_action)
            option_observation, option_reward, option_done, option_info = _step(
                runtime, option_action
            )
            if option_done:
                raise WebShopSmallContractError("option selection unexpectedly ended session")
            selected_options[str(option_name)] = option_value
            events.append(
                {
                    "event": "option_select",
                    "option_name": str(option_name),
                    "option_value": option_value,
                    "action": option_action,
                    "reward": option_reward,
                    "done": option_done,
                    "info": option_info,
                    "observation": _summary(option_observation),
                }
            )

    pre_buy_actions = runtime.get_available_actions()
    pre_buy_clickables = [str(item).lower() for item in pre_buy_actions.get("clickables", [])]
    if "buy now" not in pre_buy_clickables:
        raise WebShopSmallContractError("product state does not expose Buy Now")
    validate_execution_plan(actions)
    old_purchase_count = int(
        runtime.server.user_sessions[first_session]["actions"].get("purchase", 0)
    )
    if old_purchase_count != 0:
        raise WebShopSmallContractError("purchase side effect occurred before second reset")
    events.append(
        {
            "event": "pre_buy_now",
            "buy_now_available": True,
            "buy_now_executed": False,
            "selected_options": selected_options,
            "available_actions": pre_buy_actions,
            "purchase_count": old_purchase_count,
        }
    )

    second_observation = runtime.reset()
    second_session = str(runtime.session)
    if _summary(second_observation)["length"] == 0:
        raise WebShopSmallContractError("second reset returned an empty observation")
    if second_session == first_session:
        raise WebShopSmallContractError("second reset retained the previous session id")
    second_state = runtime.server.user_sessions[second_session]
    if second_state.get("asin") is not None or second_state.get("options"):
        raise WebShopSmallContractError("second reset retained product or option state")
    if int(second_state["actions"].get("purchase", 0)) != 0:
        raise WebShopSmallContractError("second reset retained purchase state")
    events.append(
        {
            "event": "reset_2",
            "session": second_session,
            "observation": _summary(second_observation),
            "asin": second_state.get("asin"),
            "options": second_state.get("options"),
            "purchase_count": int(second_state["actions"].get("purchase", 0)),
        }
    )
    environment.close()

    return {
        "schema": "webshop-small-smoke/v1",
        "overall_pass": True,
        "checkout": str(checkout),
        "expected_commit": expected_commit,
        "versions": {
            "python": sys.version,
            "gym": _version("gym"),
            "spacy": _version("spacy"),
            "pyserini": getattr(pyserini, "__version__", "0.17.0"),
        },
        "environment": {
            "id": "WebAgentTextEnv-v0",
            "observation_mode": "text",
            "num_products": 1000,
            "human_goals": True,
        },
        "asset_summary": asset_report,
        "keyword": keyword,
        "chosen_product": chosen_asin,
        "actions_executed": actions,
        "buy_now_available": True,
        "buy_now_executed": False,
        "events": events,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded WebShop small text smoke")
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_smoke(args.checkout, expected_commit=args.expected_commit)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
