"""Preserve each previous observation before a frozen check writes its output."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
argv=sys.argv[1:]
script=(ROOT/argv[0]).resolve()
assert script in {(TASK/"FROZEN_TESTS.py").resolve(),(TASK/"REPAIR_PROBES.py").resolve()}
assert "--out" in argv
out=(ROOT/argv[argv.index("--out")+1]).resolve()
assert out.is_relative_to((TASK/"evidence").resolve())
if out.is_file():
    data=out.read_bytes(); digest=hashlib.sha256(data).hexdigest()
    archive=TASK/"evidence/observation_archive"; archive.mkdir(parents=True,exist_ok=True)
    target=archive/(out.stem+"-"+digest+".json")
    if target.exists():
        assert target.read_bytes()==data
    else:
        target.write_bytes(data)
    print(json.dumps({"prior_observation_archived":target.relative_to(ROOT).as_posix(),"sha256":digest}),flush=True)
raise SystemExit(subprocess.run([sys.executable,"-B",*argv],cwd=ROOT).returncode)
