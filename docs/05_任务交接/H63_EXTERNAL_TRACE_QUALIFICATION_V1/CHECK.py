"""Frozen evidence-grounding and preservation checks; no product execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def value_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()

def pointer(value, path):
    assert path == '' or path.startswith('/'), 'invalid JSON pointer'
    if path:
        for part in path[1:].split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            value = value[int(part)] if isinstance(value, list) else value[part]
    return value

def validate_citation(citation, rows):
    line = citation['line']
    assert type(line) is int and 2 <= line <= len(rows), 'source line out of bounds/session metadata'
    row = rows[line - 1]
    assert row['type'] == 'message'
    assert value_sha(pointer(row, citation['pointer'])) == citation['value_sha256'], 'citation value mismatch'
    return row['message']

def validate_cost(cost):
    assert type(cost['active_minutes']) is int and 0 < cost['active_minutes'] <= 120
    for key in ['network_calls', 'model_calls', 'payment_calls', 'installation_calls', 'product_calls']:
        assert type(cost[key]) is int and cost[key] == 0, key

def validate_level(level):
    assert level == 'TRANSCRIPT_ONLY', 'preview cannot prove independent backend facts'

def has_payment_tool_call(message):
    """Match original CartTrace camelCase toolCalls; do not treat agent prose or browsing calls as payment."""
    calls = message.get('toolCalls')
    if not isinstance(calls, list):
        return False
    payment_functions = {'pay', 'request_payment', 'shop_pay_payment_request'}
    return any(isinstance(call, dict) and isinstance(call.get('function'), dict) and
               call['function'].get('name') in payment_functions for call in calls)

def source():
    lock = read(TASK / 'INPUTS.json')
    baseline = read(TASK / 'BASELINE.json')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == baseline['head']
    for name, digest in lock['frozen_files'].items():
        assert sha(TASK / name) == digest, name
    assert sha(ROOT / lock['map_path']) == lock['map_sha256'], 'new map drift'
    for name, digest in baseline['h62_files'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in baseline['other_workspace_files'].items():
        assert sha(ROOT / name) == digest, name
    historical = baseline['map_rebaseline']
    assert sha(ROOT / historical['archive']) == historical['sha256']
    for row in baseline['source_databases'].values():
        assert sha(ROOT / row['path']) == row['sha256']
    allowed = set(lock['frozen_files']) | {'INPUTS.json', 'EXTRACT.py', 'MEASUREMENT.json', 'ATTEMPT_LEDGER.json', 'REPORT.md', 'REVIEW.md'}
    for path in TASK.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in allowed or name.startswith('evidence/'), name
    known = set(lock['workspace_files'])
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    prefix = TASK.relative_to(ROOT).as_posix() + '/'
    assert all(raw.decode('utf-8').startswith(prefix) for raw in names if raw and raw.decode('utf-8') not in known), 'new file outside task'
    current = (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert 'task_id: H63_EXTERNAL_TRACE_QUALIFICATION_V1' in current
    for field in ['commit', 'push', 'history_rewrite', 'api_call']:
        assert 'authorization_' + field + ': false' in current
    print(json.dumps({'h62_preserved': len(baseline['h62_files']), 'other_preserved': len(baseline['other_workspace_files']), 'frozen': len(lock['frozen_files']), 'source_databases': 3}))

def validate_measurement(data):
    spec = read(TASK / 'SPEC.json')
    assert data['task_id'] == TASK.name
    assert [s['sample_id'] for s in data['samples']] == spec['sample_ids']
    for index, sample in enumerate(data['samples'], 1):
        name = 'references/TRACE_' + str(index).zfill(2) + '.jsonl'
        assert sample['file'] == name
        validate_level(sample['evidence_level'])
        rows = [json.loads(line) for line in (TASK / name).read_text(encoding='utf-8').splitlines() if line.strip()]
        assert sample['episode_id'] == rows[0]['id']
        assert set(sample['facts']) == set(spec['fact_keys'])
        for key, fact in sample['facts'].items():
            assert fact['status'] in spec['fact_status'] and len(fact['reason'].strip()) >= 8
            assert isinstance(fact['citations'], list)
            if fact['status'] == 'PRESENT':
                assert fact['citations'], 'present fact must cite source'
            if fact['status'] == 'ABSENT':
                assert not fact['citations'], 'absence must not cite invented positive proof'
            for citation in fact['citations']:
                message = validate_citation(citation, rows)
                role = message['role']
                if key in {'user_request', 'explicit_confirmation'}:
                    assert role == 'user', 'agent/tool cannot grant user authority'
                elif key == 'payment_request':
                    assert role == 'assistant' and has_payment_tool_call(message), 'payment request needs actual source payment tool call'
                elif key in {'checkout_snapshot', 'payment_tool_result', 'order_tool_result'}:
                    assert role == 'tool', 'result requires tool record'
        assert set(sample['contracts']) == set(spec['contract_keys'])
        for mapping in sample['contracts'].values():
            assert mapping['input_status'] in spec['input_status'] and len(mapping['reason'].strip()) >= 8
            assert set(mapping['fact_keys']) <= set(spec['fact_keys'])
            if mapping['input_status'] == 'OBSERVABLE':
                assert mapping['fact_keys'] and all(sample['facts'][k]['status'] == 'PRESENT' for k in mapping['fact_keys'])
    decision = data['decision']
    assert decision['candidate_classification'] == spec['candidate_classification']
    assert decision['view_decision'] in spec['view_decision']
    assert set(spec['required_limits']) <= set(decision['limits'])
    assert isinstance(decision['missing_inputs'], list) and decision['missing_inputs']
    assert len(decision['reason'].strip()) >= 15
    assert len(set(decision['candidate_sample_ids'])) == len(decision['candidate_sample_ids'])
    assert set(decision['candidate_sample_ids']) <= set(spec['sample_ids'])
    if decision['view_decision'] == 'STOP_PREVIEW_VIEW':
        assert not decision['candidate_sample_ids'] and decision['question'] is None
    else:
        assert decision['candidate_sample_ids'] and isinstance(decision['question'], str) and len(decision['question'].strip()) >= 15
    validate_cost(data['cost'])

def measurement():
    validate_measurement(read(TASK / 'MEASUREMENT.json'))
    print(json.dumps({'samples': 6, 'semantic_review_required': True, 'product_effect_measured': False}))

def decision():
    data = read(TASK / 'MEASUREMENT.json')
    validate_measurement(data)
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    assert ledger['task_id'] == TASK.name
    entries = ledger['sample_attempts']
    assert 6 <= len(entries) <= 18 and len({r['id'] for r in entries}) == len(entries)
    assert all(r['sample_id'] in read(TASK / 'SPEC.json')['sample_ids'] and r['started_at'] and r['terminal_status'] in {'SUCCEEDED', 'FAILED'} for r in entries)
    assert {r['sample_id'] for r in entries if r['terminal_status'] == 'SUCCEEDED'} == set(read(TASK / 'SPEC.json')['sample_ids'])
    assert 0 <= ledger['formal_l2_attempts'] <= 2
    assert data['cost']['active_minutes'] == ledger['active_minutes']
    print(json.dumps({'decision': data['decision']['view_decision'], 'sample_attempts': len(entries), 'active_minutes': ledger['active_minutes']}))

def selftest():
    row = {'type': 'message', 'message': {'role': 'user', 'content': 'approve total 10'}}
    rows = [{'type': 'session'}, row]
    good = {'line': 2, 'pointer': '/message/content', 'value_sha256': value_sha('approve total 10')}
    assert validate_citation(good, rows)['role'] == 'user'
    # Real preview positive and negative tests for the source's camelCase toolCalls.
    original = [json.loads(line) for line in (TASK / 'references/TRACE_06.jsonl').read_text(encoding='utf-8').splitlines()]
    payment_message = original[28]['message']
    actual = {'line': 29, 'pointer': '/message/toolCalls', 'value_sha256': value_sha(payment_message['toolCalls'])}
    assert validate_citation(actual, original)['role'] == 'assistant'
    assert has_payment_tool_call(payment_message), 'S06 pay call must be representable'
    assert not has_payment_tool_call({'role': 'assistant', 'content': 'Paid successfully.'})
    assert not has_payment_tool_call({'role': 'assistant', 'toolCalls': [{'function': {'name': 'search_catalog'}}]})
    assert not has_payment_tool_call({'role': 'assistant', 'tool_calls': [{'function': {'name': 'pay'}}]})
    assert not has_payment_tool_call({'role': 'tool', 'content': 'payment approved'})
    bads = [dict(good, line=1), dict(good, line=3), dict(good, value_sha256='0' * 64), dict(good, pointer='/message/missing')]
    for bad in bads:
        try:
            validate_citation(bad, rows)
        except (AssertionError, KeyError, IndexError):
            continue
        raise AssertionError('bad citation accepted')
    cost = {'active_minutes': 1, 'network_calls': 0, 'model_calls': 0, 'payment_calls': 0, 'installation_calls': 0, 'product_calls': 0}
    validate_cost(cost)
    validate_level('TRANSCRIPT_ONLY')
    for check, value in [(validate_cost, dict(cost, active_minutes=121)), (validate_cost, dict(cost, payment_calls=1)), (validate_level, 'INDEPENDENT_BACKEND_RECORD')]:
        try:
            check(value)
        except AssertionError:
            continue
        raise AssertionError('unsafe cost/evidence escalation accepted')
    print(json.dumps({'negative_checks': len(bads) + 3, 'scope': 'checker grounding only, not product safety'}))

if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'final':
        selftest()
        source()
    else:
        {'source': source, 'measurement': measurement, 'decision': decision, 'selftest': selftest}[command]()
