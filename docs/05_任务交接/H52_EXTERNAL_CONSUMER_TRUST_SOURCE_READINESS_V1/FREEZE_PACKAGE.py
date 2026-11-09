"""Evaluator-only freeze inventory. Executor must not run or modify this script."""
import hashlib
import json
from pathlib import Path
import subprocess
from RUNTIME import TASK, ROOT

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    files = {name for name in subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0") if name}
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    protected = {name: sha(ROOT / name) for name in sorted(files)
                 if not name.startswith(prefix) and name != "CURRENT.md" and (ROOT / name).is_file()}
    for directory in (
        ROOT / "local_sources/third_party/ap2-v0.2.0",
        ROOT / ".task_envs/h37_ap2_crypto/lib/python3.12/site-packages/jwcrypto",
        ROOT / ".task_envs/h37_ap2_crypto/lib/python3.12/site-packages/sd_jwt"):
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in (".py", ".json", ".md") and ".logs" not in path.parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    license_path = ROOT / "local_sources/third_party/ap2-v0.2.0/LICENSE"
    protected[license_path.relative_to(ROOT).as_posix()] = sha(license_path)
    frozen = {p.relative_to(TASK).as_posix(): sha(p) for p in TASK.rglob("*")
              if p.is_file() and not p.is_relative_to(TASK / "evidence") and "__pycache__" not in p.parts and p.name != "BASELINE.json"}
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    assert "task_id: " + TASK.name in current and "state: CONTRACT_FROZEN" in current
    value = {"schema": "h52-frozen-baseline/v1", "head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workspace_files": sorted(files), "protected_files": protected, "frozen_files": frozen,
        "current_history_sha256": hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest()}
    path = TASK / "BASELINE.json"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen),
                      "baseline_sha256": sha(path), "executor_probe_implementation_present": (TASK / "PROBES.py").exists()}))
if __name__ == "__main__":
    main()
