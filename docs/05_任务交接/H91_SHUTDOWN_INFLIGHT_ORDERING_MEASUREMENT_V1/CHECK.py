"""Read-only controlled interleavings over accepted H90 product code."""
from importlib import util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H90_STORED_MANDATE_SHUTDOWN_V1')
spec = util.spec_from_file_location('h91_h90', PARENT / 'CHECK.py')
h90 = util.module_from_spec(spec)
spec.loader.exec_module(h90)
ROWS = [('A', 'none'), ('B', 'none'), ('A', 'before_read'),
        ('B', 'before_read'), ('A', 'after_read'), ('B', 'after_read'),
        ('B', 'after_get'), ('D', 'before_read')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve():
    lock_path = TASK / 'INPUTS.json'
    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    assert 'frozen_manifest_sha256: ' + sha(lock_path) in (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == lock['head']
    assert h90.h89.source_set() == lock['source_files']
    for name, digest in lock['files'].items():
        assert sha(ROOT / name) == digest, name
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'scripts'],
                                      cwd=ROOT, text=True).splitlines()
    assert set(changed) == set(lock['inherited_product_diff']), changed
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--', 'src', 'tests', 'scripts'],
                                       cwd=ROOT, text=True).strip()
    return {'protected': len(lock['files']), 'product_changes_this_task': 0, 'result': 'PASS'}


def analyze(events, delta):
    assert events and events[0] == 'action_start' and events[-1] == 'action_return'
    assert events.count('stop_committed') <= 1
    assert events.count('read_clear') + events.count('read_stop') == 1
    assert delta == [events.count('provider_create'), events.count('provider_get'), events.count('browser_click')]
    if 'stop_committed' not in events:
        return 'NO_STOP_DURING_ACTION'
    stop_index = events.index('stop_committed')
    read_name = 'read_stop' if 'read_stop' in events else 'read_clear'
    if stop_index < events.index(read_name):
        assert delta == [0, 0, 0] or read_name == 'read_clear'
        return 'STOP_BEFORE_READ'
    effects_after = [name for name in ('provider_create', 'browser_click')
                     if name in events and events.index(name) > stop_index]
    return 'READ_THEN_STOP_THEN_EFFECT' if effects_after else 'NO_NEW_WRITE_EFFECT_AFTER_STOP'


def selfcheck():
    valid = ['action_start', 'read_clear', 'stop_committed', 'provider_create', 'action_return']
    assert analyze(valid, [1, 0, 0]) == 'READ_THEN_STOP_THEN_EFFECT'
    assert analyze(['action_start', 'stop_committed', 'read_stop', 'action_return'], [0, 0, 0]) == 'STOP_BEFORE_READ'
    invalid = [(valid, [0, 0, 0]),
               (['action_start', 'stop_committed', 'read_stop', 'browser_click', 'action_return'], [0, 0, 1]),
               (['action_start', 'stop_committed', 'stop_committed', 'read_stop', 'action_return'], [0, 0, 0]),
               (['action_start', 'provider_create', 'action_return'], [1, 0, 0])]
    for events, delta in invalid:
        try:
            analyze(events, delta)
        except AssertionError:
            continue
        raise AssertionError('invalid trace accepted')
    assert len(ROWS) == len(set(ROWS)) == 8
    return {'trace_controls': 2, 'rejected_corrupt_traces': len(invalid),
            'fixed_rows': len(ROWS), 'product_actions': 0, 'result': 'PASS'}


def measure(label, schedule):
    with tempfile.TemporaryDirectory(prefix='h91-ordering-') as tmp:
        j = h90.setup(tmp)
        u = j.units[label]
        originals = j.originals()
        writer = h90.h89.StripeLabLedger(j.path)
        reader = h90.h89.StripeLabLedger(j.path)
        trace, receipt = [], []
        read_impl = j.store.get_mandate_shutdown
        create_impl, get_impl = u['client'].create_session, u['client'].get_session

        def commit():
            if receipt:
                return
            # A anchors the shared mandate even when D is the executing control.
            args = h90.event(j, event_id='event-h91-stop')
            fact = writer.record_mandate_shutdown(j.units['A']['op'], **args)
            assert reader.get_mandate_shutdown(j.units['A']['op'], expected_sha256=j.units['A']['ref']) == fact
            receipt.append(fact)
            trace.append('stop_committed')

        def read(*args, **kwargs):
            fact = read_impl(*args, **kwargs)
            trace.append('read_stop' if fact else 'read_clear')
            if schedule == 'after_read':
                commit()
            return fact

        def create(*args, **kwargs):
            trace.append('provider_create')
            return create_impl(*args, **kwargs)

        def get(*args, **kwargs):
            trace.append('provider_get')
            value = get_impl(*args, **kwargs)
            trace.append('provider_get_return')
            if schedule == 'after_get':
                commit()
            return value

        def click(url):
            trace.append('browser_click')
            u['clicked'].append(url)

        j.store.get_mandate_shutdown = read
        u['client'].create_session, u['client'].get_session = create, get

        def invoke():
            before = j.counts(label)
            trace.append('action_start')
            if schedule == 'before_read':
                commit()
            if label == 'B':
                result = u['adapter'].authorize_stored_browser_payment(
                    j.store, operation_id=u['op'], expected_authority_sha256=u['ref'],
                    now=h90.NOW + h90.timedelta(seconds=2), browser_payment=click)
            else:
                result = j.create(label)
            gate = result.gate if isinstance(result, h90.CheckoutReceipt) else result
            trace.append('action_return')
            delta = [b - a for a, b in zip(before, j.counts(label))]
            decision = gate.final_decision.value
            assert decision in ('ALLOW', 'DENY'), decision
            expected_delta = ([0, 1, 1] if label == 'B' else [1, 0, 0]) if decision == 'ALLOW' else [0, 0, 0]
            assert delta == expected_delta
            assert gate.callback_count == (1 if decision == 'ALLOW' else 0)
            return {'decision': decision, 'effect_delta': delta, 'callback_count': gate.callback_count}

        first = invoke()
        first_trace = list(trace)
        classification = analyze(first_trace, first['effect_delta'])
        if schedule == 'none':
            assert first['decision'] == 'ALLOW' and not receipt
        elif label == 'D':
            assert first['decision'] == 'ALLOW'
        elif schedule == 'before_read':
            assert first['decision'] == 'DENY'
        if schedule == 'after_read':
            assert first_trace.index('read_clear') < first_trace.index('stop_committed')
        if schedule == 'after_get':
            assert first_trace.index('provider_get_return') < first_trace.index('stop_committed')
        matched = reader.get_mandate_shutdown(u['op'], expected_sha256=u['ref'])
        assert matched == (receipt[0] if receipt and label != 'D' else None)
        retry = None
        if receipt and label != 'D':
            trace.clear()
            retry = invoke() | {'events': list(trace)}
            assert retry['decision'] == 'DENY' and retry['effect_delta'] == [0, 0, 0]
            assert 'read_stop' in retry['events']
        assert originals == j.originals()
        row = {'label': label, 'schedule': schedule, 'operation_id': u['op'],
               'snapshot_sha256': u['ref'], 'first': first, 'events': first_trace,
               'classification': classification, 'receipt': receipt[0] if receipt else None,
               'matched_receipt': matched, 'retry': retry, 'originals': 'PASS'}
    assert not Path(tmp).exists()
    return row | {'cleanup': 'PASS'}


def matrix():
    rows = [measure(label, schedule) for label, schedule in ROWS]
    common = sorted({r['label'] for r in rows if r['schedule'] == 'after_read'
                     and r['classification'] == 'READ_THEN_STOP_THEN_EFFECT'})
    return {'rows': rows, 'common_window_entries': common,
            'capability_design_eligible': len(common) >= 2,
            'production_cancellation_guarantee': 'NOT_JUDGEABLE',
            'product_changes_this_task': 0}


def guards():
    # Reuse behavior functions, not historical strict-map/router entry points.
    return {'ingress': h90.ingress(), 'propagation': [h90.propagation(False), h90.propagation(True)],
            'integrity': h90.integrity(), 'compatibility': h90.compatibility()}


def main():
    assert os.name == 'nt' and sys.version_info[:2] == (3, 12) and not sys.flags.optimize
    command, = sys.argv[1:]
    if command == 'preflight':
        result = selfcheck()
    else:
        preserve()
        result = {'selfcheck': selfcheck, 'matrix': matrix, 'guards': guards,
                  'regressions': h90.h89.regressions, 'preserve': preserve}[command]()
        preserve()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
