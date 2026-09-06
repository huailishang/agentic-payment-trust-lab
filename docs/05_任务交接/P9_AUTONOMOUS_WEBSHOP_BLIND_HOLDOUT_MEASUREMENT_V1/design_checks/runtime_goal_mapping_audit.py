from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"
SEED = 20260823
NUM_PRODUCTS = 1000
FROZEN_H12 = {
    0: {
        "expected_asin": "B09MW563KN",
        "required_options": ["blue"],
        "expected_price": 22.9,
    },
    2: {
        "expected_asin": "B07S7HDC88",
        "required_options": ["black1901", "10.5"],
        "expected_price": 35.421970457880775,
    },
    7: {
        "expected_asin": "B09HX5CD2D",
        "required_options": ["heather charcoal", "small"],
        "expected_price": 39.95,
    },
    9: {
        "expected_asin": "B09KP78G37",
        "required_options": ["red", "x-large"],
        "expected_price": 55.69454800459104,
    },
    10: {
        "expected_asin": "B099231V35",
        "required_options": ["orange"],
        "expected_price": 16.79,
    },
}


def setup_local_jvm() -> None:
    root = Path(sys.prefix) / "Library" / "lib" / "jvm"
    candidates = [root]
    if root.is_dir():
        candidates.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    for candidate in candidates:
        if (candidate / "bin" / "java.exe").is_file() or (candidate / "bin" / "java").is_file():
            os.environ["JAVA_HOME"] = str(candidate)
            os.environ["PATH"] = str(candidate / "bin") + os.pathsep + os.environ.get("PATH", "")
            return
    raise RuntimeError("environment-local JVM not found under {}".format(root))


def checkout_head() -> str:
    completed = subprocess.run(
        ["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return completed.stdout.strip()


def normalize_required_options(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [str(raw[key]) for key in sorted(raw)]
    if isinstance(raw, (list, tuple)):
        return [str(value) for value in raw]
    raise TypeError("unsupported goal_options type: {}".format(type(raw).__name__))


def main() -> int:
    setup_local_jvm()
    random.seed(SEED)
    try:
        import numpy as np

        np.random.seed(SEED)
    except Exception:
        pass

    if str(CHECKOUT) not in sys.path:
        sys.path.insert(0, str(CHECKOUT))

    from web_agent_site.engine.engine import load_products
    from web_agent_site.engine.goal import get_goals
    from web_agent_site.utils import DEFAULT_FILE_PATH

    all_products, _product_item_dict, product_prices, _attribute_to_asins = load_products(
        filepath=DEFAULT_FILE_PATH,
        num_products=NUM_PRODUCTS,
        human_goals=True,
    )
    goals = get_goals(all_products, product_prices, human_goals=True)
    random.seed(233)
    random.shuffle(goals)

    cases = []
    all_match = True
    for goal_index, expected in sorted(FROZEN_H12.items()):
        goal = goals[goal_index]
        actual_asin = str(goal["asin"])
        actual_options = normalize_required_options(goal.get("goal_options"))
        actual_price = float(product_prices[actual_asin])
        asin_match = actual_asin.upper() == expected["expected_asin"].upper()
        options_match = sorted(value.lower() for value in actual_options) == sorted(
            value.lower() for value in expected["required_options"]
        )
        price_match = abs(actual_price - float(expected["expected_price"])) < 0.0001
        case_match = asin_match and options_match and price_match
        all_match = all_match and case_match
        cases.append(
            {
                "goal_index": goal_index,
                "asin_match": asin_match,
                "options_match": options_match,
                "price_match": price_match,
                "match": case_match,
            }
        )

    payload = {
        "schema": "webshop-runtime-goal-mapping-audit/v1",
        "checkout_head": checkout_head(),
        "seed_before_load": SEED,
        "goal_shuffle_seed": 233,
        "goal_count": len(goals),
        "known_h12_case_count": len(FROZEN_H12),
        "all_match": all_match,
        "cases": cases,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
