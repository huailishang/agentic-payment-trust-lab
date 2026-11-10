"""Read-only research gates and append-only request reservations; no network code."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
LOG = TASK / 'REQUEST_LEDGER.jsonl'
STAGES = {'entry', 'prepared_object', 'approval_authority', 'execution_consumption', 'credential_injection', 'outcome_recovery'}

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def local(name):
    p = (TASK / name).resolve()
    assert p.is_relative_to(TASK) and p != TASK, 'out of task path'
    return p

def package():
    lock = read(TASK / 'INPUTS.json')
    assert lock['task_id'] == TASK.name
    for name, value in lock['frozen'].items():
        assert sha(local(name).read_bytes().replace(b'\r\n', b'\n')) == value, name
    print(json.dumps({'package': 'PASS', 'research_executed': False}))

def source():
    package()
    lock = read(TASK / 'INPUTS.json')
    missing = [n for n in lock['protected'] if not (ROOT / n).is_file()]
    if missing:
        print(json.dumps({'result': 'INPUT_LIMIT', 'missing': missing}, ensure_ascii=True))
        raise SystemExit(3)
    for name, value in lock['protected'].items():
        assert sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) == value, name
    print(json.dumps({'protected': len(lock['protected']), 'raw_carttrace_required': False}))

def target_ok(kind, target, plan):
    if kind == 'file':
        assert target and not target.startswith('/') and '\\' not in target and ':' not in target
        assert all(x not in {'', '.', '..'} for x in target.split('/'))
        assert len(target) <= 350 and '?' not in target and '#' not in target
    elif kind == 'tree':
        assert target == plan['ref']
    elif kind in {'issue', 'pr'}:
        assert target.isdigit() and int(target) in plan['issues' if kind == 'issue' else 'prs']
    else:
        assert kind == 'l2' and target == 'VALIDATION_PLAN.yaml'

def artifact_ok(obj, reservation, plan):
    kind, target = reservation['kind'], reservation['target']
    assert obj['kind'] == kind and obj['target'] == target and obj['repository'] == plan['repository']
    if kind == 'file':
        assert obj['ref'] == plan['ref'] and obj['partial'] is False
        assert obj['url'] == f"https://github.com/{plan['repository']}/blob/{plan['ref']}/{target}"
        b = obj['content'].encode('utf-8')
        assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == obj['blob_sha']
    else:
        assert obj['observed_at'] and isinstance(obj['data'], (dict, list))
        if kind == 'tree':
            assert obj['ref'] == plan['ref']
            assert obj['url'] == f"https://api.github.com/repos/{plan['repository']}/git/trees/{plan['ref']}?recursive=1"
        else:
            segment = 'issues' if kind == 'issue' else 'pull'
            assert obj['url'] == f"https://github.com/{plan['repository']}/{segment}/{target}"

def events():
    return [json.loads(s) for s in LOG.read_text(encoding='utf-8').splitlines()] if LOG.exists() else []

def check_log(rows, verify=True, terminal=False, open_source=False):
    plan = read(TASK / 'SOURCE_PLAN.json')
    assert rows and rows[0]['action'] == 'START' and rows[0]['task_id'] == TASK.name
    first = rows[0]['monotonic']
    previous, clock, active = '', first, None
    attempts, finished, targets, archives = {}, {}, {}, {}
    used, reads, l2 = 0, 0, 0
    for index, event in enumerate(rows):
        body = {k: v for k, v in event.items() if k != 'hash'}
        assert event['seq'] == index and event['previous_hash'] == previous and sha(canon(body)) == event['hash']
        assert clock <= event['monotonic'] and event['monotonic'] - first <= plan['elapsed_seconds_max']
        assert event['at']
        previous, clock = event['hash'], event['monotonic']
        if index == 0:
            continue
        action = event['action']
        assert action in {'RESERVE', 'FINISH'}
        ident = event['attempt']
        if action == 'RESERVE':
            assert active is None and ident not in attempts, 'parallel or duplicate attempt'
            target_ok(event['kind'], event['target'], plan)
            if event['kind'] == 'l2':
                l2 += 1
                assert ident == f'L{l2:02d}' and l2 <= plan['l2_attempts_max']
            else:
                reads += 1
                assert ident == f'S{reads:02d}' and reads <= plan['source_requests_max']
                key = (event['kind'], event['target'])
                targets[key] = targets.get(key, 0) + 1
                assert targets[key] <= plan['attempts_per_target_max']
                assert used + plan['single_archive_bytes_max'] <= plan['archive_bytes_max']
                assert event['monotonic'] - first <= plan['elapsed_seconds_max'] - 30
            attempts[ident], active = event, ident
        else:
            assert active == ident and event['status'] in {'SUCCEEDED', 'FAILED'}
            reservation = attempts[ident]
            rel = event['artifact']
            expected_prefix = 'evidence/' if reservation['kind'] == 'l2' else 'sources/'
            assert rel.startswith(expected_prefix)
            p = local(rel)
            if reservation['kind'] != 'l2':
                assert 0 < event['bytes'] <= plan['single_archive_bytes_max']
                used += event['bytes']
                assert used <= plan['archive_bytes_max']
            if verify:
                b = p.read_bytes()
                assert len(b) == event['bytes'] and sha(b) == event['sha256'], 'archive changed'
                obj = json.loads(b)
                if reservation['kind'] == 'l2':
                    assert obj['task_id'] == TASK.name and obj['mode'] == 'executor'
                    assert obj['result'] == ('PASS' if event['status'] == 'SUCCEEDED' else 'FAIL')
                elif event['status'] == 'SUCCEEDED':
                    artifact_ok(obj, reservation, plan)
                    archives[rel] = obj
                else:
                    assert obj['kind'] == reservation['kind'] and obj['target'] == reservation['target']
                    assert obj['repository'] == plan['repository'] and obj['error']
            finished[ident], active = event, None
    if active:
        assert not terminal and (open_source or attempts[active]['kind'] == 'l2'), 'unclosed source request'
    return {'source_requests': reads, 'l2_attempts': l2, 'archive_bytes': used,
            'elapsed_seconds': clock - first, 'archives': archives}

def append(action, **values):
    rows = events()
    event = dict(seq=len(rows), at=datetime.now(timezone.utc).isoformat(), monotonic=time.monotonic(),
                 previous_hash=rows[-1]['hash'] if rows else '', action=action, **values)
    event['hash'] = sha(canon(event))
    # Validate before writing; a failed reservation does not authorize a source access.
    check_log(rows + [event], terminal=False, open_source=(action == 'RESERVE')) if action != 'START' else None
    with LOG.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(json.dumps(event, ensure_ascii=True))

def init():
    assert not LOG.exists(), 'ledger already exists'
    append('START', task_id=TASK.name)

def reserve(kind, target):
    rows = events()
    check_log(rows, terminal=True)
    count = sum(e['action'] == 'RESERVE' and (e['kind'] == 'l2') == (kind == 'l2') for e in rows)
    append('RESERVE', attempt=('L' if kind == 'l2' else 'S') + f'{count+1:02d}', kind=kind, target=target)

def finish(ident, rel, status):
    b = local(rel).read_bytes()
    append('FINISH', attempt=ident, artifact=rel, status=status, bytes=len(b), sha256=sha(b))

def claims(v):
    assert v['classification'] == 'REFERENCE_ONLY' and v['version'] == read(TASK / 'SOURCE_PLAN.json')['ref']
    assert v['runtime_executed'] is False and v['product_effect_measured'] is False and v['payment_executed'] is False
    assert v['consumer']['status'] in {'FOUND', 'NOT_FOUND_IN_VIEW', 'INPUT_LIMIT'}
    assert {s['name'] for s in v['stages']} == STAGES and len(v['stages']) == len(STAGES)
    for stage in v['stages']:
        assert stage['status'] in {'STATIC_PROVEN', 'UNKNOWN', 'NOT_APPLICABLE'}
        assert len(stage['reason'].strip()) >= 20
        if stage['status'] == 'STATIC_PROVEN':
            assert stage['citations']
    assert len(v['existing_coverage_comparison']) >= 4 and v['license'] and v['conclusion']
    assert v['decision'] in {'CONTINUE_TO_BOUNDED_MEASUREMENT', 'STOP_REFERENCE_ONLY', 'INPUT_LIMIT'}
    if v['decision'] == 'CONTINUE_TO_BOUNDED_MEASUREMENT':
        assert v['consumer']['status'] == 'FOUND' and v['consumer']['citations']
        assert v['consumer']['symbol'] and v['consumer']['financial_effect']
        assert all(s['status'] == 'STATIC_PROVEN' for s in v['stages'] if s['name'] in {'entry', 'prepared_object', 'approval_authority', 'execution_consumption'})
        assert len(v['next_question'].strip()) >= 20 and len(v['independent_signal'].strip()) >= 40
        assert len(v['new_boundary'].strip()) >= 40

def analysis():
    info = check_log(events(), terminal=(TASK / 'REPORT.md').exists())
    value = read(TASK / 'RESULT.json')
    assert value['task_id'] == TASK.name
    claims(value)
    archives = info['archives']
    def cite(c):
        obj = archives[c['artifact']]
        assert obj['kind'] == 'file', 'metadata is not code-path proof'
        lines = obj['content'].splitlines(keepends=True)
        assert 1 <= c['line_start'] <= c['line_end'] <= len(lines)
        assert sha(''.join(lines[c['line_start']-1:c['line_end']]).encode()) == c['text_sha256']
    for c in value['consumer']['citations']:
        cite(c)
    for stage in value['stages']:
        for c in stage['citations']:
            cite(c)
    protected = read(TASK / 'INPUTS.json')['protected']
    for comparison in value['existing_coverage_comparison']:
        assert comparison['local_paths'] and comparison['assessment'] in {'SAME', 'NEW_BOUNDARY', 'UNKNOWN'}
        assert all(p in protected for p in comparison['local_paths'])
        assert len(comparison['reason'].strip()) >= 20
    for c in value['license'].get('citations', []):
        cite(c)
    if value['decision'] == 'CONTINUE_TO_BOUNDED_MEASUREMENT':
        assert value['license']['status'] == 'DECLARED'
    print(json.dumps({'analysis': 'PASS', 'semantic_review_required': True, 'source_requests': info['source_requests']}))

def guards():
    plan = read(TASK / 'SOURCE_PLAN.json')
    good = {'classification': 'REFERENCE_ONLY', 'version': plan['ref'],
        'runtime_executed': False, 'product_effect_measured': False, 'payment_executed': False,
        'consumer': {'status': 'NOT_FOUND_IN_VIEW', 'citations': []},
        'stages': [{'name': n, 'status': 'UNKNOWN', 'reason': 'x'*40, 'citations': []} for n in sorted(STAGES)],
        'existing_coverage_comparison': [{}]*4, 'license': {'status': 'UNKNOWN'}, 'conclusion': 'bounded view only',
        'decision': 'STOP_REFERENCE_ONLY', 'next_question': '', 'independent_signal': '', 'new_boundary': ''}
    claims(good)
    def chain(records):
        out = []
        for i, r in enumerate(records):
            e = dict(seq=i, at='synthetic', monotonic=float(i), previous_hash=out[-1]['hash'] if out else '', **r)
            e['hash'] = sha(canon(e))
            out.append(e)
        return out
    start = {'action': 'START', 'task_id': TASK.name}
    pending = chain([start, {'action': 'RESERVE', 'attempt': 'S01', 'kind': 'file', 'target': 'README.md'}])
    changed = copy.deepcopy(pending[:1]); changed[0]['task_id'] = 'tampered'
    wrong = {'kind': 'file', 'target': 'README.md', 'repository': plan['repository'], 'ref': 'main', 'partial': False}
    bad_continue = copy.deepcopy(good); bad_continue['decision'] = 'CONTINUE_TO_BOUNDED_MEASUREMENT'
    bad_runtime = copy.deepcopy(good); bad_runtime['stages'][0]['status'] = 'RUNTIME_VERIFIED'
    bad_payment = copy.deepcopy(good); bad_payment['payment_executed'] = True
    over = [start]
    for i in range(21):
        ident = f'S{i+1:02d}'
        over.extend([{'action': 'RESERVE', 'attempt': ident, 'kind': 'file', 'target': f'file{i}.rs'},
            {'action': 'FINISH', 'attempt': ident, 'artifact': f'sources/{ident}.json', 'status': 'FAILED', 'bytes': 1, 'sha256': 'synthetic'}])
    checks = [lambda: check_log(changed, verify=False), lambda: check_log(pending, verify=False),
              lambda: artifact_ok(wrong, {'kind': 'file', 'target': 'README.md'}, plan),
              lambda: claims(bad_continue), lambda: claims(bad_runtime), lambda: claims(bad_payment),
              lambda: check_log(chain(over), verify=False)]
    for check in checks:
        try:
            check()
        except (AssertionError, KeyError):
            continue
        raise AssertionError('damaged research evidence accepted')
    print(json.dumps({'synthetic_mutations_rejected': len(checks), 'source_accesses_made': 0}))

def final():
    source()
    info = check_log(events(), terminal=(TASK / 'REPORT.md').exists())
    assert info['l2_attempts'] >= 1
    analysis()
    print(json.dumps({k: v for k, v in info.items() if k != 'archives'}))

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'reserve':
        reserve(*sys.argv[2:])
    elif mode == 'finish':
        finish(*sys.argv[2:])
    else:
        {'package': package, 'source': source, 'init': init, 'analysis': analysis, 'guards': guards, 'final': final}[mode]()
