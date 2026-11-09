"""Write-once H63 frozen-input manifest after evaluator preparation."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
out = TASK / 'INPUTS.json'
assert not out.exists(), 'frozen manifest already exists'
mutable = {'REPORT.md', 'REVIEW.md', 'EXTRACT.py', 'MEASUREMENT.json', 'ATTEMPT_LEDGER.json', 'INPUTS.json'}
frozen = {}
for path in sorted(TASK.rglob('*')):
    if path.is_file() and '__pycache__' not in path.parts:
        name = path.relative_to(TASK).as_posix()
        if name not in mutable and not name.startswith('evidence/'):
            frozen[name] = hashlib.sha256(path.read_bytes()).hexdigest()
names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
map_path = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
data = {'task_id': TASK.name, 'frozen_files': frozen,
        'map_path': map_path, 'map_sha256': hashlib.sha256((ROOT / map_path).read_bytes()).hexdigest(),
        'workspace_files': sorted(raw.decode('utf-8') for raw in names if raw),
        'preparation_only': True, 'formal_l2': 0, 'formal_l3': 0}
out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'frozen_files': len(frozen), 'map_revision': '2026-11-07-r101', 'formal_l2': 0, 'formal_l3': 0}))
