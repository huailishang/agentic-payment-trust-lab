"""Frozen local acceptance for one mandate shutdown fact and its consumers."""
from contextlib import closing
from dataclasses import replace
from datetime import timedelta, timezone
import hashlib
from importlib import util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1')
spec = util.spec_from_file_location('h90_parent_h89', PARENT / 'CHECK.py')
h89 = util.module_from_spec(spec)
spec.loader.exec_module(h89)

from agentic_payment_experiment.adapters.stripe_checkout import CheckoutReceipt, StripeCheckoutError
from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation

NOW = h89.NOW
TABLE = 'mandate_shutdowns'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(pre=False):
    manifest = TASK / 'INPUTS.json'
    lock = json.loads(manifest.read_text(encoding='utf-8'))
    router = (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert 'frozen_manifest_sha256: ' + sha(manifest) in router
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == lock['head']
    assert h89.source_set() == lock['source_files']
    assert set(lock['mutable']).issubset(lock['source_files'])
    for name, digest in lock['files'].items():
        assert sha(ROOT / name) == digest, name
    if pre:
        for name, digest in lock['mutable'].items():
            assert sha(ROOT / name) == digest, name
    unstaged = subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'scripts'],
                                       cwd=ROOT, text=True).splitlines()
    assert set(unstaged).issubset(lock['mutable']), unstaged
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--', 'src', 'tests', 'scripts'],
                                       cwd=ROOT, text=True).strip()
    return {'protected': len(lock['files']), 'preservation': 'PASS', 'baseline': pre}


def setup(tmp):
    j = h89.Journey(tmp)
    for label in ('A', 'B', 'D'):
        j.register(label)
    bought = j.create('B')
    assert isinstance(bought, CheckoutReceipt) and bought.gate.final_decision.value == 'ALLOW'
    j.store.bind_session(j.units['B']['op'], j.units['B']['client'].session)
    return j


def event(j, label='A', event_id='event-h90-stop'):
    u = j.units[label]
    key = u['ctx'].mandate
    return {'expected_sha256': u['ref'], 'subject_ref': key.user_id,
            'mandate_id': key.mandate_id, 'authority_version': key.authority_version,
            'event_id': event_id, 'received_at': NOW}


def lookup(j, label):
    u = j.units[label]
    return j.store.get_mandate_shutdown(u['op'], expected_sha256=u['ref'])


def stop(j, label='A', **changes):
    return j.store.record_mandate_shutdown(j.units[label]['op'], **(event(j, label) | changes))


def rejects(call):
    try:
        call()
    except StripeCheckoutError as error:
        return str(error)
    raise AssertionError('an invalid shutdown was accepted')


def action(j, label, desired, counts):
    before = j.counts(label)
    result = j.pay(label) if label == 'B' else j.create(label)
    gate = result.gate if isinstance(result, CheckoutReceipt) else result
    seen = [end - start for start, end in zip(before, j.counts(label))]
    assert seen == counts, (label, seen)
    assert gate.final_decision.value == desired and gate.callback_count == (1 if desired == 'ALLOW' else 0)
    assert gate.callback_executed == (desired == 'ALLOW')
    return {'decision': desired, 'effect_delta': seen, 'callback_count': gate.callback_count}


def baseline():
    old = h89.branch('none')
    return {'units': {label: [row['gate_decision'], row['effect_delta'], row['snapshot_sha256']]
                     for label, row in old['units'].items()},
            'whole_mandate_accepted': 0, 'cleanup': old['temporary_cleanup']}


def propagation(with_stop):
    baseline_data = json.loads((TASK / 'evidence/preparation/PREP.stdout.log').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory() as tmp:
        j = setup(tmp)
        before = j.originals()
        fact = stop(j) if with_stop else None
        if with_stop:
            args = event(j)
            assert fact == {'event_id': args['event_id'], 'subject_ref': args['subject_ref'],
                            'mandate_id': args['mandate_id'], 'authority_version': args['authority_version'],
                            'anchor_operation_id': j.units['A']['op'], 'anchor_snapshot_sha256': args['expected_sha256'],
                            'received_at': NOW.astimezone(timezone.utc).isoformat(), 'source': 'LOCAL_USER_CONTROL'}
        j.store = h89.StripeLabLedger(j.path)
        j.register('C', NOW + timedelta(seconds=1))
        rows = {}
        for label in ('A', 'B', 'C', 'D'):
            matched = with_stop and label != 'D'
            out = action(j, label, 'DENY' if matched else 'ALLOW',
                         [0, 0, 0] if matched else ([0, 1, 1] if label == 'B' else [1, 0, 0]))
            stop_fact = lookup(j, label)
            assert stop_fact == (fact if matched else None)
            u = j.units[label]
            expected_decision, expected_delta, expected_snapshot = baseline_data['baseline']['units'][label]
            assert u['ref'] == expected_snapshot
            if not matched:
                assert out['decision'] == expected_decision and out['effect_delta'] == expected_delta
            original = j.store.load_authority(u['op'], expected_sha256=u['ref'])
            assert original == u['ctx'] and original.confirmation_record.status.value == 'CONFIRMED'
            if matched:
                assert j.store.get(u['op'])['state'] == ('SESSION_OPEN' if label == 'B' else 'CREATED')
            rows[label] = out | {'operation_id': u['op'], 'snapshot_sha256': u['ref'],
                                  'stop_event_ref': stop_fact['event_id'] if stop_fact else None}
        after = j.originals()
        assert all(after[op] == row for op, row in before.items()) and len(after) == 4
    assert not Path(tmp).exists()
    return {'units': rows, 'receipt': fact, 'originals': 'PASS', 'cleanup': 'PASS'}


def ingress():
    with tempfile.TemporaryDirectory() as tmp:
        j = setup(tmp)
        before = j.originals()
        invalid = {
            'subject': {'subject_ref': 'wrong-synthetic-subject'},
            'mandate': {'mandate_id': j.units['D']['ctx'].mandate.mandate_id},
            'version': {'authority_version': 'wrong-version'},
            'sha': {'expected_sha256': j.units['D']['ref']},
            'empty_event': {'event_id': ''},
            'naive_time': {'received_at': NOW.replace(tzinfo=None)},
            'early_time': {'received_at': NOW - timedelta(seconds=1)},
        }
        results = {label: rejects(lambda: stop(j, **changes)) for label, changes in invalid.items()}
        assert lookup(j, 'A') is None and lookup(j, 'D') is None
        fact = stop(j)
        assert stop(j) == fact
        results['changed_event'] = rejects(lambda: stop(j, event_id='event-h90-other'))
        results['changed_time'] = rejects(lambda: stop(j, received_at=NOW + timedelta(seconds=1)))
        results['changed_anchor'] = rejects(lambda: stop(j, 'B'))
        results['cross_mandate_event'] = rejects(lambda: stop(j, 'D'))
        assert lookup(j, 'A') == lookup(j, 'B') == fact and lookup(j, 'D') is None
        assert before == j.originals()
    assert not Path(tmp).exists()
    return {'rejected': results, 'replay': 'SAME_RECEIPT', 'cleanup': 'PASS'}


def integrity():
    findings = {}
    for issue, sql in (
        ('unreadable', f'DROP TABLE {TABLE}'),
        ('mismatched_anchor_snapshot', f"UPDATE {TABLE} SET anchor_snapshot_sha256='{('0' * 64)}'"),
    ):
        with tempfile.TemporaryDirectory() as tmp:
            j = setup(tmp)
            stop(j)
            before = j.originals()
            with closing(sqlite3.connect(j.path)) as con:
                con.execute(sql)
                con.commit()
            for label in ('A', 'B'):
                counts = j.counts(label)
                try:
                    result = j.create(label) if label == 'A' else j.pay(label)
                except (StripeCheckoutError, sqlite3.Error):
                    pass
                else:
                    assert not isinstance(result, CheckoutReceipt)
                    assert result.final_decision.value != 'ALLOW' and result.callback_count == 0
                assert j.counts(label) == counts
            assert j.originals() == before
        assert not Path(tmp).exists()
        findings[issue] = 'BOTH_ENTRY_POINTS_DENIED'
    return findings


def h90_withdrawal_store_table(database):
    """H90 schema-aware locator; retain H88's event uniqueness check."""
    name = "confirmation_withdrawals"
    with closing(sqlite3.connect(database)) as con:
        current = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        expected = {"operations", "webhook_receipts", "delivery_attempts",
                    "recoveries", "authority_contexts", "mandate_shutdowns"}
        assert current - expected == {name}, current
        indexed = list(con.execute(
            "SELECT name FROM pragma_index_list(?) WHERE [unique]=1", (name,)
        ))
        assert any([r[0] for r in con.execute(
            "SELECT name FROM pragma_index_info(?) ORDER BY seqno", (index,)
        )] == ["event_id"] for (index,) in indexed), "event ID has no unique constraint"
    return name


def compatibility():
    # Owner-authorized H90-only adaptation of table discovery, not behavior.
    # All H88 guard assertions run unchanged; restore the original locator.
    from unittest.mock import patch
    with patch.object(h89.h88, 'withdrawal_store_table', h90_withdrawal_store_table):
        results = {'h88': h89.guards()}
    with tempfile.TemporaryDirectory() as tmp:
        j = setup(tmp)
        before = j.originals()
        with closing(sqlite3.connect(j.path)) as con:
            con.execute(f'DROP TABLE {TABLE}')
            con.commit()
        j.store = h89.StripeLabLedger(j.path)
        assert j.originals() == before and lookup(j, 'A') is None and lookup(j, 'B') is None
        results['legacy_create'] = action(j, 'A', 'ALLOW', [1, 0, 0])
        results['legacy_pay'] = action(j, 'B', 'ALLOW', [0, 1, 1])
    assert not Path(tmp).exists()
    with tempfile.TemporaryDirectory() as tmp:
        j = setup(tmp)
        u = j.units['B']
        j.store.mark_unknown(u['op'])
        session = dict(u['client'].session, status='complete', payment_status='paid',
                       payment_intent='pi_test_h90')
        intent = dict(id='pi_test_h90', livemode=False, status='succeeded',
                      latest_charge='ch_test_h90', amount=100, currency='usd')
        charge = dict(id='ch_test_h90', livemode=False, status='succeeded', paid=True,
                      captured=True, amount=100, currency='usd', payment_intent='pi_test_h90')
        j.store.observe(u['op'], session, intent, charge)
        payment = replace(u['ctx'].execution, status=PaymentStatus.UNKNOWN, provider_ref=session['id'])
        evidence = PaymentStatusObservation(payment.payment_id, payment.order_id,
                    PaymentStatus.SUCCEEDED, NOW + timedelta(seconds=3), 'stripe_api',
                    provider_ref=session['id'])
        before = j.counts('B')
        stop(j)
        j.store = h89.StripeLabLedger(j.path)
        out = j.store.recover_original(u['op'], payment, evidence)
        assert out.recovery_status.value == 'RECOVERED' and not out.retry_allowed
        assert j.counts('B') == before
        results['observed_paid_recovery'] = 'RECOVERED_NO_RETRY_NO_NEW_EFFECT'
    assert not Path(tmp).exists()
    results['cleanup'] = 'PASS'
    return results


def main():
    assert not sys.flags.optimize and os.name == 'nt' and sys.version_info[:2] == (3, 12)
    command, = sys.argv[1:]
    if command == 'prepare':
        result = h89.preflight()
        result['baseline'] = baseline()
    elif command == 'baseline':
        preserve(pre=True)
        result = baseline()
    else:
        preserve()
        commands = {'preserve': preserve, 'ingress': ingress,
                    'propagation': lambda: [propagation(False), propagation(True)],
                    'integrity': integrity, 'compatibility': compatibility, 'regressions': h89.regressions}
        result = commands[command]()
        preserve()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
