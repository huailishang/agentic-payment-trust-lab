"""Frozen repair gates. No extraction, acquisition, replay, or product execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
CACHE = {}
STATES = {'PROVEN', 'PARTIAL', 'UNKNOWN', 'INPUT_LIMIT'}

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def digest(v):
    return sha(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def package():
    lock = read(TASK / 'INPUTS.json')
    assert lock['task_id'] == TASK.name
    for name, h in lock['frozen'].items():
        assert sha((TASK / name).read_bytes().replace(b'\r\n', b'\n')) == h, name
    print(json.dumps({'package': 'PASS', 'local_source_validated': False}))

def source():
    package()
    lock = read(TASK / 'INPUTS.json')
    missing = [n for n in lock['readonly'] if not (ROOT / n).is_file()]
    if missing:
        print(json.dumps({'result': 'INPUT_LIMIT', 'missing': missing}, ensure_ascii=True))
        raise SystemExit(3)
    for name, h in lock['readonly'].items():
        assert sha((ROOT / name).read_bytes()) == h, name
    for name, h in lock['product_protected'].items():
        assert sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) == h, name
    print(json.dumps({'source': 'PASS', 'readonly': len(lock['readonly']), 'product': len(lock['product_protected'])}))

def ptr(v, p):
    for key in p.strip('/').split('/') if p else []:
        key = key.replace('~1', '/').replace('~0', '~')
        v = v[int(key)] if isinstance(v, list) else v[key]
    return v

def row_for(c, eid):
    assert c['file'] in read(TASK / 'INPUTS.json')['readonly']
    key = (c['file'], c['row_group'])
    if key not in CACHE:
        sys.path.insert(0, str(ROOT / '.task_envs/H64/parquet_reader'))
        import pyarrow.parquet as pq
        CACHE[key] = pq.ParquetFile(ROOT / c['file']).read_row_group(c['row_group']).to_pylist()
    row = CACHE[key][c['row_index']]
    assert row['episode_id'] == eid, 'cross-episode citation'
    return row

def citation(c, eid):
    row = row_for(c, eid)
    v = ptr(row, c['pointer'])
    assert digest(v) == c['value_sha256']
    if 'embedded_pointer' in c:
        v = ptr(json.loads(v), c['embedded_pointer'])
        assert digest(v) == c['decoded_value_sha256']
    return v

def invariants(result, expected):
    assert result['classification'] == 'REFERENCE_ONLY'
    assert result['replay_executed'] is False and result['product_effect_measured'] is False
    by_id = {s['episode_id']: s for s in result['samples']}
    assert len(by_id) == len(result['samples'])
    for e in expected['consents']:
        sample = by_id[e['episode_id']]
        matches = [r for r in sample['consent_records'] if r['seq'] == e['seq']]
        assert len(matches) == 1, 'structured confirmation omitted'
        r = matches[0]
        for key in ('given', 'checkout_id', 'raw_amount', 'currency'):
            assert type(r[key]) is type(e[key]) and r[key] == e[key], key
        assert r['actor'] == 'shopper' and r['kind'] == 'message'
        assert sample['binding']['scope'] == 'published_episode_consent_record_to_checkout'
        assert sample['binding']['status'] == 'PROVEN', 'do not erase direct source consent'
        assert sample['native_checkout_citations'], 'native same-episode checkout required'
    unit_sample = by_id[expected['unit']['episode_id']]
    units = [u for u in unit_sample['field_units'] if u['field'] == 'allowance.max_amount']
    assert len(units) == 1 and units[0]['status'] == 'PROVEN', 'specific field unit omitted'
    assert units[0]['scope'] == 'delegate_payment.request.allowance.max_amount', 'unit scope widened'
    assert units[0]['tool_name'] == expected['unit']['tool_name']
    assert unit_sample['protocol_result_kind'] == 'TOKEN_OR_ALLOWANCE', 'allowance is not paid money'
    complete = []
    for sample in result['samples']:
        assert sample['binding']['status'] in STATES and sample['unit']['status'] in STATES
        assert len(sample['binding']['reason'].strip()) >= 30 and len(sample['unit']['reason'].strip()) >= 30
        assert type(sample['complete_chain']) is bool
        if sample['complete_chain']:
            assert sample['binding']['status'] == sample['unit']['status'] == 'PROVEN'
            assert len(sample['chain_citations']) >= 4
            assert sample['protocol_result_kind'] != 'NONE'
            complete.append(sample['episode_id'])
    assert result['verdict'] in {'CONTINUE_TO_REPLAY_BASELINE', 'STOP_SOURCE_VIEW', 'INPUT_LIMIT'}
    if result['verdict'] == 'CONTINUE_TO_REPLAY_BASELINE':
        assert complete, 'no complete source chain'

def analysis():
    result = read(TASK / 'RESULT.json')
    expected = read(TASK / 'EXPECTED.json')
    lock = read(TASK / 'INPUTS.json')
    assert result['task_id'] == TASK.name
    assert [s['episode_id'] for s in result['samples']] == lock['episode_ids']
    invariants(result, expected)
    prior = read(ROOT / lock['prior_result'])
    for sample, old in zip(result['samples'], prior['samples']):
        eid = sample['episode_id']
        # Preserve the already-reviewed monetary inventory; add facts rather than replace it.
        assert sample['source_payment_observations'] == old['source_payment_observations']
        assert sample['source_request_allowances'] == old['source_request_allowances']
        for r in sample['consent_records']:
            c = r['source_citation']
            assert c['pointer'] == '/arguments' and c['embedded_pointer'] == '/consent'
            raw = row_for(c, eid)
            assert (raw['seq'], raw['kind'], raw['actor']) == (r['seq'], 'message', 'shopper')
            v = citation(c, eid)
            assert v['given'] is r['given'] and v['checkout_id'] == r['checkout_id']
            assert v['amount'] == r['raw_amount'] and v['currency'] == r['currency']
            tc = r['text_citation']
            assert (tc['file'], tc['row_group'], tc['row_index']) == (c['file'], c['row_group'], c['row_index'])
            assert tc['pointer'] == '/text' and citation(tc, eid)
            assert any(citation(nc, eid) == r['checkout_id'] for nc in sample['native_checkout_citations'])
        for u in sample['field_units']:
            definition = citation(u['definition_citation'], eid)
            assert u['application_citations']
            for c in u['application_citations']:
                citation(c, eid)
            if u['field'] == 'allowance.max_amount':
                target = expected['unit']
                c = u['definition_citation']
                for k in ('file', 'row_group', 'row_index', 'pointer', 'embedded_pointer'):
                    assert c[k] == target[k]
                assert definition == target['definition']
                tool = json.loads(ptr(row_for(c, eid), c['pointer']))
                assert tool['function']['name'] == target['tool_name']
        for c in sample['chain_citations']:
            citation(c, eid)
    print(json.dumps({'analysis': 'PASS', 'semantic_review_required': True, 'samples': len(result['samples'])}))

def guards():
    expected = read(TASK / 'EXPECTED.json')
    ids = read(TASK / 'INPUTS.json')['episode_ids']
    samples = []
    for eid in ids:
        rows = [dict(e, actor='shopper', kind='message') for e in expected['consents'] if e['episode_id'] == eid]
        samples.append({'episode_id': eid, 'consent_records': rows, 'native_checkout_citations': ['synthetic_only'] if rows else [],
            'field_units': [], 'binding': {'scope': 'published_episode_consent_record_to_checkout', 'status': 'PROVEN' if rows else 'UNKNOWN', 'reason': 'x'*40},
            'unit': {'status': 'PARTIAL', 'reason': 'x'*40}, 'complete_chain': False, 'chain_citations': [], 'protocol_result_kind': 'NONE'})
    unit = next(s for s in samples if s['episode_id'] == expected['unit']['episode_id'])
    unit['field_units'] = [{'field': 'allowance.max_amount', 'status': 'PROVEN', 'scope': 'delegate_payment.request.allowance.max_amount', 'tool_name': expected['unit']['tool_name']}]
    unit['protocol_result_kind'] = 'TOKEN_OR_ALLOWANCE'
    good = {'classification': 'REFERENCE_ONLY', 'samples': samples, 'verdict': 'STOP_SOURCE_VIEW', 'replay_executed': False, 'product_effect_measured': False}
    invariants(good, expected)
    for i in range(6):
        bad = copy.deepcopy(good)
        target = next(s for s in bad['samples'] if s['episode_id'] == expected['unit']['episode_id'])
        if i == 0:
            target['consent_records'] = []
        elif i == 1:
            target['consent_records'][0]['checkout_id'] = 'another_episode_checkout'
        elif i == 2:
            target['field_units'] = []
        elif i == 3:
            target['protocol_result_kind'] = 'PAYMENT_SUCCEEDED'
        elif i == 4:
            bad['verdict'] = 'CONTINUE_TO_REPLAY_BASELINE'
        else:
            bad['replay_executed'] = True
        try:
            invariants(bad, expected)
        except AssertionError:
            continue
        raise AssertionError('damaged result accepted')
    print(json.dumps({'guard_mutations_rejected': 6, 'source_results_not_measured': True}))

def final():
    source()
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    assert ledger['task_id'] == TASK.name
    assert 0 < ledger['active_minutes'] <= 45 and ledger['measurement_versions'] == 1
    assert 0 < ledger['sample_reads'] <= 8 and 0 < ledger['formal_l2_attempts'] <= 2
    for key in ('network_calls', 'installation_calls', 'model_calls', 'product_calls', 'upstream_replay_calls', 'payment_calls'):
        assert type(ledger[key]) is int and ledger[key] == 0
    assert ledger['attempts'] and all(a['started_at'] and a['finished_at'] and a['status'] in {'SUCCEEDED', 'FAILED'} for a in ledger['attempts'])
    analysis()
    print(json.dumps({'cost_boundary': 'PASS'}))

if __name__ == '__main__':
    {'package': package, 'source': source, 'analysis': analysis, 'guards': guards, 'final': final}[sys.argv[1]]()
