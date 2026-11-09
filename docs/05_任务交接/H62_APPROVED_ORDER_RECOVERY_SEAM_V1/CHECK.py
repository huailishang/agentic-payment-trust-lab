"""Frozen H62 scope, source protection and persisted behavioral-evidence checks."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from RUNTIME import TASK, ROOT, preflight
from RECOVERY_CASES import CASES, read, rows, sha, state, success


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# This is a frozen business oracle, not candidate business code.
OLD = load("h62_original_business_oracle", TASK / "references/H57_CHECK.py")
validate = OLD.validate


def baseline():
    lock = read(TASK / "INPUTS.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    for name, digest in lock["protected_files"].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in lock["frozen_files"].items():
        assert sha(TASK / name) == digest, name
    for entry in lock["source_databases"].values():
        assert sha(ROOT / entry["path"]) == entry["sha256"], entry["path"]
    known = set(lock["workspace_files"])
    now = {s.decode("utf-8") for s in subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).split(b"\0") if s}
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(n.startswith(prefix) for n in now - known)
    print(json.dumps({"protected": len(lock["protected_files"]), "source_databases": len(lock["source_databases"])}))


def scope():
    lock = read(TASK / "INPUTS.json")
    mutable = {"merchant/services/checkout_service.py", "merchant/db.py", "APPROVAL_INBOX.py", "ORDER_RECOVERY.py"}
    for name, digest in lock["product_copy"].items():
        if name not in mutable:
            assert sha(TASK / name) == digest, name
    assert (TASK / "ORDER_RECOVERY.py").is_file(), "candidate not implemented"
    for name in mutable:
        ast.parse((TASK / name).read_text(encoding="utf-8"))
    allowed = set(lock["frozen_files"]) | mutable | {"INPUTS.json", "REPORT.md", "RESULT.json", "ATTEMPT_LEDGER.json", "REVIEW.md"}
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in allowed or name.startswith("evidence/"), name
    preflight()
    print(json.dumps({"product_files_allowed": 4, "manual_shared_transaction_review_required": True}))


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def journal(path, limit):
    values = read_lines(path)
    assert len(values) <= limit and len({r["id"] if "id" in r else r["request_id"] for r in values}) == len(values)
    return values


def recovery(role):
    folder = TASK / "evidence" / ("recovery_" + role)
    run = folder / read(folder / "LATEST.json")["run"]
    data = read(run / "OBSERVATIONS.json")
    assert [r["case"] for r in data["cases"]] == CASES
    cases = journal(folder / "CASE_ATTEMPTS.jsonl", 48 if role == "executor" else 32)
    operations = journal(folder / "OPERATIONS.jsonl", 320 if role == "executor" else 160)
    assert sum(r["run"] == run.name for r in cases) == 16
    for row in data["cases"]:
        assert row == read(run / (row["case"] + ".json")) and row["result"] == "PASS"
        config = row["config"]
        assert state(config) == row["after"]
        if row["after"]["h62_consumptions"]:
            receipt = row["after"]["h62_consumptions"][0]
            assert receipt["approval_id"] == row["approval_id"]
            assert receipt["checkout_id"] == read(TASK / "INPUTS.json")["checkout_id"]
            assert receipt["payment_ref"] == read(TASK / "INPUTS.json")["payment_ref"]
            import sqlite3
            with sqlite3.connect(Path(config["transactions_path"]).resolve().as_uri() + "?mode=ro", uri=True) as conn:
                unique = set()
                for index in conn.execute("PRAGMA index_list(h62_consumptions)"):
                    if index[2]:
                        unique.add(tuple(r[2] for r in conn.execute('PRAGMA index_info("' + index[1].replace('"', '""') + '")')))
                assert all((key,) in unique for key in ("approval_id", "checkout_id", "payment_ref")), "missing business uniqueness"
        for name, digest in row["protected_source_hashes"].items():
            assert sha(config[name + "_path"]) == digest
        assert config["transactions_path"].startswith(str(ROOT / ".task_envs/H62/runs"))
        for attempt in [r for r in operations if r["case"] == row["case"] and (run / r["input"]).exists()]:
            inp = run / attempt["input"]
            stem = str(inp)[:-len(".input.json")]
            assert read(stem + ".monitor.json") == []
            proc = read(stem + ".process.json")
            request = read(str(inp))
            assert proc["pid"] == proc["worker_pid"] and proc["nonce"] == request["harness_nonce"]
            assert proc["nonce_verified"] is True and proc["real_worker_exited"] is True
            if proc["killed"]:
                marker = read(stem + ".ready")
                assert marker["pid"] == proc["worker_pid"] and marker["nonce"] == proc["nonce"]
            else:
                completed = read(stem + ".output.json")
                assert completed["pid"] == proc["worker_pid"] and completed["nonce"] == proc["nonce"]
            assert sha(stem + ".stdout.log") == proc["stdout_sha256"]
            assert sha(stem + ".stderr.log") == proc["stderr_sha256"]
            assert (proc["exit_code"] != 0) if proc["killed"] else (proc["exit_code"] == 0)
    print(json.dumps({"role": role, "recovery_cases": 16, "reserved_cases": len(cases), "worker_operations": len(operations)}))


def original(role):
    folder = TASK / "evidence" / role
    run = folder / read(folder / "LATEST.json")["run"]
    value = read(run / "observations.json")
    assert validate(value) == 18
    parent = load("h62_process_oracle", TASK / "references/H57R_PROCESS_CHECK.py")
    parent.ROOT = ROOT
    parent.process_exit(read(run / "M06_processes.json"), value["cases"][-1])
    records = read_lines(folder / "HTTP_ATTEMPTS.jsonl")
    parent.journal(records, value, run.name)
    assert len(records) <= (80 if role == "executor" else 40)
    print(json.dumps({"original_journeys": 6, "http_requests_in_latest": 18, "reserved_http_requests": len(records)}))


def approval(role):
    folder = TASK / "evidence" / ("approval_" + role)
    run = folder / read(folder / "LATEST.json")["run"]
    value = read(run / "results.json")
    assert len(value["cases"]) == 24 and all(r["result"] == "PASS" for r in value["cases"])
    journal(folder / "CASE_ATTEMPTS.jsonl", 72 if role == "executor" else 24)
    print(json.dumps({"approval_regressions": 24, "business_execution_enabled": False}))


def accounting():
    ledger = read(TASK / "ATTEMPT_LEDGER.json")
    assert ledger["task_id"] == TASK.name and 0 <= ledger["active_work_minutes"] <= 360
    intervals = ledger["work_intervals_utc"]
    assert intervals and all(r["start"] <= r["end"] for r in intervals)
    assert ledger["formal_l2_attempts"] == len(list((TASK / "evidence").glob("l2_executor_*"))) <= 2
    for key in ("network_calls", "model_calls", "provider_calls", "real_payment_calls", "packages_installed", "git_write_operations"):
        assert ledger[key] == 0
    for suffix, filename, limit in (("recovery_executor", "CASE_ATTEMPTS.jsonl", 48), ("recovery_executor", "OPERATIONS.jsonl", 320),
                                   ("approval_executor", "CASE_ATTEMPTS.jsonl", 72), ("executor", "HTTP_ATTEMPTS.jsonl", 80)):
        reserved = journal(TASK / "evidence" / suffix / filename, limit)
        assert ledger["reservations"][suffix + "/" + filename] == len(reserved)
    result = read(TASK / "RESULT.json")
    assert result["task_id"] == TASK.name and result["remaining_gaps"]
    for key in ("production_ready", "real_identity_verified", "provider_verified", "customer_value_proven", "standard_checkout_mandate_integrated"):
        assert result[key] is False
    print(json.dumps({"budget": "within_envelope", "active_work_minutes": ledger["active_work_minutes"]}))


def selftest():
    before = {"orders": [], "inventory": [{"quantity": 5}], "checkouts": [{"status": "ready_for_complete"}],
              "idempotency_records": [], "h50_attempts": [], "h53_authorizations": [], "h50_confirmations": [], "h62_consumptions": []}
    after = copy.deepcopy(before)
    after.update(orders=[{"id": "order"}], inventory=[{"quantity": 4}], checkouts=[{"status": "completed"}], idempotency_records=[{}],
        h62_consumptions=[dict(approval_id="approval", checkout_id="checkout", payment_ref="payment", source_digest="source", context_digest="context", order_id="order", response_json="{}")])
    result = {"status": "RECOVERED", "order_id": "order", "notification_status": "PENDING_NOT_SENT"}
    success(before, after, result)
    bads = []
    for key in ("orders", "h62_consumptions", "idempotency_records"):
        bad = copy.deepcopy(after)
        bad[key] = []
        bads.append(bad)
    bad = copy.deepcopy(after); bad["inventory"][0]["quantity"] = 3; bads.append(bad)
    bad = copy.deepcopy(after); bad["h50_attempts"] = [{}]; bads.append(bad)
    bad = copy.deepcopy(after); bad["h62_consumptions"][0]["order_id"] = "unrelated"; bads.append(bad)
    for bad in bads:
        try:
            success(before, bad, result)
        except (AssertionError, IndexError, KeyError):
            pass
        else:
            raise AssertionError("broken state accepted")
    print(json.dumps({"corruptions_rejected": 6, "candidate_called": False}))


if __name__ == "__main__":
    name = sys.argv[1]
    if name in {"recovery", "original", "approval"}:
        {"recovery": recovery, "original": original, "approval": approval}[name](sys.argv[2])
    else:
        {"baseline": baseline, "scope": scope, "accounting": accounting, "selftest": selftest,
         "oracle_selftest": lambda: load("h62_process_selftest", TASK / "references/H57R_PROCESS_CHECK.py").selftest()}[name]()
