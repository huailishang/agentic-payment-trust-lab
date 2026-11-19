"""H74 mandatory initial baseline and historical regression on native agent Python."""
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
E = TASK / "evidence" / "initial_baseline"
E.mkdir(parents=True, exist_ok=True)
results = []
for name, mode in (("BASELINE","baseline"),("REGRESSIONS","regressions")):
    p = subprocess.run([sys.executable, "-B", str(TASK/"CHECK.py"),mode],
        cwd=ROOT, env=os.environ.copy(), capture_output=True, timeout=180)
    for extension, data in (("stdout.log",p.stdout),("stderr.log",p.stderr)):
        (E/f"{name}.{extension}").write_bytes(data)
    results.append({"id":name,"exit_code":p.returncode,
      "stdout_sha256":hashlib.sha256(p.stdout).hexdigest(),
      "stderr_sha256":hashlib.sha256(p.stderr).hexdigest(),
      "stdout_tail":p.stdout.decode("utf-8",errors="replace")[-1800:],
      "stderr_tail":p.stderr.decode("utf-8",errors="replace")[-1800:]})
    if p.returncode:
        break
(E/"SUMMARY.json").write_text(json.dumps({"at_utc":datetime.now(timezone.utc).isoformat(),
"checks":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(results,ensure_ascii=False))
raise SystemExit(0 if len(results)==2 and all(r["exit_code"]==0 for r in results) else 1)
