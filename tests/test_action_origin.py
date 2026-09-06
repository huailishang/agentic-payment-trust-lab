from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.action_origin import (
    ActionOrigin,
    ActionOriginError,
    ActionOriginRecord,
    action_origin_records_to_primitive,
    classify_trace_event_origin,
    project_authoritative_trace_origins,
    project_autonomous_behavior_origins,
)


class ActionOriginTests(unittest.TestCase):
    def test_closed_enum_has_exactly_five_values(self) -> None:
        self.assertEqual(
            {item.value for item in ActionOrigin},
            {
                "USER_AUTHORITY",
                "AGENT_DECISION",
                "RUNTIME_DECISION",
                "EXTERNAL_FACT",
                "EXECUTION_RESULT",
            },
        )

    def test_autonomous_steps_project_to_agent_decisions_in_order(self) -> None:
        behavior = {
            "runs": [
                {
                    "steps": [
                        {
                            "chosen_action": "search[synthetic query]",
                            "sequence": 4,
                            "source": "SYNTHETIC_OBSERVATION",
                            "reason_summary": "derive a search action",
                        },
                        {
                            "chosen_action": "click[synthetic-result]",
                            "sequence": 5,
                            "source": "SYNTHETIC_OBSERVATION",
                            "reason_summary": "choose a visible result",
                        },
                    ]
                }
            ]
        }
        records = project_autonomous_behavior_origins(behavior)
        self.assertEqual(
            [record.action_origin for record in records],
            [ActionOrigin.AGENT_DECISION, ActionOrigin.AGENT_DECISION],
        )
        self.assertEqual(
            [record.action_or_event for record in records],
            ["search[synthetic query]", "click[synthetic-result]"],
        )
        self.assertEqual(
            [record.evidence_ref for record in records],
            [
                "autonomous_behavior:runs[0].steps[0].chosen_action",
                "autonomous_behavior:runs[0].steps[1].chosen_action",
            ],
        )

    def test_trace_projection_covers_five_origin_classes(self) -> None:
        events = [
            self._event(1, "AUTHORITY_RECORDED", "AUTHORITY"),
            self._event(2, "ORDER_RECORDED", "CURRENT_ORDER_SNAPSHOT"),
            self._event(3, "ACTION_RECORDED", "GOVERNED_ACTION"),
            self._event(4, "RUNTIME_DECISION_RECORDED", "RUNTIME_GATE_OBSERVATION"),
            self._event(5, "PAYMENT_OUTCOME_RECORDED", "PAYMENT_EXECUTION_OUTCOME"),
        ]
        records = project_authoritative_trace_origins({"events": events})
        self.assertEqual(
            {record.action_origin for record in records},
            set(ActionOrigin),
        )
        self.assertTrue(
            all(record.evidence_ref.startswith("authoritative_trace:events[") for record in records)
        )

    def test_order_snapshot_role_is_part_of_event_identity(self) -> None:
        records = project_authoritative_trace_origins(
            {
                "events": [
                    self._event(1, "ORDER_RECORDED", "AUTHORIZED_ORDER_SNAPSHOT"),
                    self._event(2, "ORDER_RECORDED", "CURRENT_ORDER_SNAPSHOT"),
                ]
            }
        )
        self.assertEqual(records[0].action_origin, ActionOrigin.USER_AUTHORITY)
        self.assertEqual(records[1].action_origin, ActionOrigin.EXTERNAL_FACT)
        self.assertEqual(
            records[1].action_or_event,
            "ORDER_RECORDED:CURRENT_ORDER_SNAPSHOT",
        )

    def test_runtime_binding_decision_is_runtime_decision(self) -> None:
        event = self._event(
            7,
            "ACTION_BINDING_DECISION_RECORDED",
            "ACTION_BINDING_FACT",
            status="VALID",
        )
        self.assertEqual(classify_trace_event_origin(event), ActionOrigin.RUNTIME_DECISION)

    def test_execution_outcomes_map_to_execution_result(self) -> None:
        for event_type, role in [
            ("PAYMENT_OUTCOME_RECORDED", "PAYMENT_EXECUTION_OUTCOME"),
            ("FULFILMENT_OUTCOME_RECORDED", "FULFILMENT_OUTCOME"),
            ("RESULT_RECORDED", "FINAL_OUTCOME"),
        ]:
            with self.subTest(event_type=event_type):
                self.assertEqual(
                    classify_trace_event_origin(self._event(9, event_type, role)),
                    ActionOrigin.EXECUTION_RESULT,
                )

    def test_unknown_event_or_role_fails_closed(self) -> None:
        with self.assertRaises(ActionOriginError):
            classify_trace_event_origin(self._event(1, "UNMAPPED_EVENT", "UNMAPPED_ROLE"))
        with self.assertRaises(ActionOriginError):
            classify_trace_event_origin(self._event(1, "AUTHORITY_RECORDED", "WRONG_ROLE"))

    def test_source_namespaces_stay_separate(self) -> None:
        autonomous = project_autonomous_behavior_origins(
            {"runs": [{"steps": [{"chosen_action": "search[q]", "sequence": 0}]}]}
        )
        authoritative = project_authoritative_trace_origins(
            {"events": [self._event(1, "ACTION_RECORDED", "GOVERNED_ACTION")]}
        )
        self.assertEqual(autonomous[0].source_namespace, "autonomous_behavior")
        self.assertEqual(authoritative[0].source_namespace, "authoritative_trace")
        self.assertNotEqual(autonomous[0].evidence_ref, authoritative[0].evidence_ref)

    def test_primitive_projection_is_json_serializable_and_deterministic(self) -> None:
        records = (
            ActionOriginRecord(
                action_origin=ActionOrigin.RUNTIME_DECISION,
                action_or_event="RUNTIME_DECISION_RECORDED",
                evidence_ref="authoritative_trace:events[3]",
                source_namespace="authoritative_trace",
                source_type="RuntimeRecord",
                sequence=4,
                entity_ref="RuntimeRecord:synthetic",
                decision="ALLOW",
                status="VALID",
            ),
        )
        first = action_origin_records_to_primitive(records)
        second = action_origin_records_to_primitive(records)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["action_origin"], "RUNTIME_DECISION")
        json.dumps(first, sort_keys=True)

    def test_invalid_projection_shapes_fail_closed(self) -> None:
        with self.assertRaises(ActionOriginError):
            project_autonomous_behavior_origins({"runs": []})
        with self.assertRaises(ActionOriginError):
            project_authoritative_trace_origins({"events": "not-a-list"})
        with self.assertRaises(ActionOriginError):
            action_origin_records_to_primitive([object()])

    @staticmethod
    def _event(
        sequence: int,
        event_type: str,
        entity_role: str,
        *,
        status: str | None = None,
    ) -> dict[str, object]:
        return {
            "sequence_no": sequence,
            "event_type": event_type,
            "entity_role": entity_role,
            "entity_type": "SyntheticEntity",
            "entity_ref": f"SyntheticEntity:{sequence}",
            "source_binding_ref": f"binding:{sequence}",
            "status": status,
        }


if __name__ == "__main__":
    unittest.main()
