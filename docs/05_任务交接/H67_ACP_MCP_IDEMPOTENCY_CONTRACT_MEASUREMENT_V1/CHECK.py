"""Frozen metadata-only oracle and offline attempt ledger. No network/runtime calls."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
LOG = TASK / 'ATTEMPT_LEDGER.jsonl'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def local(name):
    p = (TASK / name).resolve()
    assert p.is_relative_to(TASK) and p != TASK
    return p

def pointer(v, p):
    for k in p.strip('/').split('/') if p else []:
        k = k.replace('~1', '/').replace('~0', '~')
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v

def package():
    lock = read(TASK / 'INPUTS.json')
    assert lock['task_id'] == TASK.name
    for name, value in lock['frozen'].items():
        assert sha(local(name).read_bytes().replace(b'\r\n', b'\n')) == value, name
    print(json.dumps({'package': 'PASS', 'measurement_executed': False}))

def source():
    package()
    lock = read(TASK / 'INPUTS.json')
    missing = [n for n in lock['protected'] if not (ROOT / n).is_file()]
    if missing:
        print(json.dumps({'result': 'INPUT_LIMIT', 'missing': missing}, ensure_ascii=True))
        raise SystemExit(3)
    for name, value in lock['protected'].items():
        assert sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) == value, name
    b = read(TASK / 'SOURCE_BUNDLE.json')
    assert b['ref'] == '7fdd78df677a94dce04c770644b0fbbb1401272b' and b['upstream_status'] == 'unreleased'
    assert len(b['source_files']) == 5 and len(b['mcp']['parameters']) == len(b['examples']) == 5
    assert 'every POST' in b['normative']['text'] and 'MUST' in b['normative']['text']
    assert sha((TASK / 'UPSTREAM_LICENSE').read_bytes().replace(b'\r\n', b'\n')) == b['source_files'][4]['full_text_sha256']
    print(json.dumps({'source': 'PASS', 'protected': len(lock['protected']), 'upstream_execution': False}))

def meta_accept(schema, meta):
    """Closed subset. No domain schemas, remote refs or full-RPC validation."""
    assert set(schema) <= {'type', 'description', 'required', 'properties', 'additionalProperties'}
    assert schema['type'] == 'object' and isinstance(meta, dict)
    if any(k not in meta for k in schema.get('required', [])):
        return False
    for key, value in meta.items():
        prop = schema.get('properties', {}).get(key)
        if prop is None:
            if schema.get('additionalProperties', True) is False:
                return False
            continue
        assert set(prop) <= {'type', 'description'}, 'unsupported semantics for a probed field'
        assert prop['type'] == 'string'
        if not isinstance(value, str):
            return False
    return True

def expected(b):
    schema = b['mcp']['meta_schema']
    probes, examples = [], []
    for i, p in enumerate(b['mcp']['parameters']):
        assert p['parameter']['name'] == 'meta' and p['parameter']['schema'] == {'$ref': '#/components/schemas/meta'}
        method, verb = p['method'], p['rest_verb']
        assert verb in {'POST', 'GET'}
        for case in ('MISSING_KEY', 'PRESENT_KEY'):
            meta = {'api_version': '2026-01-30'}
            if case == 'PRESENT_KEY':
                meta['idempotency_key'] = 'offline-h67-' + method
            accepted = meta_accept(schema, meta)
            required = verb == b['normative']['mutation_verb']
            satisfied = not required or 'idempotency_key' in meta
            probes.append({'id': method + '.' + case, 'method': method, 'case': case, 'meta': meta,
                'rest_verb': verb, 'rest_contract_requires_key': required,
                'meta_container_required': p['parameter']['required'],
                'meta_internal_key_required': 'idempotency_key' in schema.get('required', []),
                'mcp_meta_schema_accepts': accepted, 'rest_rule_satisfied': satisfied,
                'mismatch': accepted and not satisfied,
                'required_citation_pointers': ['/normative', '/mcp/meta_schema', f'/mcp/parameters/{i}']})
        e = b['examples'][i]
        assert e['method'] == e['tool'] == method and e['transport'] == 'tools/call'
        accepted = meta_accept(schema, e['meta'])
        satisfied = verb != 'POST' or 'idempotency_key' in e['meta']
        examples.append({'method': method, 'key_present': 'idempotency_key' in e['meta'],
            'mcp_meta_schema_accepts': accepted, 'rest_rule_satisfied': satisfied,
            'mismatch': accepted and not satisfied,
            'required_citation_pointers': [f'/examples/{i}', '/normative', '/mcp/meta_schema']})
    return probes, examples

def validate_result(v, b, verify_citations=True):
    assert v['task_id'] == TASK.name and v['ref'] == b['ref'] and v['scope'] == 'META_ONLY'
    assert all(v[k] is False for k in ('runtime_executed', 'product_effect_measured', 'payment_executed'))
    assert v['backend_rejects_missing_key'] == v['backend_synthesizes_stable_key'] == 'UNKNOWN'
    assert v['production_duplication_observed'] == 'NOT_MEASURED'
    wanted_probes, wanted_examples = expected(b)
    assert len(v['probes']) == 10 and len(v['examples']) == 5
    for observed, wanted in zip(v['probes'] + v['examples'], wanted_probes + wanted_examples):
        for key, value in wanted.items():
            if key == 'required_citation_pointers':
                continue
            assert type(observed[key]) is type(value) and observed[key] == value, key
        citations = observed['citations']
        assert set(c['pointer'] for c in citations) >= set(wanted['required_citation_pointers'])
        if verify_citations:
            for c in citations:
                assert sha(canonical(pointer(b, c['pointer']))) == c['value_sha256']
    confirmed = any(p['mismatch'] for p in wanted_probes)
    assert v['decision'] == ('CONTRACT_WEAKENING_CONFIRMED' if confirmed else 'NO_WEAKENING_IN_FROZEN_VIEW')

def events():
    return [json.loads(s) for s in LOG.read_text(encoding='utf-8').splitlines()] if LOG.exists() else []

def ledger(rows, verify=True, allow_begin=False, terminal=False):
    assert rows and rows[0]['action'] == 'START' and rows[0]['task_id'] == TASK.name
    previous, active, counts, done = '', None, {'ANALYSIS': 0, 'L2': 0}, []
    start, clock = rows[0]['monotonic'], rows[0]['monotonic']
    for i, e in enumerate(rows):
        assert e['seq'] == i and e['previous_hash'] == previous
        assert sha(canonical({k: v for k, v in e.items() if k != 'hash'})) == e['hash']
        assert clock <= e['monotonic'] and e['monotonic'] - start <= 2700 and e['at']
        previous, clock = e['hash'], e['monotonic']
        if i == 0:
            continue
        if e['action'] == 'BEGIN':
            assert active is None and e['kind'] in counts
            counts[e['kind']] += 1
            assert counts[e['kind']] <= 2
            assert e['attempt'] == ('A' if e['kind'] == 'ANALYSIS' else 'L') + f"{counts[e['kind']]:02d}"
            active = e
        else:
            assert e['action'] == 'FINISH' and active and e['attempt'] == active['attempt']
            assert e['status'] in {'SUCCEEDED', 'FAILED'}
            prefix = 'versions/' + e['attempt'] + '/' if active['kind'] == 'ANALYSIS' else 'evidence/'
            assert e['artifact'].startswith(prefix)
            p = local(e['artifact'])
            if verify:
                raw = p.read_bytes()
                assert sha(raw) == e['sha256'] and len(raw) == e['bytes']
                obj = json.loads(raw)
                if e['status'] == 'SUCCEEDED':
                    assert obj['task_id'] == TASK.name
                    if active['kind'] == 'L2':
                        assert obj['mode'] == 'executor' and obj['result'] == 'PASS'
                else:
                    assert obj.get('error') or obj.get('result') == 'FAIL'
            done.append(dict(e, kind=active['kind']))
            active = None
    if active:
        assert not terminal and (allow_begin or active['kind'] == 'L2'), 'unfinished analysis'
    return counts, done

def append(action, **fields):
    rows = events()
    e = dict(seq=len(rows), previous_hash=rows[-1]['hash'] if rows else '', action=action,
             at=datetime.now(timezone.utc).isoformat(), monotonic=time.monotonic(), **fields)
    e['hash'] = sha(canonical(e))
    if action != 'START':
        ledger(rows + [e], allow_begin=(action == 'BEGIN'))
    with LOG.open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(e, ensure_ascii=False) + '\n')
    print(json.dumps(e, ensure_ascii=True))

def init():
    assert not LOG.exists()
    append('START', task_id=TASK.name)

def begin(kind):
    counts, _ = ledger(events(), terminal=True)
    assert kind in counts
    append('BEGIN', kind=kind, attempt=('A' if kind == 'ANALYSIS' else 'L') + f'{counts[kind]+1:02d}')

def finish(ident, name, status):
    raw = local(name).read_bytes()
    append('FINISH', attempt=ident, artifact=name, status=status, sha256=sha(raw), bytes=len(raw))

def analysis():
    _, done = ledger(events(), terminal=(TASK / 'REPORT.md').exists())
    successes = [e for e in done if e['kind'] == 'ANALYSIS' and e['status'] == 'SUCCEEDED']
    assert successes and sha((TASK / 'RESULT.json').read_bytes()) == successes[-1]['sha256']
    validate_result(read(TASK / 'RESULT.json'), read(TASK / 'SOURCE_BUNDLE.json'))
    print(json.dumps({'measurement': 'PASS', 'scope': 'META_ONLY', 'probes': 10, 'examples': 5, 'runtime_calls': 0}))

def guards():
    # Synthetic-only source; no upstream matrix result is generated here.
    schema = {'type': 'object', 'required': ['api_version'], 'properties': {'api_version': {'type': 'string'}, 'idempotency_key': {'type': 'string'}}}
    methods = ['synthetic_create', 'synthetic_get', 'synthetic_update', 'synthetic_complete', 'synthetic_cancel']
    b = {'ref': 'synthetic', 'normative': {'mutation_verb': 'POST'}, 'mcp': {'meta_schema': schema, 'parameters': []}, 'examples': []}
    for i, method in enumerate(methods):
        b['mcp']['parameters'].append({'method': method, 'rest_verb': 'GET' if i == 1 else 'POST', 'parameter': {'name': 'meta', 'required': True, 'schema': {'$ref': '#/components/schemas/meta'}}})
        b['examples'].append({'method': method, 'tool': method, 'transport': 'tools/call', 'meta': {'api_version': 'synthetic'}})
    probes, examples = expected(b)
    for row in probes + examples:
        row['citations'] = [{'pointer': p} for p in row.pop('required_citation_pointers')]
    good = {'task_id': TASK.name, 'ref': 'synthetic', 'scope': 'META_ONLY', 'decision': 'CONTRACT_WEAKENING_CONFIRMED',
        'probes': probes, 'examples': examples, 'runtime_executed': False, 'product_effect_measured': False, 'payment_executed': False,
        'backend_rejects_missing_key': 'UNKNOWN', 'backend_synthesizes_stable_key': 'UNKNOWN', 'production_duplication_observed': 'NOT_MEASURED'}
    validate_result(good, b, False)
    for i in range(6):
        bad, source_b = copy.deepcopy(good), copy.deepcopy(b)
        if i == 0:
            source_b['mcp']['meta_schema']['required'].append('idempotency_key')
        elif i == 1:
            bad['probes'][2]['rest_contract_requires_key'] = True
        elif i == 2:
            bad['probes'][1]['meta']['api_version'] = 'different'
        elif i == 3:
            bad['probes'][0]['mcp_meta_schema_accepts'] = False
        elif i == 4:
            bad['examples'][2]['key_present'] = True
        else:
            bad['payment_executed'] = True
        try:
            validate_result(bad, source_b, False)
        except AssertionError:
            continue
        raise AssertionError('damaged metadata evidence accepted')
    print(json.dumps({'synthetic_mutations_rejected': 6, 'upstream_matrix_executed': False}))

def final():
    source()
    counts, _ = ledger(events(), terminal=(TASK / 'REPORT.md').exists())
    assert counts['ANALYSIS'] and counts['L2']
    analysis()
    print(json.dumps({'attempt_counts': counts, 'source_network_calls': 0}))

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'begin':
        begin(*sys.argv[2:])
    elif mode == 'finish':
        finish(*sys.argv[2:])
    else:
        {'package': package, 'source': source, 'init': init, 'analysis': analysis, 'guards': guards, 'final': final}[mode]()
