"""Replay only H79's two observed slots using immutable pre-H80 modules."""
import argparse
from dataclasses import replace
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import CHECK
from RUN_SUPPORT import P, ROOT, active


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    active(parser.parse_args().phase)
    CHECK.need(sys.platform == "win32", "native Windows only")
    lock = CHECK.read(P / "BEFORE_LOCK.json")
    paths = {name: ROOT / item["path"] for name, item in lock["modules"].items()}
    for name, path in paths.items():
        CHECK.need(name not in sys.modules and CHECK.sha(path) == lock["modules"][name]["sha256"], "old source must be loaded first and match frozen bytes")

    class FrozenBeforeFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname in paths:
                return importlib.util.spec_from_file_location(fullname, paths[fullname])
            return None

    # A fresh child process loads both old modules consistently through normal imports.
    # No live file, enum, function, verifier output or signature result is patched.
    sys.meta_path.insert(0, FrozenBeforeFinder())
    from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession
    for name, path in paths.items():
        CHECK.need(Path(sys.modules[name].__file__).resolve() == path.resolve(), "wrong baseline module origin")
    source, data, values = CHECK.proof_values()
    fact = verify_x509_svid_credential_possession(**values)
    CHECK.need(fact.status.name == "VALID" and all((fact.credential_valid, fact.subject_binding_valid, fact.proof_of_possession_valid, fact.freshness_valid)) and not fact.replay_detected, "historical baseline proof invalid")
    fixture_path = ROOT / lock["fixture"]["path"]
    CHECK.need(CHECK.sha(fixture_path) == lock["fixture"]["sha256"], "old fixture drift")
    spec = importlib.util.spec_from_file_location("h81_before_payment_fixture", fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    rows = []
    for case_id, agent in (("M01", "h76-agent"), ("M02", "h79-other-agent")):
        case = fixture.PaymentExecutionBindingTests()
        case.setUp()
        provider, executor = "h76-provider", "h76-executor"
        case.mandate = replace(case.mandate, expected_agent_id=agent)
        case.request = replace(case.request, agent_id=agent)
        case.payment = replace(case.payment, agent_ref=agent)
        case.identity = replace(case.identity, agent_id=agent, provider=provider, executor_instance_id=executor, credential_ref=values["credential_ref"], status="active")
        outcome, calls = case.execute(identity=case.identity, provider_ref=provider, executor_ref=executor, credential_ref=values["credential_ref"], credential_possession_fact=fact)
        row = {"case_id": case_id, "consumer": {"agent": agent, "request_agent": agent, "provider": provider, "executor": executor, "credential_ref": values["credential_ref"], "status": "active"}, "identity_status": outcome.identity_fact.status.name, "assurance": outcome.identity_fact.assurance_level.name, "identity_reasons": list(outcome.identity_fact.reason_codes), "decision": outcome.decision.name, "callbacks": len(calls), "binding": outcome.binding_fact.status.name, "context_policy": outcome.context_policy_fact.status.name}
        CHECK.need(row["identity_status"] == "VALID" and row["assurance"] == "VERIFIED", "signed H79 baseline no longer reproduces")
        CHECK.need(row["binding"] == row["context_policy"] == "VALID" and row["decision"] == "ALLOW" and row["callbacks"] == 1, "confounded baseline")
        rows.append(row)
    print(json.dumps({"schema": "h81-before-observed-pair/v1", "source_run_id": data["run_id"], "observed_at_epoch": data["observed_at_epoch"], "challenge_payload_sha256": CHECK.sha(source / "payload.bin"), "source_fact_status": fact.status.name, "module_origins": {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": CHECK.sha(path)} for name, path in paths.items()}, "rows": rows, "time_mode": "CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION", "actual_payment_calls": 0, "new_issuer_runs": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
