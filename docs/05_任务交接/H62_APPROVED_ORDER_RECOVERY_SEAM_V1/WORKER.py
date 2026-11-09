"""Frozen independent process boundary. Candidate never owns safety monitors."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.dont_write_bytecode = True
for path in (ROOT, ROOT / "src", ROOT / "local_sources/third_party/ap2-v0.2.0/code/sdk/python", TASK / "merchant"):
    sys.path.insert(0, str(path))
sys.path.append(str(ROOT / ".task_envs/h37_ap2_crypto/lib/python3.12/site-packages"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    source = Path(args.input)
    if not source.name.endswith(".input.json"):
        raise ValueError("frozen input must end with .input.json")
    value = json.loads(source.read_text(encoding="utf-8"))
    prefix = source.name[:-len(".input.json")]
    if not prefix or not value.get("harness_nonce"):
        raise ValueError("missing frozen prefix or harness nonce")
    out = source.parent / (prefix + ".output.json")
    monitor = source.parent / (prefix + ".monitor.json")
    attempts = []

    def deny_network(*a, **k):
        frame = sys._getframe(1)
        if frame.f_code.co_name == "socketpair" and Path(frame.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
            return original_connect(*a, **k)
        attempts.append("network")
        monitor.write_text(json.dumps(attempts), encoding="utf-8")
        raise AssertionError("external network forbidden")

    def forbidden(label):
        async def call(*a, **k):
            attempts.append(label)
            monitor.write_text(json.dumps(attempts), encoding="utf-8")
            raise AssertionError("recovery called forbidden " + label)
        return call

    def hook(stage):
        target = value.get("pause_at")
        if target and stage == target:
            marker = Path(value["marker"])
            marker.write_text(json.dumps({"stage": stage, "pid": os.getpid(), "nonce": value["harness_nonce"]}), encoding="utf-8")
            until = time.monotonic() + 12
            while not Path(value["release"]).exists():
                if time.monotonic() >= until:
                    raise TimeoutError("frozen observer release missing")
                time.sleep(0.02)

    if value.get("operation") == "harness_probe":
        monitor.write_text("[]", encoding="utf-8")
        hook("probe")
        out.write_text(json.dumps({"result": {"status": "PROBED"}, "pid": os.getpid(),
                                   "nonce": value["harness_nonce"]}), encoding="utf-8")
        return

    original_connect = socket.socket.connect
    monitor.write_text("[]", encoding="utf-8")
    try:
        with patch.object(socket.socket, "connect", deny_network), patch.object(socket, "create_connection", deny_network), patch.object(socket, "getaddrinfo", deny_network):
            approval = load("APPROVAL_INBOX", TASK / "APPROVAL_INBOX.py")
            config = value["config"]
            operation = value["operation"]
            if operation != "recover":
                inbox = approval.ApprovalInbox(transactions_path=config["transactions_path"], psp_path=config["psp_path"],
                    ledger_path=config["ledger_path"], operator_context=config["operator_context"], now=lambda: config["now"])
            if operation == "inspect":
                result = inbox.inspect(value["request"]["checkout_id"])
            elif operation == "approve":
                result = inbox.approve(value["request"])
            elif operation == "show":
                result = inbox.show(value["request"]["approval_id"])
            elif operation == "revoke":
                result = inbox.revoke(value["request"])
            elif operation == "revoke_cli":
                context_path = source.parent / (prefix + ".operator.json")
                context_path.write_text(json.dumps(config["operator_context"]), encoding="utf-8")
                argv = [str(TASK / "APPROVAL_INBOX.py"), "--transactions", config["transactions_path"],
                        "--psp", config["psp_path"], "--ledger", config["ledger_path"],
                        "--operator-config", str(context_path), "--now", str(config["now"]), "revoke"]
                captured = io.StringIO()
                with patch.object(sys, "argv", argv), patch.object(sys, "stdin", io.StringIO(json.dumps(value["request"]))), redirect_stdout(captured):
                    approval.main()
                result = json.loads(captured.getvalue())
            elif operation == "recover":
                from services.checkout_service import CheckoutService
                from services.execution_control import ExecutionControl
                with patch.object(CheckoutService, "_process_payment", forbidden("_process_payment")), \
                     patch.object(CheckoutService, "complete_checkout", forbidden("complete_checkout")), \
                     patch.object(ExecutionControl, "claim", forbidden("claim")), \
                     patch.object(ExecutionControl, "recover", forbidden("recover")):
                    candidate = load("ORDER_RECOVERY", TASK / "ORDER_RECOVERY.py")
                    result = candidate.run(config, value["request"], hook=hook)
                assert result["status"] in {"RECOVERED", "REPLAY", "DENIED"}
            else:
                raise ValueError("unknown frozen operation")
            out.write_text(json.dumps({"result": result, "pid": os.getpid(), "nonce": value["harness_nonce"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    except approval.ApprovalDenied as exc:
        out.write_text(json.dumps({"result": {"error": exc.code}, "pid": os.getpid(), "nonce": value["harness_nonce"]}), encoding="utf-8")
    finally:
        monitor.write_text(json.dumps(attempts), encoding="utf-8")


if __name__ == "__main__":
    main()
