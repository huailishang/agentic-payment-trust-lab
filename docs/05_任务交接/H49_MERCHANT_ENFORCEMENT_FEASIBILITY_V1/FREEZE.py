"""Evaluator-only initial baseline; never use to accept Executor drift."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
MUTABLE = {"SEAM_MAP.json", "SOURCE_AUDIT.md", "MECHANISM_COMPARISON.json", "COMPARISON.md",
    "BOUNDARY_DESIGN.json", "BOUNDARY_DESIGN.md", "VALIDATION_DESIGN.json", "VALIDATION_DESIGN.md",
    "BUSINESS_CHECK.md", "DECISION.json", "ATTEMPT_LEDGER.json", "REPORT.md"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    target = TASK / "BASELINE.json"
    assert not target.exists(), "initial freeze only"
    names = [x.decode("utf-8") for x in subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).split(b"\0") if x]
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    protected = {name: sha(ROOT / name) for name in names if name != "CURRENT.md" and not name.startswith(prefix)
        and (ROOT / name).is_file()}
    common = ROOT.parent / "localagent-common"
    for folder in [common / "skills/evaluator-executor-workflow", common / "security-hooks"]:
        for path in folder.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                protected["../localagent-common/" + path.relative_to(common).as_posix()] = sha(path)
    frozen = {p.relative_to(TASK).as_posix(): sha(p) for p in TASK.rglob("*") if p.is_file()
        and p.name not in MUTABLE and p.name != "BASELINE.json" and "__pycache__" not in p.parts
        and not p.relative_to(TASK).as_posix().startswith("evidence/")}
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    data = {"schema": "h49-baseline/v1", "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workspace_files": sorted(names), "protected_files": protected, "frozen_files": frozen,
        "current_history_sha256": hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest()}
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen)}))
