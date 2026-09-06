from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"
SEED = 20260823
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
        num_products=1000,
        human_goals=True,
    )
    goals = get_goals(all_products, product_prices, human_goals=True)
    random.seed(233)
    random.shuffle(goals)

    option_count_distribution = Counter(len(goal.get("goal_options") or {}) for goal in goals)
    category_distribution = Counter(str(goal.get("category", "")) for goal in goals)
    unique_asins = {str(goal.get("asin", "")) for goal in goals}
    finite_budget_count = sum(1 for goal in goals if float(goal.get("price_upper", 1000000)) < 1000000)

    payload = {
        "schema": "webshop-holdout-goal-pool-summary/v1",
        "checkout_head": checkout_head(),
        "seed": SEED,
        "num_products": len(all_products),
        "goal_count": len(goals),
        "unique_goal_asins": len(unique_asins),
        "finite_budget_goal_count": finite_budget_count,
        "option_count_distribution": {
            str(key): option_count_distribution[key] for key in sorted(option_count_distribution)
        },
        "nonempty_category_count": sum(1 for key in category_distribution if key),
        "development_goal_indices_in_range": all(0 <= index < len(goals) for index in DEV_GOALS),
        "holdout_candidate_count_after_dev_exclusion": len(goals) - len(DEV_GOALS),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
