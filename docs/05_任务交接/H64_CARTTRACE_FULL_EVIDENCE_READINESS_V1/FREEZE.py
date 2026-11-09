"""Evaluator-only preparation and freeze. Does not download task data/install/measure."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
MAP = ROOT / 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
OLD = TASK.parent / 'H63R_CONTRACT_MAPPING_REPAIR_V1'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def write(path, value):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if sys.argv[1] == 'prepare':
    archive = MAP.parent / 'archive/PROJECT_BOTTLENECK_MAP_20261108_r102.md'
    assert sha(MAP) == 'c0a1617e9b94ed1399886faa3e18344912d8be90a50ed43910d5d37f8ba4206a'
    assert not archive.exists()
    archive.write_bytes(MAP.read_bytes())
    (TASK / 'references/PRIOR_CURRENT.md').write_bytes((ROOT / 'CURRENT.md').read_bytes())
    # Verify downloaded code bytes really belong to the resolved Git commit.
    tree = {r['path']: r for r in read(TASK / 'references/GITHUB_TREE.json')['tree']}
    for path in (TASK / 'references').glob('CODE_*'):
        original = path.name[len('CODE_'):].replace('__', '/')
        body = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        assert blob == tree[original]['sha'], original
    checksums = {}
    for line in (TASK / 'references/DATA_checksums_sha256').read_text(encoding='utf-8').splitlines():
        digest, name = line.split(maxsplit=1)
        checksums[name.lstrip('*')] = digest
    paths = ['data/messages/arts-crafts-music/validation-00000-of-00001.parquet', 'data/messages/automotive-parts/validation-00000-of-00001.parquet', 'data/turns/validation-00000-of-00001.parquet', 'data/wire/validation-00000-of-00001.parquet']
    base = 'https://huggingface.co/datasets/generalmachines/CartTrace-100k/resolve/86cab5e539e161e0915d78d8abdd9023f09b411e/'
    wheel = next(r for r in read(TASK / 'references/PYARROW_METADATA.json')['urls'] if r['filename'] == 'pyarrow-26.0.0-cp312-cp312-win_amd64.whl')
    old_samples = read(OLD.parent / 'H63_EXTERNAL_TRACE_QUALIFICATION_V1/MEASUREMENT.json')['samples']
    inputs = {'task_id': TASK.name, 'dataset_revision': '86cab5e539e161e0915d78d8abdd9023f09b411e', 'code_revision': '61f05faadc64badedd0ca727778ea5c9cd384702', 'dataset_base': base,
              'message_paths': paths[:2], 'parquet_paths': paths, 'parquet_urls': [base + p for p in paths],
              'selection_columns': ['episode_id', 'boundary', 'surface', 'currency', 'world_id', 'rail'],
              'excluded_episode_ids': [s['episode_id'] for s in old_samples],
              'decoder': {'name': 'pyarrow', 'version': '26.0.0', 'filename': wheel['filename'], 'url': wheel['url'], 'sha256': wheel['digests']['sha256'], 'size': wheel['size'], 'target': '.task_envs/H64/parquet_reader'},
              'expected_sha256': {base + p: checksums[p] for p in paths},
              'redirect_hosts': ['huggingface.co', 'cdn-lfs.huggingface.co', 'cdn-lfs-us-1.hf.co', 'cdn-lfs-eu-1.hf.co', 'cas-bridge.xethub.hf.co', 'us.aws.cdn.hf.co', 'eu.aws.cdn.hf.co', 'files.pythonhosted.org']}
    inputs['expected_sha256'][wheel['url']] = wheel['digests']['sha256']
    write(TASK / 'SOURCE_INPUTS.json', inputs)
    print(json.dumps({'source_files_verified': len(list((TASK / 'references').glob('CODE_*'))), 'datasets_sampled': 0, 'installations': 0}))
elif sys.argv[1] == 'freeze':
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    paths = {ROOT / n.decode('utf-8') for n in names if n}
    prior = read(OLD / 'BASELINE.json')
    paths.update(ROOT / n for n in prior['protected'])
    paths.update(p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for p in [TASK / 'CONTRACT.md', TASK / 'EXECUTOR_START.md']:
        assert 'CONTRACT_FROZEN' in p.read_text(encoding='utf-8')
    for p in TASK.glob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'))
    import yaml
    plan = yaml.safe_load((TASK / 'VALIDATION_PLAN.yaml').read_text(encoding='utf-8'))
    assert plan['task_id'] == TASK.name and len(plan['checks']) == 4
    assert {a for c in plan['checks'] for a in c['ac']} == {'AC-01', 'AC-02', 'AC-03', 'AC-04'}
    protected = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths) if p.is_file() and TASK not in p.parents and p != ROOT / 'CURRENT.md'}
    frozen = {p.relative_to(TASK).as_posix(): sha(p) for p in TASK.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.relative_to(TASK).as_posix().startswith('evidence/') and p.name != 'BASELINE.json'}
    prep = read(TASK / 'PREPARATION.json')
    summary = {'state': 'CONTRACT_FROZEN', 'protected': len(protected), 'frozen': len(frozen) + 1, 'preparation_gets': len(prep['requests']), 'preparation_bytes': sum(r.get('bytes', 0) for r in prep['requests']), 'actual_samples': 0, 'installations': 0, 'model_calls': 0, 'product_calls': 0, 'replays': 0, 'payment_calls': 0, 'formal_l2': 0, 'formal_l3': 0}
    write(TASK / 'READINESS.json', summary)
    frozen['READINESS.json'] = sha(TASK / 'READINESS.json')
    write(TASK / 'BASELINE.json', {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'protected': protected, 'frozen': frozen, 'preparation_only': True, 'l2': 'NOT_RUN', 'l3': 'NOT_RUN'})
    print(json.dumps(summary))
