"""Frozen offline artifact checks. Source meaning still requires independent L3 review."""
import ast
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
FACTS = {'confirmation', 'payment_call', 'payment_result', 'business_state', 'correlation', 'replay_inputs'}
STATES = {'WITHIN_CAP_OBSERVED', 'OVER_CAP_OBSERVED', 'NOT_JUDGEABLE'}
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def value_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
def verify_value(value, expected):
    assert value_sha(value) == expected, 'citation mismatch'
def local(name):
    path = (TASK / name).resolve()
    assert path.is_relative_to(TASK), 'path escapes task'
    return path
def pointer(value, path):
    assert path == '' or path.startswith('/')
    if path:
        for key in path[1:].split('/'):
            key = key.replace('~1', '/').replace('~0', '~')
            value = value[int(key)] if isinstance(value, list) else value[key]
    return value

@lru_cache(maxsize=1)
def parquet():
    # Decoder only: no upstream CartTrace modules are loaded.
    sys.path.insert(0, str(ROOT / '.task_envs/H64/parquet_reader'))
    import pyarrow
    import pyarrow.parquet as pq
    assert pyarrow.__version__ == '26.0.0'
    assert Path(pyarrow.__file__).resolve().is_relative_to(ROOT / '.task_envs/H64/parquet_reader')
    return pq

def material_paths():
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    return {r['file']: r for r in ledger['materials']}

def citation(cite):
    path = local(cite['file'])
    assert cite['file'].startswith(('references/', 'acquired/')), 'cite original source, not derived summary'
    if cite['file'].startswith('acquired/'):
        material = material_paths()[cite['file']]
        assert sha(path) == material['sha256']
    row = None
    if cite['kind'] == 'parquet':
        assert path.suffix == '.parquet'
        group = cite['row_group']
        index = cite['row_index']
        assert type(group) is int and group >= 0 and type(index) is int and index >= 0
        assert cite['pointer'].startswith('/') and len(cite['pointer']) > 1
        field = cite['pointer'][1:].split('/')[0].replace('~1', '/').replace('~0', '~')
        table = parquet().ParquetFile(path)
        columns = [field] + [n for n in ['role', 'actor'] if n != field and n in table.schema_arrow.names]
        rows = table.read_row_group(group, columns=columns).to_pylist()
        row = rows[index]
        value = pointer(row, cite['pointer'])
    elif cite['kind'] == 'json':
        row = read(path)
        value = pointer(row, cite['pointer'])
    elif cite['kind'] == 'text':
        lines = path.read_text(encoding='utf-8').splitlines()
        assert 1 <= cite['line'] <= len(lines)
        value = lines[cite['line'] - 1]
    else:
        raise AssertionError('unsupported citation kind')
    verify_value(value, cite['value_sha256'])
    return row

def invariants(data):
    assert data['task_id'] == TASK.name
    assert data['replay_executed'] is False and data['product_effect_measured'] is False
    assert data['candidate_classification'] == 'REFERENCE_ONLY'
    assert data['evidence_level'] == 'SOURCE_READINESS_ONLY'
    assert data['dataset_revision'] == '86cab5e539e161e0915d78d8abdd9023f09b411e'
    assert data['code_revision'] == '61f05faadc64badedd0ca727778ea5c9cd384702'

def source():
    base = read(TASK / 'BASELINE.json')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == base['head']
    for name, digest in base['protected'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in base['frozen'].items():
        assert sha(TASK / name) == digest, name
    known = set(base['protected']) | {'CURRENT.md'}
    prefix = TASK.relative_to(ROOT).as_posix() + '/'
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    assert all(n.decode('utf-8') in known or n.decode('utf-8').startswith(prefix) or n.decode('utf-8').startswith('.task_envs/H64/') for n in names if n), 'new file outside task'
    allowed = set(base['frozen']) | {'BASELINE.json', 'ACQUIRE.py', 'MEASURE.py', 'ORACLE.py', 'SELECTED.json', 'MEASUREMENT.json', 'ATTEMPT_LEDGER.json', 'REPORT.md', 'REVIEW.md'}
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            name = p.relative_to(TASK).as_posix()
            assert name in allowed or name.startswith(('acquired/', 'derived/', 'evidence/')), name
    print(json.dumps({'protected': len(base['protected']), 'frozen': len(base['frozen'])}))

def load_oracle():
    path = TASK / 'ORACLE.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name.split('.')[0] in {'decimal', 'typing', 'dataclasses', '__future__'} for n in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or '').split('.')[0] in {'decimal', 'typing', 'dataclasses', '__future__'}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {'open', 'exec', 'eval', 'compile', '__import__', 'input'}
    spec = importlib.util.spec_from_file_location('h64_observation_oracle', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def oracle():
    module = load_oracle()
    cases = read(TASK / 'ORACLE_CASES.json')['cases']
    for case in cases:
        assert module.evaluate(case['input']) == case['expected'], case['id']
    print(json.dumps({'oracle_cases': len(cases), 'product_control_test': False}))

def validate_ledger():
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    assert ledger['task_id'] == TASK.name
    assert type(ledger['active_minutes']) is int and 0 < ledger['active_minutes'] <= 180
    assert 0 <= ledger['formal_l2_attempts'] <= 2
    assert 0 <= ledger['measurement_versions'] <= 2
    assert 0 <= ledger['installation_calls'] <= 1
    for name in ['model_calls', 'payment_calls', 'product_calls', 'upstream_replay_calls']:
        assert type(ledger[name]) is int and ledger[name] == 0
    attempts = ledger['attempts']
    assert len({a['id'] for a in attempts}) == len(attempts)
    assert all(a['started_at'] and a['finished_at'] and a['status'] in {'SUCCEEDED', 'FAILED', 'LIMIT'} for a in attempts)
    gets = [a for a in attempts if a['kind'] == 'public_get']
    assert len(gets) <= 20 and sum(a.get('bytes_received', 0) for a in gets) <= 256 * 1024**2
    urls = [a['url'] for a in gets]
    assert all(urls.count(u) <= 2 for u in urls)
    inputs = read(TASK / 'SOURCE_INPUTS.json')
    exact = set(inputs['parquet_urls']) | {inputs['decoder']['url']}
    selected = read(TASK / 'SELECTED.json') if (TASK / 'SELECTED.json').exists() else {'samples': []}
    for sample in selected['samples']:
        for kind in ['envpacks', 'manifests']:
            relative = 'worlds/' + kind + '/' + sample['world_id'] + '.json'
            assert relative in {r['rfilename'] for r in read(TASK / 'references/HF_METADATA.json')['siblings']}
            exact.add(inputs['dataset_base'] + relative)
    assert all(u in exact for u in urls), 'unexpected source URL'
    for attempt in gets:
        assert isinstance(attempt['redirect_hosts'], list)
        assert set(attempt['redirect_hosts']) <= set(inputs['redirect_hosts'])
    materials = ledger['materials']
    assert len({m['file'] for m in materials}) == len(materials)
    for material in materials:
        assert material['url'] in exact
        assert local(material['file']).stat().st_size <= 128 * 1024**2
        assert sha(local(material['file'])) == material['sha256']
        if material['url'] in inputs['expected_sha256']:
            assert material['sha256'] == inputs['expected_sha256'][material['url']]
    return ledger

def expected_selection(inputs):
    candidates = []
    for relative in inputs['message_paths']:
        path = TASK / 'acquired' / relative
        for batch in parquet().ParquetFile(path).iter_batches(columns=inputs['selection_columns']):
            for row in batch.to_pylist():
                if row['boundary'] == 'order' and row['currency'] == 'USD' and 'webmcp' not in (row['surface'] or '').lower() and row['episode_id'] not in inputs['excluded_episode_ids']:
                    candidates.append(row)
    candidates.sort(key=lambda r: r['episode_id'])
    assert len({r['episode_id'] for r in candidates}) == len(candidates)
    return [{'episode_id': r['episode_id'], 'world_id': r['world_id']} for r in candidates[:6]]

def measurement():
    data = read(TASK / 'MEASUREMENT.json')
    invariants(data)
    ledger = validate_ledger()
    inputs = read(TASK / 'SOURCE_INPUTS.json')
    assert data['decision']['kind'] in {'CONTINUE_TO_REPLAY_BASELINE', 'STOP_SOURCE_VIEW', 'INPUT_LIMIT'}
    assert len(data['decision']['reason'].strip()) >= 40
    if data['decision']['kind'] == 'INPUT_LIMIT':
        assert any(a['status'] in {'FAILED', 'LIMIT'} for a in ledger['attempts'])
    else:
        assert read(TASK / 'SELECTED.json')['samples'] == expected_selection(inputs)
    samples = data['samples']
    chosen = read(TASK / 'SELECTED.json')['samples'] if (TASK / 'SELECTED.json').exists() else []
    assert len(samples) <= 6 and len({s['episode_id'] for s in samples}) == len(samples)
    assert all(s['episode_id'] in {c['episode_id'] for c in chosen} for s in samples)
    if data['decision']['kind'] != 'INPUT_LIMIT':
        assert [s['episode_id'] for s in samples] == [c['episode_id'] for c in chosen]
    module = load_oracle()
    for sample in samples:
        assert set(sample['facts']) == FACTS
        for key, fact in sample['facts'].items():
            assert fact['status'] in {'PRESENT', 'ABSENT', 'AMBIGUOUS'} and len(fact['reason'].strip()) >= 20
            assert isinstance(fact['citations'], list)
            if fact['status'] == 'PRESENT':
                assert fact['citations']
            if fact['status'] == 'ABSENT':
                assert not fact['citations']
            for cite in fact['citations']:
                row = citation(cite)
                if key == 'confirmation':
                    assert cite['kind'] == 'parquet' and row and (row.get('role') == 'user' or row.get('actor') == 'shopper'), 'user confirmation needs source user row'
        assert sample['observed_verdict'] in STATES
        assert module.evaluate(sample['oracle_input']) == sample['observed_verdict']
        assert sample['business_state_level'] in {'MISSING', 'REPORTED_TOOL_STATE', 'PUBLISHED_INITIAL_STATE', 'FINAL_STATE_DIGEST', 'OBSERVED_BACKEND_EVENT', 'CODE_PATH_ONLY'}
        assert len(sample['unit_and_link_reason'].strip()) >= 30
        if sample['observed_verdict'] != 'NOT_JUDGEABLE':
            assert all(sample['facts'][k]['status'] == 'PRESENT' for k in ['confirmation', 'payment_result', 'correlation'])
            assert sample['unit_citations']
            for cite in sample['unit_citations']:
                citation(cite)
    if data['decision']['kind'] == 'CONTINUE_TO_REPLAY_BASELINE':
        assert any(s['observed_verdict'] != 'NOT_JUDGEABLE' for s in samples)
        assert isinstance(data['decision']['next_question'], str) and len(data['decision']['next_question']) >= 30
        assert data['backend_access_citations']
        for cite in data['backend_access_citations']:
            citation(cite)
        for selected in chosen:
            # All selected sample materials must be present for a positive readiness claim.
            for kind in ['envpacks', 'manifests']:
                assert (TASK / 'acquired/worlds' / kind / (selected['world_id'] + '.json')).is_file()
    else:
        assert data['decision']['next_question'] is None
    print(json.dumps({'samples': len(samples), 'decision': data['decision']['kind'], 'semantic_review_required': True}))

def selftest():
    assert pointer({'a/b': [7]}, '/a~1b/0') == 7
    verify_value('source value', value_sha('source value'))
    try:
        verify_value('different value', value_sha('source value'))
    except AssertionError:
        pass
    else:
        raise AssertionError('bad value hash accepted')
    for bad in ['../CURRENT.md', '../../escape']:
        try:
            local(bad)
        except AssertionError:
            continue
        raise AssertionError('unsafe path accepted')
    good = {'task_id': TASK.name, 'replay_executed': False, 'product_effect_measured': False, 'candidate_classification': 'REFERENCE_ONLY', 'evidence_level': 'SOURCE_READINESS_ONLY', 'dataset_revision': '86cab5e539e161e0915d78d8abdd9023f09b411e', 'code_revision': '61f05faadc64badedd0ca727778ea5c9cd384702'}
    invariants(good)
    for key, value in [('replay_executed', True), ('product_effect_measured', True), ('candidate_classification', 'ABSORB'), ('evidence_level', 'REAL_PSP_VERIFIED')]:
        try:
            invariants(dict(good, **{key: value}))
        except AssertionError:
            continue
        raise AssertionError('evidence escalation accepted')
    print(json.dumps({'boundary_negative_checks': 7, 'measurement_or_product_test': False}))

if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'final':
        validate_ledger()
        selftest()
        source()
    else:
        {'source': source, 'measurement': measurement, 'oracle': oracle, 'selftest': selftest}[command]()
