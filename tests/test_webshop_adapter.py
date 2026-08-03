from __future__ import annotations

import ast
import builtins
import copy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters import (
    WebShopCommerceAdaptation,
    adapt_webshop_purchase_candidate,
)
from agentic_payment_experiment.adapters import webshop as webshop_adapter


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
EXPORT_HELPER = ROOT / "scripts/validation/webshop/export_webshop_commerce_fixture.py"
ADAPTER_PATH = ROOT / "src/agentic_payment_experiment/adapters/webshop.py"
EXPECTED_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
EXPECTED_SMOKE_SHA256 = "d1998c49a7afa14ee4534cd266d4e9e9c386ff2c2c8d85114aad19c304467e74"
EXPECTED_LIMITATIONS = {
    "instruction_product_match_not_assessed",
    "instruction_is_not_authorization_mandate",
    "merchant_and_payee_from_experiment_context",
    "no_runtime_authorization_decision",
    "no_purchase_or_payment_executed",
}


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class WebShopAdapterTest(unittest.TestCase):
    def assert_not_ready(
        self,
        fixture: dict[str, object],
        expected_field: str,
    ) -> WebShopCommerceAdaptation:
        adapted = adapt_webshop_purchase_candidate(fixture)
        self.assertFalse(adapted.ready)
        self.assertIsNone(adapted.order)
        self.assertIsNone(adapted.payment_request)
        self.assertIn(expected_field, adapted.missing_fields)
        return adapted

    def test_export_helper_reproduces_the_committed_single_item_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "fixture.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EXPORT_HELPER),
                    "--repo-root",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(FIXTURE_PATH.read_bytes(), output.read_bytes())
            summary = json.loads(completed.stdout)
            self.assertEqual(1, summary["product_count"])
            self.assertFalse(summary["buy_now_executed"])
            self.assertEqual(EXPECTED_COMMIT, summary["source_commit"])
            self.assertEqual(EXPECTED_SMOKE_SHA256, summary["source_smoke_sha256"])
            self.assertEqual(
                hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
                summary["fixture_sha256"],
            )

    def test_fixture_is_minimal_traceable_and_preserves_unrelated_facts(self) -> None:
        fixture = load_fixture()

        self.assertEqual("webshop-pre-buy-now-candidate/v1", fixture["fixture_schema"])
        self.assertEqual("v1", fixture["fixture_version"])
        self.assertEqual(EXPECTED_COMMIT, fixture["source"]["webshop_commit"])
        self.assertEqual(EXPECTED_SMOKE_SHA256, fixture["source"]["smoke_result_sha256"])
        self.assertTrue(fixture["source"]["provenance"]["immutable"])
        self.assertEqual("local_p9_a2_evidence", fixture["source"]["provenance"]["kind"])
        self.assertEqual(
            ["search[vhomes lights reclaimed]", "click[b06y3vldfb]"],
            fixture["actions_executed"],
        )
        self.assertTrue(fixture["buy_now_available"])
        self.assertFalse(fixture["buy_now_executed"])
        self.assertIn("cargo pants", fixture["instruction_text"])
        self.assertEqual("B06Y3VLDFB", fixture["product"]["asin"])
        self.assertIn("Vhomes Lights", fixture["product"]["title"])
        self.assertEqual("877.80", fixture["product"]["unit_price"])
        self.assertEqual("877.80", fixture["product"]["order_total"])
        self.assertEqual({}, fixture["product"]["selected_options"])
        self.assertEqual(
            "explicit_experiment_context_not_webshop_verified",
            fixture["experiment_context"]["origin"],
        )
        serialized = json.dumps(fixture, ensure_ascii=False).lower()
        self.assertNotIn("items_shuffle_1000.json\": [", serialized)
        self.assertNotIn("click[buy now]", serialized)

    def test_happy_path_maps_to_existing_neutral_order_and_request(self) -> None:
        fixture = load_fixture()
        adapted = adapt_webshop_purchase_candidate(fixture)

        self.assertTrue(adapted.ready)
        self.assertEqual((), adapted.missing_fields)
        self.assertEqual((), adapted.unmapped_fields)
        self.assertEqual(fixture["instruction_text"], adapted.user_intent_text)
        self.assertEqual(EXPECTED_COMMIT, adapted.source_commit)
        self.assertEqual(EXPECTED_SMOKE_SHA256, adapted.source_smoke_sha256)
        self.assertIsNotNone(adapted.order)
        self.assertIsNotNone(adapted.payment_request)
        order = adapted.order
        request = adapted.payment_request
        assert order is not None
        assert request is not None
        self.assertEqual(1, len(order.items))
        self.assertEqual("B06Y3VLDFB", order.items[0].item_id)
        self.assertIn("Vhomes Lights", order.items[0].name)
        self.assertEqual("home_furniture", order.items[0].category)
        self.assertEqual(1, order.items[0].quantity)
        self.assertEqual(Decimal("877.80"), order.items[0].unit_amount)
        self.assertEqual(Decimal("877.80"), order.total_amount)
        self.assertEqual("USD", order.currency)
        self.assertEqual("webshop-experiment-merchant-v1", order.merchant)
        self.assertEqual("webshop-experiment-payee-v1", order.payee)
        self.assertEqual(
            "explicit_experiment_context_not_webshop_verified",
            adapted.experiment_context_origin,
        )
        self.assertEqual((), adapted.selected_options)

    def test_ids_decimal_total_and_order_request_bindings_are_deterministic(self) -> None:
        fixture = load_fixture()
        first = adapt_webshop_purchase_candidate(fixture)
        second = adapt_webshop_purchase_candidate(copy.deepcopy(fixture))

        self.assertEqual(first, second)
        order = first.order
        request = first.payment_request
        assert order is not None
        assert request is not None
        self.assertEqual("webshop-order-9eccab2b0154fca4af27f322", order.order_id)
        self.assertEqual("webshop-request-6c6a78eddffdb552c2af66ef", request.request_id)
        self.assertEqual(order.order_id, request.order_ref)
        self.assertEqual(order.total_amount, request.amount)
        self.assertEqual(order.currency, request.currency)
        self.assertEqual(order.items[0].category, request.category)
        self.assertEqual(order.merchant, request.merchant)
        self.assertEqual(order.payee, request.payee)
        self.assertEqual(order.mandate_ref, request.authority_ref)
        self.assertEqual(order.authority_version_ref, request.authority_version_ref)

    def test_selected_options_are_preserved_in_sorted_metadata_and_item_name(self) -> None:
        fixture = load_fixture()
        fixture["product"]["selected_options"] = {
            "material": "wood",
            "finish": "natural",
        }

        adapted = adapt_webshop_purchase_candidate(fixture)

        self.assertTrue(adapted.ready)
        self.assertEqual(
            (("finish", "natural"), ("material", "wood")),
            adapted.selected_options,
        )
        assert adapted.order is not None
        self.assertTrue(
            adapted.order.items[0].name.endswith(
                "options: finish=natural, material=wood"
            )
        )

    def test_semantic_separation_limitations_are_explicit(self) -> None:
        adapted = adapt_webshop_purchase_candidate(load_fixture())

        self.assertTrue(EXPECTED_LIMITATIONS.issubset(set(adapted.limitations)))
        self.assertIn("cargo pants", adapted.user_intent_text)
        assert adapted.order is not None
        self.assertIn("Vhomes Lights", adapted.order.items[0].name)
        self.assertNotIn("matched", adapted.limitations)
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("IntentMandate", source)
        self.assertNotIn("Decision", source)
        self.assertNotIn("validate_request", source)

    def test_missing_or_empty_instruction_fails_closed(self) -> None:
        for value in (None, "", "   "):
            with self.subTest(value=value):
                fixture = load_fixture()
                fixture["instruction_text"] = value
                self.assert_not_ready(fixture, "instruction_text")

    def test_missing_product_currency_and_context_bridge_fields_fail_closed(self) -> None:
        cases = (
            (("product", "asin"), "product.asin"),
            (("product", "title"), "product.title"),
            (("product", "unit_price"), "product.unit_price"),
            (("experiment_context", "currency"), "experiment_context.currency"),
            (("experiment_context", "merchant"), "experiment_context.merchant"),
            (("experiment_context", "payee"), "experiment_context.payee"),
            (("experiment_context", "category"), "experiment_context.category"),
            (("experiment_context", "quote_expires_at"), "experiment_context.quote_expires_at"),
            (("experiment_context", "fulfilment_terms"), "experiment_context.fulfilment_terms"),
            (("experiment_context", "mandate_ref"), "experiment_context.mandate_ref"),
            (("experiment_context", "authority_version"), "experiment_context.authority_version"),
            (("experiment_context", "request_timestamp"), "experiment_context.request_timestamp"),
        )
        for (section, field), expected in cases:
            with self.subTest(field=expected):
                fixture = load_fixture()
                del fixture[section][field]
                self.assert_not_ready(fixture, expected)

    def test_malformed_nonpositive_or_non_string_prices_fail_closed(self) -> None:
        for value in ("not-money", "-1.00", "0.00", 877.80, True, "NaN", "Infinity"):
            with self.subTest(value=value):
                fixture = load_fixture()
                fixture["product"]["unit_price"] = value
                self.assert_not_ready(fixture, "product.unit_price")

    def test_zero_negative_noninteger_or_boolean_quantity_fails_closed(self) -> None:
        for value in (0, -1, 1.5, "1", True):
            with self.subTest(value=value):
                fixture = load_fixture()
                fixture["product"]["quantity"] = value
                self.assert_not_ready(fixture, "product.quantity")

    def test_total_must_equal_quantity_times_decimal_unit_price(self) -> None:
        fixture = load_fixture()
        fixture["product"]["quantity"] = 2
        fixture["product"]["order_total"] = "877.80"

        self.assert_not_ready(fixture, "product.order_total")

        fixture["product"]["order_total"] = "1755.60"
        adapted = adapt_webshop_purchase_candidate(fixture)
        self.assertTrue(adapted.ready)
        assert adapted.order is not None
        self.assertEqual(Decimal("1755.60"), adapted.order.total_amount)

    def test_selected_options_field_is_required_but_empty_mapping_is_allowed(self) -> None:
        fixture = load_fixture()
        del fixture["product"]["selected_options"]
        self.assert_not_ready(fixture, "product.selected_options")

        fixture = load_fixture()
        fixture["product"]["selected_options"] = {}
        self.assertTrue(adapt_webshop_purchase_candidate(fixture).ready)

    def test_wrong_commit_missing_or_mutable_provenance_fails_closed(self) -> None:
        fixture = load_fixture()
        fixture["source"]["webshop_commit"] = "0" * 40
        self.assert_not_ready(fixture, "source.webshop_commit")

        fixture = load_fixture()
        del fixture["source"]["provenance"]
        self.assert_not_ready(fixture, "source.provenance")

        fixture = load_fixture()
        fixture["source"]["provenance"]["immutable"] = False
        self.assert_not_ready(fixture, "source.provenance.immutable")

        fixture = load_fixture()
        fixture["source"]["smoke_result_sha256"] = "main"
        self.assert_not_ready(fixture, "source.smoke_result_sha256")

        fixture = load_fixture()
        fixture["source"]["smoke_result_sha256"] = "0" * 64
        self.assert_not_ready(fixture, "source.smoke_result_sha256")

        fixture = load_fixture()
        fixture["source"]["evidence_path"] = "main/latest-smoke.json"
        self.assert_not_ready(fixture, "source.evidence_path")

        fixture = load_fixture()
        fixture["source"]["asset_hashes"]["items_shuffle_1000.json"] = "latest"
        self.assert_not_ready(
            fixture,
            "source.asset_hashes.items_shuffle_1000.json",
        )

        fixture = load_fixture()
        fixture["source"]["asset_hashes"]["items_shuffle_1000.json"] = "0" * 64
        self.assert_not_ready(
            fixture,
            "source.asset_hashes.items_shuffle_1000.json",
        )

    def test_buy_now_availability_execution_and_action_sequence_are_gated(self) -> None:
        fixture = load_fixture()
        fixture["buy_now_available"] = False
        self.assert_not_ready(fixture, "buy_now_available")

        fixture = load_fixture()
        fixture["buy_now_executed"] = True
        self.assert_not_ready(fixture, "buy_now_executed")

        fixture = load_fixture()
        fixture["actions_executed"].append(" click[ Buy Now ] ")
        self.assert_not_ready(fixture, "actions_executed.buy_now_forbidden")

    def test_binding_mismatch_discards_both_neutral_objects(self) -> None:
        baseline = adapt_webshop_purchase_candidate(load_fixture())
        assert baseline.payment_request is not None
        mismatched = replace(
            baseline.payment_request,
            amount=baseline.payment_request.amount + Decimal("1.00"),
        )

        with patch.object(
            webshop_adapter,
            "_build_transaction_request",
            return_value=mismatched,
        ):
            adapted = adapt_webshop_purchase_candidate(load_fixture())

        self.assertFalse(adapted.ready)
        self.assertIsNone(adapted.order)
        self.assertIsNone(adapted.payment_request)
        self.assertEqual(("order_request_binding",), adapted.missing_fields)

    def test_unknown_top_level_fields_are_reported_not_trusted(self) -> None:
        fixture = load_fixture()
        fixture["webshop_reward"] = 1.0
        fixture["allow_purchase"] = True

        adapted = adapt_webshop_purchase_candidate(fixture)

        self.assertTrue(adapted.ready)
        self.assertEqual(
            ("top_level.allow_purchase", "top_level.webshop_reward"),
            adapted.unmapped_fields,
        )

    def test_result_is_immutable_and_equal_for_repeated_adaptation(self) -> None:
        first = adapt_webshop_purchase_candidate(load_fixture())
        second = adapt_webshop_purchase_candidate(load_fixture())

        self.assertEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.source_commit = "changed"  # type: ignore[misc]

    def test_adapter_performs_no_file_network_environment_or_process_action(self) -> None:
        fixture = load_fixture()
        with (
            patch.object(builtins, "open", side_effect=AssertionError("file access forbidden")) as open_mock,
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch.object(subprocess, "run", side_effect=AssertionError("process forbidden")) as run_mock,
            patch.object(os, "getenv", side_effect=AssertionError("environment forbidden")) as getenv_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            adapted = adapt_webshop_purchase_candidate(fixture)

        self.assertTrue(adapted.ready)
        open_mock.assert_not_called()
        socket_mock.assert_not_called()
        run_mock.assert_not_called()
        getenv_mock.assert_not_called()
        urlopen_mock.assert_not_called()

    def test_static_import_and_side_effect_boundary(self) -> None:
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)

        self.assertTrue(
            imported.issubset(
                {
                    "__future__",
                    "dataclasses",
                    "datetime",
                    "decimal",
                    "hashlib",
                    "typing",
                    "models",
                }
            ),
            imported,
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "write_text",
                    "write_bytes",
                    "getenv",
                    "Popen",
                    "run",
                    "urlopen",
                    "socket",
                    "step",
                    "done",
                    "evaluate",
                    "execute_payment",
                }
            ),
            called_names,
        )
        for forbidden_import in (
            "gym",
            "web_agent_site",
            "pyserini",
            "spacy",
            "torch",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "os",
            "pathlib",
        ):
            self.assertNotIn(forbidden_import, imported)

    def test_non_mapping_input_fails_closed(self) -> None:
        for value in (None, [], "fixture"):
            with self.subTest(value=value):
                adapted = adapt_webshop_purchase_candidate(value)  # type: ignore[arg-type]
                self.assertFalse(adapted.ready)
                self.assertEqual(("snapshot",), adapted.missing_fields)
                self.assertIsNone(adapted.order)
                self.assertIsNone(adapted.payment_request)


if __name__ == "__main__":
    unittest.main()
