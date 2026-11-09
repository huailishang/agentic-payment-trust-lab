"""One-shot local candidate packager for H46, no network and no upstream runtime.

Executes Executor.run_probe using the pinned source-slice oracle's injected methods.
It never invokes the frozen oracle's measure() wrapper or derives authority from Gold.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
BUNDLE = TASK / "candidate_bundle"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise ValueError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def produce_records() -> dict:
    oracle = load(TASK / "EVALUATOR_CHECK.py", "h46_pinned_local_oracle")
    executor = load(TASK / "MEASUREMENT.py", "h46_executor_packaging")
    ns, checks = oracle.source_slice()
    fixture = json.loads((TASK / "FIXTURE.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "src"))
    from agentic_payment_experiment.models import Decision
    from agentic_payment_experiment.payment_execution import execute_with_payment_binding_gate

    def new_account(case_id, repeat):
        return oracle.initial_account(ns)

    def send_money(account, **kwargs):
        return ns["send_money"](account, **kwargs)

    def evaluate(account):
        return oracle.score(checks, oracle.initial_account(ns), account)

    def missing_binding_probe():
        calls = []
        outcome = execute_with_payment_binding_gate(
            Decision.ALLOW, None, None, None, None, lambda: calls.append("checkout"))
        return {
            "decision": outcome.decision.value,
            "reason_codes": list(outcome.gate_reason_codes),
            "callback_count": len(calls),
            "executed": outcome.executed,
        }

    with oracle.no_network():
        result = executor.run_probe(
            cases=copy.deepcopy(fixture["cases"]), repeats=fixture["repeats"],
            new_account=new_account, send_money=send_money, evaluate=evaluate,
            missing_binding_probe=missing_binding_probe,
        )
    if len(result["records"]) != 8 or len(result["applicability"]) != 2:
        raise ValueError("unexpected frozen measurement record count")
    return result


def main():
    # This creates only task-owned portable candidate files; all source is frozen/read-only.
    result = produce_records()
    lock = json.loads((TASK / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    BUNDLE.mkdir(exist_ok=True)
    for name in ("FIXTURE.json", "SOURCE_LOCK.json", "DECISION.json", "verify_bundle.py"):
        shutil.copyfile(TASK / name, BUNDLE / name)
    for item in lock["files"]:
        source = TASK / item["path"]
        destination = BUNDLE / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    shutil.copyfile(TASK / "LIMITATIONS.md", BUNDLE / "LIMITATIONS.md")
    (BUNDLE / "README.md").write_text(
        "# H46 portable source-slice candidate (UNREVIEWED_CANDIDATE)\n\n"
        "AgentDojo release v0.1.35, commit `a75aba7631d3ca5fb7ab938965c97ead2f9ff84b`, "
        "v1 banking, MIT license: see `sources/LICENSE` and `SOURCE_LOCK.json`.\n\n"
        "Synthetic source-slice only: four deterministic scripted bank actions × two repeats, "
        "with original send_money, UserTask3.utility and InjectionTask5.security bodies extracted "
        "from these pinned source files. No model, full runtime, outside transaction or funds.\n\n"
        "Run with already-installed Python and Pydantic 2: "
        "`python verify_bundle.py .` after copying this folder elsewhere. "
        "The verifier checks membership, hashes, frozen inputs, source/license and independently "
        "recomputes all eight actual tool state transitions and score values. "
        "The two product missing-binding observations are **stored-only integrity checked**, "
        "not rerun in the portable verifier.\n\n"
        "Do not present this pack as an accepted third-party benchmark, full gate comparison "
        "or proof of production authorization. See `LIMITATIONS.md`, `DECISION.json`.\n",
        encoding="utf-8",
    )
    (BUNDLE / "records.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files = {
        p.relative_to(BUNDLE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in BUNDLE.rglob("*") if p.is_file() and p.name != "MANIFEST.json"
    }
    manifest = {
        "schema": "h46-portable-candidate-manifest/v1",
        "status": "UNREVIEWED_CANDIDATE",
        "task_id": "H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1",
        "measurement_level": "SOURCE_SLICE_WITH_SYNTHETIC_STATE_AND_SCRIPTED_ACTIONS",
        "files": dict(sorted(files.items())),
        "third_party_verified": False,
    }
    (BUNDLE / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verifier = load(BUNDLE / "verify_bundle.py", "h46_portable_local_selfcheck")
    verified = verifier.verify(BUNDLE)
    if verified != {"valid": True, "records": result}:
        raise AssertionError("packaged candidate failed local independent recomputation")
    print(json.dumps({
        "status": manifest["status"], "members": len(files),
        "records": len(result["records"]), "applicability": len(result["applicability"]),
        "portable_selfcheck": "PASS",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
