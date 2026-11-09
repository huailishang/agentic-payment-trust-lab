"""Frozen repair regression runner using the unchanged independent generator."""
import argparse
import asyncio
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import yaml
from RUNTIME import TASK, ROOT, bootstrap
bootstrap()
from FROZEN_TESTS import P

SOURCE = TASK / "sources/evaluator/INDEPENDENT_CASES.py"
spec = importlib.util.spec_from_file_location("h53r_frozen_independent_source", SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    assert out.is_relative_to((TASK / "evidence").resolve())
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name and route["current_role"] in {"Executor", "Evaluator"}
    evaluator = route["current_role"] == "Evaluator"
    assert ("l3" in out.stem) == evaluator
    ledger_path = TASK / ("evidence/evaluator_attempt_ledger.json" if evaluator else "ATTEMPT_LEDGER.json")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"artifact_cases_run": 0, "runs": []}
    assert ledger["artifact_cases_run"] + len(source.CASES) <= (102 if evaluator else 272)
    ledger["artifact_cases_run"] += len(source.CASES)
    attempt = {"output": out.relative_to(ROOT).as_posix(), "cases_reserved": len(source.CASES),
               "status": "RESERVED", "started_at_utc": datetime.now(timezone.utc).isoformat()}
    ledger.setdefault("runs", []).append(attempt)
    save(ledger_path, ledger)
    if out.exists():
        raw = out.read_bytes()
        archive = TASK / "evidence/archive" / (out.stem + "-" + hashlib.sha256(raw).hexdigest() + ".json")
        if archive.exists(): assert archive.read_bytes() == raw
        else:
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(raw)
    result = {"schema": "h53r-terminal-cases/v1", "network_calls": 0, "asgi_requests": 0,
              "real_payment_calls": 0, "cases": []}
    try:
        P.setup_imports(False)
        sys.path.insert(0, str(TASK / "merchant"))
        for name in source.CASES:
            with tempfile.TemporaryDirectory(prefix="tail-", dir=ROOT / ".task_envs/H53R/runs") as directory:
                result["cases"].append(asyncio.run(source.run_case(name, directory)))
            save(out, result)
            assert result["cases"][-1]["contract_satisfied"], name
        attempt["status"] = "OBSERVED"
    except BaseException as exc:
        attempt.update(status="FAILED", error=type(exc).__name__, detail=str(exc))
        result["failure"] = dict(attempt)
        save(out, result)
        raise
    finally:
        attempt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        save(ledger_path, ledger)
    print(json.dumps({"tail_cases": len(result["cases"]), "all_contract_satisfied": True}))
