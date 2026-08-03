from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

from scripts.validation.webshop.verify_webshop_small_assets import (
    APPROVED_MIRRORS,
    AssetSpec,
    WebShopSmallContractError,
    build_resources_1k,
    validate_asset_file,
    validate_assets,
    validate_execution_plan,
    validate_mirror_source,
    validate_small_data,
    validate_staging_and_promote,
)


class WebShopSmallRuntimeContractTest(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repo), *args),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail(
                "git command failed: {}\nstdout={}\nstderr={}".format(
                    args, result.stdout, result.stderr
                )
            )
        return result.stdout.strip()

    def create_fixture(self, root: Path, product_count: int = 1000) -> Tuple[Path, str]:
        checkout = root / "webshop"
        checkout.mkdir(parents=True)
        self.run_git(checkout, "init")
        self.run_git(checkout, "config", "user.name", "WebShop Small Contract Test")
        self.run_git(
            checkout,
            "config",
            "user.email",
            "webshop-small-contract@example.invalid",
        )
        (checkout / ".gitignore").write_text(
            "data/\nsearch_engine/resources_1k/\nsearch_engine/indexes_1k/\n",
            encoding="utf-8",
        )
        (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
        self.run_git(checkout, "add", ".gitignore", "README.md")
        self.run_git(checkout, "commit", "-m", "fixture source")
        commit = self.run_git(checkout, "rev-parse", "HEAD")

        data_dir = checkout / "data"
        data_dir.mkdir()
        products: List[Dict[str, Any]] = []
        attributes: List[Dict[str, Any]] = []
        for index in range(product_count):
            asin = "A{:09d}".format(index)
            products.append(
                {
                    "asin": asin,
                    "Title": "Fixture Product {}".format(index),
                    "Description": "Description {}".format(index),
                    "BulletPoints": ["Bullet {}".format(index)],
                    "options": {"size": ["small", "large"]},
                }
            )
            attributes.append({"asin": asin, "attributes": ["fixture"]})
        (data_dir / "items_shuffle_1000.json").write_text(
            json.dumps(products), encoding="utf-8"
        )
        (data_dir / "items_ins_v2_1000.json").write_text(
            json.dumps(attributes), encoding="utf-8"
        )
        (data_dir / "items_human_ins.json").write_text(
            json.dumps([{"instruction": "fixture"}]), encoding="utf-8"
        )

        resources = checkout / "search_engine" / "resources_1k"
        resources.mkdir(parents=True)
        (resources / "documents.jsonl").write_text("{}\n", encoding="utf-8")
        indexes = checkout / "search_engine" / "indexes_1k"
        indexes.mkdir(parents=True)
        (indexes / "segments_1").write_bytes(b"fixture-index")
        return checkout, commit

    @staticmethod
    def tiny_spec(path: Path, json_type: str, count: int) -> AssetSpec:
        return AssetSpec(
            filename=path.name,
            google_drive_id="fixture-id",
            byte_length=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            json_type=json_type,
            top_level_count=count,
        )

    def test_missing_one_small_data_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, commit = self.create_fixture(Path(temp_dir))
            (checkout / "data" / "items_human_ins.json").unlink()
            with self.assertRaisesRegex(
                WebShopSmallContractError, "items_human_ins.json"
            ):
                validate_assets(
                    checkout,
                    expected_commit=commit,
                    enforce_approved_fingerprints=False,
                )

    def test_product_count_other_than_1000_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, commit = self.create_fixture(Path(temp_dir), product_count=999)
            with self.assertRaisesRegex(WebShopSmallContractError, "product count mismatch"):
                validate_assets(
                    checkout,
                    expected_commit=commit,
                    enforce_approved_fingerprints=False,
                )

    def test_missing_indexes_1k_fails_before_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, commit = self.create_fixture(Path(temp_dir))
            (checkout / "search_engine" / "indexes_1k" / "segments_1").unlink()
            (checkout / "search_engine" / "indexes_1k").rmdir()
            with self.assertRaisesRegex(WebShopSmallContractError, "missing indexes_1k"):
                validate_assets(
                    checkout,
                    expected_commit=commit,
                    enforce_approved_fingerprints=False,
                )

    def test_checkout_at_wrong_commit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, _ = self.create_fixture(Path(temp_dir))
            with self.assertRaisesRegex(WebShopSmallContractError, "commit mismatch"):
                validate_assets(
                    checkout,
                    expected_commit="0" * 40,
                    enforce_approved_fingerprints=False,
                )

    def test_execution_plan_with_buy_now_fails_closed(self) -> None:
        with self.assertRaisesRegex(WebShopSmallContractError, "forbidden"):
            validate_execution_plan(
                ["search[fixture]", "click[a000000000]", " click[ Buy Now ] "]
            )

    def test_valid_fixture_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, commit = self.create_fixture(Path(temp_dir))
            report = validate_assets(
                checkout,
                expected_commit=commit,
                enforce_approved_fingerprints=False,
            )
        self.assertTrue(report["overall_pass"])
        self.assertEqual(1000, report["data"]["product_count"])
        self.assertEqual(1, report["index"]["index_file_count"])
        self.assertEqual("fixture product", report["derived_search_keyword"])

    def test_build_resources_writes_only_1k_document_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, commit = self.create_fixture(Path(temp_dir))
            report = build_resources_1k(
                checkout,
                expected_commit=commit,
                enforce_approved_fingerprints=False,
            )
            documents = checkout / "search_engine" / "resources_1k" / "documents.jsonl"
            lines = documents.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1000, report["document_count"])
        self.assertEqual(1000, len(lines))
        self.assertFalse((checkout / "search_engine" / "resources").exists())
        self.assertFalse((checkout / "search_engine" / "resources_100").exists())
        self.assertFalse((checkout / "search_engine" / "resources_100k").exists())

    def test_valid_data_can_be_checked_without_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout, _ = self.create_fixture(Path(temp_dir))
            report = validate_small_data(
                checkout,
                enforce_approved_fingerprints=False,
            )
        self.assertEqual(1000, report["product_count"])
        self.assertEqual(1000, report["unique_product_asins"])

    def test_mutable_main_mirror_url_is_rejected(self) -> None:
        with self.assertRaisesRegex(WebShopSmallContractError, "mutable"):
            validate_mirror_source(
                repository="YWZBrandon/webshop-data",
                revision="main",
                url=(
                    "https://huggingface.co/datasets/YWZBrandon/webshop-data/resolve/"
                    "main/items_shuffle_1000.json"
                ),
                allow_checksum_mirror_fallback=True,
            )

    def test_unapproved_repository_or_revision_is_rejected(self) -> None:
        with self.assertRaisesRegex(WebShopSmallContractError, "unapproved mirror repository"):
            validate_mirror_source(
                repository="unknown/webshop",
                revision="0" * 40,
                url="https://huggingface.co/unknown/webshop/resolve/{}/items_shuffle_1000.json".format(
                    "0" * 40
                ),
                allow_checksum_mirror_fallback=True,
            )
        mirror = APPROVED_MIRRORS["YWZBrandon/webshop-data"]
        with self.assertRaisesRegex(WebShopSmallContractError, "unapproved mirror revision"):
            validate_mirror_source(
                repository=mirror.repository,
                revision="0" * 40,
                url=mirror.base_url + "items_shuffle_1000.json",
                allow_checksum_mirror_fallback=True,
            )

    def test_fallback_switch_is_required(self) -> None:
        mirror = APPROVED_MIRRORS["YWZBrandon/webshop-data"]
        with self.assertRaisesRegex(WebShopSmallContractError, "disabled"):
            validate_mirror_source(
                repository=mirror.repository,
                revision=mirror.revision,
                url=mirror.base_url + "items_shuffle_1000.json",
                allow_checksum_mirror_fallback=False,
            )

    def test_valid_pinned_mirror_metadata_passes(self) -> None:
        mirror = APPROVED_MIRRORS["YWZBrandon/webshop-data"]
        report = validate_mirror_source(
            repository=mirror.repository,
            revision=mirror.revision,
            url=mirror.base_url + "items_shuffle_1000.json",
            allow_checksum_mirror_fallback=True,
        )
        self.assertEqual(mirror.repository, report["repository"])
        self.assertEqual(mirror.revision, report["revision"])
        self.assertEqual("items_shuffle_1000.json", report["filename"])

    def test_wrong_bytes_hash_type_or_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.json"
            path.write_text('[{"a": 1}]', encoding="utf-8")
            valid = self.tiny_spec(path, "list", 1)
            self.assertEqual(1, validate_asset_file(path, valid)["top_level_count"])

            wrong_bytes = AssetSpec(**{**valid.__dict__, "byte_length": valid.byte_length + 1})
            with self.assertRaisesRegex(WebShopSmallContractError, "byte length"):
                validate_asset_file(path, wrong_bytes)

            wrong_hash = AssetSpec(**{**valid.__dict__, "sha256": "0" * 64})
            with self.assertRaisesRegex(WebShopSmallContractError, "SHA-256"):
                validate_asset_file(path, wrong_hash)

            wrong_type = AssetSpec(**{**valid.__dict__, "json_type": "dict"})
            with self.assertRaisesRegex(WebShopSmallContractError, "JSON type"):
                validate_asset_file(path, wrong_type)

            wrong_count = AssetSpec(**{**valid.__dict__, "top_level_count": 2})
            with self.assertRaisesRegex(WebShopSmallContractError, "top-level count"):
                validate_asset_file(path, wrong_count)

    def test_invalid_staging_is_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging = root / "staging"
            destination = root / "data"
            staging.mkdir()
            (staging / "unexpected.json").write_text("{}", encoding="utf-8")
            mirror = APPROVED_MIRRORS["YWZBrandon/webshop-data"]
            with self.assertRaises(WebShopSmallContractError):
                validate_staging_and_promote(
                    staging_dir=staging,
                    destination_dir=destination,
                    repository=mirror.repository,
                    revision=mirror.revision,
                    allow_checksum_mirror_fallback=True,
                    promote=True,
                )
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
