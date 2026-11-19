"""Evaluator source seal and offline package readiness; never runs the matrix."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def snapshot():
    refs = P / "references/before_h79"
    refs.mkdir(parents=True, exist_ok=False)
    for name, rel in (("CURRENT_H78_PASS.md", "CURRENT.md"), ("REMOTE_HANDOFF.md", "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r133.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        shutil.copyfile(ROOT / rel, refs / name)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261117_r133.md"
    if archive.exists():
        assert sha(archive) == sha(refs / "PROJECT_BOTTLENECK_MAP_r133.md")
    else:
        shutil.copyfile(refs / "PROJECT_BOTTLENECK_MAP_r133.md", archive)
    source = OLD / "evidence/evaluator_runs/7efc9f24b12c47389c5aee779843c425"
    inputs = {name: sha(source / name) for name in ("RESULT.json", "root.pem", "leaf.pem", "payload.bin", "signature.b64", "SOURCE.json", "PUBLIC_INDEX.json")}
    save(P / "SOURCE.json", {"schema": "h79-captured-h78-input/v1", "source_directory": source.relative_to(ROOT).as_posix(), "public_inputs": inputs, "source_review": (OLD / "REVIEW.md").relative_to(ROOT).as_posix(), "source_review_sha256": sha(OLD / "REVIEW.md"), "time_mode": "captured observation; not current authentication"})
    for rel, digest in read(OLD / "evidence/ACCEPTED.json")["files"].items():
        assert sha(ROOT / rel) == digest, "parent accepted drift before governance: " + rel
    print(json.dumps({"parent_accepted_unchanged": 2229, "source_public_inputs": len(inputs), "measurement_runs": 0}))


def freeze():
    refs = P / "references/before_h79"
    aliases = {"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": refs / "PROJECT_BOTTLENECK_MAP_r133.md", "REMOTE_HANDOFF.md": refs / "REMOTE_HANDOFF.md"}
    protected = {}
    for rel, digest in read(OLD / "evidence/ACCEPTED.json")["files"].items():
        source = aliases.get(rel, ROOT / rel)
        assert sha(source) == digest, "historical accepted drift: " + rel
        protected[source.relative_to(ROOT).as_posix()] = digest
    for path in OLD.rglob("*"):
        if path.is_file() and "runtime" not in path.relative_to(OLD).parts and "__pycache__" not in path.parts:
            protected[path.relative_to(ROOT).as_posix()] = sha(path)
    for rel in ("docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", "REMOTE_HANDOFF.md"):
        protected[rel] = sha(ROOT / rel)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == "61414d05521f7c9fe15cf0299b48b25916f5fa0e"
    common = read(OLD / "BASELINE.json")["common_protected"]
    for rel, digest in common.items():
        assert sha(ROOT.parent / "localagent-common" / rel) == digest
    save(P / "BASELINE.json", {"head": head, "files": protected, "common_protected": common, "historical_aliases": {key: value.relative_to(ROOT).as_posix() for key, value in aliases.items()}})
    syntax = []
    for path in P.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        syntax.append(path.name)
    import yaml
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    matrix = read(P / "SCENARIOS.json")
    assert plan["task_id"] == P.name and len(plan["checks"]) == 4
    assert [case["id"] for case in matrix["cases"]] == ["M01", "M02", "M03", "M04", "M05", "M06"]
    for check in plan["checks"]:
        for key in ("command", "evaluator_command"):
            if key in check:
                assert (ROOT / check[key][2]).is_file()
    save(P / "READINESS.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "package_ready": True, "syntax_checked": sorted(syntax), "protected_files": len(protected), "planned_probe_slots": 6, "measurement_runs": 0, "formal_l2": 0, "formal_l3": 0, "new_issuer_runs": 0, "source_mode": "captured H78 public observation, not current authentication"})
    files = {path.relative_to(P).as_posix(): sha(path) for path in P.rglob("*") if path.is_file() and path.name != "FREEZE.json" and "__pycache__" not in path.parts and "runtime" not in path.relative_to(P).parts}
    save(P / "FREEZE.json", {"files": files})
    print(json.dumps({"frozen_files": len(files), "protected_files": len(protected), "measurement_runs": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "freeze"))
    globals()[parser.parse_args().action]()

