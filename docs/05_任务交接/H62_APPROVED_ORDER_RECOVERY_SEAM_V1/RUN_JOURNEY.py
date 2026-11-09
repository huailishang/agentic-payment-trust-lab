"""H57 six native HTTP journeys, raw evidence and distinct-process recovery.

Runs are append-only. Failed observations are preserved and never counted as PASS.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback

from RUNTIME import ROOT, TASK
from HTTP_RUNTIME import NativeProbe, read_rows

CASES = [
    "M01_NORMAL_REPLAY_QUERY",
    "M02_CHANGED_AFTER_CONFIRM",
    "M03_MISSING_CONFIRMATION",
    "M04_INVALID_AUTHORIZATION",
    "M05_UNCONFIGURED_APP",
    "M06_ORDER_FAILURE_RESTART_QUERY",
]
BOUNDARY = "NATIVE_DEFAULT_FACTORY_LOCAL_ASGI_WITH_FAKE_PSP"


def save(path, data):
    """Store JSON without pretending it is a complete signed transaction."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def new_run(role):
    parent = TASK / "evidence" / role
    parent.mkdir(parents=True, exist_ok=True)
    prior = [
        int(x.name.split("_")[-1])
        for x in parent.glob("run_[0-9][0-9][0-9][0-9]")
        if x.is_dir()
    ]
    seq = max(prior, default=0) + 1
    folder = parent / ("run_" + str(seq).zfill(4))
    folder.mkdir(exist_ok=False)
    return folder


def state_after(path):
    return {
        "orders": read_rows(path, "orders"),
        "inventory": read_rows(path, "inventory"),
        "checkouts": read_rows(path, "checkouts"),
        "attempts": read_rows(path, "h50_attempts"),
    }


async def worker_process(payload):
    """A new interpreter, new merchant app and sessions, same durable DB/PSP."""
    directory = Path(payload["directory"])
    Path(payload["pid_path"]).write_text(str(os.getpid()), encoding="ascii")
    async with NativeProbe(
        directory,
        case=CASES[5],
        run=payload["run"],
        role=payload["role"],
        seed=False,
        trusted_context=payload["trusted_context"],
    ) as probe:
        cid = payload["checkout_id"]
        checkout_response = await probe.request(
            "GET", "/checkout-sessions/" + cid, {}, key="restart-get"
        )
        assert checkout_response.status_code == 200, checkout_response.text[:500]
        retry = await probe.request(
            "POST", "/checkout-sessions/" + cid + "/complete",
            {
                "payment": probe.fixture.payment(),
                "risk_signals": {
                    "h50_confirmation_ref": payload["confirmation_ref"],
                    "h53_authorization": payload["authorization"],
                },
            },
            key="new-after-crash",
        )
        assert retry.status_code == 409, retry.text[:500]
        assert retry.json()["messages"][0]["code"] == "H50_EXECUTION_DENIED"
        recovery = await probe.control.recover(cid)
        assert recovery["decision"] == "QUERY"
        assert recovery["payment_state"] == "SUCCEEDED"
        assert os.getpid() != payload["previous_pid"]
        assert len(probe.payment_port.calls()) == 1
        result = {
            "worker_pid": os.getpid(),
            "calls": probe.calls,
            "recovery": recovery,
            "queries": probe.psp_queries(),
            "payment_calls": probe.payment_port.calls(),
        }
        save(Path(payload["result_path"]), result)
        print(json.dumps({
            "worker_pid": os.getpid(),
            "checkout_status": checkout_response.status_code,
            "retry_status": retry.status_code,
            "recovery": recovery["decision"],
            "charge_invocations": len(probe.payment_port.calls()),
        }))


async def first_worker_process(payload):
    """The first merchant lives only in this separate OS process."""
    directory = Path(payload["directory"])
    Path(payload["pid_path"]).write_text(str(os.getpid()), encoding="ascii")

    async def fail_after_charge(event, checkout_id):
        if event == "before_order_commit":
            raise RuntimeError("H57 injected before_order_commit fault")

    async with NativeProbe(
        directory,
        case=CASES[5],
        run=payload["run"],
        role=payload["role"],
        hook=fail_after_charge,
    ) as probe:
        checkout = await probe.create()
        ref, authorization, snapshot = await probe.confirm()
        finish = await probe.complete(ref, authorization)
        assert finish.status_code == 500, finish.text[:500]
        assert len(probe.payment_port.calls()) == 1
        save(Path(payload["result_path"]), {
            "first_pid": os.getpid(),
            "checkout_id": probe.cid,
            "calls": list(probe.calls),
            "confirmation": {"ref": ref, "snapshot": snapshot},
            "authorization": authorization,
            "trusted_context": probe.authorization_fixture.context(probe.keys),
            "authorization_public_keys": probe.public_keys(),
            "authorization_records": probe.authorization_records(),
            "psp_calls": probe.payment_port.calls(),
        })
    print(json.dumps({"first_pid": os.getpid(), "status": 500}))


def run_case_m06(run_dir, role):
    """Supervisor never hosts the M06 merchant; it observes two true OS exits."""
    case = CASES[5]
    scratch = ROOT / ".task_envs" / "H62" / "runs"
    scratch.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="h57-m06-", dir=scratch))
    first_result_path = directory / "first_result.json"
    second_result_path = directory / "worker_result.json"
    proof = {
        "supervisor_pid": os.getpid(),
        "transactions_db": str(directory / "transactions.db"),
        "psp_db": str(directory / "psp.db"),
        "events": [],
        "artifacts": {},
    }

    def call_worker(phase, argument, flag):
        # Spawn, synchronously wait for actual process exit and only then
        # return to the supervisor. No worker overlap is possible.
        command = [sys.executable, "-B", str(Path(__file__).resolve()), flag]
        pid_path = directory / (phase + "_worker.pid")
        argument = dict(argument)
        argument["pid_path"] = str(pid_path)
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Windows venv python.exe may be a launcher with a different PID.
        # Capture the actual live merchant process PID from its handshake.
        process.stdin.write(json.dumps(argument).encode("utf-8"))
        process.stdin.close()
        process.stdin = None
        deadline = time.monotonic() + 35
        while not pid_path.is_file() and time.monotonic() < deadline:
            if process.poll() is not None:
                break
            time.sleep(0.05)
        assert pid_path.is_file(), "M06 worker never registered its real PID"
        worker_pid = int(pid_path.read_text(encoding="ascii"))
        proof["events"].append({
            "phase": phase, "event": "started", "pid": worker_pid,
            "monotonic_ns": time.monotonic_ns(),
            "launcher_pid": process.pid,
        })
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            raise RuntimeError("M06 worker timed out; next worker not launched")
        proof["events"].append({
            "phase": phase, "event": "exited", "pid": worker_pid,
            "monotonic_ns": time.monotonic_ns(),
            "exit_code": process.returncode,
            "launcher_pid": process.pid,
        })
        artifacts = {}
        for stream, raw in (("stdout", stdout), ("stderr", stderr)):
            (run_dir / ("M06_" + phase + "." + stream + ".log")).write_bytes(raw)
            artifacts[stream + "_sha256"] = hashlib.sha256(raw).hexdigest()
        artifacts["exit_code"] = process.returncode
        artifacts["launcher_pid"] = process.pid
        proof["artifacts"][phase] = artifacts
        save(run_dir / "M06_processes.json", proof)
        assert process.returncode == 0, (
            "M06 " + phase + " worker failed", stderr[-900:]
        )
        return worker_pid

    first_pid = call_worker("first", {
        "directory": str(directory), "run": run_dir.name, "role": role,
        "result_path": str(first_result_path),
    }, "--first-worker")
    first = json.loads(first_result_path.read_text(encoding="utf-8"))
    assert first["first_pid"] == first_pid
    second_pid = call_worker("second", {
        "directory": str(directory), "run": run_dir.name, "role": role,
        "checkout_id": first["checkout_id"],
        "confirmation_ref": first["confirmation"]["ref"],
        "authorization": first["authorization"],
        "trusted_context": first["trusted_context"],
        "previous_pid": first_pid,
        "result_path": str(second_result_path),
    }, "--worker")
    second = json.loads(second_result_path.read_text(encoding="utf-8"))
    assert second["worker_pid"] == second_pid
    assert len({os.getpid(), first_pid, second_pid}) == 3
    assert len(proof["events"]) == 4
    assert proof["events"][1]["monotonic_ns"] < proof["events"][2]["monotonic_ns"]
    calls = first["calls"] + second["calls"]
    assert [c["worker_pid"] for c in calls] == [first_pid, first_pid, second_pid, second_pid]

    state = state_after(directory / "transactions.db")
    state["payment_calls"] = len(first["psp_calls"])
    row = {
        "case": case,
        "app_configured": True,
        "default_factory_used": True,
        "dependency_overrides_empty": True,
        "calls": calls,
        "worker_pids": [first_pid, second_pid],
        "state": state,
        "psp_calls": first["psp_calls"],
        "authorization_records": first["authorization_records"],
        "confirmation": first["confirmation"],
        "authorization_public_keys": first["authorization_public_keys"],
        "psp_queries": second["queries"],
        "recovery": second["recovery"],
        "durable_storage": {
            "transactions_db": str(directory / "transactions.db"),
            "psp_db": str(directory / "psp.db"),
            "same_storage_across_pids": True,
        },
        "restart": {
            "first_pid": first_pid, "second_pid": second_pid,
            "exit_code": proof["events"][3]["exit_code"],
        },
    }
    save(run_dir / (case + ".json"), row)
    return row


async def run_case(case, run_dir, role):
    if case == CASES[5]:
        return run_case_m06(run_dir, role)
    scratch = ROOT / ".task_envs" / "H62" / "runs"
    scratch.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="h57-" + case[:3].lower() + "-", dir=scratch))
    run_id = run_dir.name

    async def fail_after_charge(event, checkout_id):
        if event == "before_order_commit":
            raise RuntimeError("H57 injected before_order_commit fault")

    async with NativeProbe(
        directory,
        case=case,
        run=run_id,
        role=role,
        configured=case != CASES[4],
        hook=fail_after_charge if case == CASES[5] else None,
    ) as probe:
        checkout = await probe.create()
        confirmation = None
        authorization = None
        worker_pids = [os.getpid()]
        worker_result = None
        if case == CASES[4]:
            finish = await probe.complete(None, None)
        else:
            ref, authorization, snapshot = await probe.confirm()
            confirmation = {"ref": ref, "snapshot": snapshot}
            if case == CASES[1]:
                update_body = probe.fixture.payload(2)
                update_body["line_items"][0]["id"] = checkout["line_items"][0]["id"]
                update = await probe.request(
                    "PUT", "/checkout-sessions/" + probe.cid,
                    update_body, key="update",
                )
                assert update.status_code == 200, update.text[:500]
            if case == CASES[2]:
                finish = await probe.request(
                    "POST",
                    "/checkout-sessions/" + probe.cid + "/complete",
                    {
                        "payment": probe.fixture.payment(),
                        "risk_signals": {"h53_authorization": authorization},
                    },
                    key="complete",
                )
            elif case == CASES[3]:
                bad = dict(authorization)
                token = bad["payment_token"]
                position = max(10, len(token) // 2)
                bad["payment_token"] = (
                    token[:position] +
                    ("A" if token[position] != "A" else "B") +
                    token[position + 1:]
                )
                finish = await probe.complete(ref, bad)
            else:
                finish = await probe.complete(ref, authorization)

        if case == CASES[0]:
            replay = await probe.complete(ref, authorization, key="complete")
            get_checkout = await probe.request(
                "GET", "/checkout-sessions/" + probe.cid, {}, key="read-checkout"
            )
            order_id = finish.json()["order"]["id"]
            get_order = await probe.request(
                "GET", "/orders/" + order_id, {}, key="read-order"
            )
            assert [
                finish.status_code, replay.status_code,
                get_checkout.status_code, get_order.status_code,
            ] == [200, 200, 200, 200]
            assert finish.json() == replay.json()

        if case == CASES[5]:
            assert finish.status_code == 500, finish.text[:500]
            assert len(probe.payment_port.calls()) == 1
            result_path = directory / "worker_result.json"
            payload = {
                "directory": str(directory),
                "run": run_id,
                "role": role,
                "checkout_id": probe.cid,
                "confirmation_ref": ref,
                "authorization": authorization,
                "trusted_context": probe.authorization_fixture.context(probe.keys),
                "previous_pid": os.getpid(),
                "result_path": str(result_path),
            }
            # Exit the first app lifespan before the restart process starts.
        else:
            payload = None

        initial_calls = list(probe.calls)
        public_keys = probe.public_keys()
        first_pid = os.getpid()

    if payload is not None:
        completed = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--worker"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=45,
        )
        (run_dir / "M06_restart.stdout").write_text(
            completed.stdout, encoding="utf-8"
        )
        (run_dir / "M06_restart.stderr").write_text(
            completed.stderr, encoding="utf-8"
        )
        save(run_dir / "M06_restart.exit.json", {
            "exit_code": completed.returncode,
            "first_pid": first_pid,
            "worker_result_path": str(result_path),
        })
        assert completed.returncode == 0, (
            "M06 worker process failed",
            completed.stderr[-900:],
        )
        worker_result = json.loads(result_path.read_text(encoding="utf-8"))
        worker_pids.append(worker_result["worker_pid"])
        initial_calls.extend(worker_result["calls"])

    state = state_after(directory / "transactions.db")
    psp = probe.payment_port
    psp_calls = psp.calls()
    state["payment_calls"] = len(psp_calls)
    row = {
        "case": case,
        "app_configured": case != CASES[4],
        "default_factory_used": True,
        "dependency_overrides_empty": True,
        "calls": initial_calls,
        "worker_pids": worker_pids,
        "state": state,
        "psp_calls": psp_calls,
        "authorization_records": probe.authorization_records(),
        "confirmation": confirmation,
        "authorization_public_keys": public_keys,
    }
    if case == CASES[5]:
        row["psp_queries"] = worker_result["queries"]
        row["recovery"] = worker_result["recovery"]
        row["durable_storage"] = {
            "transactions_db": str(directory / "transactions.db"),
            "psp_db": str(directory / "psp.db"),
            "same_storage_across_pids": True,
        }
        row["restart"] = {
            "first_pid": first_pid,
            "second_pid": worker_result["worker_pid"],
            "exit_code": completed.returncode,
        }
    save(run_dir / (case + ".json"), row)
    return row


def execute(role, case_filter):
    run_dir = new_run(role)
    selected = [case_filter] if case_filter else CASES
    cases = []
    try:
        for case in selected:
            result = asyncio.run(run_case(case, run_dir, role))
            cases.append(result)
            print(json.dumps({
                "case": case,
                "http": [c["response_status"] for c in result["calls"]],
                "fake_psp_calls": len(result["psp_calls"]),
                "worker_pids": result["worker_pids"],
            }))
        observations = {
            "schema": "h57-journey-observations/v1",
            "boundary": BOUNDARY,
            "require_signatures": True,
            "asgi_requests": sum(len(c["calls"]) for c in cases),
            "cases": cases,
        }
        save(run_dir / "observations.json", observations)
        if not case_filter:
            from CHECK import validate
            checked_requests = validate(observations)
            assert checked_requests == observations["asgi_requests"]
            # The formal L2 runner creates its attempt directory before VP-03.
            # Reconcile observed request reservations before VP-04; never
            # reset inherited charges or invent an unperformed formal run.
            save(run_dir.parent / "LATEST.json", {"run": run_dir.name})
        print(json.dumps({
            "run": run_dir.name,
            "journeys": len(cases),
            "requests": observations["asgi_requests"],
            "strict_observations_check": not bool(case_filter),
            "legacy_ledger_unchanged": True,
        }))
    except BaseException:
        (run_dir / "ERROR.txt").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        save(run_dir / "PARTIAL.json", {
            "cases_completed": [c["case"] for c in cases],
            "status": "FAILED_NOT_ACCEPTED",
        })
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["executor", "evaluator"], default="executor")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--first-worker", action="store_true")
    args = parser.parse_args()
    if args.first_worker:
        asyncio.run(first_worker_process(json.loads(sys.stdin.read())))
    elif args.worker:
        asyncio.run(worker_process(json.loads(sys.stdin.read())))
    else:
        execute(args.role, args.case)


if __name__ == "__main__":
    main()
