"""H74 local package controls. Behavioral truth additionally needs independent L3."""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(value, reason):
    if not value: raise ValueError(reason)
def route(): return yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
def frozen():
    for rel, expected in read(P / "FREEZE.json")["files"].items(): need(sha(P / rel) == expected, "frozen drift:" + rel)
def package():
    frozen()
    for rel, expected in read(P / "BASELINE.json")["protected"].items(): need(sha(ROOT / rel) == expected, "protected drift:" + rel)
    print(json.dumps({"package_only": True, "formal_gates": 0}))
def preservation():
    package()
    need(sys.platform == "win32" and sys.version_info[:3] == (3, 12, 13), "native Conda agent environment")
    import tests
    need([str(Path(p).resolve()) for p in tests.__path__] == [str((ROOT / "tests").resolve())], "task-local tests path")
    r = route()
    need(r["task_id"] == P.name and r["task_kind"] == "capability_experiment" and r["baseline_commit"] == read(P / "BASELINE.json")["head"], "router identity")
    need(r["project_map_revision"] == "2026-11-16-r125" and r["active_bottleneck_id"] == "B-22" and r["hypothesis_id"] == "H-74", "router strategy")
    roles = {"CONTRACT_FROZEN": "Executor", "EXECUTING": "Executor", "READY_FOR_REVIEW": "Evaluator", "PASS": "Evaluator", "REJECTED": "Evaluator", "HUMAN_REQUIRED": "Human"}
    need(roles.get(r["state"]) == r["current_role"], "role/state")
    keys = {"authorization_" + name for name in ("commit", "push", "history_rewrite", "api_call", "reference_read", "install", "local_service", "browser_test_only", "test_payments")}
    need(keys <= set(r) and all(v is False for k,v in r.items() if k.startswith("authorization_")), "authorization")
    spec, baseline = read(P / "SPEC.json"), read(P / "BASELINE.json")
    allowed = set(baseline["protected"]) | set(spec["mutable_existing"]) | set(spec["allowed_new"]) | {"CURRENT.md"}
    prefix = P.relative_to(ROOT).as_posix() + "/"
    paths = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    for rel in filter(None, paths):
        if not rel.startswith(prefix): need(rel in allowed, "outside scope:" + rel)
    target = ROOT / "tests/test_stripe_authority_context.py"
    if target.exists():
        tree = ast.parse(target.read_text(encoding="utf-8"))
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        need(set(spec["required_test_classes"]) <= {n.name for n in classes}, "required test classes")
        need(not any(f.name == "fail" for n in classes for f in n.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))), "unittest fail override forbidden")
def run(argv, env=None):
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True)
    sys.stdout.buffer.write(result.stdout); sys.stderr.buffer.write(result.stderr)
    need(result.returncode == 0, "child process failed")
def baseline():
    data = read(P / "BASELINE.json")
    role = route()["current_role"]
    dest = P / ("derived/baseline_src" if role == "Executor" else "evidence/l3_review/baseline_src")
    dest.mkdir(parents=True, exist_ok=True)
    for rel, expected in data["source_files"].items():
        source = P / "references/initial_source" / rel if rel in data["mutable_initial"] else ROOT / rel
        need(sha(source) == expected, "baseline source drift")
        target = dest / Path(rel).relative_to("src")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(dest), PYTHONIOENCODING="utf-8")
    run([sys.executable, "-B", str(P / "BASELINE_PROBE.py")], env)
def regressions():
    run([sys.executable, "-B", "-m", "unittest", "tests.test_stripe_checkout_adapter", "tests.test_stripe_checkout_lab", "tests.test_h72_stripe_journey"])
    helper = "docs/05_任务交接/H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/CHECK.py"
    run([sys.executable, "-B", helper, "safety"])
    run([sys.executable, "-B", helper, "regressions"])
def impact():
    data, spec = read(P / "MEASUREMENT.json"), read(P / "SPEC.json")
    need(data.get("schema") == "h74-measurement/v1" and data.get("baseline") == "UNSUPPORTED_DURABLE_API", "measurement baseline")
    units = data.get("units", [])
    need(len(units) == 3 and {u["unit"] for u in units} == set(spec["units"]), "exact three units")
    for unit in units:
        need(set(spec["unit_result_keys"]) <= set(unit), "unit evidence fields")
        for key in ("input_sha256", "original_graph_sha256", "reloaded_graph_sha256", "snapshot_sha256"):
            need(isinstance(unit[key], str) and re.fullmatch("[0-9a-f]{64}", unit[key]), "unit digest")
        need(unit["original_graph_sha256"] == unit["reloaded_graph_sha256"], "original graph changed")
        need(unit["cold_process"] is True and unit["original_times_preserved"] is True and unit["consumer_or_recovery_observed"] is True and type(unit["unexpected_payment_callbacks"]) is int and unit["unexpected_payment_callbacks"] == 0, "unit observation")
        need(bool(unit["raw_evidence"]), "raw evidence required")
        for ref in unit["raw_evidence"]:
            path = (P / ref["path"]).resolve()
            need(path.is_relative_to(P) and sha(path) == ref["sha256"], "raw evidence reference")
    print(json.dumps({"baseline": "UNSUPPORTED_DURABLE_API", "after_cold_original_context_units": 3, "scope": "new synthetic stored path only; semantic L3 required"}))
def budget():
    data = read(P / "ATTEMPT_LEDGER.json")
    need(data["schema"] == "h74-cost/v1" and all(w["role"] == "Executor" for w in data["windows"]), "Executor ledger")
    need(type(data["implementation_attempts"]) is int and 1 <= data["implementation_attempts"] <= 2 and data["l3_attempts"] == 0, "implementation/role attempts")
    all_data = [data]
    if route()["current_role"] == "Evaluator":
        extra = read(P / "evidence/l3_review/COST.json")
        need(extra["schema"] == data["schema"] and extra["l2_attempts"] == 0 and extra["l3_attempts"] == 1 and bool(extra["windows"]) and all(w["role"] == "Evaluator" for w in extra["windows"]), "independent evaluator cost")
        all_data.append(extra)
    totals, spans, previous = {"Executor": 0.0, "Evaluator": 0.0}, {}, None
    now = datetime.now(timezone.utc)
    for ledger in all_data:
        need(ledger["external_actions"] == read(P / "SPEC.json")["side_effect_limits"], "external actions")
        for win in ledger["windows"]:
            need("end_utc" in win, "end key")
            begin = datetime.fromisoformat(win["begin_utc"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(win["end_utc"].replace("Z", "+00:00")) if win["end_utc"] else now
            need(begin <= end <= now and (previous is None or begin >= previous), "cost ordering")
            previous = end
            totals[win["role"]] += (end - begin).total_seconds()/60
            spans.setdefault(win["role"], [begin, end])[1] = end
    need(totals["Executor"] <= 105 and totals["Evaluator"] <= 45 and sum(totals.values()) <= 150, "cost budget")
    need(all((end-begin).total_seconds() <= (4 if role == "Executor" else 2)*3600 for role,(begin,end) in spans.items()), "wall span")
    need(type(data["l2_attempts"]) is int and 0 <= data["l2_attempts"] <= 2, "L2 budget")
    l2 = sorted(p.name for p in (P/"evidence").glob("l2_attempt_*") if p.is_dir())
    need(l2 == [f"l2_attempt_{i:03d}" for i in range(1,data["l2_attempts"]+1)], "L2 directories")
    print(json.dumps({"charged_role_windows_minutes": totals, "actual_active_time": "UNKNOWN"}))
if __name__ == "__main__":
    try:
        mode = sys.argv[1]
        if mode == "final": preservation(); budget()
        else: {"package": package, "preservation": preservation, "baseline": baseline, "regressions": regressions, "impact": impact}[mode]()
        print(json.dumps({"check": mode, "status": "PASS"}))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__, "reason": str(exc) if isinstance(exc, ValueError) else "input or environment unavailable"}))
        sys.exit(1)
