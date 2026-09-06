from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TASK_DIR = ROOT / "docs" / "05_任务交接" / "P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1"
MANIFEST = TASK_DIR / "HOLDOUT_MANIFEST.json"
CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"
POLICY = ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"
TEST = ROOT / "tests" / "test_webshop_agent_behavior.py"
DRIVER = ROOT / "scripts" / "validation" / "webshop" / "run_autonomous_prebuy_behavior.py"
VALIDATOR = ROOT / "scripts" / "validation" / "webshop" / "validate_autonomous_prebuy_behavior.py"

EXPECTED_HASHES = {
    POLICY: "55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e",
    TEST: "719970d6fac0e6d2dec2eee58fabc9ee9fb2dc80691062390aac1b8a4ac1221b",
    DRIVER: "8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40",
    VALIDATOR: "182342b50b038759030ed0faa92ebbfd7f37ab71bb9c442a58b1a168c16127d7",
}
DEV_INDICES = {0, 2, 7, 9, 10}
DEV_ASINS = {"B09MW563KN", "B07S7HDC88", "B09HX5CD2D", "B09KP78G37", "B099231V35"}
EXPECTED_CHECKOUT_HEAD = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
EXPECTED_SEED = 20260823
EXPECTED_SHUFFLE_SEED = 233
EXPECTED_GOAL_COUNT = 13


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "webshop-blind-holdout-manifest/v1", "wrong manifest schema")
    require(manifest.get("checkout_head") == EXPECTED_CHECKOUT_HEAD, "manifest checkout HEAD changed")
    require(int(manifest.get("seed_before_load")) == EXPECTED_SEED, "manifest seed changed")
    require(int(manifest.get("goal_shuffle_seed")) == EXPECTED_SHUFFLE_SEED, "manifest shuffle seed changed")
    require(int(manifest.get("goal_count")) == EXPECTED_GOAL_COUNT, "manifest goal count changed")
    require(set(manifest.get("development_exclusions", [])) == DEV_INDICES, "development exclusions changed")
    require(set(manifest.get("development_target_asins", [])) == DEV_ASINS, "development target ASINs changed")

    for path, expected_hash in EXPECTED_HASHES.items():
        require(path.is_file(), "missing accepted file {}".format(path))
        require(sha256(path) == expected_hash, "accepted file hash changed: {}".format(path))
    require(checkout_head() == EXPECTED_CHECKOUT_HEAD, "WebShop checkout HEAD changed")

    setup_local_jvm()
    random.seed(EXPECTED_SEED)
    try:
        import numpy as np

        np.random.seed(EXPECTED_SEED)
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
    random.seed(EXPECTED_SHUFFLE_SEED)
    random.shuffle(goals)
    require(len(goals) == EXPECTED_GOAL_COUNT, "runtime goal count changed")

    expected_indices = set(range(EXPECTED_GOAL_COUNT)) - DEV_INDICES
    cases = manifest.get("cases", [])
    actual_indices = {int(case["goal_index"]) for case in cases}
    require(actual_indices == expected_indices, "holdout is not the full complement of development indices")
    require(len(cases) == 8 and int(manifest.get("holdout_count")) == 8, "holdout count must be 8")

    observed_asins = set()
    for case in cases:
        index = int(case["goal_index"])
        goal = goals[index]
        actual_asin = str(goal["asin"])
        actual_options = normalize_required_options(goal.get("goal_options"))
        actual_price = float(product_prices[actual_asin])
        actual_instruction_hash = hashlib.sha256(
            str(goal.get("instruction_text", "")).encode("utf-8")
        ).hexdigest()

        require(actual_asin.upper() == str(case["expected_asin"]).upper(), "ASIN mismatch at goal {}".format(index))
        require(
            sorted(value.lower() for value in actual_options)
            == sorted(str(value).lower() for value in case.get("required_options", [])),
            "required option mismatch at goal {}".format(index),
        )
        require(abs(actual_price - float(case["expected_price"])) < 0.0001, "price mismatch at goal {}".format(index))
        require(actual_instruction_hash == case.get("instruction_sha256"), "instruction hash mismatch at goal {}".format(index))
        require(actual_asin.upper() not in {asin.upper() for asin in DEV_ASINS}, "development product leaked into holdout")
        observed_asins.add(actual_asin.upper())

    require(len(observed_asins) == 8, "holdout target ASINs must be unique")
    print(
        json.dumps(
            {
                "schema": "webshop-blind-holdout-truth-audit/v1",
                "result": "PASS",
                "manifest_sha256": sha256(MANIFEST),
                "holdout_count": 8,
                "unique_holdout_asins": 8,
                "development_overlap_count": 0,
                "runtime_mapping_verified": True,
                "accepted_snapshot_hashes_verified": True,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
