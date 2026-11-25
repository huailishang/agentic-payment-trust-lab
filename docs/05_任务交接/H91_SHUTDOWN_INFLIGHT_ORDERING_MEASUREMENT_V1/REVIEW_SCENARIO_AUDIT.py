"""Evaluator-owned submission audit and independent raw matrix recomputation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OUT = TASK / 'evidence/scenario/evaluator'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_check(directory, prefix):
    result = []
    for number in range(1, 7):
        meta_path = directory / f'{prefix}-{number:02}.meta.json'
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        assert meta['exit_code'] == 0
        for stream in ('stdout', 'stderr'):
            path = directory / meta[stream + '_path']
            assert path.stat().st_size == meta[stream + '_bytes']
            assert sha(path) == meta[stream + '_sha256']
        result.append(meta_path.relative_to(ROOT).as_posix())
    return result


def recompute(directory, prefix):
    def read(n):
        return json.loads((directory / f'{prefix}-{n:02}.stdout.log').read_text(encoding='utf-8'))
    inventory, order, recovery, guards, tests, preservation = [read(n) for n in range(1, 7)]
    assert len(inventory['inventory']['symbols']) == 10
    assert len(inventory['inventory']['native_tables']) == 7
    assert len(inventory['inventory']['families']) == 6
    rows = order['rows']
    assert [(r['label'], r['schedule']) for r in rows] == [
        ('A', 'none'), ('B', 'none'), ('A', 'before_read'), ('B', 'before_read'),
        ('A', 'after_read'), ('B', 'after_read'), ('B', 'after_get'), ('D', 'before_read')]
    windows = []
    gates_without_event = 0
    for i, row in enumerate(rows, 1):
        events, delta = row['events'], row['first']['effect_delta']
        assert delta == [events.count(n) for n in ('provider_create', 'provider_get', 'browser_click')]
        native = row['native_gate_observations'][0]['record']
        assert native['final_decision'] == row['first']['decision']
        assert native['callback_count'] == row['first']['callback_count']
        assert row['originals'] == row['cleanup'] == 'PASS'
        assert row['evidence_join_origin'].startswith('TEST_CORRELATED')
        assert row['admission_linearization_claim'] == 'NONE'
        gates_without_event += 'shutdown_event_ref' not in native
        if i in (3, 4):
            assert events.index('stop_committed') < events.index('read_stop')
            assert row['first']['decision'] == 'DENY' and delta == [0, 0, 0]
        if i in (5, 6, 7):
            assert events.index('read_clear') < events.index('stop_committed')
            effect = 'provider_create' if i == 5 else 'browser_click'
            assert events.index('stop_committed') < events.index(effect)
            assert row['first']['decision'] == 'ALLOW'
            windows.append('O' + str(i))
        if i in (3, 4, 5, 6, 7):
            assert row['matched_receipt'] == row['receipt']
            assert row['receipt']['event_id'] == 'event-h91-stop'
            assert row['receipt']['anchor_operation_id'] == 'operation-h89-A'
            assert row['retry']['decision'] == 'DENY' and row['retry']['effect_delta'] == [0, 0, 0]
        if i == 8:
            assert row['matched_receipt'] is None and row['first']['decision'] == 'ALLOW'
    recoveries = recovery['rows']
    assert [r['status_case'] for r in recoveries] == ['unknown', 'pending', 'late_success', 'terminal_failed', 'already_paid']
    denied, queries = 0, 0
    for row in recoveries:
        assert row['observed_effect_delta'] == [0, 2, 0] and row['query_count'] == 2
        queries += row['query_count']
        assert row['native_recovery_record_count'] == 1
        assert row['stop_replay_same_receipt'] and row['originals'] == row['cleanup'] == 'PASS'
        assert row['stop_receipt']['anchor_operation_id'] == 'operation-h89-A'
        assert row['stop_receipt']['event_id'] == 'event-h91-lifecycle'
        assert row['payment_reference'] == 'cs_test_h89_B'
        assert row['recovery_observations'][0] == row['recovery_observations'][1]
        assert len(row['stopped_entry_attempts']) == 4
        for attempt in row['stopped_entry_attempts']:
            assert attempt['decision'] == 'DENY' and attempt['callback_count'] == 0
            assert attempt['effect_delta'] == [0, 0, 0]
            denied += 1
        outcome = row['recovery_observations'][0]
        assert outcome['retry_allowed'] is False
        if row['status_case'] in ('unknown', 'pending'):
            assert outcome['recovery_status'] == 'UNRESOLVED'
            assert row['operation_state_after'] == 'UNKNOWN'
        elif row['status_case'] in ('late_success', 'already_paid'):
            assert outcome['recovery_status'] == 'RECOVERED'
            assert row['operation_state_after'] == 'PAID_CONFIRMED'
        else:
            assert row['operation_state_after'] == 'CANCELLED'
            assert outcome['recovery_status'] == 'BLOCKED'
            assert outcome['effective_status'] == 'FAILED'
    assert tests == {'passed': 124, 'skipped': 0}
    assert preservation['protected'] == 499 and preservation['product_changes_this_package'] == 0
    return {'families': 6, 'ordering_rows': 8, 'recovery_rows': 5,
            'windows': windows, 'independent_window_entries': ['A', 'B'],
            'native_gate_first_observations_without_event_field': gates_without_event,
            'recovery_stopped_entry_denials': denied, 'permitted_queries': queries,
            'admission_violation_inferred': False, 'paid_is_order_completion': False,
            'regressions': tests, 'protected': 499, 'result': 'PASS'}


def main(stage):
    OUT.mkdir(parents=True, exist_ok=True)
    submission_path = TASK / 'SUBMISSION_SCENARIO.json'
    submission = json.loads(submission_path.read_text(encoding='utf-8'))
    files = dict(submission['files'])
    files[submission_path.relative_to(ROOT).as_posix()] = sha(submission_path)
    if stage == 'post':
        acceptance = json.loads((OUT / 'ACCEPTANCE.json').read_text(encoding='utf-8'))
        files = acceptance['immutable_files']
    for name, digest in files.items():
        assert sha(ROOT / name) == digest, name
    inputs = json.loads((TASK / 'SCENARIO_INPUTS.json').read_text(encoding='utf-8'))
    assert len(inputs['files']) == 499
    for name, digest in inputs['files'].items():
        assert sha(ROOT / name) == digest, name
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == submission['head']
    l2 = TASK / 'evidence/scenario/attempt-1'
    gate = json.loads((l2 / 'L2-GATE.json').read_text(encoding='utf-8'))
    assert gate['result'] == 'PASS' and gate['checks_total'] == 6 and not gate['mandatory_failures']
    meta_checked = raw_check(l2, 'EV')
    observations = recompute(l2, 'EV')
    record = {'stage': stage, 'at': datetime.now(timezone.utc).isoformat(), 'result': 'PASS',
              'head': submission['head'], 'protected': 499, 'raw_l2_meta_checked': meta_checked,
              'recomputed_l2': observations, 'active_minutes': 'UNKNOWN'}
    if stage == 'accept':
        (OUT / 'CURRENT.submitted.md').write_bytes((ROOT / 'CURRENT.md').read_bytes())
        record['submitted_file_count_with_router_and_submission'] = len(files)
        record['immutable_files'] = {name: digest for name, digest in files.items() if name != 'CURRENT.md'}
        destination = OUT / 'ACCEPTANCE.json'
    else:
        l3 = OUT / 'l3'
        l3gate = json.loads((l3 / 'L3-GATE.json').read_text(encoding='utf-8'))
        assert l3gate['result'] == 'PASS' and l3gate['checks_total'] == 6 and not l3gate['mandatory_failures']
        record['raw_l3_meta_checked'] = raw_check(l3, 'RV-EV')
        record['recomputed_l3'] = recompute(l3, 'RV-EV')
        assert record['recomputed_l3'] == observations
        record['l2_l3_semantic_equal'] = {}
        for number in range(1, 7):
            a = (l2 / f'EV-{number:02}.stdout.log').read_text(encoding='utf-8')
            b = (l3 / f'RV-EV-{number:02}.stdout.log').read_text(encoding='utf-8')
            equal = json.loads(a) == json.loads(b)
            assert equal, number
            record['l2_l3_semantic_equal'][f'VP-{number:02}'] = equal
        record['accepted_immutable_count'] = len(files)
        destination = OUT / 'POSTCHECK.json'
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in record.items() if k not in ('immutable_files',)}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
