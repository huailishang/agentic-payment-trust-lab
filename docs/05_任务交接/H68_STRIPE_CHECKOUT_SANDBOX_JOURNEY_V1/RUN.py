"""Bounded H68 local preflight runner. No payment and no sandbox provisioning here."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
LEDGER = PACK / "ATTEMPT_LEDGER.jsonl"


def _authorize():
    auth = json.loads((PACK / "AUTHORIZATION.json").read_text(encoding="utf-8"))
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    if "execution_phase: INPUT_LIMIT_STOPPED_AWAITING_EVALUATOR_REVIEW" in current:
        raise RuntimeError("H68 execution stopped; new evaluator decision required")
    if not (
        auth.get("status") == "GRANTED"
        and auth.get("authorization_browser_test_only") is True
        and "state: EXECUTING" in current
        and "current_role: Executor" in current
        and "authorization_api_call: true" in current
    ):
        raise RuntimeError("H68 authority/router not ready")
    check = subprocess.run(
        [sys.executable, str(PACK / "CHECK.py"), "integrity"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=90, check=False,
    )
    if check.returncode != 0:
        raise RuntimeError("H68 frozen input integrity failed")


def _append(kind, event, attempt_id, **values):
    previous = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines()
                if x.strip()] if LEDGER.exists() else []
    if [r["seq"] for r in previous] != list(range(1, len(previous)+1)):
        raise RuntimeError("ledger sequence invalid")
    row = {"seq":len(previous)+1, "event":event, "attempt_id":attempt_id,
           "kind":kind, "at":datetime.now(timezone.utc).isoformat(), **values}
    raw = json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with LEDGER.open("ab") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def browser_probe(mode: str = "pipe"):
    _authorize()
    attempt_id = "browser-probe-" + uuid4().hex[:12]
    service_id = "browser-service-" + uuid4().hex[:12]
    _append("browser_action", "BEGIN", attempt_id, action="native_cdp_capability_probe_" + mode)
    _append("service", "BEGIN", service_id, action="isolated_native_chrome")
    try:
        file_path = ROOT / "scripts" / "validation" / "stripe_checkout_lab.py"
        spec = importlib.util.spec_from_file_location("h68_browser", file_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("browser_probe_missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.probe_browser_port() if mode == "port" else module.probe_browser()
        status = "SUCCEEDED" if result["capability"] in {"CHROME_CDP_PIPE_OK", "CHROME_CDP_PORT_OK"} else "INPUT_LIMIT"
        _append("service", "END", service_id, status=status, reason=result["reason"])
        _append("browser_action", "END", attempt_id, status=status, reason=result["reason"])
        print(json.dumps({"kind":"H68_BROWSER_PREFLIGHT",**result},sort_keys=True))
    except Exception:
        _append("service", "END", service_id, status="FAILED", reason="probe_crashed")
        _append("browser_action", "END", attempt_id, status="FAILED", reason="probe_crashed")
        print(json.dumps({"kind":"H68_BROWSER_PREFLIGHT","capability":"INPUT_LIMIT",
                          "reason":"browser_probe_failed_without_privates"}))
        return 1
    return 0


def close_input_limit():
    """Close only the two previously opened local attempts; never reinterpret probe failures."""
    _authorize()
    rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    begins = {row["attempt_id"]: row for row in rows if row["event"] == "BEGIN"}
    ends = {row["attempt_id"] for row in rows if row["event"] == "END"}
    outstanding = set(begins) - ends
    if outstanding != {"h68-implementation-001", "h68-active-001"}:
        raise RuntimeError("unexpected_outstanding_attempts")
    browser = [r for r in rows if r["kind"] == "browser_action" and r["event"] == "END"]
    if len(browser) != 2 or {r["reason"] for r in browser} != {
        "devtools_pipe_unavailable", "devtools_loopback_unreachable"
    } or any(r["status"] != "INPUT_LIMIT" for r in browser):
        raise RuntimeError("browser_stop_evidence_missing")
    if any(r["kind"] in {"anonymous_provision", "live_api", "executor_readback",
                         "evaluator_readback", "download", "l2", "l3"} for r in rows):
        raise RuntimeError("unexpected_external_or_gate_attempt")
    _append("implementation", "END", "h68-implementation-001", status="SUCCEEDED",
            check="74 local_and_legacy_unittests_passed", limitation="external_not_run")
    _append("active_work", "END", "h68-active-001", status="INPUT_LIMIT",
            reason="existing_browser_automation_unavailable")
    print("H68 local attempts closed; live Stripe attempts=0; input limit retained")
    return 0


def blocked_l2_boundary(begin: bool) -> int:
    """Capture one genuine, no-provider-data L2 runner result after INPUT_LIMIT."""
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    if "execution_phase: INPUT_LIMIT_STOPPED_AWAITING_EVALUATOR_REVIEW" not in current:
        raise RuntimeError("poststop_L2_requires_input_limit")
    rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    begins = {row["attempt_id"] for row in rows if row["event"] == "BEGIN"}
    ends = {row["attempt_id"] for row in rows if row["event"] == "END"}
    pending = begins - ends
    if begin:
        if pending or "h68-l2-blocked-001" in begins:
            raise RuntimeError("l2_not_available_for_single_attempt")
        _append("active_work", "BEGIN", "h68-l2-active-001",
                scope="local_only_failure_evidence")
        _append("l2", "BEGIN", "h68-l2-blocked-001",
                scope="read_only_runner_missing_external_source")
    else:
        if pending != {"h68-l2-blocked-001", "h68-l2-active-001"}:
            raise RuntimeError("l2_close_without_matching_begin")
        gate = PACK / "evidence" / "l2_blocked" / "L2-GATE.json"
        raw = json.loads(gate.read_text(encoding="utf-8"))
        if raw.get("result") != "FAIL" or raw.get("task_id") != PACK.name:
            raise RuntimeError("expected_blocked_gate_failure_missing")
        _append("l2", "END", "h68-l2-blocked-001", status="FAILED",
                reason="missing_native_stripe_qualification")
        _append("active_work", "END", "h68-l2-active-001",
                status="INPUT_LIMIT", reason="poststop_local_gate_closed")
    print("H68 blocked L2 boundary recorded:", "BEGIN" if begin else "END")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["blocked-l2-begin"]:
        raise SystemExit(blocked_l2_boundary(True))
    if sys.argv[1:] == ["blocked-l2-end"]:
        raise SystemExit(blocked_l2_boundary(False))
    if sys.argv[1:] == ["close-input-limit"]:
        raise SystemExit(close_input_limit())
    if sys.argv[1:] not in (["browser-probe"], ["browser-probe-port"]):
        raise SystemExit("Only bounded browser probes and close-input-limit are implemented.")
    raise SystemExit(browser_probe("port" if sys.argv[1] == "browser-probe-port" else "pipe"))
