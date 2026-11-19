"""Evaluator freezes repair scope and old-byte aliases; never changes product."""
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
OLD = P.parent / "H79_VERIFIED_FACT_CONTEXT_CONSUMER_MEASUREMENT_V1"
PRODUCT = ["src/agentic_payment_experiment/trusted_execution/credential_possession.py", "src/agentic_payment_experiment/trusted_execution/execution_facts.py", "tests/trusted_execution/test_payment_binding.py"]
NEW_TEST = "tests/trusted_execution/test_credential_context_consumption.py"
MAP = "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def snapshot():
    accepted = read(OLD / "evidence/ACCEPTED.json")
    for rel, digest in accepted["files"].items():
        assert sha(ROOT / rel) == digest, rel
    refs = P / "references/before_h80"
    refs.mkdir(parents=True, exist_ok=False)
    for rel in ["CURRENT.md", "REMOTE_HANDOFF.md", MAP, *PRODUCT]:
        dest = refs / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261117_r134.md"
    assert not archive.exists()
    shutil.copyfile(ROOT / MAP, archive)
    shutil.copyfile(OLD / "SOURCE.json", P / "SOURCE.json")
    save(P / "PARENT_ACCEPTANCE_CHECK.json", {"accepted_unchanged_before_governance": len(accepted["files"]), "parent_review_sha256": sha(OLD / "REVIEW.md"), "product_edits": 0})
    print(json.dumps({"accepted_unchanged": len(accepted["files"]), "snapshots": 6, "product_edits": 0}))


def freeze():
    refs = P / "references/before_h80"
    aliases = {rel: (refs / rel).relative_to(ROOT).as_posix() for rel in [MAP, "REMOTE_HANDOFF.md", *PRODUCT]}
    protected = {}
    for rel, digest in read(OLD / "evidence/ACCEPTED.json")["files"].items():
        target = aliases.get(rel, rel)
        assert sha(ROOT / target) == digest, rel
        protected[target] = digest
    # L3 is created after parent acceptance and evidence may be Git-ignored.
    for path in OLD.rglob("*"):
        if path.is_file() and "runtime" not in path.relative_to(OLD).parts and "__pycache__" not in path.parts:
            protected[path.relative_to(ROOT).as_posix()] = sha(path)
    # Protect all pre-existing non-runtime files, including inherited uncommitted work.
    inventory = subprocess.check_output(["git", "ls-files", "-c", "-o", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    for rel in inventory:
        path = ROOT / rel
        if not rel or not path.is_file() or rel == "CURRENT.md" or path.is_relative_to(P) or any(part in {"runtime", "__pycache__"} for part in path.parts):
            continue
        target = aliases.get(rel, rel)
        protected[target] = sha(ROOT / target)
    for rel in [MAP, "REMOTE_HANDOFF.md"]:
        protected[rel] = sha(ROOT / rel)
    common = read(OLD / "BASELINE.json")["common_protected"]
    for rel, digest in common.items():
        assert sha(ROOT.parent / "localagent-common" / rel) == digest
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == "61414d05521f7c9fe15cf0299b48b25916f5fa0e"
    assert not (ROOT / NEW_TEST).exists()
    save(P / "BASELINE.json", {"head": head, "files": protected, "common_protected": common, "historical_aliases": aliases, "mutable": PRODUCT + [NEW_TEST], "existing_inventory": sorted(set(filter(None, inventory))), "initial_mutable_sha256": {rel: sha(ROOT / rel) for rel in PRODUCT}})
    syntax = []
    for path in P.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
        syntax.append(path.name)
    import yaml
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    assert plan["task_id"] == P.name and len(plan["checks"]) == 4
    for item in plan["checks"]:
        assert item["command"][2] == (P / "CHECK.py").relative_to(ROOT).as_posix()
    save(P / "READINESS.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "package_ready": True, "syntax_checked": syntax, "protected_files": len(protected), "product_edits": 0, "behavior_runs": 0, "formal_l2": 0, "formal_l3": 0, "new_issuer_runs": 0})
    files = {path.relative_to(P).as_posix(): sha(path) for path in P.rglob("*") if path.is_file() and path.name != "FREEZE.json" and "__pycache__" not in path.parts}
    save(P / "FREEZE.json", {"files": files})
    print(json.dumps({"frozen_files": len(files), "protected_files": len(protected), "product_edits": 0, "behavior_runs": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "freeze"))
    globals()[parser.parse_args().action]()
