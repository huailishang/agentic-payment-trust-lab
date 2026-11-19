"""Evaluator activation snapshots and read-only handoff verification; never executes H72."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PACK = Path(__file__).resolve().parent
MAP = ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
BEFORE = PACK / "references/before_activation"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, "refuse snapshot overwrite"
    else:
        path.write_bytes(raw)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def dump(path, value):
    save(path, (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode())

def lsfiles(*args):
    result = subprocess.run(["git", "ls-files", *args, "-z"], cwd=ROOT, capture_output=True, check=True)
    return [p.decode("utf-8") for p in result.stdout.split(b"\0") if p]

def archive():
    old = read(PACK / "BASELINE.json")
    for rel, expected in old["protected"].items():
        assert sha(ROOT / rel) == expected, rel
    for group in ("frozen", "references"):
        for rel, expected in old[group].items():
            assert sha(PACK / rel) == expected, rel
    snapshots = {}
    for name in (*old["frozen"], "BASELINE.json", "PREPARATION.md"):
        path = PACK / name
        save(BEFORE / "task" / name, path.read_bytes())
        snapshots["task/" + name] = sha(path)
    for path in (ROOT / "CURRENT.md", ROOT / "REMOTE_HANDOFF.md", MAP):
        save(BEFORE / "governance" / path.name, path.read_bytes())
        snapshots["governance/" + path.name] = sha(path)
    save(MAP.parent / "archive/PROJECT_BOTTLENECK_MAP_20261115_r119.md", MAP.read_bytes())
    dump(BEFORE / "SNAPSHOT.json", snapshots)
    print(json.dumps({"pre_activation_archive": "PASS", "snapshots": len(snapshots),
                      "prior_protected_verified": len(old["protected"])}))

def seal():
    old = read(BEFORE / "task/BASELINE.json")
    governance = {"REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"}
    for rel, expected in old["protected"].items():
        if rel not in governance:
            assert sha(ROOT / rel) == expected, "unapproved drift: " + rel
    for rel, expected in old["allowed_product_initial"].items():
        assert sha(ROOT / rel) == expected, "activation modified product: " + rel
    modified_control = {"CONTRACT.md", "SPEC.json", "EXECUTOR_START.md", "AUTHORIZATION.md", "AUTHORIZATION.json", "PREPARE.py"}
    for name, expected in old["frozen"].items():
        if name not in modified_control:
            assert sha(PACK / name) == expected, "unexpected control change: " + name
    paths = set(old["protected"]) | set(lsfiles("-c", "-o", "--exclude-standard"))
    prefix = PACK.relative_to(ROOT).as_posix() + "/"
    protected = {rel: sha(ROOT / rel) for rel in sorted(paths)
                 if rel != "CURRENT.md" and rel not in old["allowed_product_initial"]
                 and not rel.startswith(prefix) and (ROOT / rel).is_file()}
    names = [*old["frozen"], "FREEZE.py", "AUTONOMY.md"]
    references = {p.relative_to(PACK).as_posix(): sha(p)
                  for p in (PACK / "references").rglob("*") if p.is_file()}
    value = {**old, "state": "CONTRACT_FROZEN", "project_map_revision": "2026-11-15-r120",
             "protected": protected, "frozen": {name: sha(PACK / name) for name in names},
             "references": references,
             "inherited_untracked": [p for p in lsfiles("--others", "--exclude-standard") if not p.startswith(prefix)],
             "current_route_at_seal_sha256": sha(ROOT / "CURRENT.md"),
             "authorization_sha256": sha(PACK / "AUTHORIZATION.json"),
             "draft_baseline_sha256": sha(BEFORE / "task/BASELINE.json"),
             "activation_note": "Human grant recorded; explicit in-scope autonomy/retry amendment; immutable history and test plan retained"}
    # Deliberate Evaluator replacement after preserving the exact draft bytes above.
    (PACK / "BASELINE.json").write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"freeze_seal": "PASS", "protected_files": len(protected),
                      "frozen_files": len(names), "references": len(references),
                      "baseline_sha256": sha(PACK / "BASELINE.json")}))

def verify():
    baseline = read(PACK / "BASELINE.json")
    assert baseline["state"] == "CONTRACT_FROZEN"
    for rel, expected in baseline["protected"].items():
        assert sha(ROOT / rel) == expected, rel
    for group in ("frozen", "references"):
        for rel, expected in baseline[group].items():
            assert sha(PACK / rel) == expected, rel
    for rel, expected in baseline["allowed_product_initial"].items():
        assert sha(ROOT / rel) == expected, rel
    for rel, node in baseline["special_nodes"].items():
        assert (ROOT / rel).lstat().st_reparse_tag == node["reparse_tag"]
        query = subprocess.run(["fsutil", "reparsepoint", "query", str(ROOT / rel)],
                               cwd=ROOT, capture_output=True, check=True)
        assert hashlib.sha256(query.stdout).hexdigest() == node["query_stdout_sha256"], rel
    auth = read(PACK / "AUTHORIZATION.json")
    assert auth["status"] == "GRANTED" and auth["grant_quote"]
    assert datetime.fromisoformat(auth["expires_at_utc"].replace("Z", "+00:00")) > datetime.fromisoformat(auth["granted_at_utc"].replace("Z", "+00:00"))
    for name, flag in auth["flags"].items():
        assert flag is (name not in {"authorization_commit", "authorization_push", "authorization_history_rewrite"})
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    assert "state: CONTRACT_FROZEN" in current and "current_role: Executor" in current
    for name, flag in auth["flags"].items():
        assert name + ": " + str(flag).lower() in current
    common = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts"
    sys.path.insert(0, str(common))
    import validate_workflow as workflow
    import run_validation as runner
    findings = workflow.validate(ROOT, ROOT / "CURRENT.md")
    assert all(f.level == "OK" for f in findings), [(f.level, f.message) for f in findings]
    for mode in ("executor", "evaluator"):
        task, checks = runner.load_plan(ROOT, PACK / "VALIDATION_PLAN.yaml", mode=mode)
        assert task == PACK.name and len(checks) == 15
    assert sha(PACK / "VALIDATION_PLAN.yaml") == sha(BEFORE / "task/VALIDATION_PLAN.yaml")
    supersession = read(PACK / "SUPERSESSION.json")
    assert all(sha(ROOT / rel) == expected for rel, expected in supersession["previous_task_files"].items())
    assert not (PACK / "REPORT.md").exists() and not list(PACK.rglob("L2-GATE.json")) and not list(PACK.rglob("L3-GATE.json"))
    spec = read(PACK / "SPEC.json")
    assert spec["budgets"]["checkout_sessions"] == 4 and spec["budgets"]["payment_submissions"] == 3
    assert spec["retry_policy"]["read_only_max_attempts_per_unit"] == 4
    print(json.dumps({"frozen_handoff_verification": "PASS", "state": "CONTRACT_FROZEN",
                      "role": "Executor", "authorization": "GRANTED", "plan_checks": 15,
                      "old_h71r3_files_preserved": len(supersession["previous_task_files"]),
                      "protected_files": len(baseline["protected"]), "product_changes": 0,
                      "formal_l2_l3_runs": 0, "runtime_api_calls": 0}))

if __name__ == "__main__":
    actions = {"archive": archive, "seal": seal, "verify": verify}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit("archive | seal | verify")
    actions[sys.argv[1]]()
