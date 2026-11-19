"""Prepare a reviewable candidate; only Evaluator authority can seal it."""
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
R2 = P.parent / "H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1"
R3 = P.parent / "H77R3_ENTRY_CREATE_RESPONSE_OFFLINE_REPAIR_V1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def prepare():
    refs = P / "references/before_executor_completion"
    refs.mkdir(parents=True, exist_ok=False)
    for name in ("CONTRACT.md", "AUTHORIZATION_REQUEST.md"):
        shutil.copyfile(P / name, refs / name)
    for name, rel in (("CURRENT.md", "CURRENT.md"), ("REMOTE_HANDOFF.md", "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r132.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        shutil.copyfile(ROOT / rel, refs / name)
    inherited = read(R3 / "evidence/ACCEPTED.json")["files"]
    for rel, digest in inherited.items():
        assert sha(ROOT / rel) == digest, "accepted source drift: " + rel
    protected = dict(inherited)
    for task in (R2, R3):
        for path in task.rglob("*"):
            if path.is_file() and "runtime" not in path.relative_to(task).parts and "__pycache__" not in path.parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    copies = {
        "WORKLOAD.py": R3 / "WORKLOAD.py", "RUN.py": R3 / "RUN.py",
        "TASK_TESTS.py": R3 / "TASK_TESTS.py", "BINARY_MEMBER_LOCK.json": R3 / "BINARY_MEMBER_LOCK.json",
        "AUDIT.py": R2 / "AUDIT.py", "CHECK.py": R2 / "CHECK.py",
        "BOOTSTRAP.py": R2 / "BOOTSTRAP.py", "ASSET_PREFLIGHT.py": R2 / "ASSET_PREFLIGHT.py",
        "PROTOCOL_CHECK.py": R3 / "CHECK.py",
        "evidence/preparation/H76_INPUT_SEAL.json": R2 / "evidence/preparation/H76_INPUT_SEAL.json",
    }
    records = {}
    for name, source in copies.items():
        assert not (P / name).exists(), name
        (P / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, P / name)
        records[name] = {"source": source.relative_to(ROOT).as_posix(), "initial_sha256": sha(source), "copy_rule": "candidate_adaptation" if name in ("CHECK.py", "BOOTSTRAP.py") else "byte_exact"}
    fixtures = P / "fixtures"
    fixtures.mkdir()
    for path in (R3 / "fixtures").iterdir():
        if path.is_file():
            shutil.copyfile(path, fixtures / path.name)
    source = read(R3 / "SOURCE_LOCK.json")
    source["h78_origin"] = {"h77r3_accepted": sha(R3 / "evidence/ACCEPTED.json"), "h77r3_review": sha(R3 / "REVIEW.md"), "new_issuance_in_preparation": False}
    save(P / "SOURCE_LOCK.json", source)
    save(P / "COPY_MANIFEST.json", {"schema": "h78-source-copy/v1", "files": records})
    common = read(R3 / "BASELINE.json")["common_protected"]
    for rel, digest in common.items():
        assert sha(ROOT.parent / "localagent-common" / rel) == digest
    save(P / "PREPARATION_BASELINE.json", {"schema": "h78-preparation-baseline/v1", "at_utc": datetime.now(timezone.utc).isoformat(), "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "protected": protected, "common_protected": common, "router_sha256": sha(ROOT / "CURRENT.md"), "parent_accepted_count": len(inherited), "governance_snapshots": {"CURRENT.md": "references/before_executor_completion/CURRENT.md", "REMOTE_HANDOFF.md": "references/before_executor_completion/REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": "references/before_executor_completion/PROJECT_BOTTLENECK_MAP_r132.md"}})
    print(json.dumps({"candidate_copied": len(records), "parent_accepted_preserved": len(inherited), "protected": len(protected), "authority_changed": False, "wsl_calls": 0}))


def seal():
    import yaml
    import CONTROL as c
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    c.need((route["task_id"], route["state"], route["current_role"]) == (P.name, "CONTRACT_FROZEN", "Executor"), "Evaluator must freeze and route H78 first")
    c.need("Contract state: CONTRACT_FROZEN" in (P / "CONTRACT.md").read_text(encoding="utf-8"), "contract still draft")
    project_map = (ROOT / route["project_map_path"]).read_text(encoding="utf-8")
    c.need("Map revision: " + route["project_map_revision"] in project_map and "Hypothesis ID: H-78" in project_map and "Active bottleneck ID: B-15" in project_map, "Evaluator map/hypothesis update missing")
    authority = read(P / "AUTHORIZATION.json")
    c.need(authority["status"] == "GRANTED" and authority.get("owner_quote") and authority.get("source"), "explicit owner decision missing")
    for key in ("authorization_existing_wsl", "authorization_local_service", "authorization_ephemeral_test_credentials"):
        c.need(route.get(key) is True and authority["flags"].get(key) is True, "missing H78 permission: " + key)
    for key in ("authorization_commit", "authorization_push", "authorization_api_call", "authorization_install", "authorization_artifact_download", "authorization_test_payments"):
        c.need(route.get(key) is False, "permission exceeds H78: " + key)
    baseline = read(P / "PREPARATION_BASELINE.json")
    c.need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD changed before freeze")
    protected = {}
    for rel, digest in baseline["protected"].items():
        source = ROOT / rel
        if rel in baseline["governance_snapshots"]:
            source = P / baseline["governance_snapshots"][rel]
        c.need(sha(source) == digest, "old immutable input drift: " + rel)
        protected[source.relative_to(ROOT).as_posix()] = digest
    for rel, digest in baseline["common_protected"].items():
        c.need(sha(ROOT.parent / "localagent-common" / rel) == digest, "shared workflow drift")
    for rel in ("docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", "REMOTE_HANDOFF.md"):
        protected[rel] = sha(ROOT / rel)
    save(P / "BASELINE.json", {"head": baseline["head"], "protected": protected, "common_protected": baseline["common_protected"], "governance_aliases": baseline["governance_snapshots"]})
    files = {path.relative_to(P).as_posix(): sha(path) for path in P.rglob("*") if path.is_file() and "runtime" not in path.relative_to(P).parts and "__pycache__" not in path.parts and path.name not in ("FREEZE.json", "CANDIDATE_MANIFEST.json")}
    save(P / "FREEZE.json", {"schema": "h78-frozen-measurement/v1", "files": files})
    print(json.dumps({"frozen_files": len(files), "protected": len(protected), "authority_source": authority["source"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "seal"))
    globals()[parser.parse_args().action]()
