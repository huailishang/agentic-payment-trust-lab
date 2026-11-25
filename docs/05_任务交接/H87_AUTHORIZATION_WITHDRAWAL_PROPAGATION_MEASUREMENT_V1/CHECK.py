"""H87 frozen offline measurement of confirmation withdrawal propagation."""
import ast
from dataclasses import fields, replace
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
SUITES = {
    "tests.test_webshop_runtime_gate": 42,
    "tests.trusted_execution.test_credential_possession": 6,
    "tests.trusted_execution.test_credential_context_consumption": 6,
    "tests.trusted_execution.test_identity_assurance": 6,
    "tests.trusted_execution.test_payment_binding": 18,
    "tests.trusted_execution.test_signed_instruction_es256": 8,
    "tests.test_stripe_checkout_adapter": 7,
    "tests.test_stripe_authority_context": 16,
    "tests.test_stripe_checkout_lab": 6,
    "tests.trusted_execution.test_confirmation": 9,
}
RECORDS = (
    "docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/REVIEW.md",
    "docs/05_任务交接/H86_ACTUAL_CONSUMER_EVIDENCE_QUALIFICATION_V1/REVIEW.md",
)
CODE_FILES = (
    "src/agentic_payment_experiment/adapters/stripe_checkout.py",
    "src/agentic_payment_experiment/stripe_checkout_lab.py",
    "src/agentic_payment_experiment/trusted_execution/confirmation.py",
    "src/agentic_payment_experiment/models.py",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files():
    return sorted(p.relative_to(ROOT).as_posix()
                  for directory in ("src", "scripts", "tests")
                  for p in (ROOT / directory).rglob("*.py")
                  if "__pycache__" not in p.parts)


def preserve():
    lock = json.loads((TASK / "INPUTS.json").read_text(encoding="utf-8"))
    assert source_files() == lock["source_files"], "source file set changed"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    for name, expected in lock["files"].items():
        assert sha(ROOT / name) == expected, name
    print(json.dumps({"preservation": "PASS", "files": len(lock["files"])}))


def preflight():
    for name, expected in SUITES.items():
        suite = unittest.defaultTestLoader.loadTestsFromName(name)
        assert suite.countTestCases() == expected, name
        module = importlib.import_module(name)
        assert Path(module.__file__).resolve().is_relative_to(ROOT / "tests"), name
    assert sum(SUITES.values()) == 124
    print(json.dumps({"classification": "PREPARATION_ONLY", "test_count": 124,
                      "behavior_measurement_runs": 0, "formal_gates": 0}))


def interfaces():
    preserve()
    result = {}
    for name in CODE_FILES:
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        result[name] = [
            {"kind": type(node).__name__, "name": node.name, "line": node.lineno}
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    from agentic_payment_experiment.models import IntentMandate
    from agentic_payment_experiment.adapters.stripe_checkout import GateContext
    from agentic_payment_experiment.trusted_execution.confirmation import ConfirmationStatus
    print(json.dumps({"source_symbols": result,
                      "mandate_fields": [f.name for f in fields(IntentMandate)],
                      "context_fields": [f.name for f in fields(GateContext)],
                      "confirmation_states": [v.value for v in ConfirmationStatus]},
                     ensure_ascii=False, indent=2))


def counts(fixture):
    return {"provider_creates": len(fixture.client.created),
            "provider_queries": len(fixture.client.queries)}


def measure():
    preserve()
    from tests.test_stripe_authority_context import _Fixture, graph_sha
    from tests.test_stripe_checkout_adapter import NOW, SHA
    from agentic_payment_experiment.trusted_execution.confirmation import ConfirmationStatus

    fixture = _Fixture()
    fixture.setUp()
    try:
        fixture.ref = fixture.recorded()
        original = fixture.reopened().load_authority(
            "operation-h68", expected_sha256=fixture.ref)
        created = fixture.stored_create()
        fixture.store.bind_session("operation-h68", fixture.session())
        assert counts(fixture) == {"provider_creates": 1, "provider_queries": 0}
        changed = replace(original, confirmation_record=replace(
            original.confirmation_record, status=ConfirmationStatus.REVOKED))
        clicked = []
        direct_before = counts(fixture)
        direct = fixture.adapter.authorize_browser_payment(
            changed, session_id=created.session_id, now=NOW, browser_payment=clicked.append,
            resource_sha256=SHA, run_id="run-h68", operation_id="operation-h68")
        direct_observation = {
            "confirmation_status": changed.confirmation_record.status.value,
            "decision": direct.final_decision.value, "reasons": list(direct.reason_codes),
            "callback_count": direct.callback_count, "simulated_clicks": len(clicked),
            "before": direct_before, "after": counts(fixture),
        }
        assert not direct.callback_executed and clicked == [], "revoked direct input executed"
        assert counts(fixture) == direct_before, "revoked direct input reached provider"
        withdrawal_accepted = False
        update_error = None
        try:
            fixture.recorded(changed)
            withdrawal_accepted = True
        except Exception as error:
            from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
            if not isinstance(error, StripeCheckoutError):
                raise
            update_error = str(error)
        reloaded = fixture.reopened().load_authority(
            "operation-h68", expected_sha256=fixture.ref)
        before_pay = counts(fixture)
        stored = fixture.stored_pay(fixture.reopened(), clicked=clicked)
        stored_observation = {
            "withdrawal_input_accepted": withdrawal_accepted,
            "update_error": update_error,
            "original_graph_sha256": graph_sha(original),
            "reloaded_graph_sha256": graph_sha(reloaded),
            "reloaded_confirmation_status": reloaded.confirmation_record.status.value,
            "decision": stored.final_decision.value, "reasons": list(stored.reason_codes),
            "callback_count": stored.callback_count, "simulated_clicks": len(clicked),
            "before": before_pay, "after": counts(fixture),
            "classification": "REPRESENTABLE" if withdrawal_accepted else "NOT_REPRESENTABLE_VIA_RECORD_AUTHORITY",
        }
        assert not (withdrawal_accepted and stored.callback_executed), "accepted withdrawal reached effect"
        assert stored.callback_count == len(clicked)
        assert len(fixture.client.created) == 1, "measurement created a second session"
        print(json.dumps({
            "kind": "SYNTHETIC_LOCAL_CONFIRMATION_WITHDRAWAL",
            "fixed_time": NOW.isoformat(), "whole_mandate_revocation": "NOT_JUDGEABLE",
            "normal_session_creation": {"decision": created.gate.final_decision.value,
                                        "callbacks": created.gate.callback_count},
            "direct_revoked": direct_observation, "stored_after_attempt": stored_observation,
            "references": {"operation_id": "operation-h68", "authority_ref": original.mandate.mandate_id,
                           "authority_version": original.mandate.authority_version,
                           "confirmation_id": original.confirmation_record.confirmation_id,
                           "order_id": original.order.order_id, "request_id": original.request.request_id,
                           "payment_id": original.execution.payment_id},
        }, ensure_ascii=False, indent=2))
    finally:
        fixture.doCleanups()
        assert not fixture.db.exists(), "temporary database cleanup failed"
    preserve()


def regressions():
    preserve()
    total = 0
    for name, expected in SUITES.items():
        suite = unittest.defaultTestLoader.loadTestsFromName(name)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        assert result.wasSuccessful() and not result.skipped and result.testsRun == expected, name
        total += result.testsRun
    assert total == 124
    print(json.dumps({"passed": total, "skipped": 0}))
    preserve()


if __name__ == "__main__":
    commands = {"preflight": preflight, "preserve": preserve, "interfaces": interfaces,
                "measure": measure, "regressions": regressions}
    commands[sys.argv[1]]()
