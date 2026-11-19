"""Historical draft-only preparation. Current authorized handoff uses FREEZE.py verify.

Never runs payments or task gates; old draft expectations are preserved intentionally.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PACK = Path(__file__).resolve().parent
OLD = PACK.parent / "H71R3_CONDA_AGENT_TEST_IMPORT_ISOLATION_V1"
MAP = ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
TASK = PACK.name

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, "refuse to replace existing snapshot: " + str(path)
    else:
        path.write_bytes(raw)

def output(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode())

def lsfiles(*args):
    raw = subprocess.run(["git", "ls-files", *args, "-z"], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return [p.decode("utf-8") for p in raw.split(b"\0") if p]

def history_files():
    return [p for p in OLD.rglob("*") if "__pycache__" not in p.parts
            and p.suffix != ".pyc" and p.is_file()]

def assert_old_snapshot():
    baseline = json.loads((OLD / "BASELINE.json").read_text(encoding="utf-8"))
    for rel, expected in baseline["protected"].items():
        assert sha(ROOT / rel) == expected, "pre-merge protected drift: " + rel
    for group in ("frozen", "references"):
        for rel, expected in baseline[group].items():
            assert sha(OLD / rel) == expected, "pre-merge frozen drift: " + rel
    assert not (OLD / "REPORT.md").exists()
    assert not list(OLD.rglob("L2-GATE.json")) and not list(OLD.rglob("L3-GATE.json"))
    return baseline

def archive():
    previous = assert_old_snapshot()
    saved = {}
    for path in [ROOT / "CURRENT.md", ROOT / "REMOTE_HANDOFF.md", MAP]:
        target = PACK / "references/governance_before_merge" / path.name
        write_new(target, path.read_bytes())
        saved[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in ("CONTRACT.md", "VALIDATION_PLAN.yaml", "BASELINE.json", "AMENDMENT_01.md", "EVALUATOR_BASIS.md", "REASSESSMENT_20261114.md"):
        path = OLD / name
        write_new(PACK / "references/h71r3_before_merge" / name, path.read_bytes())
        saved[path.relative_to(ROOT).as_posix()] = sha(path)
    write_new(MAP.parent / "archive/PROJECT_BOTTLENECK_MAP_20261114_r118.md", MAP.read_bytes())
    output(PACK / "references/ORIGINAL_SNAPSHOT.json", saved)
    manifest = {p.relative_to(ROOT).as_posix(): sha(p) for p in history_files()}
    output(PACK / "SUPERSESSION.json", {
        "schema": "h72-explicit-unexecuted-supersession/v1", "task_id": TASK,
        "prepared_date": "2026-11-15", "previous_task": OLD.name,
        "previous_status": "CONTRACT_FROZEN_UNEXECUTED", "status": "SUPERSEDED_UNEXECUTED",
        "human_preparation_quote": "那你把那个收尾包的工作和这个承包都写到一起，然后我让执行者去执行",
        "scope": "P0 imports the local closeout obligations; final independent review remains mandatory",
        "previous_formal_l2_count": 0, "previous_formal_l3_count": 0,
        "historical_verdicts_rehabilitated": False, "prior_external_authority_inherited": False,
        "previous_task_files": manifest, "prior_protected_verified": len(previous["protected"]),
        "activation_pending_fresh_human_authority": True})
    print(json.dumps({"archive": "PASS", "original_snapshots": len(saved),
                      "previous_task_files": len(manifest), "old_protected_verified": len(previous["protected"])}))

def seal():
    old = json.loads((OLD / "BASELINE.json").read_text(encoding="utf-8"))
    spec = json.loads((PACK / "SPEC.json").read_text(encoding="utf-8"))
    paths = set(old["protected"]) | set(lsfiles("-c", "-o", "--exclude-standard"))
    paths.update(p.relative_to(ROOT).as_posix() for p in history_files())
    prefix = PACK.relative_to(ROOT).as_posix() + "/"
    mutable = {}
    for rel in spec["allowed_product_files"]:
        path = ROOT / rel
        mutable[rel] = sha(path)
        write_new(PACK / "references/product_before" / rel, path.read_bytes())
    assert not (ROOT / spec["allowed_new_test"]).exists(), "new-test path already occupied"
    protected = {rel: sha(ROOT / rel) for rel in sorted(paths)
                 if rel != "CURRENT.md" and rel not in mutable and not rel.startswith(prefix)
                 and (ROOT / rel).is_file()}
    frozen_names = ("CONTRACT.md", "SPEC.json", "VALIDATION_PLAN.yaml", "EXECUTOR_START.md",
                    "AUTHORIZATION.md", "AUTHORIZATION.json", "SOURCE_LOCK.json", "RESOURCE.txt",
                    "SUPERSESSION.json", "PREPARE.py")
    frozen = {name: sha(PACK / name) for name in frozen_names}
    references = {p.relative_to(PACK).as_posix(): sha(p) for p in (PACK / "references").rglob("*") if p.is_file()}
    output(PACK / "BASELINE.json", {
        "schema": "h72-preservation-baseline/v1", "task_id": TASK,
        "state": "DRAFT_PENDING_NEW_AUTHORIZATION", "head": old["head"],
        "project_map_revision": "2026-11-15-r119", "protected": protected,
        "special_nodes": old["special_nodes"], "allowed_product_initial": mutable,
        "frozen": frozen, "references": references,
        "inherited_untracked": [p for p in lsfiles("--others", "--exclude-standard") if not p.startswith(prefix)],
        "current_route_at_seal_sha256": sha(ROOT / "CURRENT.md"),
        "historical_h71r2_gate_sha256": old["historical_gate_sha256"],
        "allowed_new_test": spec["allowed_new_test"],
        "activation_note": "Preserve this draft baseline before explicit authorization/freeze; Evaluator reseals changed governance only, without weakening old input checks"})
    print(json.dumps({"draft_seal": "PASS", "protected": len(protected), "frozen": len(frozen),
                      "references": len(references), "mutable_product_files": len(mutable),
                      "special_nodes": len(old["special_nodes"]), "baseline_sha256": sha(PACK / "BASELINE.json")}))

def verify():
    baseline = json.loads((PACK / "BASELINE.json").read_text(encoding="utf-8"))
    for rel, expected in baseline["protected"].items():
        assert sha(ROOT / rel) == expected, rel
    for group in ("frozen", "references"):
        for rel, expected in baseline[group].items():
            assert sha(PACK / rel) == expected, rel
    for rel, expected in baseline["allowed_product_initial"].items():
        assert sha(ROOT / rel) == expected, "preparation changed product: " + rel
    for rel, node in baseline["special_nodes"].items():
        assert (ROOT / rel).lstat().st_reparse_tag == node["reparse_tag"]
        query = subprocess.run(["fsutil", "reparsepoint", "query", str(ROOT / rel)], cwd=ROOT,
                               capture_output=True, check=True)
        assert hashlib.sha256(query.stdout).hexdigest() == node["query_stdout_sha256"], rel
    supersession = json.loads((PACK / "SUPERSESSION.json").read_text(encoding="utf-8"))
    for rel, expected in supersession["previous_task_files"].items():
        assert sha(ROOT / rel) == expected, "old H71R3 modified: " + rel
    auth = json.loads((PACK / "AUTHORIZATION.json").read_text(encoding="utf-8"))
    assert auth["status"] == "PENDING_HUMAN" and auth["grant_quote"] is None
    assert all(value is False for value in auth["flags"].values())
    common = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts"
    sys.path.insert(0, str(common))
    import validate_workflow as workflow
    import run_validation as runner
    findings, acs, plan_ref = workflow.validate_contract(
        PACK / "CONTRACT.md", task_id=TASK, baseline=baseline["head"], version="v2.2",
        task_kind="capability_experiment", project_map_path="docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md",
        map_revision="2026-11-15-r119", bottleneck_id="B-21", hypothesis_id="H-72")
    findings += workflow.validate_v22_plan(ROOT, ROOT / plan_ref, task_id=TASK, contract_acs=acs)
    findings += workflow.validate_project_map(MAP, revision="2026-11-15-r119", bottleneck_id="B-21", hypothesis_id="H-72")
    assert not findings, [(f.level, f.message) for f in findings]
    for mode in ("executor", "evaluator"):
        task, checks = runner.load_plan(ROOT, PACK / "VALIDATION_PLAN.yaml", mode=mode)
        assert task == TASK and len(checks) == 15 and all(c.mandatory for c in checks)
    assert acs == {f"AC-{i:02d}" for i in range(1, 13)}
    old_plan = json.loads((OLD / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    plan = json.loads((PACK / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    assert [c["command"] for c in old_plan["checks"][2:7]] == [c["command"] for c in plan["checks"][2:7]]
    assert not (PACK / "REPORT.md").exists() and not list(PACK.rglob("L2-GATE.json")) and not list(PACK.rglob("L3-GATE.json"))
    print(json.dumps({"preparation_verification": "PASS", "prospective_contract_and_plan": "VALID",
                      "draft_not_execution_authority": True, "protected_files": len(baseline["protected"]),
                      "original_h71r3_files_preserved": len(supersession["previous_task_files"]),
                      "acceptance_criteria": len(acs), "plan_checks": 15,
                      "new_formal_gates": 0, "product_modified_during_preparation": False}))

if __name__ == "__main__":
    actions = {"archive": archive, "seal": seal, "verify": verify}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit("archive | seal | verify")
    actions[sys.argv[1]]()
