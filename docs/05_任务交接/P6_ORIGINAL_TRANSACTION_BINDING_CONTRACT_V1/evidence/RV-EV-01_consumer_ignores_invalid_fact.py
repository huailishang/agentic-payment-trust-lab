from dataclasses import replace

from tests.test_payment_recovery import PaymentRecoveryTest
from tests.test_remediation import RemediationTest
from agentic_payment_experiment.models import PaymentStatus


recovery_case = PaymentRecoveryTest()
recovery_case.setUp()
missing_provider = replace(
    recovery_case.observation,
    provider_ref=None,
    status=PaymentStatus.SUCCEEDED,
)
recovery = recovery_case.assess(observation=missing_provider)

remediation_case = RemediationTest()
remediation_case.setUp()
missing_payment_refund = replace(remediation_case.scenario.refund, payment_id=None)
remediation = remediation_case.assess(refund=missing_payment_refund)

print(f"query_recovery={recovery.recovery_status.value}")
print(f"query_next_action={recovery.next_action}")
print(f"refund_remediation={remediation.remediation.status.value}")
print(f"refund_next_action={remediation.remediation.next_action}")

assert recovery.recovery_status.value != "RECOVERED"
assert remediation.remediation.status.value != "RESOLVED"
