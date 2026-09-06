from __future__ import annotations

import hashlib
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
DEV_GOALS = {0, 2, 7, 9, 10}


def setup_local_jvm() -> str:
    root = Path(sys.prefix) / "Library" / "lib" / "jvm"
    candidates = [root]
    if root.is_dir():
        candidates.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    for candidate in candidates:
        if (candidate / "bin" / "java.exe").is_file() or (candidate / "bin" / "java").is_file():
            os.environ["JAVA_HOME"] = str(candidate)
            os.environ["PATH"] = str(candidate / "bin") + os.pathsep + os.environ.get("PATH", "")
            return str(candidate)
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
    selected_indices = [index for index in range(len(goals)) if index not in DEV_GOALS]

    cases = []
    for index in selected_indices:
        goal = goals[index]
        options = goal.get("goal_options") or {}
        if isinstance(options, dict):
            required_options = [str(options[key]) for key in sorted(options)]
        elif isinstance(options, (list, tuple)):
            required_options = [str(value) for value in options]
        else:
            raise TypeError("unsupported goal_options type: {}".format(type(options).__name__))
        instruction_text = str(goal.get("instruction_text", ""))
        cases.append(
            {
                "goal_index": index,
                "expected_asin": str(goal["asin"]),
                "required_options": required_options,
                "expected_price": float(product_prices[str(goal["asin"])]),
                "instruction_sha256": hashlib.sha256(instruction_text.encode("utf-8")).hexdigest(),
                "option_count": len(required_options),
            }
        )

    payload = {
        "schema": "webshop-blind-holdout-manifest/v1",
        "selection_rule": "all generated WebShop small human goals except H-12 development indices",
        "checkout_head": checkout_head(),
        "seed": SEED,
        "num_products": NUM_PRODUCTS,
        "development_exclusions": sorted(DEV_GOALS),
        "goal_count": len(goals),
        "holdout_count": len(cases),
        "truth_provenance": {
            "products": "local_sources/third_party/webshop/data/items_shuffle_1000.json",
            "human_attributes": "local_sources/third_party/webshop/data/items_human_ins.json",
            "goal_builder": "local_sources/third_party/webshop/web_agent_site/engine/goal.py:get_human_goals",
            "product_loader": "local_sources/third_party/webshop/web_agent_site/engine/engine.py:load_products",
        },
        "cases": cases,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
