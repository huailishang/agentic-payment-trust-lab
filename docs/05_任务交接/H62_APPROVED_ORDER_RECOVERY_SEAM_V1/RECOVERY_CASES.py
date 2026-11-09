"""Frozen behavioral oracle. Reads committed databases independently of the candidate."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import sysconfig
import tempfile
import time
import traceback
import uuid

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
NOW = 1800000000
CONTEXT = {"operator_id": "local-reviewer-01", "active": True, "roles": ["RECONCILIATION_APPROVER"], "policy_version": "h60-local-v1"}


def direct_worker_runtime():
    """Use a real OS Python process, not the Windows venv redirector."""
    if os.name != "nt":
        return sys.executable, os.environ.copy()
    executable = Path(sys._base_executable)
    purelib = Path(sysconfig.get_path("purelib"))
    if not executable.is_file() or not purelib.is_dir():
        raise RuntimeError("direct worker interpreter unavailable")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(purelib) + os.pathsep + environment.get("PYTHONPATH", "")
    return str(executable), environment


CASES = ["R01_NORMAL", "R02_EXPIRED_REPLAY", "R03_REVOKED", "R04_EXPIRED", "R05_CHANGED_SOURCE", "R06_WRONG_PAYMENT",
         "R07_NO_ROLE", "R08_CHANGED_POLICY", "R09_SHORTAGE", "R10_MISSING_PRODUCT", "R11_CRASH_BEFORE_COMMIT",
         "R12_CRASH_AFTER_COMMIT", "R13_CONCURRENT_CONSUMERS", "R14_REVOKE_AFTER_CONSUMER", "R15_OLD_CONFIRMATION_REVOKED", "R16_PSP_CHANGED"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path, table):
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        found = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not found:
            return []
        return [dict(r) for r in conn.execute('SELECT * FROM "' + table.replace('"', '""') + '" ORDER BY rowid')]


def state(config):
    tx = config["transactions_path"]
    return {name: rows(tx, name) for name in ("orders", "inventory", "checkouts", "idempotency_records", "h50_attempts", "h53_authorizations", "h50_confirmations", "h62_consumptions")}


def mutate(path, sql, params=()):
    with sqlite3.connect(path) as conn:
        conn.execute(sql, params)


def reserve(path, entry, maximum):
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    assert len(previous) < maximum, "frozen budget exhausted"
    assert all(json.loads(line)["id"] != entry["id"] for line in previous)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(entry) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


class Fixture:
    def __init__(self, role, run, case):
        self.role, self.run, self.case = role, run, case
        base = ROOT / ".task_envs/H62/runs"
        base.mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix=case.lower() + "-", dir=base))
        lock = read(TASK / "INPUTS.json")
        for name, source in lock["source_databases"].items():
            if name == "approvals":
                continue
            shutil.copyfile(ROOT / source["path"], self.folder / (name + ".db"))
        self.config = {"transactions_path": str(self.folder / "transactions.db"), "products_path": str(self.folder / "products.db"),
            "psp_path": str(self.folder / "psp.db"), "ledger_path": str(self.folder / "approvals.db"),
            "operator_context": copy.deepcopy(CONTEXT), "now": NOW, "base_url": "https://h62-merchant.example"}
        self.cid, self.payment = lock["checkout_id"], lock["payment_ref"]
        self.number = 0

    def start(self, operation, request, *, config=None, pause=None):
        self.number += 1
        assert self.number <= 16
        prefix = self.run / (self.case + "_" + str(self.number).zfill(2))
        entry = {"id": uuid.uuid4().hex, "case": self.case, "operation": operation, "input": prefix.name + ".input.json"}
        reserve(TASK / "evidence" / ("recovery_" + self.role) / "OPERATIONS.jsonl", entry, 320 if self.role == "executor" else 160)
        nonce = uuid.uuid4().hex
        value = {"config": config or self.config, "operation": operation, "request": request,
                 "harness_nonce": nonce}
        if pause:
            value.update(pause_at=pause, marker=str(prefix) + ".ready", release=str(prefix) + ".release")
        save(Path(str(prefix) + ".input.json"), value)
        out = open(str(prefix) + ".stdout.log", "xb")
        err = open(str(prefix) + ".stderr.log", "xb")
        python, environment = direct_worker_runtime()
        proc = subprocess.Popen([python, "-B", str(TASK / "WORKER.py"), str(prefix) + ".input.json"],
                                cwd=ROOT, env=environment, stdout=out, stderr=err)
        return {"proc": proc, "prefix": prefix, "stdout": out, "stderr": err, "pid": proc.pid,
                "nonce": nonce, "pause_at": pause, "worker_verified": False, "started": time.monotonic()}

    def finish(self, running, *, killed=False):
        proc, prefix = running["proc"], running["prefix"]
        try:
            code = proc.wait(timeout=25)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise
        finally:
            running["stdout"].close()
            running["stderr"].close()
        output = Path(str(prefix) + ".output.json")
        if killed:
            identity_verified = (running["worker_verified"] and running.get("worker_pid") == running["pid"]
                                 and code != 0 and proc.poll() is not None)
            record = None
        elif code == 0 and output.exists():
            record = read(output)
            identity_verified = (record.get("pid") == running["pid"]
                                 and record.get("nonce") == running["nonce"]
                                 and proc.poll() is not None)
        else:
            record, identity_verified = None, False
        save(Path(str(prefix) + ".process.json"), {"pid": running["pid"], "worker_pid": (
            running.get("worker_pid") if killed else (record or {}).get("pid")),
            "nonce": running["nonce"], "nonce_verified": identity_verified,
            "real_worker_exited": proc.poll() is not None and identity_verified,
            "exit_code": code, "killed": killed,
            "elapsed_seconds": time.monotonic() - running["started"],
            "stdout_sha256": sha(str(prefix) + ".stdout.log"), "stderr_sha256": sha(str(prefix) + ".stderr.log")})
        assert identity_verified, "OS worker process/nonce/exit proof failed"
        assert read(str(prefix) + ".monitor.json") == [], "forbidden call observed"
        if killed:
            return None
        return record["result"]

    def call(self, operation, request, *, config=None):
        return self.finish(self.start(operation, request, config=config))

    def approve(self):
        inspected = self.call("inspect", {"checkout_id": self.cid})
        assert inspected["eligible"]
        approved = self.call("approve", {"request_key": "approve-" + self.case, "checkout_id": self.cid, "payment_ref": self.payment,
            "expected_source_digest": inspected["source_digest"], "disposition": "ORDER_COMPLETION", "reason": "isolated H62 case", "expires_at": NOW + 60})
        assert approved["current"] and approved["effective_state"] == "APPROVAL_CURRENT"
        self.aid = approved["record"]["approval_id"]
        self.request = {"approval_id": self.aid, "checkout_id": self.cid, "payment_ref": self.payment, "request_key": "recover-" + self.case}
        return approved

    def revoke_request(self):
        return {"approval_id": self.aid, "request_key": "revoke-" + self.case, "reason": "isolated test revoke"}

    def wait_marker(self, running):
        until = time.monotonic() + 10
        path = Path(str(running["prefix"]) + ".ready")
        while not path.exists():
            assert running["proc"].poll() is None, operation_error(running["prefix"])
            if time.monotonic() > until:
                running["proc"].kill()
                running["proc"].wait()
                raise TimeoutError("candidate failed to reach actual transaction hook")
            time.sleep(0.02)
        marker = read(path)
        assert (marker.get("pid") == running["pid"]
                and marker.get("nonce") == running["nonce"]
                and marker.get("stage") == running["pause_at"]
                and running["proc"].poll() is None), "actual worker handshake mismatch"
        running["worker_verified"] = True
        running["worker_pid"] = marker["pid"]


def operation_error(prefix):
    return Path(str(prefix) + ".stderr.log").read_text(encoding="utf-8", errors="replace")[-1200:]


def success(before, after, result):
    assert result["status"] in {"RECOVERED", "REPLAY"}
    assert len(before["orders"]) == 0 and len(after["orders"]) == 1
    assert len(after["h62_consumptions"]) == 1
    receipt = after["h62_consumptions"][0]
    assert receipt["order_id"] == after["orders"][0]["id"] == result["order_id"]
    assert all(receipt.get(k) for k in ("approval_id", "checkout_id", "payment_ref", "source_digest", "context_digest", "response_json"))
    assert after["inventory"][0]["quantity"] == before["inventory"][0]["quantity"] - 1
    assert after["checkouts"][0]["status"] == "completed"
    assert len(after["idempotency_records"]) == len(before["idempotency_records"]) + 1
    for key in ("h50_attempts", "h53_authorizations", "h50_confirmations"):
        assert before[key] == after[key], key
    assert result.get("notification_status") == "PENDING_NOT_SENT"


def run_case(case, role, run):
    env = Fixture(role, run, case)
    if case == "R09_SHORTAGE":
        mutate(env.config["transactions_path"], "UPDATE inventory SET quantity=0 WHERE product_id='rose'")
    if case == "R10_MISSING_PRODUCT":
        mutate(env.config["products_path"], "DELETE FROM products WHERE id='rose'")
    env.approve()
    config = copy.deepcopy(env.config)
    request = copy.deepcopy(env.request)
    if case == "R03_REVOKED":
        assert env.call("revoke", env.revoke_request())["effective_state"] == "APPROVAL_REVOKED"
    elif case == "R04_EXPIRED":
        config["now"] = NOW + 60
    elif case == "R05_CHANGED_SOURCE":
        mutate(config["transactions_path"], "UPDATE inventory SET quantity=4 WHERE product_id='rose'")
    elif case == "R06_WRONG_PAYMENT":
        request["payment_ref"] = "unrelated-payment"
    elif case == "R07_NO_ROLE":
        config["operator_context"]["roles"] = []
    elif case == "R08_CHANGED_POLICY":
        config["operator_context"]["policy_version"] = "changed-policy"
    elif case == "R15_OLD_CONFIRMATION_REVOKED":
        mutate(config["transactions_path"], "UPDATE h50_confirmations SET revoked=1")
    elif case == "R16_PSP_CHANGED":
        mutate(config["psp_path"], "UPDATE receipts SET snapshot_json='{}'")
    before = state(config)
    protected = {name: sha(config[name + "_path"]) for name in ("products", "psp")}
    processes = []
    if case in {"R11_CRASH_BEFORE_COMMIT", "R12_CRASH_AFTER_COMMIT"}:
        point = "before_commit" if case.startswith("R11") else "after_commit"
        worker = env.start("recover", request, config=config, pause=point)
        processes.append(worker["pid"])
        env.wait_marker(worker)
        visible = state(config)
        if point == "before_commit":
            assert visible == before
        else:
            success(before, visible, {"status": "RECOVERED", "order_id": visible["orders"][0]["id"], "notification_status": "PENDING_NOT_SENT"})
        worker["proc"].terminate()
        env.finish(worker, killed=True)
        assert worker["proc"].poll() is not None
        if point == "after_commit":
            config["now"] = NOW + 600
        result = env.call("recover", request, config=config)
        assert result["status"] == ("RECOVERED" if point == "before_commit" else "REPLAY")
    elif case in {"R13_CONCURRENT_CONSUMERS", "R14_REVOKE_AFTER_CONSUMER"}:
        first = env.start("recover", request, pause="approval_locked")
        processes.append(first["pid"])
        env.wait_marker(first)
        started = time.monotonic()
        if case.startswith("R13"):
            blocked = env.call("recover", request)
            assert blocked["status"] == "DENIED"
        else:
            blocked = env.call("revoke_cli", env.revoke_request())
            assert "error" in blocked, "busy revoke cannot claim to have revoked"
        assert time.monotonic() - started <= 3
        Path(str(first["prefix"]) + ".release").touch()
        result = env.finish(first)
        assert result["status"] == "RECOVERED"
        if case.startswith("R13"):
            another = {**request, "request_key": "a-new-retry-key"}
            assert env.call("recover", another)["status"] == "REPLAY"
        else:
            after_revoke = env.call("revoke", env.revoke_request())
            assert after_revoke.get("effective_state") == "APPROVAL_CONSUMED" or after_revoke.get("error") == "APPROVAL_CONSUMED"
            after_cli = env.call("revoke_cli", env.revoke_request())
            assert after_cli.get("effective_state") == "APPROVAL_CONSUMED" or after_cli.get("error") == "APPROVAL_CONSUMED"
            assert not any(r["kind"] == "REVOKED" for r in rows(config["ledger_path"], "approval_events"))
    else:
        result = env.call("recover", request, config=config)
    after = state(config)
    if case in {"R01_NORMAL", "R02_EXPIRED_REPLAY", "R11_CRASH_BEFORE_COMMIT", "R12_CRASH_AFTER_COMMIT", "R13_CONCURRENT_CONSUMERS", "R14_REVOKE_AFTER_CONSUMER"}:
        success(before, after, result)
        shown = env.call("show", {"approval_id": env.aid}, config=config)
        assert shown["effective_state"] == "APPROVAL_CONSUMED" and shown["current"] is False
        if case == "R02_EXPIRED_REPLAY":
            config["now"] = NOW + 600
            replay = env.call("recover", request, config=config)
            assert replay["status"] == "REPLAY" and replay["order_id"] == result["order_id"]
            assert state(config) == after
            assert env.call("show", {"approval_id": env.aid}, config=config)["effective_state"] == "APPROVAL_CONSUMED"
            wrong = {**request, "payment_ref": "unrelated-payment-after-success"}
            assert env.call("recover", wrong, config=config)["status"] == "DENIED"
            assert state(config) == after
    else:
        assert result["status"] == "DENIED" and result.get("reason")
        assert after == before, "denied consumer changed business state"
    assert all(sha(config[name + "_path"]) == digest for name, digest in protected.items())
    return {"case": case, "result": "PASS", "before": before, "after": after, "response": result, "config": config,
            "approval_id": env.aid, "worker_operations": env.number, "observed_pids": processes, "protected_source_hashes": protected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    parent = TASK / "evidence" / ("recovery_" + args.role)
    parent.mkdir(parents=True, exist_ok=True)
    previous = [int(p.name[4:]) for p in parent.glob("run_[0-9][0-9][0-9][0-9]")]
    run = parent / ("run_" + str(max(previous, default=0) + 1).zfill(4))
    run.mkdir()
    observations = []
    try:
        for case in ([args.case] if args.case else CASES):
            reserve(parent / "CASE_ATTEMPTS.jsonl", {"id": uuid.uuid4().hex, "case": case, "run": run.name}, 48 if args.role == "executor" else 32)
            row = run_case(case, args.role, run)
            save(run / (case + ".json"), row)
            observations.append(row)
            print(json.dumps({"case": case, "result": "PASS", "operations": row["worker_operations"]}))
        save(run / "OBSERVATIONS.json", {"cases": observations, "role": args.role})
        if not args.case:
            save(parent / "LATEST.json", {"run": run.name})
    except BaseException:
        (run / "ERROR.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
