from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import Decision
from agentic_payment_experiment.trusted_execution import (
    ReplayEvent,
    ReplayEventType,
    ReplaySourceType,
    ReplayStatus,
    RuntimeGateRecord,
    replay_events,
)


class ReplayTests(unittest.TestCase):
    def _event(self, event_id: str, event_type: ReplayEventType, previous: str | None, *, decision=Decision.ALLOW) -> ReplayEvent:
        return ReplayEvent(
            event_id=event_id,
            event_type=event_type,
            occurred_at=datetime(2026, 7, 11, 12, tzinfo=timezone.utc),
            subject_ref="user-1",
            agent_ref="agent-1",
            authority_ref="mandate-1",
            transaction_object_ref="request-1",
            payment_ref="payment-1",
            source_type=ReplaySourceType.SYSTEM_RUNTIME,
            source_ref=f"fixture:{event_id}",
            decision=decision,
            reason_codes=("fixture_reason",),
            previous_event_ref=previous,
            runtime_gate=(
                RuntimeGateRecord(
                    preliminary_decision=decision,
                    final_decision=decision,
                    binding_status="VALID",
                    binding_reason_codes=("binding_match",),
                    identity_status="VALID",
                    identity_reason_codes=("identity_match",),
                    context_policy_status="VALID",
                    context_policy_reason_codes=("context_match",),
                    callback_executed=decision is Decision.ALLOW,
                    callback_count=1 if decision is Decision.ALLOW else 0,
                    callback_result_ref="fixture-payment" if decision is Decision.ALLOW else None,
                    reason_codes=("fixture_reason",),
                )
                if event_type is ReplayEventType.RUNTIME_DECISION_RECORDED
                else None
            ),
        )

    def _chain(self) -> list[ReplayEvent]:
        types = (
            ReplayEventType.AUTHORITY_RECORDED,
            ReplayEventType.ORDER_RECORDED,
            ReplayEventType.REQUEST_RECORDED,
            ReplayEventType.RUNTIME_DECISION_RECORDED,
            ReplayEventType.PAYMENT_OUTCOME_RECORDED,
        )
        events: list[ReplayEvent] = []
        for index, event_type in enumerate(types):
            events.append(self._event(f"event-{index}", event_type, events[-1].event_id if events else None))
        return events

    def test_replays_complete_allow_chain_as_structured_facts(self) -> None:
        result = replay_events(self._chain())
        self.assertEqual(ReplayStatus.VALID, result.status)
        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertEqual(5, result.event_count)
        self.assertIn("ALLOW", result.explanation)

    def test_replays_confirmation_and_deny_from_recorded_decision(self) -> None:
        for decision in (Decision.CONFIRMATION_REQUIRED, Decision.DENY):
            with self.subTest(decision=decision):
                events = self._chain()
                events[3] = self._event("event-3", ReplayEventType.RUNTIME_DECISION_RECORDED, "event-2", decision=decision)
                events[4] = self._event("event-4", ReplayEventType.PAYMENT_OUTCOME_RECORDED, "event-3", decision=decision)
                result = replay_events(events)
                self.assertEqual(ReplayStatus.VALID, result.status)
                self.assertEqual(decision, result.decision)

    def test_rejects_unknown_enum_and_missing_reference(self) -> None:
        with self.assertRaises(ValueError):
            ReplayEvent(
                **{**self._chain()[0].__dict__, "event_type": "UNKNOWN"}
            )
        with self.assertRaises(ValueError):
            ReplayEvent(**{**self._chain()[0].__dict__, "agent_ref": ""})

    def test_fails_closed_for_broken_link_duplicate_and_reference_mismatch(self) -> None:
        broken = self._chain()
        broken[1] = self._event("event-1", ReplayEventType.ORDER_RECORDED, "wrong")
        self.assertEqual(ReplayStatus.INVALID, replay_events(broken).status)

        duplicate = self._chain()
        duplicate[1] = self._event("event-0", ReplayEventType.ORDER_RECORDED, "event-0")
        self.assertEqual(ReplayStatus.INVALID, replay_events(duplicate).status)

        mismatch = self._chain()
        mismatch[1] = ReplayEvent(**{**mismatch[1].__dict__, "subject_ref": "user-2"})
        self.assertEqual(ReplayStatus.INVALID, replay_events(mismatch).status)

    def test_marks_missing_required_event_as_indeterminate(self) -> None:
        result = replay_events(self._chain()[:-1])
        self.assertEqual(ReplayStatus.INDETERMINATE, result.status)
        self.assertIn("missing_required_event", result.reason_codes[0])


if __name__ == "__main__":
    unittest.main()
