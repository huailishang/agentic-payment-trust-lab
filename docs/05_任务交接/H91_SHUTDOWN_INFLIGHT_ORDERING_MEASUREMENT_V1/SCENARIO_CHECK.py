"""Whole-family shutdown measurement; product behavior remains unchanged."""
from contextlib import closing
from dataclasses import asdict, replace
from enum import Enum
import hashlib
from importlib import util
import inspect
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
spec = util.spec_from_file_location('h91_original_ordering', TASK / 'CHECK.py')
ordering = util.module_from_spec(spec)
spec.loader.exec_module(ordering)
h90 = ordering.h90
from agentic_payment_experiment.adapters import stripe_checkout as adapter_module
from agentic_payment_experiment.payment_execution import observe_payment_execution_gate
from agentic_payment_experiment.payment_recovery import assess_payment_recovery

STATUS_CASES = ('unknown', 'pending', 'late_success', 'terminal_failed', 'already_paid')
FAMILIES = ('not_started', 'admission_dispatch_boundary', 'inflight_unknown',
            'already_succeeded', 'restart_replay', 'untrusted_stop_state')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def preserve():
    path = TASK / 'SCENARIO_INPUTS.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    current = (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert 'frozen_manifest_sha256: ' + sha(path) in current
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == manifest['head']
    assert h90.h89.source_set() == manifest['source_files']
    for name, digest in manifest['files'].items():
        assert sha(ROOT / name) == digest, name
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'scripts'],
                                      cwd=ROOT, text=True).splitlines()
    assert set(changed) == set(manifest['inherited_product_diff']), changed
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--', 'src', 'tests', 'scripts'],
                                       cwd=ROOT, text=True).strip()
    return {'protected': len(manifest['files']), 'product_changes_this_package': 0, 'result': 'PASS'}


def inventory():
    ledger = h90.h89.StripeLabLedger
    objects = (
        ('stop_acceptance', ledger.record_mandate_shutdown),
        ('stop_read', ledger.get_mandate_shutdown),
        ('stored_create', adapter_module.StripeCheckoutAdapter.create_stored_session),
        ('stored_payment', adapter_module.StripeCheckoutAdapter.authorize_stored_browser_payment),
        ('payment_dispatch', adapter_module.StripeCheckoutAdapter.authorize_browser_payment),
        ('gate_observation', observe_payment_execution_gate),
        ('unknown_record', ledger.mark_unknown), ('provider_observation', ledger.observe),
        ('recovery_owner', ledger.recover_original), ('recovery_candidate', assess_payment_recovery),
    )
    symbols = []
    for role, function in objects:
        source, line = inspect.getsourcelines(function)
        path = Path(inspect.getsourcefile(function)).resolve()
        symbols.append({'role': role, 'symbol': function.__qualname__,
                        'path': path.relative_to(ROOT).as_posix(), 'line': line,
                        'file_sha256': sha(path),
                        'symbol_sha256': hashlib.sha256(''.join(source).encode('utf-8')).hexdigest()})
    with tempfile.TemporaryDirectory(prefix='h91-schema-') as tmp:
        store = ledger(Path(tmp) / 'synthetic.sqlite3')
        with closing(sqlite3.connect(store.path if hasattr(store, 'path') else Path(tmp) / 'synthetic.sqlite3')) as con:
            tables = sorted(r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    assert not Path(tmp).exists()
    return {'symbols': symbols, 'native_tables': tables,
            'operational_cut': 'gate invocation and local simulated callback entry are observable; durable admission is not assumed',
            'admission_contract_status': 'NOT_ESTABLISHED_BY_CURRENT_OBSERVATION',
            'recovery_owner': 'StripeLabLedger.recover_original / assess_payment_recovery',
            'recovery_candidate_is_payment_authorization': False,
            'shutdown_closure_projection': 'NOT_CLAIMED',
            'families': list(FAMILIES), 'cleanup': 'PASS'}


def check_recovery_observation(row):
    assert row['observed_effect_delta'][0] == 0 and row['observed_effect_delta'][2] == 0
    assert row['query_count'] == row['observed_effect_delta'][1] == 2
    assert row['scope'] == 'LOCAL_SYNTHETIC'
    assert row['status_case'] in STATUS_CASES
    assert len(row['recovery_observations']) == 2
    assert row['recovery_observations'][0] == row['recovery_observations'][1]
    for action in row['stopped_entry_attempts']:
        assert action['decision'] == 'DENY' and action['effect_delta'] == [0, 0, 0]
    assert len(row['stopped_entry_attempts']) == 4
    assert row['stop_replay_same_receipt'] and row['originals'] == 'PASS' and row['cleanup'] == 'PASS'
    outcome = row['recovery_observations'][0]
    if row['status_case'] in ('unknown', 'pending'):
        assert outcome['recovery_status'] == 'UNRESOLVED' and outcome['retry_allowed'] is False
    elif row['status_case'] in ('late_success', 'already_paid'):
        assert outcome['recovery_status'] == 'RECOVERED' and outcome['retry_allowed'] is False
        assert row['operation_state_after'] == 'PAID_CONFIRMED'
    else:
        assert outcome['recovery_status'] in ('RETRY_CANDIDATE', 'BLOCKED')
    return True


def selfcheck():
    parent = ordering.selfcheck()
    sample = {'observed_effect_delta': [0, 2, 0], 'query_count': 2, 'scope': 'LOCAL_SYNTHETIC',
              'status_case': 'unknown', 'recovery_observations': [
                  {'recovery_status': 'UNRESOLVED', 'retry_allowed': False},
                  {'recovery_status': 'UNRESOLVED', 'retry_allowed': False}],
              'stopped_entry_attempts': [{'decision': 'DENY', 'effect_delta': [0, 0, 0]} for _ in range(4)],
              'stop_replay_same_receipt': True, 'originals': 'PASS', 'cleanup': 'PASS'}
    assert check_recovery_observation(sample)
    mutations = [dict(sample, observed_effect_delta=[1, 2, 0]),
                 dict(sample, observed_effect_delta=[0, 2, 1]),
                 dict(sample, recovery_observations=[{'recovery_status': 'UNRESOLVED', 'retry_allowed': True}] * 2),
                 dict(sample, stopped_entry_attempts=[{'decision': 'ALLOW', 'effect_delta': [0, 0, 1]}] * 4)]
    for candidate in mutations:
        try:
            check_recovery_observation(candidate)
        except AssertionError:
            continue
        raise AssertionError('unsafe recovery projection accepted')
    return {'ordering_selfcheck': parent, 'recovery_positive_controls': 1,
            'recovery_corruptions_rejected': len(mutations), 'families': list(FAMILIES),
            'ordering_rows': len(ordering.ROWS), 'recovery_rows': len(STATUS_CASES),
            'product_actions': 0, 'result': 'PASS'}


def ordering_matrix():
    rows = []
    native_gate = adapter_module._gate
    for label, schedule in ordering.ROWS:
        gates = []

        def observe(ctx, decision, callback):
            result = native_gate(ctx, decision, callback)
            gates.append({'payment_id': ctx.execution.payment_id, 'record': clean(asdict(result))})
            return result

        with patch.object(adapter_module, '_gate', observe):
            row = ordering.measure(label, schedule)
        # First observation is always the B pre-created setup control.
        actual = gates[1:]
        assert len(actual) == (2 if row['retry'] is not None else 1)
        assert actual[0]['record']['final_decision'] == row['first']['decision']
        assert actual[0]['record']['callback_count'] == row['first']['callback_count']
        row['native_gate_observations'] = actual
        row['evidence_join_origin'] = 'TEST_CORRELATED_BY_OPERATION_SNAPSHOT_AND_EVENT'
        row['native_shutdown_event_field'] = 'shutdown_event_ref' in actual[0]['record']
        row['admission_linearization_claim'] = 'NONE'
        rows.append(row)
    common = sorted({r['label'] for r in rows if r['schedule'] == 'after_read'
                     and r['classification'] == 'READ_THEN_STOP_THEN_EFFECT'})
    return {'rows': rows, 'common_observed_window_entries': common,
            'window_is_existing_contract_violation': 'NOT_INFERRED',
            'native_admission_and_shutdown_event_link': 'REQUIRES_EVALUATOR_SEMANTIC_REVIEW',
            'scope': 'LOCAL_SYNTHETIC', 'product_changes_this_package': 0}


def paid_objects(unit):
    session = dict(unit['client'].session, status='complete', payment_status='paid', payment_intent='pi_test_h91')
    intent = dict(id='pi_test_h91', livemode=False, status='succeeded', latest_charge='ch_test_h91', amount=100, currency='usd')
    charge = dict(id='ch_test_h91', livemode=False, status='succeeded', paid=True, captured=True,
                  amount=100, currency='usd', payment_intent='pi_test_h91')
    return session, intent, charge


def recovery_row(status_case):
    with tempfile.TemporaryDirectory(prefix='h91-lifecycle-') as tmp:
        j = h90.setup(tmp)
        unit = j.units['B']
        initial = j.pay('B')
        assert initial.final_decision.value == 'ALLOW' and initial.callback_count == 1
        j.store.mark_unknown(unit['op'])
        if status_case == 'already_paid':
            j.store.observe(unit['op'], *paid_objects(unit))
        originals = j.originals()
        args = h90.event(j, event_id='event-h91-lifecycle') | {'received_at': h90.NOW + h90.timedelta(seconds=4)}
        receipt = j.store.record_mandate_shutdown(j.units['A']['op'], **args)
        before = j.counts('B')
        observations, attempts, native_states = [], [], []
        initial_state = j.store.get(unit['op'])['state']
        status = {'unknown': h90.PaymentStatus.UNKNOWN, 'pending': h90.PaymentStatus.PENDING,
                  'late_success': h90.PaymentStatus.SUCCEEDED, 'already_paid': h90.PaymentStatus.SUCCEEDED,
                  'terminal_failed': h90.PaymentStatus.FAILED}[status_case]
        payment = replace(unit['ctx'].execution,
                          status=h90.PaymentStatus.SUCCEEDED if status_case == 'already_paid' else h90.PaymentStatus.UNKNOWN,
                          provider_ref=unit['client'].session['id'])
        fact = h90.PaymentStatusObservation(payment.payment_id, payment.order_id, status,
                    h90.NOW + h90.timedelta(seconds=5), 'stripe_api', provider_ref=payment.provider_ref)
        for _ in range(2):
            j.store = h90.h89.StripeLabLedger(j.path)
            assert j.store.get_mandate_shutdown(unit['op'], expected_sha256=unit['ref']) == receipt
            assert j.store.record_mandate_shutdown(j.units['A']['op'], **args) == receipt
            if status_case in ('late_success', 'already_paid'):
                unit['client'].session = paid_objects(unit)[0]
                session = unit['client'].get_session(payment.provider_ref)
                native = j.store.observe(unit['op'], session, *paid_objects(unit)[1:])
            elif status_case == 'terminal_failed':
                unit['client'].session = dict(unit['client'].session, status='expired', payment_status='unpaid')
                session = unit['client'].get_session(payment.provider_ref)
                native = j.store.observe(unit['op'], session, None, None)
            else:
                session = unit['client'].get_session(payment.provider_ref)
                try:
                    j.store.observe(unit['op'], session, None, None)
                except h90.StripeCheckoutError as error:
                    assert str(error) == 'provider_status_inconclusive'
                    native = str(error)
                else:
                    raise AssertionError('inconclusive session falsely resolved')
            native_states.append(native)
            result = j.store.recover_original(unit['op'], payment, fact)
            observations.append(clean(asdict(result)))
            for entry in ('create', 'pay'):
                counts = j.counts('B')
                gate = j.create('B') if entry == 'create' else j.pay('B')
                assert not isinstance(gate, h90.CheckoutReceipt)
                attempts.append({'entry': entry, 'decision': gate.final_decision.value,
                                 'callback_count': gate.callback_count,
                                 'effect_delta': [b - a for a, b in zip(counts, j.counts('B'))]})
        assert j.originals() == originals
        after_state = j.store.get(unit['op'])['state']
        with closing(sqlite3.connect(j.path)) as con:
            recovery_record_count = con.execute('SELECT count(*) FROM recoveries WHERE operation_id=?', (unit['op'],)).fetchone()[0]
        assert recovery_record_count == 1
        row = {'status_case': status_case, 'scope': 'LOCAL_SYNTHETIC', 'operation_id': unit['op'],
               'snapshot_sha256': unit['ref'], 'stop_receipt': receipt,
               'payment_reference': payment.provider_ref, 'observation': clean(asdict(fact)),
               'fixture_status_source': 'SYNTHETIC_STATUS_FACT; not inferred from an open session',
               'operation_state_before': initial_state, 'operation_state_after': after_state,
               'provider_observe_results': native_states, 'recovery_observations': observations,
               'stopped_entry_attempts': attempts, 'query_count': 2,
               'observed_effect_delta': [b - a for a, b in zip(before, j.counts('B'))],
               'stop_replay_same_receipt': True, 'originals': 'PASS',
               'native_recovery_record_count': recovery_record_count,
               'responsibility': 'native next_action; task runner only correlates, no production assignment claimed'}
    assert not Path(tmp).exists()
    row['cleanup'] = 'PASS'
    check_recovery_observation(row)
    return row


def recovery_matrix():
    return {'rows': [recovery_row(name) for name in STATUS_CASES],
            'automatic_payment_retry_executed': False,
            'refund_or_cancellation_executed': False,
            'paid_state_is_not_order_or_shutdown_completion': True}


def main():
    assert os.name == 'nt' and sys.version_info[:2] == (3, 12) and not sys.flags.optimize
    command, = sys.argv[1:]
    if command == 'preflight':
        result = {'selfcheck': selfcheck(), 'inventory': inventory()}
    else:
        preserve()
        commands = {'inventory': lambda: {'inventory': inventory(), 'selfcheck': selfcheck()},
                    'ordering': ordering_matrix, 'recovery': recovery_matrix, 'guards': h90_guard,
                    'regressions': h90.h89.regressions, 'preserve': preserve}
        result = commands[command]()
        preserve()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def h90_guard():
    return {'ingress': h90.ingress(), 'propagation': [h90.propagation(False), h90.propagation(True)],
            'integrity': h90.integrity(), 'compatibility': h90.compatibility()}


if __name__ == '__main__':
    main()
