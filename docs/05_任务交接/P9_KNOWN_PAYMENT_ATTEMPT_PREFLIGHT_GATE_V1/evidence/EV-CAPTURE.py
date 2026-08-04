from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

label = sys.argv[1]
outdir = Path(sys.argv[2])
command = sys.argv[3:]
started = dt.datetime.now(dt.timezone.utc)
proc = subprocess.run(command, cwd=os.getcwd(), capture_output=True, text=True, encoding='utf-8', errors='replace')
ended = dt.datetime.now(dt.timezone.utc)
stdout = proc.stdout
stderr = proc.stderr
(outdir / f'{label}.stdout.log').write_text(stdout, encoding='utf-8')
(outdir / f'{label}.stderr.log').write_text(stderr, encoding='utf-8')
meta = {
    'schema': 'executor-evidence/v1',
    'label': label,
    'cwd': os.getcwd(),
    'command': command,
    'started_at_utc': started.isoformat(),
    'ended_at_utc': ended.isoformat(),
    'duration_seconds': (ended - started).total_seconds(),
    'exit_code': proc.returncode,
    'stdout_sha256': hashlib.sha256(stdout.encode()).hexdigest(),
    'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
}
(outdir / f'{label}.meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
sys.stdout.write(stdout)
sys.stderr.write(stderr)
raise SystemExit(proc.returncode)
