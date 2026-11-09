"""Frozen source/route protection and independent measurement assertions."""
import argparse
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import yaml
from HTTP_CHECKER import validate, validate_result

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
MUTABLE = {"HTTP_RUNTIME.py", "HTTP_MEASURE.py", "REPORT.md", "DESIGN.md", "RESULT.json", "ATTEMPT_LEDGER.json"}
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))
def workspace():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    return {name.decode("utf-8") for name in raw.split(b"\0") if name}
def baseline():
    lock = read("BASELINE.json")
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(current.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name and route["task_kind"] == "one_off"
    assert route["project_map_revision"] == "2026-10-20-r82" and route["active_bottleneck_id"] == "B-17" and route["hypothesis_id"] == "H-51"
    assert (route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}
    assert all(route["authorization_" + key] is False for key in ("api_call", "commit", "push", "history_rewrite"))
    assert hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    for name, expected in lock["protected_files"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in lock["frozen_files"].items():
        assert sha(TASK / name) == expected, name
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(name.startswith(prefix) for name in workspace() - set(lock["workspace_files"]))
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in lock["frozen_files"] or name in MUTABLE or name == "BASELINE.json" or name.startswith("evidence/"), name
    files = read("INHERITED_COPY.json")["files"]
    assert len(files) == 36
    for name, expected in files.items():
        assert sha(TASK / name) == expected, name
    env = json.loads((TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1/ENVIRONMENT.json").read_text(encoding="utf-8"))
    assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix
    assert all(importlib.metadata.version(name) == version for name, version in env["packages"].items())
    print(json.dumps({"baseline": "PASS", "protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"]), "immutable_merchant_files": len(files)}))
def materials(http):
    baseline()
    validate(json.loads((ROOT / http).read_text(encoding="utf-8")))
    validate_result(read("RESULT.json"))
    ledger = read("ATTEMPT_LEDGER.json")
    assert 1 <= ledger["formal_l2_attempts"] <= 2 and 0 <= ledger["active_work_minutes"] <= 240
    assert 0 < ledger["asgi_requests"] <= 160
    assert all(ledger[x] == 0 for x in ("network_calls", "model_calls", "provider_calls", "external_runtime_calls"))
    for name in ("REPORT.md", "DESIGN.md"):
        assert len((TASK / name).read_text(encoding="utf-8").strip()) >= 250
    assert "SUBMITTED_FOR_REVIEW" in (TASK / "REPORT.md").read_text(encoding="utf-8")
    for name in ("HTTP_RUNTIME.py", "HTTP_MEASURE.py"):
        ast.parse((TASK / name).read_text(encoding="utf-8"))
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    print("Frozen HTTP observations/materials PASS; real routing, signature verification and accounting require independent source review.")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "materials"])
    parser.add_argument("--http")
    args = parser.parse_args()
    baseline() if args.mode == "baseline" else materials(args.http)
