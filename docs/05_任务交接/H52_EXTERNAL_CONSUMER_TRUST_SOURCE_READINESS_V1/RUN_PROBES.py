"""Frozen task-owned runner, preserving outputs and reserving bounded work."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import yaml
from datetime import datetime, timezone
from RUNTIME import TASK, ROOT, bootstrap

if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--out"
    out = (ROOT / sys.argv[2]).resolve()
    assert out.is_relative_to((TASK / "evidence").resolve())
    router = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(router.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name
    evaluator = route["current_role"] == "Evaluator"
    assert route["current_role"] in ("Executor", "Evaluator")
    assert ("l3" in out.stem) == evaluator, "output suffix must match the routed role"
    ledger_path = TASK / ("evidence/evaluator_attempt_ledger.json" if evaluator else "ATTEMPT_LEDGER.json")
    value = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    field = "evaluator_artifact_cases_run" if evaluator else "artifact_cases_run"
    value.setdefault(field, 0)
    assert value[field] + 12 <= (72 if evaluator else 144), "artifact case budget exhausted"
    value[field] += 12
    attempt = {"output": out.relative_to(ROOT).as_posix(), "cases_reserved": 12,
               "started_at_utc": datetime.now(timezone.utc).isoformat(), "status": "RESERVED"}
    value.setdefault("artifact_attempts", []).append(attempt)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    def save():
        ledger_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    if out.exists():
        raw = out.read_bytes()
        archived = TASK / "evidence/observation_archive" / (out.stem + "-" + hashlib.sha256(raw).hexdigest() + ".json")
        archived.parent.mkdir(parents=True, exist_ok=True)
        if archived.exists():
            assert archived.read_bytes() == raw
        else:
            archived.write_bytes(raw)
    bootstrap()
    sys.argv = [str(TASK / "PROBES.py"), "--out", out.relative_to(ROOT).as_posix()]
    try:
        runpy.run_path(str(TASK / "PROBES.py"), run_name="__main__")
        assert out.is_file(), "probe must persist its observations"
        attempt["status"] = "OBSERVED"
    except BaseException as exc:
        attempt.update(status="FAILED", error=type(exc).__name__)
        raise
    finally:
        attempt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        save()
