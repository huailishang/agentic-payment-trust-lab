from dataclasses import replace

from agentic_payment_experiment.models import (
    DisputeRecord,
    DisputeStatus,
    PaymentRecoveryStatus,
    RemediationStatus,
)
from tests.test_payment_recovery import PaymentRecoveryTest
from tests.test_remediation import RemediationTest


recovery_case = PaymentRecoveryTest()
recovery_case.setUp()
for field in ("provider_ref", "payment_id", "order_id"):
    result = recovery_case.assess(
        observation=replace(recovery_case.observation, **{field: None})
    )
    print(
        f"query_missing_{field}={result.recovery_status.value},"
        f"retry={result.retry_allowed},next={result.next_action}"
    )
    assert result.recovery_status is PaymentRecoveryStatus.BLOCKED
    assert result.retry_allowed is False
    assert result.next_action == "investigate_status_observation_binding"

remediation_case = RemediationTest()
remediation_case.setUp()
for field in ("payment_id", "order_id"):
    refund_result = remediation_case.assess(
        refund=replace(remediation_case.scenario.refund, **{field: None})
    )
    print(
        f"refund_missing_{field}={refund_result.remediation.status.value},"
        f"next={refund_result.remediation.next_action}"
    )
    assert refund_result.remediation.status is RemediationStatus.REQUIRED
    assert (
        refund_result.remediation.next_action
        == "preserve_evidence_and_investigate_remediation_binding"
    )

base_dispute = DisputeRecord(
    dispute_id="dispute-rv",
    payment_id=remediation_case.scenario.payment_execution.payment_id,
    order_id=remediation_case.scenario.final_order.order_id,
    status=DisputeStatus.OPEN,
    opened_at=remediation_case.scenario.fulfillment.occurred_at,
)
for field in ("payment_id", "order_id"):
    dispute_result = remediation_case.assess(
        refund=None,
        dispute=replace(base_dispute, **{field: None}),
    )
    print(
        f"dispute_missing_{field}={dispute_result.remediation.status.value},"
        f"next={dispute_result.remediation.next_action}"
    )
    assert dispute_result.remediation.status is RemediationStatus.REQUIRED
    assert (
        dispute_result.remediation.next_action
        == "preserve_evidence_and_investigate_remediation_binding"
    )

valid_query = recovery_case.assess()
valid_refund = remediation_case.assess()
valid_dispute = remediation_case.assess(refund=None, dispute=base_dispute)
print(f"valid_query={valid_query.recovery_status.value}")
print(f"valid_refund={valid_refund.remediation.status.value}")
print(f"valid_dispute={valid_dispute.remediation.status.value}")
assert valid_query.recovery_status is PaymentRecoveryStatus.RECOVERED
assert valid_refund.remediation.status is RemediationStatus.RESOLVED
assert valid_dispute.remediation.status is RemediationStatus.IN_PROGRESS
