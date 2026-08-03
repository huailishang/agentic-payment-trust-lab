from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

WEBSHOP_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
SMOKE_RELATIVE_PATH = (
    "docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/"
    "evidence/rv_webshop_small_smoke.json"
)
EXPECTED_SMOKE_SHA256 = "d1998c49a7afa14ee4534cd266d4e9e9c386ff2c2c8d85114aad19c304467e74"
EXPECTED_ASSET_HASHES = {
    "items_shuffle_1000.json": "30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269",
    "items_ins_v2_1000.json": "f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f",
    "items_human_ins.json": "cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3",
}
FIXTURE_SCHEMA = "webshop-pre-buy-now-candidate/v1"
FIXTURE_VERSION = "v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a mapping")
    return value


def extract_instruction(smoke: Mapping[str, Any]) -> str:
    events = smoke.get("events")
    if not isinstance(events, list):
        raise ValueError("smoke.events must be a list")
    reset = next(
        (event for event in events if isinstance(event, Mapping) and event.get("event") == "reset_1"),
        None,
    )
    if reset is None:
        raise ValueError("reset_1 event missing")
    observation = as_mapping(reset.get("observation"), "reset_1.observation")
    preview = observation.get("preview")
    if not isinstance(preview, str):
        raise ValueError("reset_1 observation preview missing")
    prefix = "WebShop [SEP] Instruction: [SEP] "
    suffix = " [SEP] Search"
    if not preview.startswith(prefix) or not preview.endswith(suffix):
        raise ValueError("reset_1 observation preview format changed")
    instruction = preview[len(prefix) : -len(suffix)]
    if not instruction.strip():
        raise ValueError("instruction is empty")
    return instruction


def selected_options(smoke: Mapping[str, Any]) -> Mapping[str, str]:
    events = smoke.get("events")
    if not isinstance(events, list):
        raise ValueError("smoke.events must be a list")
    pre_buy = next(
        (event for event in events if isinstance(event, Mapping) and event.get("event") == "pre_buy_now"),
        None,
    )
    if pre_buy is None:
        raise ValueError("pre_buy_now event missing")
    options = pre_buy.get("selected_options")
    if not isinstance(options, Mapping):
        raise ValueError("pre_buy_now.selected_options must be a mapping")
    normalized: dict[str, str] = {}
    for key, value in options.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("selected options must contain string keys and values")
        normalized[key] = value
    return dict(sorted(normalized.items()))


def parse_price(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("product pricing is missing")
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        parsed = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("product pricing is not decimal-safe") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError("product pricing must be positive")
    return format(parsed.quantize(Decimal("0.01")), "f")


def build_fixture(repo_root: Path) -> dict[str, Any]:
    smoke_path = repo_root / SMOKE_RELATIVE_PATH
    if not smoke_path.is_file():
        raise FileNotFoundError(smoke_path)
    smoke_hash = sha256(smoke_path)
    if smoke_hash != EXPECTED_SMOKE_SHA256:
        raise ValueError(
            f"unexpected smoke SHA-256: expected {EXPECTED_SMOKE_SHA256}, got {smoke_hash}"
        )
    smoke = as_mapping(load_json(smoke_path), "smoke")
    if smoke.get("overall_pass") is not True:
        raise ValueError("source smoke did not pass")
    if smoke.get("expected_commit") != WEBSHOP_COMMIT:
        raise ValueError("source smoke commit mismatch")
    if smoke.get("buy_now_available") is not True:
        raise ValueError("source smoke did not reach Buy Now")
    if smoke.get("buy_now_executed") is not False:
        raise ValueError("source smoke executed Buy Now")

    actions = smoke.get("actions_executed")
    if not isinstance(actions, list) or not actions:
        raise ValueError("source smoke actions missing")
    if any(
        isinstance(action, str)
        and "".join(action.lower().split()) == "click[buynow]"
        for action in actions
    ):
        raise ValueError("source smoke contains forbidden Buy Now action")

    events = smoke.get("events")
    if not isinstance(events, list):
        raise ValueError("source smoke events missing")
    reset = next(
        (event for event in events if isinstance(event, Mapping) and event.get("event") == "reset_1"),
        None,
    )
    if reset is None or not isinstance(reset.get("session"), str):
        raise ValueError("source session missing")
    session_id = reset["session"]

    chosen_asin = smoke.get("chosen_product")
    if not isinstance(chosen_asin, str) or not chosen_asin.strip():
        raise ValueError("chosen product missing")
    chosen_asin = chosen_asin.upper()

    data_dir = repo_root / "local_sources/third_party/webshop/data"
    parsed_assets: dict[str, Any] = {}
    actual_hashes: dict[str, str] = {}
    for name, expected_hash in EXPECTED_ASSET_HASHES.items():
        path = data_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"asset hash mismatch for {name}: expected {expected_hash}, got {actual_hash}"
            )
        actual_hashes[name] = actual_hash
        parsed_assets[name] = load_json(path)

    products = parsed_assets["items_shuffle_1000.json"]
    attributes = parsed_assets["items_ins_v2_1000.json"]
    human_instructions = parsed_assets["items_human_ins.json"]
    if not isinstance(products, list) or len(products) != 1000:
        raise ValueError("items_shuffle_1000.json must contain exactly 1000 products")
    if not isinstance(attributes, Mapping) or len(attributes) != 1000:
        raise ValueError("items_ins_v2_1000.json must contain exactly 1000 entries")
    if not isinstance(human_instructions, Mapping) or len(human_instructions) != 10136:
        raise ValueError("items_human_ins.json must contain exactly 10136 entries")

    product = next(
        (
            item
            for item in products
            if isinstance(item, Mapping)
            and str(item.get("asin") or "").upper() == chosen_asin
        ),
        None,
    )
    if product is None:
        raise ValueError(f"selected ASIN not found: {chosen_asin}")
    title = product.get("name")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("selected product title missing")
    unit_price = parse_price(product.get("pricing"))
    quantity = 1
    order_total = format(Decimal(unit_price) * quantity, "f")

    fixture = {
        "fixture_schema": FIXTURE_SCHEMA,
        "fixture_version": FIXTURE_VERSION,
        "source": {
            "webshop_commit": WEBSHOP_COMMIT,
            "evidence_path": SMOKE_RELATIVE_PATH,
            "smoke_result_sha256": smoke_hash,
            "asset_hashes": dict(sorted(actual_hashes.items())),
            "provenance": {
                "kind": "local_p9_a2_evidence",
                "immutable": True,
            },
        },
        "session_id": session_id,
        "task_identifier": f"webshop-session-{session_id}",
        "instruction_text": extract_instruction(smoke),
        "actions_executed": actions,
        "buy_now_available": True,
        "buy_now_executed": False,
        "product": {
            "asin": chosen_asin,
            "title": title,
            "selected_options": selected_options(smoke),
            "quantity": quantity,
            "unit_price": unit_price,
            "order_total": order_total,
        },
        "experiment_context": {
            "origin": "explicit_experiment_context_not_webshop_verified",
            "merchant": "webshop-experiment-merchant-v1",
            "payee": "webshop-experiment-payee-v1",
            "category": "home_furniture",
            "currency": "USD",
            "quote_expires_at": "2026-08-03T05:00:00+00:00",
            "fulfilment_terms": "offline_experiment_only_no_fulfilment_commitment",
            "mandate_ref": "experiment-context-mandate-ref-v1",
            "authority_version": "experiment-authority-v1",
            "request_timestamp": "2026-08-02T05:00:00+00:00",
        },
    }
    return fixture


def serialize_fixture(fixture: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("samples/external/webshop/pre_buy_now_candidate_v1.json"),
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output
    if not output.is_absolute():
        output = repo_root / output
    fixture = build_fixture(repo_root)
    serialized = serialize_fixture(fixture)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(serialized)
    try:
        fixture_path = output.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        fixture_path = str(output.resolve())
    summary = {
        "fixture_path": fixture_path,
        "fixture_sha256": hashlib.sha256(serialized).hexdigest(),
        "fixture_bytes": len(serialized),
        "source_smoke_sha256": fixture["source"]["smoke_result_sha256"],
        "source_commit": fixture["source"]["webshop_commit"],
        "product_count": 1,
        "buy_now_executed": fixture["buy_now_executed"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
