"""Frozen offline source-grounding checks for the H64 semantic repair."""
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = TASK.parent / 'H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1'
TOOLS = {'pay', 'send_payment_mandate', 'delegate_payment', 'shop_pay_payment_request'}
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def pointer(value, path):
    assert path == '' or path.startswith('/')
    for part in path[1:].split('/') if path else []:
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value
@lru_cache(maxsize=1)
def decoder():
    sys.path.insert(0, str(ROOT / '.task_envs/H64/parquet_reader'))
    import pyarrow
    import pyarrow.parquet as pq
    assert pyarrow.__version__ == '26.0.0'
    return pq

def cite(c):
    path = (ROOT / c['file']).resolve()
    assert path.is_relative_to(OLD / 'acquired') or path.is_relative_to(OLD / 'references')
    row = None
    if c['kind'] == 'parquet':
        assert c['pointer'].startswith('/')
        field = c['pointer'][1:].split('/')[0].replace('~1', '/').replace('~0', '~')
        pf = decoder().ParquetFile(path)
        extra = ['episode_id', 'kind', 'actor', 'role', 'seq', 'call_id', 'tool_call_id', 'source_call_id']
        columns = list(dict.fromkeys([field] + [f for f in extra if f in pf.schema_arrow.names]))
        row = pf.read_row_group(c['row_group'], columns=columns).to_pylist()[c['row_index']]
        value = pointer(row, c['pointer'])
    elif c['kind'] == 'json':
        value = pointer(read(path), c['pointer'])
    elif c['kind'] == 'text':
        value = path.read_text(encoding='utf-8').splitlines()[c['line']-1]
    else:
        raise AssertionError('invalid citation kind')
    assert digest(value) == c['value_sha256']
    if 'embedded_pointer' in c:
        assert isinstance(value, str)
        value = pointer(json.loads(value), c['embedded_pointer'])
        assert digest(value) == c['decoded_value_sha256']
    return value, row

def source():
    base = read(TASK / 'BASELINE.json')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == base['head']
    for name, h in base['protected'].items():
        assert sha(ROOT / name) == h, name
    for name, h in base['frozen'].items():
        assert sha(TASK / name) == h, name
    known = set(base['protected']) | {'CURRENT.md'}
    prefix = TASK.relative_to(ROOT).as_posix() + '/'
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    assert all(n.decode() in known or n.decode().startswith(prefix) for n in names if n)
    allowed = set(base['frozen']) | {'BASELINE.json', 'EXTRACT.py', 'MEASUREMENT.json', 'ATTEMPT_LEDGER.json', 'REPORT.md', 'REVIEW.md'}
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            name = p.relative_to(TASK).as_posix()
            assert name in allowed or name.startswith(('derived/', 'evidence/'))
    print(json.dumps({'protected': len(base['protected']), 'frozen': len(base['frozen'])}))

def pure_oracle():
    spec = importlib.util.spec_from_file_location('h64_frozen_pure_oracle', OLD / 'ORACLE.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.evaluate

def ledger():
    data = read(TASK / 'ATTEMPT_LEDGER.json')
    assert data['task_id'] == TASK.name
    assert 0 < data['active_minutes'] <= 90 and 0 < data['measurement_versions'] <= 2
    assert 0 <= data['formal_l2_attempts'] <= 2
    for key in ['network_calls', 'installation_calls', 'model_calls', 'payment_calls', 'product_calls', 'upstream_replay_calls']:
        assert type(data[key]) is int and data[key] == 0
    attempts = data['attempts']
    assert len({a['id'] for a in attempts}) == len(attempts)
    assert all(a['started_at'] and a['finished_at'] and a['status'] in {'SUCCEEDED', 'FAILED'} for a in attempts)
    assert 6 <= len([a for a in attempts if a['kind'] == 'sample']) <= 12

def all_calls():
    chosen = {s['episode_id'] for s in read(OLD / 'SELECTED.json')['samples']}
    found = {eid: set() for eid in chosen}
    pf = decoder().ParquetFile(OLD / 'acquired/data/turns/validation-00000-of-00001.parquet')
    for b in pf.iter_batches(columns=['episode_id', 'kind', 'tool', 'call_id']):
        for r in b.to_pylist():
            if r['episode_id'] in found and r['kind'] == 'tool_call' and r['tool'] in TOOLS:
                found[r['episode_id']].add(r['call_id'])
    return found

def validate(data):
    assert data['task_id'] == TASK.name and data['replay_executed'] is False and data['product_effect_measured'] is False
    assert data['classification'] == 'REFERENCE_ONLY'
    selected = read(OLD / 'SELECTED.json')['samples']
    assert [s['episode_id'] for s in data['samples']] == [s['episode_id'] for s in selected]
    expected = all_calls()
    oracle = pure_oracle()
    for sample in data['samples']:
        eid = sample['episode_id']
        chains = sample['call_chains']
        assert len({c['call_id'] for c in chains}) == len(chains)
        assert {c['call_id'] for c in chains} == expected[eid]
        for chain in chains:
            callid = chain['call_id']
            value, row = cite(chain['call_citation'])
            assert value == callid and row['episode_id'] == eid and row['kind'] == 'tool_call'
            for key in ['result_citations', 'wire_citations']:
                for citation in chain[key]:
                    val, row = cite(citation)
                    assert val == callid and row['episode_id'] == eid, 'mixed call ids'
            complete = bool(chain['result_citations'] and chain['wire_citations'])
            assert chain['status'] == ('COMPLETE' if complete else 'PARTIAL')
        for obs in sample['raw_payment_observations']:
            for field, key in [('raw_amount', 'amount_citation'), ('currency_raw', 'currency_citation'), ('checkout_id', 'checkout_citation')]:
                val, row = cite(obs[key])
                assert val == obs[field] and row['episode_id'] == eid
            callid, row = cite(obs['call_id_citation'])
            assert callid == obs['call_id'] and row['episode_id'] == eid
            assert obs['origin'] in {'tool_response', 'protocol_response', 'backend_event'}
            assert obs['phase'] in {'REQUEST', 'TOKEN_ALLOWANCE', 'REPORTED_COMPLETION', 'UNKNOWN'}
            assert obs['unit_status'] in {'PROVEN', 'UNKNOWN'}
            if obs['unit_status'] == 'UNKNOWN':
                assert obs['amount_minor'] is None
            else:
                assert type(obs['amount_minor']) is int and obs['amount_minor'] >= 0 and obs['unit_citations']
                for c in obs['unit_citations']:
                    cite(c)
        assert sample['binding_status'] in {'PROVEN', 'AMBIGUOUS', 'MISSING'}
        assert isinstance(sample['missing_dimensions'], list)
        assert len(sample['reason'].strip()) >= 40
        assert oracle(sample['oracle_input']) == sample['source_verdict']
        if sample['source_verdict'] != 'NOT_JUDGEABLE':
            assert sample['binding_status'] == 'PROVEN' and sample['binding_citations']
        for c in sample['binding_citations']:
            cite(c)
    s4 = next(s for s in data['samples'] if s['episode_id'] == 'ep-09bafc6d1c7e')
    assert {'call-32', 'call-34'} <= {c['call_id'] for c in s4['call_chains']}
    s6 = next(s for s in data['samples'] if s['episode_id'] == 'ep-172fbb8cce5b')
    assert any(o['call_id'] == 'call-68' and o['raw_amount'] == 4425 and o['currency_raw'] == 'usd' and o['checkout_id'] == 'checkout-3766021cd113' and o['phase'] == 'REPORTED_COMPLETION' for o in s6['raw_payment_observations']), 'known reported amount discarded'
    assert data['access_limit']['missing_world_ids'] == ['env-bd45a7e9be19']
    assert len(data['assessment'].strip()) >= 40

def measurement():
    ledger()
    validate(read(TASK / 'MEASUREMENT.json'))
    print(json.dumps({'samples': 6, 'independent_semantic_review_required': True}))

def regression():
    good = read(TASK / 'MEASUREMENT.json')
    validate(good)
    for variant in range(4):
        bad = copy.deepcopy(good)
        s4 = next(s for s in bad['samples'] if s['episode_id'] == 'ep-09bafc6d1c7e')
        s6 = next(s for s in bad['samples'] if s['episode_id'] == 'ep-172fbb8cce5b')
        if variant == 0:
            c32 = next(c for c in s4['call_chains'] if c['call_id'] == 'call-32')
            c34 = next(c for c in s4['call_chains'] if c['call_id'] == 'call-34')
            assert c34['wire_citations']
            c32['wire_citations'] = c34['wire_citations']
            c32['status'] = 'COMPLETE'
        elif variant == 1:
            s6['raw_payment_observations'] = []
        elif variant == 2:
            target = next(o for o in s6['raw_payment_observations'] if o['call_id'] == 'call-68')
            target['raw_amount'] = 0
        else:
            bad['replay_executed'] = True
        try:
            validate(bad)
        except AssertionError:
            continue
        raise AssertionError('repair regression accepted')
    print(json.dumps({'regression_mutations_rejected': 4}))

def oracle():
    evaluate = pure_oracle()
    for case in read(OLD / 'ORACLE_CASES.json')['cases']:
        assert evaluate(case['input']) == case['expected'], case['id']
    source()
    print(json.dumps({'inherited_oracle_cases': 8}))

if __name__ == '__main__':
    {'source': source, 'measurement': measurement, 'regression': regression, 'oracle': oracle}[sys.argv[1]]()
