from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from urllib.parse import urlparse


EXPECTED_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
BUY_NOW_ACTION = "click[buy now]"


@dataclass(frozen=True)
class AssetSpec:
    filename: str
    google_drive_id: str
    byte_length: int
    sha256: str
    json_type: str
    top_level_count: int


@dataclass(frozen=True)
class MirrorSpec:
    repository: str
    revision: str
    base_url: str


APPROVED_ASSETS: Mapping[str, AssetSpec] = {
    "items_shuffle_1000.json": AssetSpec(
        filename="items_shuffle_1000.json",
        google_drive_id="1EgHdxQ_YxqIQlvvq5iKlCrkEKR6-j0Ib",
        byte_length=4_467_013,
        sha256="30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269",
        json_type="list",
        top_level_count=1_000,
    ),
    "items_ins_v2_1000.json": AssetSpec(
        filename="items_ins_v2_1000.json",
        google_drive_id="1IduG0xl544V_A_jv3tHXC0kyFi7PnyBu",
        byte_length=147_099,
        sha256="f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f",
        json_type="dict",
        top_level_count=1_000,
    ),
    "items_human_ins.json": AssetSpec(
        filename="items_human_ins.json",
        google_drive_id="14Kb5SPBk_jfdLZ_CDBNitW98QLDlKR5O",
        byte_length=5_137_548,
        sha256="cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3",
        json_type="dict",
        top_level_count=10_136,
    ),
}
APPROVED_DATA_FILES: Mapping[str, str] = {
    name: spec.google_drive_id for name, spec in APPROVED_ASSETS.items()
}
APPROVED_MIRRORS: Mapping[str, MirrorSpec] = {
    "YWZBrandon/webshop-data": MirrorSpec(
        repository="YWZBrandon/webshop-data",
        revision="ce990fff5aee388db2706f07820c578ab68e0453",
        base_url=(
            "https://huggingface.co/datasets/YWZBrandon/webshop-data/resolve/"
            "ce990fff5aee388db2706f07820c578ab68e0453/"
        ),
    ),
    "HongbangYuan/webshop": MirrorSpec(
        repository="HongbangYuan/webshop",
        revision="0129d4a81dbdb827e76afd20a1e2c38b61098613",
        base_url=(
            "https://huggingface.co/datasets/HongbangYuan/webshop/resolve/"
            "0129d4a81dbdb827e76afd20a1e2c38b61098613/"
        ),
    ),
    "Merlin-Hongru/tmp-files": MirrorSpec(
        repository="Merlin-Hongru/tmp-files",
        revision="c38999b0787132502fcf85d02ff92ea6347baf87",
        base_url=(
            "https://huggingface.co/Merlin-Hongru/tmp-files/resolve/"
            "c38999b0787132502fcf85d02ff92ea6347baf87/"
        ),
    ),
}
FORBIDDEN_INDEX_NAMES = (
    "indexes",
    "indexes_100",
    "indexes_100k",
    "resources",
    "resources_100",
    "resources_100k",
)


class WebShopSmallContractError(ValueError):
    """Raised when the bounded WebShop small-runtime contract is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_git_executable() -> str:
    configured = os.environ.get("WEBSHOP_GIT_EXE")
    candidates = [
        configured,
        shutil.which("git"),
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise WebShopSmallContractError(
        "Git executable not found; set WEBSHOP_GIT_EXE or install Git for Windows"
    )


def _run_git(checkout: Path, *args: str) -> str:
    git_executable = _resolve_git_executable()
    result = subprocess.run(
        (git_executable, "-C", str(checkout), *args),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise WebShopSmallContractError(
            "git command failed for {}: {}".format(checkout, result.stderr.strip())
        )
    return result.stdout.strip()


def validate_checkout(
    checkout: Path,
    expected_commit: str = EXPECTED_COMMIT,
) -> Dict[str, Any]:
    checkout = checkout.resolve()
    if not checkout.is_dir():
        raise WebShopSmallContractError("missing WebShop checkout: {}".format(checkout))
    actual_commit = _run_git(checkout, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        raise WebShopSmallContractError(
            "checkout commit mismatch: expected {}, actual {}".format(
                expected_commit, actual_commit
            )
        )
    status = _run_git(checkout, "status", "--short")
    if status:
        raise WebShopSmallContractError(
            "tracked or untracked source change detected in pinned checkout: {}".format(
                status
            )
        )
    return {
        "checkout": str(checkout),
        "expected_commit": expected_commit,
        "actual_commit": actual_commit,
        "git_clean": True,
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebShopSmallContractError(
            "invalid JSON asset {}: {}".format(path, exc)
        ) from exc


def _json_type_name(value: Any) -> str:
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def _top_level_count(value: Any) -> int:
    if isinstance(value, (list, dict)):
        return len(value)
    return 0


def validate_execution_plan(actions: Sequence[str]) -> List[str]:
    normalized = [re.sub(r"\s+", "", action).lower() for action in actions]
    if BUY_NOW_ACTION.replace(" ", "") in normalized:
        raise WebShopSmallContractError("execution plan contains forbidden click[buy now]")
    return list(actions)


def validate_mirror_source(
    repository: str,
    revision: str,
    url: str,
    allow_checksum_mirror_fallback: bool,
) -> Dict[str, str]:
    if not allow_checksum_mirror_fallback:
        raise WebShopSmallContractError(
            "checksum mirror fallback is disabled; explicit approval switch is required"
        )
    if revision.lower() in {"main", "master", "latest", "head"}:
        raise WebShopSmallContractError("mutable mirror revision is forbidden: {}".format(revision))
    mirror = APPROVED_MIRRORS.get(repository)
    if mirror is None:
        raise WebShopSmallContractError("unapproved mirror repository: {}".format(repository))
    if revision != mirror.revision:
        raise WebShopSmallContractError(
            "unapproved mirror revision for {}: {}".format(repository, revision)
        )
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "huggingface.co":
        raise WebShopSmallContractError("mirror URL must use https://huggingface.co")
    if not url.startswith(mirror.base_url):
        raise WebShopSmallContractError(
            "mirror URL is not pinned to the approved repository revision"
        )
    filename = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    if filename not in APPROVED_ASSETS:
        raise WebShopSmallContractError("unapproved mirror filename: {}".format(filename))
    return {
        "repository": mirror.repository,
        "revision": mirror.revision,
        "base_url": mirror.base_url,
        "url": url,
        "filename": filename,
    }


def validate_asset_file(path: Path, spec: AssetSpec) -> Dict[str, Any]:
    if path.name != spec.filename:
        raise WebShopSmallContractError(
            "asset filename mismatch: expected {}, actual {}".format(spec.filename, path.name)
        )
    if not path.is_file():
        raise WebShopSmallContractError("missing asset: {}".format(path))
    actual_bytes = path.stat().st_size
    if actual_bytes != spec.byte_length:
        raise WebShopSmallContractError(
            "asset byte length mismatch for {}: expected {}, actual {}".format(
                spec.filename, spec.byte_length, actual_bytes
            )
        )
    actual_sha256 = sha256_file(path)
    if actual_sha256 != spec.sha256:
        raise WebShopSmallContractError(
            "asset SHA-256 mismatch for {}: expected {}, actual {}".format(
                spec.filename, spec.sha256, actual_sha256
            )
        )
    payload = _load_json(path)
    actual_type = _json_type_name(payload)
    if actual_type != spec.json_type:
        raise WebShopSmallContractError(
            "asset JSON type mismatch for {}: expected {}, actual {}".format(
                spec.filename, spec.json_type, actual_type
            )
        )
    actual_count = _top_level_count(payload)
    if actual_count != spec.top_level_count:
        raise WebShopSmallContractError(
            "asset top-level count mismatch for {}: expected {}, actual {}".format(
                spec.filename, spec.top_level_count, actual_count
            )
        )
    return {
        "filename": spec.filename,
        "path": str(path.resolve()),
        "bytes": actual_bytes,
        "sha256": actual_sha256,
        "json_type": actual_type,
        "top_level_count": actual_count,
        "google_drive_id": spec.google_drive_id,
    }


def validate_staging_and_promote(
    staging_dir: Path,
    destination_dir: Path,
    repository: str,
    revision: str,
    allow_checksum_mirror_fallback: bool,
    promote: bool = False,
) -> Dict[str, Any]:
    mirror = APPROVED_MIRRORS.get(repository)
    if mirror is None:
        raise WebShopSmallContractError("unapproved mirror repository: {}".format(repository))
    files: Dict[str, Dict[str, Any]] = {}
    for name, spec in APPROVED_ASSETS.items():
        source_url = mirror.base_url + name
        source = validate_mirror_source(
            repository,
            revision,
            source_url,
            allow_checksum_mirror_fallback,
        )
        file_report = validate_asset_file(staging_dir / name, spec)
        file_report["source"] = source
        files[name] = file_report

    unexpected = sorted(
        path.name for path in staging_dir.iterdir() if path.is_file() and path.name not in APPROVED_ASSETS
    )
    if unexpected:
        raise WebShopSmallContractError(
            "unexpected staging file(s): {}".format(", ".join(unexpected))
        )

    promoted: List[str] = []
    if promote:
        destination_dir.mkdir(parents=True, exist_ok=True)
        for name in APPROVED_ASSETS:
            source = staging_dir / name
            destination = destination_dir / name
            source.replace(destination)
            promoted.append(str(destination.resolve()))
    return {
        "schema": "webshop-small-mirror-assets/v1",
        "description": "checksum-verified mirror copies of the WebShop small assets",
        "repository": mirror.repository,
        "revision": mirror.revision,
        "base_url": mirror.base_url,
        "staging_dir": str(staging_dir.resolve()),
        "destination_dir": str(destination_dir.resolve()),
        "files": files,
        "promoted": promote,
        "promoted_paths": promoted,
        "overall_pass": True,
    }


def validate_small_data(
    checkout: Path,
    expected_product_count: int = 1000,
    enforce_approved_fingerprints: bool = True,
) -> Dict[str, Any]:
    data_dir = checkout / "data"
    missing = [name for name in APPROVED_DATA_FILES if not (data_dir / name).is_file()]
    if missing:
        raise WebShopSmallContractError(
            "missing approved small-data file(s): {}".format(", ".join(missing))
        )

    payloads: Dict[str, Any] = {}
    files: Dict[str, Dict[str, Any]] = {}
    for name, file_id in APPROVED_DATA_FILES.items():
        path = data_dir / name
        payload = _load_json(path)
        payloads[name] = payload
        count = _top_level_count(payload)
        if count == 0:
            raise WebShopSmallContractError("small-data file is empty: {}".format(name))
        if enforce_approved_fingerprints:
            files[name] = validate_asset_file(path, APPROVED_ASSETS[name])
        else:
            files[name] = {
                "google_drive_id": file_id,
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "json_type": _json_type_name(payload),
                "top_level_count": count,
            }

    products = payloads["items_shuffle_1000.json"]
    if not isinstance(products, list):
        raise WebShopSmallContractError("product asset must contain a top-level list")
    if len(products) != expected_product_count:
        raise WebShopSmallContractError(
            "product count mismatch: expected {}, actual {}".format(
                expected_product_count, len(products)
            )
        )

    normalized_product_keys = ("asin", "Title", "Description", "BulletPoints")
    raw_product_keys = ("asin", "name", "full_description", "small_description")
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise WebShopSmallContractError("product {} is not an object".format(index))
        normalized_missing = [key for key in normalized_product_keys if key not in product]
        raw_missing = [key for key in raw_product_keys if key not in product]
        if normalized_missing and raw_missing:
            raise WebShopSmallContractError(
                "product {} matches neither normalized nor raw WebShop schema; "
                "normalized missing: {}; raw missing: {}".format(
                    index,
                    ", ".join(normalized_missing),
                    ", ".join(raw_missing),
                )
            )

    product_asins = {str(item.get("asin", "")) for item in products}
    if len(product_asins) != expected_product_count or "" in product_asins:
        raise WebShopSmallContractError("product ASINs must be non-empty and unique")

    attributes = payloads["items_ins_v2_1000.json"]
    human = payloads["items_human_ins.json"]
    return {
        "data_dir": str(data_dir.resolve()),
        "description": "checksum-verified mirror copies of the WebShop small assets",
        "files": files,
        "product_count": len(products),
        "unique_product_asins": len(product_asins),
        "attribute_top_level_count": _top_level_count(attributes),
        "human_instruction_top_level_count": _top_level_count(human),
        "products": products,
    }


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def product_to_document(product: Mapping[str, Any]) -> Dict[str, Any]:
    option_texts: List[str] = []
    options = product.get("options", {})
    if not isinstance(options, dict) or not options:
        options = {}
        customization_options = product.get("customization_options", {})
        if isinstance(customization_options, dict):
            for option_name, option_contents in customization_options.items():
                if not isinstance(option_contents, list):
                    continue
                option_values = [
                    str(item.get("value", "")).strip().replace("/", " | ").lower()
                    for item in option_contents
                    if isinstance(item, dict) and str(item.get("value", "")).strip()
                ]
                if option_values:
                    options[str(option_name).lower()] = option_values
    for option_name, option_values in options.items():
        if isinstance(option_values, list):
            values = ", ".join(str(value) for value in option_values)
        else:
            values = str(option_values)
        option_texts.append("{}: {}".format(option_name, values))
    bullet_points = product.get("BulletPoints", product.get("small_description", []))
    first_bullet = bullet_points[0] if isinstance(bullet_points, list) and bullet_points else bullet_points
    contents = " ".join(
        (
            _safe_text(product.get("Title", product.get("name"))),
            _safe_text(product.get("Description", product.get("full_description"))),
            _safe_text(first_bullet),
            ", and ".join(option_texts),
        )
    ).lower()
    return {
        "id": str(product["asin"]),
        "contents": contents,
        "product": dict(product),
    }


def build_resources_1k(
    checkout: Path,
    expected_commit: str = EXPECTED_COMMIT,
    enforce_approved_fingerprints: bool = True,
) -> Dict[str, Any]:
    validate_checkout(checkout, expected_commit=expected_commit)
    data = validate_small_data(
        checkout,
        enforce_approved_fingerprints=enforce_approved_fingerprints,
    )
    resources_dir = checkout / "search_engine" / "resources_1k"
    resources_dir.mkdir(parents=True, exist_ok=True)
    documents_path = resources_dir / "documents.jsonl"
    temporary_path = resources_dir / "documents.jsonl.tmp"
    with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
        for product in data["products"]:
            handle.write(json.dumps(product_to_document(product), ensure_ascii=False) + "\n")
    temporary_path.replace(documents_path)
    return {
        "resources_dir": str(resources_dir.resolve()),
        "documents_path": str(documents_path.resolve()),
        "document_count": data["product_count"],
        "documents_sha256": sha256_file(documents_path),
        "source_product_sha256": data["files"]["items_shuffle_1000.json"]["sha256"],
    }


def validate_index(checkout: Path) -> Dict[str, Any]:
    search_dir = checkout / "search_engine"
    resources_dir = search_dir / "resources_1k"
    documents_path = resources_dir / "documents.jsonl"
    indexes_dir = search_dir / "indexes_1k"
    if not documents_path.is_file():
        raise WebShopSmallContractError("missing resources_1k/documents.jsonl")
    if not indexes_dir.is_dir():
        raise WebShopSmallContractError("missing indexes_1k before runtime smoke")
    inventory = sorted(
        [
            {
                "relative_path": path.relative_to(indexes_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in indexes_dir.rglob("*")
            if path.is_file()
        ],
        key=lambda item: item["relative_path"],
    )
    if not inventory:
        raise WebShopSmallContractError("indexes_1k is empty")
    forbidden_present = [name for name in FORBIDDEN_INDEX_NAMES if (search_dir / name).exists()]
    if forbidden_present:
        raise WebShopSmallContractError(
            "forbidden search artifact(s) present: {}".format(", ".join(forbidden_present))
        )
    return {
        "resources_dir": str(resources_dir.resolve()),
        "documents_path": str(documents_path.resolve()),
        "documents_sha256": sha256_file(documents_path),
        "indexes_dir": str(indexes_dir.resolve()),
        "index_file_count": len(inventory),
        "index_inventory": inventory,
        "forbidden_search_artifacts": forbidden_present,
    }


def derive_search_keyword(products: Sequence[Mapping[str, Any]]) -> str:
    for product in products:
        title = _safe_text(product.get("Title", product.get("name")))
        words = [word.lower() for word in re.findall(r"[A-Za-z0-9]+", title)]
        words = [word for word in words if len(word) >= 3]
        if words:
            return " ".join(words[:3])
    raise WebShopSmallContractError("cannot derive deterministic keyword from products")


def query_index_1k(checkout: Path, k: int = 10) -> Dict[str, Any]:
    data = validate_small_data(checkout)
    index = validate_index(checkout)
    keyword = derive_search_keyword(data["products"])
    try:
        from pyserini.search.lucene import LuceneSearcher
    except ImportError as exc:
        raise WebShopSmallContractError("pyserini is required for direct index query") from exc
    searcher = LuceneSearcher(str(checkout / "search_engine" / "indexes_1k"))
    hits = searcher.search(keyword, k=k)
    if not hits:
        raise WebShopSmallContractError(
            "direct Lucene query returned no result for {!r}".format(keyword)
        )
    return {
        "keyword": keyword,
        "k": k,
        "hit_count": len(hits),
        "hits": [
            {"rank": rank, "docid": str(hit.docid), "score": float(hit.score)}
            for rank, hit in enumerate(hits, start=1)
        ],
        "index": index,
        "overall_pass": True,
    }


def validate_assets(
    checkout: Path,
    require_index: bool = True,
    expected_commit: str = EXPECTED_COMMIT,
    enforce_approved_fingerprints: bool = True,
) -> Dict[str, Any]:
    checkout_report = validate_checkout(checkout, expected_commit=expected_commit)
    data_report = validate_small_data(
        checkout,
        enforce_approved_fingerprints=enforce_approved_fingerprints,
    )
    report: Dict[str, Any] = {
        "schema": "webshop-small-assets/v2",
        "checkout": checkout_report,
        "data": {key: value for key, value in data_report.items() if key != "products"},
        "derived_search_keyword": derive_search_keyword(data_report["products"]),
        "require_index": require_index,
    }
    if require_index:
        report["index"] = validate_index(checkout)
    report["overall_pass"] = True
    return report


def write_json(payload: Mapping[str, Any], output: Optional[Path]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate bounded WebShop small-runtime assets")
    parser.add_argument("--checkout", type=Path)
    parser.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--build-resources", action="store_true")
    parser.add_argument("--no-index", action="store_true")
    parser.add_argument("--staging-dir", type=Path)
    parser.add_argument("--destination-dir", type=Path)
    parser.add_argument("--mirror-repository")
    parser.add_argument("--mirror-revision")
    parser.add_argument("--allow-checksum-mirror-fallback", action="store_true")
    parser.add_argument("--promote-staged-data", action="store_true")
    parser.add_argument("--query-index", action="store_true")
    parser.add_argument("--checkout-only", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.staging_dir is not None:
        required = {
            "destination_dir": args.destination_dir,
            "mirror_repository": args.mirror_repository,
            "mirror_revision": args.mirror_revision,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise WebShopSmallContractError(
                "staging validation missing argument(s): {}".format(", ".join(missing))
            )
        payload = validate_staging_and_promote(
            staging_dir=args.staging_dir,
            destination_dir=args.destination_dir,
            repository=args.mirror_repository,
            revision=args.mirror_revision,
            allow_checksum_mirror_fallback=args.allow_checksum_mirror_fallback,
            promote=args.promote_staged_data,
        )
    else:
        if args.checkout is None:
            raise WebShopSmallContractError("--checkout is required outside staging mode")
        if args.checkout_only:
            payload = validate_checkout(args.checkout, expected_commit=args.expected_commit)
            payload["overall_pass"] = True
        elif args.build_resources:
            payload = build_resources_1k(args.checkout, expected_commit=args.expected_commit)
            payload["overall_pass"] = True
        elif args.query_index:
            validate_checkout(args.checkout, expected_commit=args.expected_commit)
            payload = query_index_1k(args.checkout)
        else:
            payload = validate_assets(
                args.checkout,
                require_index=not args.no_index,
                expected_commit=args.expected_commit,
            )
    write_json(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
