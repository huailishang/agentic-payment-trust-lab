"""H74 one-time native Windows preflight; do not change frozen files."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
EVIDENCE = TASK / "evidence" / "preflight_001"
EVIDENCE.mkdir(parents=True, exist_ok=True)
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
result = subprocess.run(
    [sys.executable, "-B", str(TASK / "CHECK.py"), "preservation"],
    cwd=ROOT, capture_output=True, env=os.environ.copy(),
)
(EVIDENCE / "PRESERVATION.stdout.log").write_bytes(result.stdout)
(EVIDENCE / "PRESERVATION.stderr.log").write_bytes(result.stderr)
import tests
actual = [str(Path(p).resolve()) for p in tests.__path__]
expected = [str((ROOT / "tests").resolve())]
diagnosis = {
    "at_utc": datetime.now(timezone.utc).isoformat(),
    "platform": sys.platform, "python_version": list(sys.version_info[:3]),
    "tests_module_origin_in_repo": Path(tests.__file__).resolve().is_relative_to(ROOT),
    "tests_module_origin_in_task_userbase": Path(tests.__file__).resolve().is_relative_to(TASK / "runtime" / "userbase"),
    "user_site_configured": str(Path(os.environ["PYTHONUSERBASE"]).resolve()),
    "expected_repo_tests_path_matches": actual == expected,
    "actual_tests_path_within_repo": [Path(p).resolve().is_relative_to(ROOT) for p in actual],
    "actual_tests_directory_exists": [Path(p).is_dir() for p in actual],
    "preservation_exit_code": result.returncode,
    "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
    "stdout_last_line": result.stdout.decode("utf-8", errors="replace").strip().splitlines()[-1],
    "external_actions": 0, "code_modified": False,
}
(EVIDENCE / "PREFLIGHT.json").write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(diagnosis, ensure_ascii=False))
raise SystemExit(0 if result.returncode == 0 else 1)
