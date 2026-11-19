"""Frozen observer checks; correct measurement may expose a product counterexample."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def preservation():
    baseline = read(P / "BASELINE.json")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD drift")
    for rel, digest in baseline["files"].items():
        need(sha(ROOT / rel) == digest, "protected drift: " + rel)
    for rel, digest in baseline["common_protected"].items():
        need(sha(ROOT.parent / "localagent-common" / rel) == digest, "shared workflow drift")
    for rel, digest in read(P / "FREEZE.json")["files"].items():
        need(sha(P / rel) == digest, "frozen measurement drift: " + rel)
    if (P / "evidence/ACCEPTED.json").exists():
        for rel, digest in read(P / "evidence/ACCEPTED.json")["files"].items():
            need(sha(ROOT / rel) == digest, "accepted drift")
    return {"protected": len(baseline["files"]), "source_code_changed": False}


def result(phase):
    data = read(P / "evidence" / (phase + "_measurement") / "RESULT.json")
    matrix = read(P / "SCENARIOS.json")
    need(data["phase"] == phase and data["schema"] == "h79-captured-fact-consumer-measurement/v1", "measurement schema/phase")
    need(data["matrix_sha256"] == sha(P / "SCENARIOS.json") and data["source_lock_sha256"] == sha(P / "SOURCE.json"), "input drift")
    need(data["time_mode"] == "CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION" and data["source_fact_status"] == "VALID", "historical source semantics")
    need([row["case_id"] for row in data["cases"]] == [row["id"] for row in matrix["cases"]], "lost/planted cases")
    stopped = False
    observed = 0
    for row, expected in zip(data["cases"], matrix["cases"]):
        if stopped:
            need(row == {"case_id": expected["id"], "status": "NOT_RUN_AFTER_COUNTEREXAMPLE"}, "must stop remaining probes")
            continue
        need(row["status"] == "OBSERVED" and row["consumer_input"] == expected, "probe input mismatch")
        observed += 1
        need(row["proof_status"] == "VALID" and row["binding_status"] == row["context_policy_status"] == "VALID", "confounded probe")
        matches = all(expected[key] == row["source_context"][key] for key in ("agent", "provider", "executor"))
        need(matches == row["source_context_matches_consumer"], "context classification mismatch")
        need(row["credential_ref_matches"] == (expected["credential_ref"] == "SOURCE"), "credential reference probe mismatch")
        wrong_verified = not matches and row["assurance"] == "VERIFIED"
        revoked = expected["identity_status"] == "revoked" and (row["identity_status"] != "INVALID" or row["callback_count"] != 0)
        need(row["context_counterexample"] == wrong_verified and row["revoked_guard_counterexample"] == revoked, "counterexample classification mismatch")
        if expected["id"] == "M01":
            need(row["assurance"] == "VERIFIED" and row["callback_count"] == 1, "positive control not reached")
        stopped = wrong_verified or revoked
    need(data["stopped_on_counterexample"] == stopped and observed >= 1, "stop accounting mismatch")
    need(all(data[key] == 0 for key in ("actual_payment_calls", "new_credentials", "new_issuer_runs", "network_calls")), "forbidden measurement effects")
    return {"observed_cases": observed, "stopped_on_counterexample": stopped, "finding_is_not_task_verdict": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preservation", "result"))
    parser.add_argument("--phase", choices=("executor", "evaluator"), default="executor")
    args = parser.parse_args()
    print(json.dumps(result(args.phase) if args.check == "result" else preservation()))
