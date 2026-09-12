from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for search_path in (ROOT / "src", ROOT / "scripts" / "validation" / "webshop"):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

import run_same_journey_remediation_closure as h21

from agentic_payment_experiment.action_origin import (
    action_origin_records_to_primitive,
    project_authoritative_trace_origins,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.authoritative_trace_consumer import (
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.remediation import assess_remediation
from agentic_payment_experiment.trusted_execution import verify_original_transaction
from agentic_payment_experiment.webshop_remediation_trace import (
    extend_product_authoritative_trace_with_remediation,
)


H20 = ROOT / "docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/H20_LIFECYCLE_BRANCH_RESULT.json"
MATRIX = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evaluator_fixtures/REMEDIATION_CLOSURE_MATRIX.json"


class WebShopRemediationTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.h20 = json.loads(H20.read_text(encoding="utf-8"))
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.parent = h21.reconstruct_parent_journey(cls.h20, cls.matrix)

    def _measure_case(self, case_index: int):
        case = self.matrix["cases"][case_index]
        action, refund, dispute = h21.build_follow_up(case, self.parent["payment"])
        observation = refund if refund is not None else dispute
        assert observation is not None
        closure = assess_remediation(
            self.parent["order"],
            self.parent["payment"],
            self.parent["lifecycle"],
            refund=refund,
            dispute=dispute,
        )
        binding_fact = verify_original_transaction(
            action,
            self.parent["payment"],
            observation,
        )
        trace = extend_product_authoritative_trace_with_remediation(
            self.parent["authoritative_trace"],
            observation,
            binding_fact,
            closure,
        )
        return case, observation, binding_fact, closure, trace

    def test_all_five_branches_use_one_valid_source_bound_extension(self) -> None:
        expected_source_types = (
            "RefundRecord",
            "RefundRecord",
            "DisputeRecord",
            "DisputeRecord",
            "RefundRecord",
        )
        for index, source_type in enumerate(expected_source_types):
            with self.subTest(index=index):
                _, _, binding_fact, _, trace = self._measure_case(index)
                self.assertIsNotNone(trace)
                assert trace is not None
                validation = validate_product_authoritative_trace(trace)
                self.assertEqual(TraceValidationStatus.VALID, validation.status)

                consumed = consume_authoritative_trace(trace)
                self.assertIsNotNone(consumed.read_model)
                primitive = trace_read_model_to_primitive(consumed.read_model)
                events = {item["entity_role"]: item for item in primitive["events"]}
                bindings = {
                    item["binding_ref"]: item for item in primitive["source_bindings"]
                }

                observation_event = events["REMEDIATION_OBSERVATION"]
                binding_event = events["ORIGINAL_TRANSACTION_BINDING_FACT"]
                closure_event = events["REMEDIATION_CLOSURE_OUTCOME"]
                self.assertEqual(
                    source_type,
                    bindings[observation_event["source_binding_ref"]]["source_object_type"],
                )
                self.assertEqual(
                    "OriginalTransactionBindingFact",
                    bindings[binding_event["source_binding_ref"]]["source_object_type"],
                )
                self.assertEqual(
                    binding_fact.status.value,
                    binding_event["status"],
                )
                self.assertEqual(
                    "LifecycleResult",
                    bindings[closure_event["source_binding_ref"]]["source_object_type"],
                )

                origins = action_origin_records_to_primitive(
                    project_authoritative_trace_origins(primitive)
                )
                origin_by_role = {
                    primitive["events"][item["sequence"] - 1]["entity_role"]: item[
                        "action_origin"
                    ]
                    for item in origins
                    if item["sequence"] is not None
                }
                self.assertEqual(
                    "EXTERNAL_FACT", origin_by_role["REMEDIATION_OBSERVATION"]
                )
                self.assertEqual(
                    "RUNTIME_DECISION",
                    origin_by_role["ORIGINAL_TRANSACTION_BINDING_FACT"],
                )
                self.assertEqual(
                    "EXECUTION_RESULT",
                    origin_by_role["REMEDIATION_CLOSURE_OUTCOME"],
                )

    def test_invalid_payment_binding_is_recorded_without_false_payment_relation(self) -> None:
        _, observation, binding_fact, _, trace = self._measure_case(4)
        self.assertEqual("INVALID", binding_fact.status.value)
        self.assertIn(
            "original_transaction_payment_ref_mismatch", binding_fact.reason_codes
        )
        self.assertTrue(observation.payment_id.endswith("-mismatch"))
        self.assertIsNotNone(trace)
        assert trace is not None
        observation_event = next(
            item for item in trace.events if item.entity_role == "REMEDIATION_OBSERVATION"
        )
        self.assertEqual(
            {"CURRENT_ORDER_SNAPSHOT"},
            {item.target_entity_role for item in observation_event.relations},
        )
        self.assertNotIn(
            "PAYMENT_EXECUTION_OUTCOME",
            {item.target_entity_role for item in observation_event.relations},
        )
        self.assertEqual(
            TraceValidationStatus.VALID,
            validate_product_authoritative_trace(trace).status,
        )

    def test_malformed_cross_source_closure_fails_closed(self) -> None:
        _, observation, binding_fact, closure, _ = self._measure_case(0)
        wrong_closure = replace(
            closure,
            remediation=replace(closure.remediation, case_ref="wrong-remediation-case"),
        )
        self.assertIsNone(
            extend_product_authoritative_trace_with_remediation(
                self.parent["authoritative_trace"],
                observation,
                binding_fact,
                wrong_closure,
            )
        )

    def test_malformed_follow_up_binding_fails_closed(self) -> None:
        _, observation, binding_fact, closure, _ = self._measure_case(0)
        wrong_fact = replace(binding_fact, follow_up_order_ref="wrong-order")
        self.assertIsNone(
            extend_product_authoritative_trace_with_remediation(
                self.parent["authoritative_trace"],
                observation,
                wrong_fact,
                closure,
            )
        )


if __name__ == "__main__":
    unittest.main()
