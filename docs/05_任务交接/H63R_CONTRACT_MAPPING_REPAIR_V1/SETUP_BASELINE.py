"""Evaluator preparation only; not task L2 or implementation."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
paths = {ROOT / n.decode('utf-8') for n in names if n}
old = TASK.parent / 'H63_EXTERNAL_TRACE_QUALIFICATION_V1'
paths.update(p for p in old.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
previous = json.loads((old / 'BASELINE.json').read_text(encoding='utf-8'))
paths.update(ROOT / n for n in previous['h62_files'])
paths.update(ROOT / n for n in previous['other_workspace_files'])
paths.update(ROOT / r['path'] for r in previous['source_databases'].values())
protected = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths) if p.is_file() and TASK not in p.parents and p != ROOT / 'CURRENT.md'}
frozen = {p.name: sha(p) for p in TASK.iterdir() if p.is_file() and p.name != 'BASELINE.json'}
base = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'protected': protected, 'frozen': frozen, 'preparation_only': True}
(TASK / 'BASELINE.json').write_text(json.dumps(base, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'protected': len(protected), 'frozen': len(frozen), 'l2': 'NOT_RUN', 'l3': 'NOT_RUN'}))
