"""Frozen H77 checks. Executor implements only RUN.py and its task-local helpers."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from AUDIT import OLD, ROOT, SOURCE, crypto, need, read, sha

P = Path(__file__).resolve().parent


def preservation():
    baseline = read(P / "BASELINE.json")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD drift")
    for rel, digest in baseline["protected"].items():
        need((ROOT / rel).is_file() and sha(ROOT / rel) == digest, "protected file: " + rel)
    for rel, digest in baseline["common_protected"].items():
        need(sha(ROOT.parent / "localagent-common" / rel) == digest, "common workflow drift: " + rel)
    for rel, digest in read(P / "FREEZE.json")["files"].items():
        need(sha(P / rel) == digest, "frozen file: " + rel)
    return {"protected": len(baseline["protected"]), "historical_bytes_unchanged": True}


def historical():
    for rel, digest in read(SOURCE / "EVIDENCE_INDEX.json")["public_files"].items():
        need(sha(SOURCE / rel) == digest, "H76 public index: " + rel)
    for rel, digest in read(P / "evidence/preparation/H76_INPUT_SEAL.json")["files"].items():
        need(sha(ROOT / rel) == digest, "H76 accepted input: " + rel)
    result = crypto(SOURCE)
    need(b"PermissionDenied" in (SOURCE / "nonmatching.stderr.log").read_bytes(), "historical RPC log")
    return {"historical": result, "fresh_issuance": False, "h76_formal_pass": False}


def output():
    result = (P / read(P / "evidence/evaluator_current.json")["output"]).resolve()
    need(result.is_relative_to((P / "evidence/evaluator_runs").resolve()), "output escape")
    return result


def live():
    preservation()
    import yaml
    router = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    need(router["task_id"] == P.name and router["state"] == "READY_FOR_REVIEW" and router["current_role"] == "Evaluator", "only accepted Evaluator may issue")
    for field in ("authorization_local_service", "authorization_ephemeral_test_credentials", "authorization_existing_wsl"):
        need(router.get(field) is True, "missing inherited authority: " + field)
    acceptance = read(P / "evidence/ACCEPTED.json")
    for rel, digest in acceptance["files"].items():
        need(sha(ROOT / rel) == digest, "accepted snapshot drift: " + rel)
    l2_path = (ROOT / acceptance["l2_gate_path"]).resolve()
    need(l2_path in [(P / "evidence" / name / "L2-GATE.json").resolve() for name in ("l2", "l2_retry_02")], "accepted L2 path")
    need(l2_path.relative_to(ROOT).as_posix() in acceptance["files"], "accepted L2 must be sealed")
    l2 = read(l2_path)
    need(l2.get("mandatory_failures") == 0 and l2.get("result") == "PASS", "accepted L2 must pass")
    marker = P / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json"
    run_id, nonce = uuid.uuid4().hex, uuid.uuid4().hex
    begin = int(datetime.now(timezone.utc).timestamp())
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"run_id": run_id, "nonce": nonce, "begin_epoch": begin, "state": "STARTED", "budget_consumed": 1}, stream)
    out = P / "evidence/evaluator_runs" / run_id
    out.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run([sys.executable, "-B", str(P / "RUN.py"), "collect", "--run-id", run_id, "--nonce", nonce, "--out", out.relative_to(ROOT).as_posix()], cwd=ROOT, timeout=1250, check=False)
    need(completed.returncode == 0, "independent issuance failed; preserve and stop, no retry")
    end = int(datetime.now(timezone.utc).timestamp())
    data = read(out / "RESULT.json")
    need(data["run_id"] == run_id and data["nonce"] == nonce and begin <= data["issued_at_epoch"] <= end, "independent fresh challenge")
    need(begin <= data["observed_at_epoch"] <= end and 0 <= data["observed_at_epoch"] - data["issued_at_epoch"] <= 300, "real collection observation window")
    need(nonce != read(SOURCE / "RESULT.json")["nonce"], "old nonce reused")
    (P / "evidence/evaluator_current.json").write_text(json.dumps({"output": out.relative_to(P).as_posix(), "run_id": run_id, "nonce": nonce}) + "\n", encoding="utf-8")
    result = verify("evaluator")
    (out / "EVALUATOR_TIME_WINDOW.json").write_text(json.dumps({"begin_epoch": begin, "end_epoch": end}) + "\n", encoding="utf-8")
    return result


def verify(phase):
    if phase == "executor":
        return historical()
    out = output()
    result = crypto(out)
    need(result["root_der_sha256"] != crypto(SOURCE)["root_der_sha256"], "old management root reused")
    for rel, digest in read(out / "PUBLIC_INDEX.json")["files"].items():
        path = (out / rel).resolve()
        need(path.is_relative_to(out) and path.is_file() and sha(path) == digest, "public file seal: " + rel)
    denied = (out / "nonmatching.stderr.log").read_text(encoding="utf-8")
    need("PermissionDenied" in denied and "no identity issued" in denied, "actual Workload API rejection")
    need("connect: permission denied" not in denied.lower() and "connection refused" not in denied.lower(), "transport failure is not selector refusal")
    proof = read(out / "SOURCE.json")
    lock = read(OLD / "ASSET_LOCK.json")["files"][0]
    need(proof["archive_sha256"] == lock["sha256"] and proof["archive_size"] == lock["size"], "official locked source")
    need(proof["source"] == "fresh_extraction_from_locked_archive" and proof["asset_downloads"] == 0, "no unbound cached binary or new download")
    for executable in ("spire-server", "spire-agent"):
        binary = proof["binaries"][executable]
        need(binary["version"] == "1.16.0" and len(binary["archive_member_sha256"]) == 64 and binary["archive_member_sha256"] == binary["executed_sha256"], "executed binary provenance")
    need(proof["root_source"] == "server_management_socket_before_agent_start" and proof["parent_source"] == "server_management_agent_list", "management origin; no log fallback")
    need(proof["selector"] == ["unix:uid:1001"] and proof["target"] == "spiffe://h76.test/agent/h76-agent/executor/h76-executor", "exact entry")
    entry = read(out / "entry.redacted.json")
    agent = read(out / "agent-list.redacted.json")
    need(bool(entry) and bool(agent), "actual management responses")
    process = read(out / "PROCESSES.json")
    for key, uid in (("matching", 1001), ("nonmatching", 1002), ("signing", 1001)):
        item = process[key]
        need(type(item["pid"]) is int and item["pid"] > 0 and item["kernel_uid"] == uid and item["kernel_euid"] == uid, "kernel process observation: " + key)
        need("Uid:" in item["proc_status"] and all(int(value) == uid for value in item["proc_status"].split("Uid:", 1)[1].splitlines()[0].split()[:2]), "raw kernel UID: " + key)
        need(item["same_workload_socket"] is True, "workload API reference: " + key)
    need(process["matching_svid_count"] == 1 and process["nonmatching_svid_count"] == 0, "identity count")
    need(process["private_key_owner_uid"] == 1001 and process["private_directory_mode"] == "0700" and process["private_key_mode"] == "0600", "holder private boundary")
    env = read(out / "ENVIRONMENT.json")
    need(env["distribution"] == "Ubuntu" and env["host_installs"] == 0 and env["package_installs"] == 0 and env["docker_used"] is False, "native frozen environment")
    need(bool(env["python_version"]) and bool(env["cryptography_version"]) and bool(env["cryptography_files_sha256"]), "existing signing dependency fingerprint")
    return {"fresh_actual_source": True, "crypto": result, "manual_provenance_review_required": True}


def regressions():
    env = os.environ.copy()
    base = P / "runtime/userbase"
    shim = base / ("Python" + str(sys.version_info.major) + str(sys.version_info.minor)) / "site-packages/tests"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "__init__.py").write_text("__path__ = [" + repr(str(ROOT / "tests")) + "]\n", encoding="utf-8")
    env.update(PYTHONUSERBASE=str(base), PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    commands = [
        [sys.executable, "-B", "-m", "unittest", "tests.trusted_execution.test_credential_possession", "tests.trusted_execution.test_identity_assurance", "tests.test_stripe_authority_context"],
        [sys.executable, "-B", "docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/CHECK.py", "regressions"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, env=env, check=True, timeout=240)
    return {"original_tests": "PASS", "expected_identity_context": 28, "expected_stripe_security_business": [19, 9, 74]}


def closeout(phase):
    historical()
    if phase == "executor":
        need(not (P / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json").exists(), "Executor must not start a live issuer")
        return {"executor_live_runs": 0, "historical_attempts": 3, "historical_retry_deviation_preserved": True}
    out = output()
    cleanup = read(out / "CLEANUP.json")
    need(cleanup["owned_processes_alive"] == [] and cleanup["private_tmpfs_exists"] is False and cleanup["public_private_key_files"] == 0, "independent cleanup")
    need(cleanup["independent_check_exit_code"] == 0 and bool(cleanup["independent_check_command"]), "separate cleanup observation")
    for path in out.rglob("*"):
        if path.is_file():
            need(path.suffix.lower() not in (".key", ".p12", ".pfx") and b"PRIVATE KEY-----" not in path.read_bytes(), "public private material")
    for rel, digest in read(P / "evidence/ACCEPTED.json")["files"].items():
        need(sha(ROOT / rel) == digest, "post-L3 accepted snapshot drift: " + rel)
    need(len([p for p in (P / "evidence/evaluator_runs").iterdir() if p.is_dir()]) == 1, "one live run only")
    return {"live_runs": 1, "cleaned": True, "accepted_snapshot_unchanged": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preservation", "historical", "live", "verify", "regressions", "closeout"))
    parser.add_argument("--phase", choices=("executor", "evaluator"), default="executor")
    args = parser.parse_args()
    if args.check in ("verify", "closeout"):
        result = globals()[args.check](args.phase)
    else:
        result = globals()[args.check]()
    print(json.dumps({"check": args.check, "phase": args.phase, "result": result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
