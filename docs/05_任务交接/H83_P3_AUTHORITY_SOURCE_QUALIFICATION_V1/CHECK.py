"""Frozen offline checks for the WebShop use-time credential experiment."""

from __future__ import annotations

import argparse
import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
LOCK = json.loads((TASK / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
GATE = "src/agentic_payment_experiment/webshop_runtime_gate.py"
FIXTURE = "tests/test_webshop_runtime_gate.py"
CONTEXT = ("h76-agent", "h76-provider", "h76-executor")
REPLAY_REASON = "webshop:credential_use_time_mismatch"
MISSING_REASON = "webshop:credential_use_time_missing_or_invalid"
INVALID_REASON = "webshop:credential_fact_invalid_type"
PROTECTED_DIRS = ("src", "tests", "samples", "scripts")

sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment import payment_execution
from agentic_payment_experiment.trusted_execution import create_confirmation_record
from agentic_payment_experiment.trusted_execution.credential_possession import (
    verify_x509_svid_credential_possession,
)


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_hashes(hashes):
    for name, expected in hashes.items():
        need(sha256((ROOT / name).read_bytes()).hexdigest() == expected, f"frozen file drift: {name}")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8").strip()


def preservation():
    freeze = json.loads((TASK / "FREEZE.json").read_text(encoding="utf-8"))
    verify_hashes(freeze["frozen_sha256"])
    verify_hashes(LOCK["protected_sha256"])
    need(git("rev-parse", "HEAD") == LOCK["baseline_head"], "baseline HEAD changed")
    tracked = git("diff", "--name-only", LOCK["baseline_head"], "--", *PROTECTED_DIRS)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *PROTECTED_DIRS)
    need(set(tracked.splitlines()) <= {GATE}, f"out-of-scope tracked changes: {tracked}")
    need(not untracked, f"out-of-scope untracked files: {untracked}")
    return {"protected": len(LOCK["protected_sha256"]), "product_changes": tracked.splitlines()}


def proof():
    source = ROOT / LOCK["source_directory"]
    data = json.loads((source / "RESULT.json").read_text(encoding="utf-8"))
    need(data["observed_at_epoch"] == LOCK["capture_epoch"], "capture epoch changed")
    fact = verify_x509_svid_credential_possession(
        leaf_svid_pem=(source / "leaf.pem").read_bytes(),
        trusted_ca_pem=(source / "root.pem").read_bytes(),
        expected_trust_domain="h76.test",
        expected_agent_ref=CONTEXT[0],
        expected_provider_ref=CONTEXT[1],
        expected_executor_instance_ref=CONTEXT[2],
        credential_ref="h79:captured-h78:" + data["run_id"],
        challenge_payload=(source / "payload.bin").read_bytes(),
        challenge_signature=base64.b64decode((source / "signature.b64").read_bytes().strip(), validate=True),
        nonce_ref=data["nonce"],
        issued_at_epoch=data["issued_at_epoch"],
        observed_at_epoch=data["observed_at_epoch"],
        max_age_seconds=300,
    )
    need(fact.status.name == "VALID", f"archived proof no longer verifies: {fact.reason_codes}")
    need(fact.observed_at_epoch == LOCK["capture_epoch"], "verifier observation mismatch")
    need(
        (fact.verified_agent_ref, fact.verified_provider_ref, fact.verified_executor_instance_ref) == CONTEXT,
        "verified context mismatch",
    )
    return fact


def fixture(fact):
    spec = spec_from_file_location("h83_webshop_fixture", ROOT / FIXTURE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    case = module.WebShopRuntimeGateTest()
    case.setUp()
    at = datetime.fromtimestamp(fact.observed_at_epoch, timezone.utc)
    order = replace(case.adaptation.order, quote_expires_at=at + timedelta(hours=2))
    request = replace(case.bound_request, agent_id=CONTEXT[0], occurred_at=at - timedelta(seconds=1))
    mandate = replace(case.mandate, expected_agent_id=CONTEXT[0], expires_at=at + timedelta(hours=2))
    identity = replace(
        case.identity,
        agent_id=CONTEXT[0],
        provider=CONTEXT[1],
        executor_instance_id=CONTEXT[2],
        credential_ref=fact.credential_ref,
    )
    return case, {
        "adaptation": replace(case.adaptation, order=order, payment_request=request),
        "mandate": mandate,
        "declared_agent_id": CONTEXT[0],
        "agent_identity": identity,
        "execution_candidate": replace(case.execution, agent_ref=CONTEXT[0], occurred_at=at),
        "current_provider_ref": CONTEXT[1],
        "current_executor_instance_ref": CONTEXT[2],
        "current_credential_ref": fact.credential_ref,
        "context_policy_fact": module.context_fact(mandate, order, request),
        "confirmation_record": create_confirmation_record(
            confirmation_id="h83-offline-confirmation",
            authority_id=mandate.mandate_id,
            authority_version=mandate.authority_version,
            order=order,
            confirmed_at=at - timedelta(minutes=10),
            expires_at=at + timedelta(hours=1),
        ),
    }


def observe(case, values, name, assurance, decision, callbacks, reason=None, **overrides):
    real_gate = payment_execution.execute_with_payment_binding_gate
    observations = []

    def observe_core(*args, **kwargs):
        outcome = real_gate(*args, **kwargs)
        observations.append(outcome)
        return outcome

    with patch.object(payment_execution, "execute_with_payment_binding_gate", side_effect=observe_core):
        result, calls = case.invoke(**(values | overrides))
    need(len(observations) == 1, f"{name}: WebShop must reach the unchanged P3 gate once")
    identity = observations[0].identity_fact
    need(identity.assurance_level.name == assurance, f"{name}: actual assurance {identity.assurance_level.name}")
    need(result.decision.name == decision, f"{name}: actual decision {result.decision.name}")
    need(len(calls) == result.callback_count == callbacks, f"{name}: callback count drift")
    need(reason is None or reason in result.reason_codes, f"{name}: missing reason {reason}")
    return {
        "case": name,
        "assurance": identity.assurance_level.name,
        "identity_status": identity.status.name,
        "decision": result.decision.name,
        "test_callbacks": result.callback_count,
        "reasons": list(result.reason_codes),
    }


def before():
    preservation()
    need(sha256((ROOT / GATE).read_bytes()).hexdigest() == LOCK["original_gate_sha256"], "original gate drift")
    fact = proof()
    case, values = fixture(fact)
    return {"observed_at_epoch": fact.observed_at_epoch, "rows": [
        observe(case, values, "baseline_original_webshop", "BOUND", "ALLOW", 1),
    ]}


def behavior(role):
    preservation()
    fact = proof()
    at = fact.observed_at_epoch
    case, values = fixture(fact)
    shift = 1 if role == "executor" else 301
    rows = [
        observe(case, values, "legacy", "BOUND", "ALLOW", 1),
        observe(case, values, "same_action_observation", "VERIFIED", "ALLOW", 1,
                credential_possession_fact=fact, credential_use_at_epoch=at),
        observe(case, values, "past_observation", "BOUND", "ALLOW", 1, REPLAY_REASON,
                credential_possession_fact=fact, credential_use_at_epoch=at + shift),
        observe(case, values, "missing_time", "BOUND", "ALLOW", 1, MISSING_REASON,
                credential_possession_fact=fact),
        observe(case, values, "invalid_time", "BOUND", "ALLOW", 1, MISSING_REASON,
                credential_possession_fact=fact, credential_use_at_epoch=True),
        observe(case, values, "invalid_fact", "BOUND", "ALLOW", 1, INVALID_REASON,
                credential_possession_fact={"observed_at_epoch": at}, credential_use_at_epoch=at),
        observe(case, values, "revoked_identity", "DECLARED", "DENY", 0,
                agent_identity=replace(values["agent_identity"], status="revoked"),
                credential_possession_fact=fact, credential_use_at_epoch=at),
    ]
    if role == "evaluator":
        rows.append(observe(
            case, values, "future_observation", "BOUND", "ALLOW", 1, REPLAY_REASON,
            credential_possession_fact=fact, credential_use_at_epoch=at - 1,
        ))
    return {
        "role": role,
        "archive_capture_epoch": at,
        "historical_replay_use_epoch": at + shift,
        "production_authority_state": "UNKNOWN",
        "rows": rows,
    }


def regressions():
    preservation()
    suites = {
        "tests": ("test_webshop_runtime_gate.py",),
        "tests/trusted_execution": (
            "test_credential_possession.py",
            "test_credential_context_consumption.py",
            "test_identity_assurance.py",
            "test_payment_binding.py",
            "test_signed_instruction_es256.py",
        ),
    }
    counts = {}
    for directory, patterns in suites.items():
        for pattern in patterns:
            suite = unittest.defaultTestLoader.discover(str(ROOT / directory), pattern=pattern)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            need(result.testsRun > 0 and result.wasSuccessful() and not result.skipped, f"regression: {pattern}")
            counts[pattern] = result.testsRun
    return {"regressions": counts, "total": sum(counts.values()), "skipped": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preservation", "before", "behavior", "regressions"))
    parser.add_argument("--role", choices=("executor", "evaluator"), default="executor")
    args = parser.parse_args()
    result = behavior(args.role) if args.check == "behavior" else globals()[args.check]()
    print(json.dumps({"check": args.check, **result}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
