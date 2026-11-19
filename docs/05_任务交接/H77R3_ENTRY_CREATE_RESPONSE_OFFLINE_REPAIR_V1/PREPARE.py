"""Evaluator-owned snapshot and freeze; no services, issuance, WSL, or network."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1"
RUN = OLD / "evidence/evaluator_runs/fef81b90a6594345b1212498ee52f90d"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def capture():
    refs = P / "references/before_repair"
    refs.mkdir(parents=True, exist_ok=False)
    for name, rel in (("CURRENT_REJECTED.md", "CURRENT.md"), ("REMOTE_HANDOFF.md", "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r131.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        shutil.copyfile(ROOT / rel, refs / name)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261117_r131.md"
    if archive.exists():
        assert sha(archive) == sha(refs / "PROJECT_BOTTLENECK_MAP_r131.md")
    else:
        shutil.copyfile(refs / "PROJECT_BOTTLENECK_MAP_r131.md", archive)
    for name in ("WORKLOAD.py", "TASK_TESTS.py", "RUN.py", "BINARY_MEMBER_LOCK.json"):
        assert not (P / name).exists()
        shutil.copyfile(OLD / name, P / name)
    fixtures = P / "fixtures"
    fixtures.mkdir()
    origins = {"entry_create.redacted.json": RUN / "raw/013_entry_create.stdout.log", "agent_list.redacted.json": RUN / "raw/012_agent_list_1.stdout.log"}
    records = {}
    for name, source in origins.items():
        raw = source.read_bytes()
        assert b"PRIVATE KEY-----" not in raw
        assert b"[REDACTED_JOIN_TOKEN]" in raw
        shutil.copyfile(source, fixtures / name)
        records[name] = {"source": source.relative_to(ROOT).as_posix(), "sha256": sha(source), "projection": "complete historical CLI text with explicit join-token redaction; not a fresh issuance"}
    save(P / "SOURCE_LOCK.json", {"schema": "h77r3-actual-cli-response-input/v1", "parent_task": OLD.name, "parent_workload_sha256": sha(OLD / "WORKLOAD.py"), "fixtures": records, "parent_l3_result": "FAIL", "parent_issuer_attempts": 1, "parent_services_started": 2, "new_issuer_authority": False})
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
    (refs / "final_workflow.stdout.log").write_bytes(result.stdout)
    (refs / "final_workflow.stderr.log").write_bytes(result.stderr)
    assert result.returncode == 0
    print(json.dumps({"snapshot": "PASS", "parent_final_state": "REJECTED", "actual_response_fixtures": len(records), "new_issuer_runs": 0}))


def freeze():
    import yaml
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == P.name and route["state"] == "CONTRACT_FROZEN"
    assert route["project_map_revision"] == "2026-11-17-r132"
    assert all(route.get(k) is False for k in ("authorization_local_service", "authorization_existing_wsl", "authorization_ephemeral_test_credentials", "authorization_api_call", "authorization_commit", "authorization_push"))
    refs = P / "references/before_repair"
    inherited = read(OLD / "evidence/ACCEPTED.json")["files"]
    aliases = {
        "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": refs / "PROJECT_BOTTLENECK_MAP_r131.md",
        "REMOTE_HANDOFF.md": refs / "REMOTE_HANDOFF.md",
    }
    protected = {}
    for rel, digest in inherited.items():
        path = aliases.get(rel, ROOT / rel)
        assert path.is_file() and sha(path) == digest, "inherited drift: " + rel
        protected[path.relative_to(ROOT).as_posix()] = digest
    for path in OLD.rglob("*"):
        if path.is_file() and "runtime" not in path.relative_to(OLD).parts and "__pycache__" not in path.parts:
            protected[path.relative_to(ROOT).as_posix()] = sha(path)
    for rel in ("docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", "REMOTE_HANDOFF.md"):
        protected[rel] = sha(ROOT / rel)
    common = read(OLD / "BASELINE.json")["common_protected"]
    for rel, digest in common.items():
        assert sha(ROOT.parent / "localagent-common" / rel) == digest
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == "61414d05521f7c9fe15cf0299b48b25916f5fa0e"
    save(P / "BASELINE.json", {"head": head, "at_utc": datetime.now(timezone.utc).isoformat(), "files": protected, "common_protected": common, "historical_governance_aliases": {key: value.relative_to(ROOT).as_posix() for key, value in aliases.items()}, "parent_accepted_files": len(inherited), "parent_immutable_files_unchanged": True})
    frozen = {path.relative_to(P).as_posix(): sha(path) for path in P.rglob("*") if path.is_file() and path.name not in ("WORKLOAD.py", "FREEZE.json") and "__pycache__" not in path.parts and "runtime" not in path.relative_to(P).parts}
    save(P / "FREEZE.json", {"schema": "h77r3-freeze/v1", "files": frozen})
    print(json.dumps({"freeze": "PASS", "protected": len(protected), "frozen": len(frozen), "issuer_budget": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("capture", "freeze"))
    args = parser.parse_args()
    globals()[args.action]()

