"""Evaluator-only initial freeze. Never run by Executor or to accept drift."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
MUTABLE = {"PROJECTOR.py", "INPUT_LINEAGE.md", "ANALYSIS.md", "DEMO.md", "RESULT.json",
           "ATTEMPT_LEDGER.json", "REPORT.md"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    target = TASK / "BASELINE.json"
    assert not target.exists(), "initial freeze only; do not replace a baseline"
    names = [x.decode("utf-8") for x in subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).split(b"\0") if x]
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    protected = {x: sha(ROOT / x) for x in names if x != "CURRENT.md" and not x.startswith(prefix) and (ROOT / x).is_file()}
    common = ROOT.parent / "localagent-common"
    for folder in [common / "skills/evaluator-executor-workflow", common / "security-hooks"]:
        for path in folder.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                protected["../localagent-common/" + path.relative_to(common).as_posix()] = sha(path)
    frozen = {p.relative_to(TASK).as_posix(): sha(p) for p in TASK.rglob("*") if p.is_file()
              and p.name not in MUTABLE and p.name != "BASELINE.json"
              and "__pycache__" not in p.parts and not p.relative_to(TASK).as_posix().startswith("evidence/")}
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    data = {"schema": "h48-baseline/v1", "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workspace_files": sorted(names), "protected_files": protected, "frozen_files": frozen,
        "current_narrative_sha256": hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest()}
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen)}))
