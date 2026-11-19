"""Candidate H78 gates and independent raw-fact checks; no issuer dispatch."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority(task, root, phase):
    need(sys.platform == "win32", "native Windows agent Python required")
    import yaml
    route = yaml.safe_load((root / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    allowed = {("Executor", "CONTRACT_FROZEN"), ("Executor", "EXECUTING")} if phase == "executor" else {("Evaluator", "READY_FOR_REVIEW")}
    need(route["task_id"] == task.name and (route["current_role"], route["state"]) in allowed, "H78 is not frozen/routed for this role")
    grant = read(task / "AUTHORIZATION.json")
    need(grant["status"] == "GRANTED" and bool(grant.get("source")) and bool(grant.get("owner_quote")), "explicit H78 owner grant missing")
    for key in ("authorization_existing_wsl", "authorization_local_service", "authorization_ephemeral_test_credentials"):
        need(route.get(key) is True and grant["flags"].get(key) is True, "missing H78 authority: " + key)
    for key in ("authorization_commit", "authorization_push", "authorization_api_call", "authorization_install", "authorization_artifact_download", "authorization_test_payments"):
        need(route.get(key) is False, "forbidden authority expansion: " + key)
    need((task / "FREEZE.json").is_file(), "Evaluator freeze not sealed")
    return route


def sources(task, root):
    manifest = read(task / "COPY_MANIFEST.json")
    for name, item in manifest["files"].items():
        need(sha(root / item["source"]) == item["initial_sha256"], "accepted source changed: " + name)
        if item["copy_rule"] == "byte_exact":
            need(sha(task / name) == item["initial_sha256"], "reused implementation changed: " + name)
    return {"source_copies": len(manifest["files"]), "byte_exact_collector": True}


def check_window(data, marker, windows_end):
    need(data["run_id"] == marker["run_id"] and data["nonce"] == marker["nonce"], "fresh challenge binding mismatch")
    need(data["status"] == "ISSUER_FETCH_SIGNATURE_CAPTURED", "incomplete source run")
    start = datetime.fromisoformat(data["started_utc"])
    end = datetime.fromisoformat(data["finished_utc"])
    need(start.tzinfo is not None and end.tzinfo is not None, "source clock timezone missing")
    issued, observed = data["issued_at_epoch"], data["observed_at_epoch"]
    need(type(issued) is int and type(observed) is int, "source epochs must be integer")
    need(int(start.timestamp()) <= issued <= observed <= int(end.timestamp()), "source-clock ordering invalid")
    need(observed - issued <= 300, "source challenge stale")
    need(type(marker["begin_epoch"]) is int and type(windows_end) is int and windows_end >= marker["begin_epoch"], "Windows orchestration clock reversed")
    return {"source_clock": "WSL_UTC", "source_started_utc": data["started_utc"], "source_finished_utc": data["finished_utc"], "challenge_age_seconds": observed - issued, "windows_begin_epoch": marker["begin_epoch"], "windows_end_epoch": windows_end, "cross_clock_offset": "NOT_MEASURED", "cross_clock_comparison_used": False, "freshness_basis": "unique accepted nonce/run binding plus source-clock ordering and original verifier"}


def attempt_output(task):
    marker = read(task / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json")
    need(isinstance(marker["run_id"], str) and re.fullmatch(r"[0-9a-f]{32}", marker["run_id"]), "invalid issuance marker")
    need(marker["budget_consumed"] == 1, "issuance attempt not charged")
    parent = task / "evidence/evaluator_runs"
    out = parent / marker["run_id"]
    need(out.resolve() == out.absolute() and not out.is_symlink() and out.is_dir(), "invalid own run directory")
    need([p.name for p in parent.iterdir() if p.is_dir()] == [marker["run_id"]], "more than one issuance directory")
    return out


def public_seal(out):
    index = read(out / "PUBLIC_INDEX.json")["files"]
    for rel, digest in index.items():
        path = (out / rel).resolve()
        need(path.is_relative_to(out.resolve()) and path.is_file() and not (out / rel).is_symlink() and sha(path) == digest, "public evidence seal drift: " + rel)
    for path in out.rglob("*"):
        need(not path.is_symlink(), "public symlink")
        if path.is_file():
            need(path.suffix.lower() not in (".key", ".p12", ".pfx") and b"PRIVATE KEY-----" not in path.read_bytes(), "private material in public evidence")
    return len(index)


def cleanup_facts(out):
    data = read(out / "CLEANUP.json")
    need(data["owned_processes_alive"] == [] and data["private_tmpfs_exists"] is False and data["public_private_key_files"] == 0, "resource cleanup incomplete")
    need(data["independent_check_exit_code"] == 0 and bool(data["independent_check_command"]), "independent cleanup command missing")
    raw = data["independent_check_raw"]
    path = (out / raw["stdout"]).resolve()
    need(path.is_relative_to(out.resolve()), "cleanup evidence escape")
    observed = read(path)
    need(observed["owned_processes_alive"] == [] and observed["private_tmpfs_exists"] is False and observed["public_private_key_files"] == 0, "independent cleanup raw facts disagree")
    return {"cleanup_proven": True, "source_status": read(out / "RESULT.json")["status"], "public_files": public_seal(out)}


def closeout(task, root, phase):
    if phase == "executor":
        need(not (task / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json").exists(), "Executor must not issue")
        return {"executor_issuer_runs": 0}
    for rel, digest in read(task / "evidence/ACCEPTED.json")["files"].items():
        need(sha(root / rel) == digest, "accepted input changed: " + rel)
    if not (task / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json").exists():
        parent = task / "evidence/asset_preflight/evaluator_01"
        paths = [p for p in (parent / "RESULT.json", parent / "FAILURE.json") if p.is_file()]
        need(len(paths) == 1 and read(paths[0])["scratch_removed"] is True, "preflight cleanup not independently evidenced")
        return {"issuer_runs": 0, "asset_scratch_cleaned": True, "source_completed": False}
    out = attempt_output(task)
    return {"issuer_runs": 1, "accepted_snapshot_unchanged": True, **cleanup_facts(out)}


def inspect_run(task, root, out):
    import WORKLOAD as w
    commands = [json.loads(line) for line in (out / "COMMANDS.jsonl").read_text(encoding="utf-8").splitlines()]
    def command(name):
        matches = [item for item in commands if item["name"] == name]
        need(len(matches) == 1 and matches[0]["exit_code"] == 0, "required successful command: " + name)
        return matches[0]
    def raw(name):
        item = command(name)
        path = (out / item["stdout"]).resolve()
        need(path.is_relative_to(out.resolve()), "raw command path escape")
        return read(path)
    agents = read(out / "agent-list.redacted.json")
    list_matches = [c for c in commands if c["name"].startswith("agent_list_") and c.get("exit_code") == 0 and read(out / c["stdout"]) == agents]
    need(len(list_matches) == 1, "management list lacks unique successful raw source")
    parent = w.parent_from_management(agents)
    created, shown = raw("entry_create"), raw("entry_show")
    entry_id = w.entry_identity(created)
    w.validate_entry(created, parent, entry_id)
    w.validate_entry(shown, parent, entry_id)
    need(shown == read(out / "entry.redacted.json"), "entry show projection mismatch")
    source, lock = read(out / "SOURCE.json"), read(task / "BINARY_MEMBER_LOCK.json")
    need(source["entry_id"] == entry_id and source["parent_id_sha256"] == source["agent_list_raw_parent_id_sha256"] == source["entry_raw_parent_id_sha256"], "management parent correlation mismatch")
    need(source["root_pem_sha256"] == sha(out / "root.pem"), "root management projection mismatch")
    root_command = command("management_root_before_agent")
    management_raw = (out / root_command["stdout"]).read_bytes()
    certs = re.findall(rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", management_raw, re.S)
    need(len(certs) == 1 and certs[0] + b"\n" == (out / "root.pem").read_bytes(), "management root raw output mismatch")
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    current_root = x509.load_pem_x509_certificate((out / "root.pem").read_bytes()).fingerprint(hashes.SHA256())
    old_roots = list((task.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1/evidence/wsl_experiment").glob("*/root.pem"))
    old_roots += list((task.parent / "H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/evaluator_runs").glob("*/root.pem"))
    for old_root in old_roots:
        need(current_root != x509.load_pem_x509_certificate(old_root.read_bytes()).fingerprint(hashes.SHA256()), "historical management root reused")
    for name, expected in lock["binaries"].items():
        actual = source["binaries"][name]
        need(actual["archive_member"] == expected["archive_member"] and actual["archive_member_sha256"] == actual["executed_sha256"] == expected["sha256"], "executed member lock mismatch")
        command(name + "_version")
    data = read(out / "RESULT.json")
    starts = [event for event in data["events"] if event["kind"] == "service_start"]
    need([item["name"] for item in starts] == ["server", "agent"], "service start count/order mismatch")
    captured = [event for event in data["events"] if event["kind"] == "management_root_captured_before_agent"]
    need(len(captured) == 1 and starts[0]["at_utc"] < captured[0]["at_utc"] < starts[1]["at_utc"], "management root must precede Agent")
    processes = read(out / "PROCESSES.json")
    for operation, uid in (("matching", 1001), ("nonmatching", 1002), ("signing", 1001)):
        proof = processes[operation]
        need(proof["kernel_uid"] == proof["kernel_euid"] == uid and proof["socket_path"] == "/dev/shm/h77w" + data["run_id"] + "/workload/api.sock", "kernel UID/socket mismatch")
        need(proof["same_workload_socket"] is True and operation in proof["argv_public"], "operation provenance missing")
        first = (out / proof["raw"]["stdout"]).read_bytes().splitlines()[0]
        need(first.startswith(b"H77_KERNEL "), "kernel handshake raw output missing")
        kernel = json.loads(first[len(b"H77_KERNEL "):])
        need(kernel["pid"] == proof["pid"] and kernel["start_ticks"] == proof["start_ticks"] and kernel["kernel_uid"] == uid, "parent/kernel observation mismatch")
    return {"raw_management_chain": True, "raw_kernel_operations": 3, "services_started": 2, **cleanup_facts(out)}
