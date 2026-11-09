"""Capture the accepted H62 era before explicit governance-only rebaselining."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
H62 = ROOT / 'docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1'
OUT = TASK / 'BASELINE.json'
assert not OUT.exists(), 'baseline is write-once'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

inputs = json.loads((H62 / 'INPUTS.json').read_text(encoding='utf-8'))
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == inputs['head']
for name, digest in inputs['protected_files'].items():
    assert sha(ROOT / name) == digest, name
for row in inputs['source_databases'].values():
    assert sha(ROOT / row['path']) == row['sha256'], row['path']
map_path = ROOT / 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
archive = ROOT / 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261106_r100.md'
assert not archive.exists()
archive.parent.mkdir(parents=True, exist_ok=True)
archive.write_bytes(map_path.read_bytes())
(TASK / 'references/PRIOR_CURRENT.md').write_bytes((ROOT / 'CURRENT.md').read_bytes())
files = sorted(p for p in H62.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
snapshot = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
tracked = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
other = {}
for raw in tracked:
    if not raw:
        continue
    name = raw.decode('utf-8')
    if name in {'CURRENT.md', 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'} or name.startswith(TASK.relative_to(ROOT).as_posix() + '/') or name == archive.relative_to(ROOT).as_posix():
        continue
    path = ROOT / name
    if path.is_file():
        other[name] = sha(path)
data = {'task_id': TASK.name, 'created_at': datetime.now(timezone.utc).isoformat(),
        'head': head, 'h62_files': snapshot, 'other_workspace_files': other,
        'h62_protected_count': len(inputs['protected_files']),
        'source_databases': inputs['source_databases'],
        'map_rebaseline': {'original': map_path.relative_to(ROOT).as_posix(),
                         'archive': archive.relative_to(ROOT).as_posix(),
                         'sha256': sha(map_path), 'old_revision': '2026-11-06-r100',
                         'new_revision': '2026-11-07-r101',
                         'reason': 'H62 PASS / IMPROVED / STOP; new evaluator-only source qualification'},
        'permitted_existing_changes': ['CURRENT.md', map_path.relative_to(ROOT).as_posix()]}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'h62_files': len(snapshot), 'other_workspace_files': len(other),
                  'protected_before_rebaseline': len(inputs['protected_files']),
                  'map_archive_sha256': sha(archive), 'baseline': head}))
