"""Frozen H85 validation. Candidate implementation belongs to the Executor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

import yaml

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
EVIDENCE = TASK / "evidence"
RUNNER = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"
CANDIDATE = TASK / "CANDIDATE.py"
CALLER = "scripts/validation/webshop/run_same_journey_responsibility.py"
ADAPTER = "scripts/validation/webshop/action_time_authority.py"
MUTABLE = {CALLER, ADAPTER}
LOCAL_FLAGS = {"authorization_existing_wsl", "authorization_local_service", "authorization_ephemeral_test_credentials"}
ROUTES = {"executor": ("EXECUTING", "Executor"), "evaluator": ("READY_FOR_REVIEW", "Evaluator")}
PREREQUISITES = ("VP-01", "VP-02", "VP-03")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path, data):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha(path):
    need(path.is_file() and not path.is_symlink(), f"missing regular input: {path.name}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def product_files():
    items = git("ls-files", "-z", "--cached", "--others", "--exclude-standard",
                "--", "src", "scripts", "tests", "samples").decode().split("\0")
    return set(items) - {""} - MUTABLE


def preservation():
    lock = read(TASK / "FREEZE.json")
    need(lock["task_id"] == TASK.name, "freeze task mismatch")
    need(git("rev-parse", "HEAD").decode().strip() == lock["head"], "HEAD drift")
    route = current_route()
    need(route["frozen_manifest_sha256"] == sha(TASK / "FREEZE.json"), "freeze hash mismatch")
    need(product_files() == set(lock["protected_product"]), "unexpected product file set")
    for group in ("frozen", "protected_product", "protected_evidence"):
        for name, expected in lock[group].items():
            need(sha(ROOT / name) == expected, f"protected input drift: {name}")
    return lock


def current_route():
    return yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8")
                          .split("```yaml", 1)[1].split("```", 1)[0])


def authorize(role, route):
    grant = read(TASK / "AUTHORIZATION.json")
    need(role in ROUTES, "unknown role")
    need(route.get("task_id") == TASK.name, "wrong current task")
    need((route.get("state"), route.get("current_role")) == ROUTES[role], "role is not active")
    expected = {key for key, value in route.items() if key.startswith("authorization_") and value is True}
    need(expected == LOCAL_FLAGS == set(grant["enabled_flags"]), "authorization scope drift")
    need(grant["task_id"] == TASK.name and grant["role_live_attempt_limit"] == 1, "grant mismatch")


def candidate_hashes():
    files = {ROOT / CALLER, CANDIDATE}
    optional = ROOT / ADAPTER
    if optional.exists():
        files.add(optional)
    support = TASK / "candidate"
    if support.exists():
        need(support.is_dir() and not support.is_symlink(), "invalid candidate support directory")
        for path in support.rglob("*"):
            need(not path.is_symlink(), "candidate contains a symbolic link")
            if path.is_file():
                files.add(path)
    return {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(files)}


def existing_host():
    need(sys.platform == "linux", "run formal gate inside the existing Ubuntu WSL")
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    need(re.search(r'^ID="?ubuntu"?$', os_release, re.MULTILINE) is not None, "Ubuntu required")
    need("microsoft" in os.uname().release.lower(), "existing WSL required")
    member_lock = read(TASK / "BINARY_MEMBER_LOCK.json")
    archive = Path.home() / ".cache/h76-spire-source" / member_lock["archive_name"]
    need(archive.is_file() and not archive.is_symlink(), "existing SPIRE archive absent")
    need(archive.stat().st_size == member_lock["archive_size"], "SPIRE archive size mismatch")
    need(sha(archive) == member_lock["archive_sha256"], "SPIRE archive hash mismatch")


def role_live_marker(role):
    return EVIDENCE / f"{role}_LIVE.json"


def context():
    attempt = os.environ.get("H85_FORMAL_ATTEMPT", "")
    need(re.fullmatch(r"executor-[12]|evaluator-1", attempt) is not None, "formal gate reservation required")
    role = attempt.split("-")[0]
    authorize(role, current_route())
    folder = EVIDENCE / attempt
    dispatch = read(folder / "DISPATCH.json")
    need(dispatch["attempt"] == attempt and dispatch["role"] == role, "dispatch mismatch")
    need((EVIDENCE / "FORMAL_ACTIVE.json").is_file(), "no active formal gate")
    need(read(EVIDENCE / "FORMAL_ACTIVE.json") == dispatch, "active gate mismatch")
    need(dispatch["candidate_sha256"] == candidate_hashes(), "candidate changed during gate")
    preservation()
    return role, folder, dispatch


def invoke_candidate(phase, role, folder):
    output = folder / phase
    output.mkdir()
    command = [sys.executable, "-B", str(CANDIDATE), phase, "--role", role, "--out", str(output)]
    subprocess.run(command, cwd=ROOT, check=True)
    return output


def observe(row, assurance):
    need(row["assurance"] == assurance and row["decision"] == "ALLOW", "wrong observed gate outcome")
    need(type(row["callback_count"]) is int and row["callback_count"] == 1, "wrong callback count")


def observation_rows(data, keys):
    need(set(data) == set(keys), "unexpected observation set")
    for key, outcome in keys.items():
        observe(data[key], outcome)
    return data


def offline(role, folder):
    output = invoke_candidate("offline", role, folder)
    data = read(output / "OBSERVATIONS.json")
    observation_rows(data, {"baseline": "BOUND", "issued": "VERIFIED", "unavailable": "BOUND", "time_mismatch": "BOUND"})
    need(len({r["business_digest"] for r in data.values()}) == 1, "business inputs differ")
    need(data["unavailable"]["source_status"] == "UNKNOWN", "unavailable source misclassified")
    need(data["time_mismatch"]["fact_supplied"] is False, "mismatched time passed a Fact")
    original = read(TASK / "evidence/BASELINE_PROBE.json")
    need(data["baseline"]["trace_validation"] == original["trace_validation"], "baseline trace degraded")
    return {"observation_sha256": sha(output / "OBSERVATIONS.json"), "modes": list(data)}


def regressions():
    suites = (
        ("tests", "test_webshop_runtime_gate.py", 42),
        ("tests/trusted_execution", "test_credential_possession.py", 6),
        ("tests/trusted_execution", "test_credential_context_consumption.py", 6),
        ("tests/trusted_execution", "test_identity_assurance.py", 6),
        ("tests/trusted_execution", "test_payment_binding.py", 18),
        ("tests/trusted_execution", "test_signed_instruction_es256.py", 8),
    )
    sys.path.insert(0, str(ROOT / "src"))
    for directory, pattern, expected in suites:
        tests = unittest.defaultTestLoader.discover(str(ROOT / directory), pattern=pattern)
        result = unittest.TextTestRunner(verbosity=1).run(tests)
        need(result.wasSuccessful() and not result.skipped and result.testsRun == expected, f"regression: {pattern}")
    return {"passed": sum(row[2] for row in suites), "skipped": 0}


def live(role, folder, dispatch):
    for index, check in enumerate(PREREQUISITES, 1):
        receipt = read(folder / f"{check}.json")
        need(receipt["dispatch"] == dispatch and receipt["check"] == check, "prerequisite receipt mismatch")
        prefix = "EV" if role == "executor" else "RV-EV"
        meta = read(folder / f"{prefix}-{index:02d}.meta.json")
        need(meta["exit_code"] == 0, f"{check} did not pass in this runner")
    existing_host()
    write_new(role_live_marker(role), dispatch)
    output = invoke_candidate("live", role, folder)
    data = read(output / "OBSERVATIONS.json")
    before, after = data["before"], data["after"]
    observation_rows({"before": before, "after": after}, {"before": "VERIFIED", "after": "BOUND"})
    need(data["run_role"] == role and data["network_scope"] == "loopback", "unexpected live scope")
    need(before["source_status"] == "ISSUED" and after["source_status"] == "DENIED", "source transition unknown")
    need(before["fact_supplied"] is True and after["fact_supplied"] is False, "Fact handling mismatch")
    need(before["business_digest"] == after["business_digest"] and before["action_id"] != after["action_id"], "comparison drift")
    need(before["holder_uid"] == after["holder_uid"] == 1001 and before["socket_ref"] == after["socket_ref"], "workload scope drift")
    need(1 <= data["post_delete_probes"] <= 12 and 0 <= data["delete_to_denial_monotonic_seconds"] <= 90, "observation limit exceeded")
    need(data["registrations_created"] == data["registrations_deleted"] == data["server_starts"] == data["agent_starts"] == 1, "live resource count mismatch")
    need(data["initial_fetch_attempts"] <= 3 and data["holder_signatures"] == 1, "initial issuance budget exceeded")
    need(before["observed_at_epoch"] == before["use_at_epoch"] < after["use_at_epoch"] <= data["old_leaf_not_after_epoch"], "use time or leaf validity mismatch")
    need(data["cleanup"] == {"owned_processes_alive": [], "private_tmpfs_exists": False, "public_private_key_files": 0}, "cleanup unproven")
    for name, expected in data["raw_sha256"].items():
        path = output / name
        need(path.resolve().is_relative_to(output.resolve()), "raw evidence outside run")
        need(sha(path) == expected, f"raw evidence drift: {name}")
    need(bool(data["raw_sha256"]), "missing raw evidence index")
    print(json.dumps({"live_observations_sha256": sha(output / "OBSERVATIONS.json"), "role": role}))


def gate(role):
    authorize(role, current_route())
    preservation()
    existing_host()
    snapshot = candidate_hashes()
    if role == "evaluator":
        accepted = read(EVIDENCE / "ACCEPTED_CANDIDATE.json")
        need(accepted["candidate_sha256"] == snapshot, "candidate differs from accepted L2")
    need(not role_live_marker(role).exists(), "live budget already used")
    indices = (1, 2) if role == "executor" else (1,)
    index = next((n for n in indices if not (EVIDENCE / f"{role}-{n}").exists()), None)
    need(index is not None, "formal gate budget already used")
    attempt = f"{role}-{index}"
    folder = EVIDENCE / attempt
    dispatch = {"role": role, "attempt": attempt, "candidate_sha256": snapshot}
    active = EVIDENCE / "FORMAL_ACTIVE.json"
    write_new(active, dispatch)
    try:
        folder.mkdir()
        write_new(folder / "DISPATCH.json", dispatch)
        command = [
            sys.executable, "-B", str(RUNNER), "--repo", str(ROOT),
            "--plan", str(TASK / "VALIDATION_PLAN.yaml"), "--out", str(folder), "--mode", role,
        ]
        env = os.environ | {"H85_FORMAL_ATTEMPT": attempt}
        result = subprocess.run(command, cwd=ROOT, env=env)
        preservation()
        need(snapshot == candidate_hashes(), "candidate changed during the formal gate")
        return result.returncode
    except KeyboardInterrupt:
        raise SystemExit("interrupted; preserve the active reservation and inspect the run before any retry")
    finally:
        if sys.exc_info()[0] is not SystemExit:
            active.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("gate", "baseline", "offline", "regressions", "live", "preservation"))
    parser.add_argument("--role", choices=tuple(ROUTES))
    args = parser.parse_args()
    if args.step == "gate":
        return gate(args.role)
    if args.step == "preservation":
        lock = preservation()
        print(f"preservation PASS ({len(lock['protected_product'])} product inputs)")
        return 0
    role, folder, dispatch = context()
    if args.step == "live":
        need(role == args.role, "live role mismatch")
        live(role, folder, dispatch)
    else:
        if args.step == "baseline":
            existing_host()
            result = {"preservation": "PASS", "asset_archive": "PASS"}
        elif args.step == "offline":
            result = offline(role, folder)
        else:
            result = regressions()
        check = PREREQUISITES[("baseline", "offline", "regressions").index(args.step)]
        write_new(folder / f"{check}.json", {"dispatch": dispatch, "check": check, "result": result})
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
