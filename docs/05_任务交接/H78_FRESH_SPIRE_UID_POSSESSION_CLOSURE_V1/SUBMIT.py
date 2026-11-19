"""Seal the complete Executor package after one successful frozen public L2."""
from datetime import datetime, timezone
import json
from pathlib import Path

import CONTROL
import CHECK

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    route = CONTROL.authority(P, ROOT, "executor")
    CONTROL.need(route["state"] == "EXECUTING", "submit only from executing Executor")
    CHECK.preservation()
    CONTROL.need("SUBMITTED_FOR_REVIEW" in (P / "REPORT.md").read_text(encoding="utf-8"), "complete Executor report first")
    gates = [path for path in (P / "evidence/l2/L2-GATE.json", P / "evidence/l2_retry_02/L2-GATE.json") if path.is_file() and CONTROL.read(path)["result"] == "PASS"]
    CONTROL.need(len(gates) == 1, "exactly one passing gate required")
    gate = CONTROL.read(gates[0])
    CONTROL.need(gate["mandatory_failures"] == 0 and gate["checks_total"] == 6, "incomplete L2")
    for check in gate["checks"]:
        meta = CONTROL.read(ROOT / check["meta"])
        CONTROL.need(meta["exit_code"] == 0 and check["result"] == "PASS", "failed mandatory evidence")
        for kind in ("stdout", "stderr"):
            path = ROOT / check[kind]
            CONTROL.need(CONTROL.sha(path) == meta[kind + "_sha256"] and path.stat().st_size == meta[kind + "_bytes"], "L2 raw evidence changed")
    files = dict(CONTROL.read(P / "BASELINE.json")["protected"])
    for path in P.rglob("*"):
        if path.is_file() and "runtime" not in path.relative_to(P).parts and "__pycache__" not in path.parts and path.name != "SUBMISSION.json":
            files[path.relative_to(ROOT).as_posix()] = CONTROL.sha(path)
    data = {"schema": "h78-executor-submission/v1", "task_id": P.name, "status": "SUBMITTED_FOR_REVIEW", "at_utc": datetime.now(timezone.utc).isoformat(), "files": files, "l2_gate_path": gates[0].relative_to(ROOT).as_posix(), "excluded": {"SUBMISSION.json": "Evaluator seals separately", "CURRENT.md": "mutable router", "runtime/": "temporary test environment", "future_evaluator_outputs": "not yet created"}, "executor_issuer_runs": 0, "live_source_claim": "UNKNOWN until independent fresh L3"}
    with (P / "SUBMISSION.json").open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"sealed_files": len(files), "l2_gate": data["l2_gate_path"], "issuer_runs": 0}))


if __name__ == "__main__":
    main()
