"""H65 public-package and local-source gates; no acquisition or product execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
STATES = {'PROVEN', 'PARTIAL', 'UNKNOWN', 'INPUT_LIMIT'}

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def digest(v):
    return sha(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def package():
    data = read(TASK / 'INPUTS.json')
    assert data['task_id'] == TASK.name
    for name, h in data['frozen'].items():
        assert sha((TASK / name).read_bytes().replace(b'\r\n', b'\n')) == h, name
    print(json.dumps({'package': 'PASS', 'frozen': len(data['frozen']), 'local_source_validated': False}))

def source():
    package()
    data = read(TASK / 'INPUTS.json')
    missing = [n for n in data['readonly'] if not (ROOT / n).is_file()]
    if missing:
        print(json.dumps({'result': 'INPUT_LIMIT', 'missing_count': len(missing), 'missing': missing}, ensure_ascii=False))
        raise SystemExit(3)
    for name, h in data['readonly'].items():
        assert sha((ROOT / name).read_bytes()) == h, name
    for name, h in data['product_protected'].items():
        assert sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) == h, name
    print(json.dumps({'source': 'PASS', 'readonly': len(data['readonly']), 'product_protected': len(data['product_protected'])}))

def pointer(v, p):
    for key in p.strip('/').split('/') if p else []:
        key = key.replace('~1', '/').replace('~0', '~')
        v = v[int(key)] if isinstance(v, list) else v[key]
    return v

def citation(c, eid):
    inputs = read(TASK / 'INPUTS.json')
    assert c['file'] in inputs['readonly']
    p = ROOT / c['file']
    if 'row_group' in c:
        sys.path.insert(0, str(ROOT / '.task_envs/H64/parquet_reader'))
        import pyarrow.parquet as pq
        row = pq.ParquetFile(p).read_row_group(c['row_group']).to_pylist()[c['row_index']]
        assert row['episode_id'] == eid
        value = pointer(row, c['pointer'])
        assert digest(value) == c['value_sha256']
        if 'embedded_pointer' in c:
            value = pointer(json.loads(value), c['embedded_pointer'])
            assert digest(value) == c['decoded_value_sha256']
    else:
        assert c['line_start'] >= 1 and c['line_end'] >= c['line_start']
        lines = p.read_bytes().splitlines(keepends=True)
        assert c['line_end'] <= len(lines)
        assert sha(b''.join(lines[c['line_start']-1:c['line_end']])) == c['text_sha256']

def guards_for_result(result):
    assert result['replay_executed'] is False and result['product_effect_measured'] is False
    complete = False
    for sample in result['samples']:
        for name in ('unit', 'binding'):
            fact = sample[name]
            assert fact['status'] in STATES
            assert len(fact['reason'].strip()) >= 40
            if fact['status'] == 'PROVEN':
                assert fact['citations'], 'proven fact without source'
        edges = sample['binding']['edges']
        assert all(e['origin'] in {'SOURCE_OBSERVATION', 'CODE_INTENT', 'INFERENCE'} and e['citation'] for e in edges)
        if sample['binding']['status'] == 'PROVEN':
            assert any(e['origin'] == 'SOURCE_OBSERVATION' for e in edges), 'code intent is not source proof'
        complete |= sample['unit']['status'] == sample['binding']['status'] == 'PROVEN'
    assert result['verdict'] in {'CONTINUE_TO_REPLAY_BASELINE', 'STOP_SOURCE_VIEW', 'INPUT_LIMIT'}
    if result['verdict'] == 'CONTINUE_TO_REPLAY_BASELINE':
        assert complete, 'no complete source chain'

def analysis():
    result = read(TASK / 'RESULT.json')
    assert result['task_id'] == TASK.name and len(result['reason'].strip()) >= 40
    assert [s['episode_id'] for s in result['samples']] == read(TASK / 'INPUTS.json')['episode_ids']
    guards_for_result(result)
    for sample in result['samples']:
        for fact in ('unit', 'binding'):
            for c in sample[fact]['citations']:
                citation(c, sample['episode_id'])
        for edge in sample['binding']['edges']:
            citation(edge['citation'], sample['episode_id'])
    print(json.dumps({'samples': len(result['samples']), 'semantic_review_required': True}))

def guards():
    fact = {'status': 'PROVEN', 'reason': 'x' * 40, 'citations': [{'source': 'synthetic_guard_only'}]}
    good = {'samples': [{'unit': copy.deepcopy(fact), 'binding': dict(copy.deepcopy(fact), edges=[{'origin': 'SOURCE_OBSERVATION', 'citation': {'source': 'guard'}}])}],
            'verdict': 'CONTINUE_TO_REPLAY_BASELINE', 'replay_executed': False, 'product_effect_measured': False}
    guards_for_result(good)
    for i in range(4):
        bad = copy.deepcopy(good)
        if i == 0:
            bad['samples'][0]['binding']['edges'][0]['origin'] = 'CODE_INTENT'
        elif i == 1:
            bad['samples'][0]['unit']['citations'] = []
        elif i == 2:
            bad['replay_executed'] = True
        else:
            bad['samples'][0]['unit']['status'] = 'PARTIAL'
        try:
            guards_for_result(bad)
        except AssertionError:
            continue
        raise AssertionError('damaged guard accepted')
    print(json.dumps({'guard_mutations_rejected': 4, 'source_results_not_measured': True}))

def final():
    source()
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    assert ledger['task_id'] == TASK.name
    assert 0 < ledger['active_minutes'] <= 75 and ledger['measurement_versions'] == 1
    assert 0 <= ledger['sample_reads'] <= 12 and 0 < ledger['formal_l2_attempts'] <= 2
    for key in ('network_calls', 'installation_calls', 'model_calls', 'product_calls', 'upstream_replay_calls', 'payment_calls'):
        assert type(ledger[key]) is int and ledger[key] == 0
    assert ledger['attempts'] and all(a['started_at'] and a['finished_at'] and a['status'] in {'SUCCEEDED', 'FAILED'} for a in ledger['attempts'])
    analysis()
    print(json.dumps({'cost_boundary': 'PASS'}))

if __name__ == '__main__':
    {'package': package, 'source': source, 'analysis': analysis, 'guards': guards, 'final': final}[sys.argv[1]]()
