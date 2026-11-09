"""Evaluator-only creation of immutable public metadata and exact local input hashes."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = TASK.parent / 'H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1'
REPAIR = TASK.parent / 'H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    target = TASK / 'INPUTS.json'
    assert not target.exists()
    snapshot = json.loads((REPAIR / 'evidence/l3_evaluator_20261109/ACCEPTED_SNAPSHOT.json').read_text(encoding='utf-8'))
    readonly = {REPAIR / name for name in snapshot['files']}
    readonly |= {REPAIR / 'REVIEW.md', OLD / 'SELECTED.json', OLD / 'ORACLE.py', OLD / 'ORACLE_CASES.json'}
    readonly |= {p for p in (OLD / 'acquired/data').rglob('*.parquet')}
    readonly |= {p for p in (OLD / 'acquired/worlds').rglob('*.json')}
    readonly |= {p for p in (OLD / 'references').iterdir() if p.name.startswith('CODE_') or p.name in {'DATA_SCHEMA_md', 'DATA_README_md', 'DATA_NOTICE'}}
    readonly.add(ROOT / '.task_envs/H64/parquet_reader/pyarrow/__init__.py')
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'src', 'tests', 'samples', 'config'], cwd=ROOT).split(b'\0')
    protected = {n.decode(): sha((ROOT / n.decode()).read_bytes().replace(b'\r\n', b'\n')) for n in tracked if n and (ROOT / n.decode()).is_file()}
    files = ['CONTRACT.md', 'VALIDATION_PLAN.yaml', 'CHECK.py', 'EXECUTOR_START.md', 'FREEZE.py', 'PUBLICATION_READINESS.md']
    result = {'task_id': TASK.name, 'snapshot_basis_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'episode_ids': [s['episode_id'] for s in json.loads((OLD / 'SELECTED.json').read_text(encoding='utf-8'))['samples']],
              'frozen': {n: sha((TASK / n).read_bytes().replace(b'\r\n', b'\n')) for n in files},
              'readonly': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(readonly)},
              'product_protected': protected, 'analysis_executed': False, 'new_network': 0}
    target.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({'frozen': len(files), 'readonly': len(readonly), 'product_protected': len(protected), 'analysis_executed': False}))

if __name__ == '__main__':
    main()
