"""Evaluator-only: record a real environment or freeze the prepared snapshot."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sys.argv[1:] == ["environment"]:
        packages = {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()}
        data = {"schema": "h47-environment/v1", "platform": "Windows", "python": ".".join(map(str, sys.version_info[:3])),
                "packages": dict(sorted(packages.items())), "runtime": ".task_envs/H47/.venv/Scripts/python.exe",
                "requirements_lock_sha256": sha(TASK / "requirements.lock"), "system_environment_modified": False}
        (TASK / "ENVIRONMENT.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"packages": len(packages), "python": data["python"]}))
        return
    assert sys.argv[1:] == ["baseline"]
    from EVALUATOR_CHECK import MUTABLE
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    files = sorted({name.decode("utf-8") for name in raw.split(b"\0") if name})
    task_rel = TASK.relative_to(ROOT).as_posix() + "/"
    protected = {path: sha(ROOT / path) for path in files if path != "CURRENT.md" and not path.startswith(task_rel) and (ROOT / path).is_file()}
    for name in ["SKILL.md", "scripts/run_validation.py", "scripts/validate_workflow.py", "scripts/capture_evidence.py"]:
        relative = "../localagent-common/skills/evaluator-executor-workflow/" + name
        protected[relative] = sha(ROOT / relative)
    frozen = {}
    for path in TASK.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(TASK).as_posix()
        if relative == "BASELINE.json" or relative in MUTABLE or relative.startswith("evidence/") or "__pycache__/" in relative:
            continue
        frozen[relative] = sha(path)
    data = {"schema": "h47-baseline/v1", "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "workspace_files": files, "protected_files": protected, "frozen_files": dict(sorted(frozen.items()))}
    # BASELINE is pinned by the frozen contract and final handoff digest; no self-hash.
    (TASK / "BASELINE.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"protected": len(protected), "frozen": len(frozen), "head": data["head"]}))


if __name__ == "__main__":
    main()
