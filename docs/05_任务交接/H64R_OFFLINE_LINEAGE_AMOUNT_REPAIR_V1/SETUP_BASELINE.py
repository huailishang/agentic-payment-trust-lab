"""Evaluator-only archive/freeze. No download, install or repair execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = TASK.parent / 'H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1'
MAP = ROOT / 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data):
    assert not path.exists()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

audit = read(OLD / 'evidence/independent_evaluator_20261108/RV-EV-05.stdout.log')
for name, expected in audit['submitted_snapshot'].items():
    assert sha(OLD / name) == expected, name
if sys.argv[1] == 'archive':
    assert sha(MAP) == '0fd46544e823738b164210264a21c2e220e24c4324f06b0e187c55c2a311ad9d'
    archive = MAP.parent / 'archive/PROJECT_BOTTLENECK_MAP_20261108_r103.md'
    assert not archive.exists()
    archive.write_bytes(MAP.read_bytes())
    refs = TASK / 'references'
    refs.mkdir(exist_ok=True)
    (refs / 'PRIOR_CURRENT.md').write_bytes((ROOT / 'CURRENT.md').read_bytes())
    print('r103 and rejected H64 router preserved; submitted artifacts unchanged.')
elif sys.argv[1] == 'freeze':
    files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    paths = {ROOT / n.decode() for n in files if n}
    paths.update(ROOT / n for n in read(OLD / 'BASELINE.json')['protected'])
    paths.update(p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update(p for p in (ROOT / '.task_envs/H64/parquet_reader').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for path in TASK.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    import yaml
    plan = yaml.safe_load((TASK/'VALIDATION_PLAN.yaml').read_text(encoding='utf-8'))
    assert plan['task_id'] == TASK.name and len(plan['checks']) == 4
    assert {a for check in plan['checks'] for a in check['ac']} == {'AC-01','AC-02','AC-03','AC-04'}
    protected = {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths) if p.is_file() and TASK not in p.parents and p != ROOT/'CURRENT.md'}
    frozen = {p.relative_to(TASK).as_posix():sha(p) for p in TASK.rglob('*') if p.is_file() and not p.relative_to(TASK).as_posix().startswith('evidence/') and p.name not in {'BASELINE.json','READINESS.json'}}
    ready = {'task_id':TASK.name,'state':'CONTRACT_FROZEN','protected':len(protected),'frozen':len(frozen)+1,'repair_executed':False,'formal_l2':0,'formal_l3':0,'new_network':0,'new_installations':0,'parent_snapshot_unchanged':True}
    write(TASK/'READINESS.json',ready)
    frozen['READINESS.json']=sha(TASK/'READINESS.json')
    write(TASK/'BASELINE.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protected':protected,'frozen':frozen,'preparation_only':True})
    print(json.dumps(ready))
