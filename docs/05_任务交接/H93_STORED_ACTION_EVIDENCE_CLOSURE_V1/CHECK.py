"""Frozen acceptance of native stored-action control across the H91 family."""
from contextlib import closing
from importlib import util
import hashlib
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
PARENT = TASK.with_name('H91_SHUTDOWN_INFLIGHT_ORDERING_MEASUREMENT_V1')
spec = util.spec_from_file_location('h92_scene', PARENT / 'SCENARIO_CHECK.py')
scene = util.module_from_spec(spec)
spec.loader.exec_module(scene)
h90 = scene.h90
Ledger = h90.h89.StripeLabLedger
Adapter = scene.adapter_module.StripeCheckoutAdapter
TABLE = 'stored_action_control_events'
METHODS = ('begin_stored_action', 'finish_stored_action', 'get_shutdown_control_view')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(pre=False):
    path = TASK / 'INPUTS.json'
    lock = json.loads(path.read_text(encoding='utf-8'))
    assert 'frozen_manifest_sha256: ' + sha(path) in (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == lock['head']
    assert h90.h89.source_set() == lock['source_files']
    for name, digest in lock['files'].items():
        assert sha(ROOT / name) == digest, name
    if pre:
        for name, digest in lock['mutable'].items():
            assert sha(ROOT / name) == digest, name
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'scripts'], cwd=ROOT, text=True).splitlines()
    assert set(changed).issubset(lock['mutable']), changed
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--', 'src', 'tests', 'scripts'], cwd=ROOT, text=True).strip()
    return {'protected': len(lock['files']), 'result': 'PASS', 'pre_implementation': pre}


def view(j, label='A'):
    u = j.units[label]
    result = j.store.get_shutdown_control_view(u['op'], expected_sha256=u['ref'])
    assert result['source'] == 'NATIVE_STORED_ACTION_CONTROL'
    assert result['operation_id'] == u['op']
    assert result['state'] in ('ACTIVE', 'STOP_ACCEPTED_PENDING', 'STOP_ACCEPTED_LOCAL_QUIESCENT')
    assert result['new_actions_blocked'] is bool(result['stop_event_ref'])
    sequences = [e['sequence'] for e in result['events']]
    assert sequences == sorted(set(sequences)) and all(type(s) is int and s > 0 for s in sequences)
    assert result['order_status'] in ('NATIVE', 'LEGACY_UNRECORDED')
    if result['stop_sequence'] is not None:
        assert result['order_status'] == 'NATIVE'
        assert all(a['admission_sequence'] < result['stop_sequence'] for a in result['attempts'])
    elif result['stop_event_ref']:
        assert result['order_status'] == 'LEGACY_UNRECORDED'
    keys = [(a['operation_id'], a['action']) for a in result['attempts']]
    assert len(keys) == len(set(keys))
    pending = bool(result['unresolved_admission_refs'] or result['unresolved_operation_ids'])
    if result['stop_event_ref']:
        assert result['state'] == ('STOP_ACCEPTED_PENDING' if pending else 'STOP_ACCEPTED_LOCAL_QUIESCENT')
    return result


def protocol():
    assert all(callable(getattr(Ledger, name, None)) for name in METHODS)
    with tempfile.TemporaryDirectory(prefix='h92-protocol-') as tmp:
        j = h90.setup(tmp)
        before = j.originals()
        u = j.units['A']
        admitted = j.store.begin_stored_action(u['op'], expected_sha256=u['ref'], action='CREATE_SESSION')
        assert admitted['decision'] == 'ALLOW' and admitted['admission_ref']
        assert admitted['sequence'] > 0
        pending = view(j)
        assert admitted['admission_ref'] in pending['unresolved_admission_refs']
        receipt = h90.stop(j, event_id='event-h92-stop')
        assert h90.stop(j, event_id='event-h92-stop') == receipt
        stopped = view(j)
        assert stopped['stop_event_ref'] == receipt['event_id']
        assert admitted['sequence'] < stopped['stop_sequence']
        assert stopped['state'] == 'STOP_ACCEPTED_PENDING'
        denied = j.store.begin_stored_action(u['op'], expected_sha256=u['ref'], action='CREATE_SESSION')
        assert denied['decision'] == 'DENY' and denied['admission_ref'] is None
        assert denied['stop_event_ref'] == receipt['event_id']
        finished = j.store.finish_stored_action(admitted['admission_ref'], outcome='NO_EFFECT', result_ref=None, gate_record={'decision': 'DENY', 'callback_count': 0, 'reason': ['controlled_pre_provider_denial']})
        assert j.store.finish_stored_action(admitted['admission_ref'], outcome='NO_EFFECT', result_ref=None, gate_record={'decision': 'DENY', 'callback_count': 0, 'reason': ['controlled_pre_provider_denial']}) == finished
        assert view(j)['state'] == 'STOP_ACCEPTED_LOCAL_QUIESCENT'
        assert view(j, 'D')['state'] == 'ACTIVE'
        for call in (
            lambda: j.store.begin_stored_action(u['op'], expected_sha256='0' * 64, action='CREATE_SESSION'),
            lambda: j.store.begin_stored_action(u['op'], expected_sha256=u['ref'], action='UNRECOGNIZED'),
            lambda: j.store.finish_stored_action('foreign-admission', outcome='COMPLETED', result_ref=None),
            lambda: j.store.finish_stored_action(admitted['admission_ref'], outcome='UNKNOWN', result_ref=None),
        ):
            try:
                call()
            except (h90.StripeCheckoutError, ValueError):
                continue
            raise AssertionError('invalid/conflicting control write accepted')
        assert j.originals() == before
    assert not Path(tmp).exists()
    return {'protocol': 'PASS', 'ordering': 'ADMITTED_BEFORE_STOP', 'negative_controls': 4, 'cleanup': 'PASS'}


def matrix():
    captures = []
    original_create = Adapter.create_stored_session
    original_pay = Adapter.authorize_stored_browser_payment

    def capture(function, action):
        def wrapped(self, store, **kwargs):
            result = function(self, store, **kwargs)
            current = store.get_shutdown_control_view(kwargs['operation_id'], expected_sha256=kwargs['expected_authority_sha256'])
            gate = result.gate if isinstance(result, h90.CheckoutReceipt) else result
            captures.append({'action': action, 'operation_id': kwargs['operation_id'],
                             'gate': scene.clean(scene.asdict(gate)), 'view': current})
            return result
        return wrapped

    with patch.object(Adapter, 'create_stored_session', capture(original_create, 'CREATE_SESSION')), \
         patch.object(Adapter, 'authorize_stored_browser_payment', capture(original_pay, 'BROWSER_PAYMENT')):
        ordering = scene.ordering_matrix()
        recovery = scene.recovery_matrix()
    rows = ordering['rows']
    assert len(rows) == 8 and len(recovery['rows']) == 5
    for index in (4, 5):
        assert rows[index]['first']['decision'] == 'DENY'
        assert rows[index]['first']['effect_delta'] == [0, 0, 0]
    assert rows[6]['first']['decision'] == 'ALLOW'
    assert rows[6]['first']['effect_delta'] == [0, 1, 1]
    for captured in captures:
        current = captured['view']
        assert current['source'] == 'NATIVE_STORED_ACTION_CONTROL'
        assert current['operation_id'] == captured['operation_id']
        if current['stop_event_ref']:
            assert current['new_actions_blocked'] is True
            assert any(e['kind'] == 'DENIED' and e['operation_id'] == captured['operation_id']
                       and e['stop_event_ref'] == current['stop_event_ref'] for e in current['events']) or any(
                           a['operation_id'] == captured['operation_id'] and a['action'] == captured['action']
                           and a['admission_sequence'] < current['stop_sequence']
                           for a in current['attempts'])
        if captured['gate']['callback_count'] == 1:
            assert any(a['operation_id'] == captured['operation_id'] and a['action'] == captured['action']
                       and a['outcome'] == 'COMPLETED' for a in current['attempts'])
    assert any(c['view']['state'] == 'STOP_ACCEPTED_PENDING' for c in captures)
    assert any(c['view']['stop_event_ref'] and any(e['kind'] == 'RECOVERY_OBSERVED' for e in c['view']['events']) for c in captures)
    return {'ordering_rows': rows, 'recovery_rows': recovery['rows'], 'native_captures': captures,
            'O5_O6': 'DENY_NO_EFFECT', 'real_cancellation_claim': False}


def uncertain_attempts():
    findings = []
    for label, action in (('A', 'CREATE_SESSION'), ('B', 'BROWSER_PAYMENT')):
        with tempfile.TemporaryDirectory(prefix='h92-unknown-') as tmp:
            j = h90.setup(tmp)
            u = j.units[label]
            original = j.originals()
            if label == 'A':
                native = u['client'].create_session

                def lost(*args, **kwargs):
                    native(*args, **kwargs)
                    raise RuntimeError('synthetic_response_lost_after_effect')

                with patch.object(u['client'], 'create_session', lost):
                    try:
                        j.create(label)
                    except RuntimeError as error:
                        assert str(error) == 'synthetic_response_lost_after_effect'
                    else:
                        raise AssertionError('post-effect failure hidden')
            else:
                def lost(url):
                    u['clicked'].append(url)
                    raise RuntimeError('synthetic_response_lost_after_effect')
                try:
                    u['adapter'].authorize_stored_browser_payment(j.store, operation_id=u['op'],
                        expected_authority_sha256=u['ref'], now=h90.NOW + h90.timedelta(seconds=2), browser_payment=lost)
                except RuntimeError as error:
                    assert str(error) == 'synthetic_response_lost_after_effect'
                else:
                    raise AssertionError('post-effect failure hidden')
            counts = j.counts(label)
            j.store = Ledger(j.path)
            result = j.create(label) if label == 'A' else j.pay(label)
            assert not isinstance(result, h90.CheckoutReceipt)
            assert result.final_decision.value == 'INDETERMINATE' and result.callback_count == 0
            assert j.counts(label) == counts
            receipt = h90.stop(j, event_id='event-h92-unknown')
            current = view(j, label)
            assert current['state'] == 'STOP_ACCEPTED_PENDING' and current['stop_event_ref'] == receipt['event_id']
            result = j.create(label) if label == 'A' else j.pay(label)
            assert result.final_decision.value == 'DENY' and result.callback_count == 0
            assert j.counts(label) == counts and j.originals() == original
            findings.append({'operation_id': u['op'], 'action': action, 'view': current, 'replay_effect_delta': [0, 0, 0]})
        assert not Path(tmp).exists()
    with tempfile.TemporaryDirectory(prefix='h92-admitted-') as tmp:
        j = h90.setup(tmp)
        u = j.units['A']
        fact = j.store.begin_stored_action(u['op'], expected_sha256=u['ref'], action='CREATE_SESSION')
        j.store = Ledger(j.path)
        counts = j.counts('A')
        result = j.create('A')
        assert result.final_decision.value == 'INDETERMINATE' and result.callback_count == 0
        assert j.counts('A') == counts and fact['admission_ref'] in view(j)['unresolved_admission_refs']
    assert not Path(tmp).exists()
    return {'post_effect_failures': findings, 'admission_only_restart': 'NO_REPLAY', 'cleanup': 'PASS'}


def locator(database):
    with closing(sqlite3.connect(database)) as con:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert tables == {'operations', 'authority_contexts', 'confirmation_withdrawals', 'mandate_shutdowns',
                          'webhook_receipts', 'delivery_attempts', 'recoveries', TABLE}
        indexes = list(con.execute("SELECT name FROM pragma_index_list('confirmation_withdrawals') WHERE [unique]=1"))
        assert any([r[0] for r in con.execute('SELECT name FROM pragma_index_info(?) ORDER BY seqno', (name,))] == ['event_id']
                   for (name,) in indexes)
    return 'confirmation_withdrawals'


def guards():
    with patch.object(h90, 'h90_withdrawal_store_table', locator):
        inherited = scene.h90_guard()
    with tempfile.TemporaryDirectory(prefix='h92-unreadable-') as tmp:
        j = h90.setup(tmp)
        h90.stop(j)
        with closing(sqlite3.connect(j.path)) as con:
            con.execute('DROP TABLE ' + TABLE)
            con.commit()
        for label in ('A', 'B'):
            counts = j.counts(label)
            try:
                result = j.create(label) if label == 'A' else j.pay(label)
            except (h90.StripeCheckoutError, sqlite3.Error):
                pass
            else:
                assert not isinstance(result, h90.CheckoutReceipt)
                assert result.final_decision.value != 'ALLOW' and result.callback_count == 0
            assert j.counts(label) == counts
    assert not Path(tmp).exists()
    with tempfile.TemporaryDirectory(prefix='h92-corrupt-') as tmp:
        j = h90.setup(tmp)
        with closing(sqlite3.connect(j.path)) as con:
            con.execute('UPDATE ' + TABLE + ' SET fact_sha256=?', ('0' * 64,))
            con.commit()
        try:
            view(j)
        except (h90.StripeCheckoutError, ValueError, sqlite3.Error):
            pass
        else:
            raise AssertionError('corrupt journal accepted as trusted view')
        for label in ('A', 'B'):
            counts = j.counts(label)
            try:
                result = j.create(label) if label == 'A' else j.pay(label)
            except (h90.StripeCheckoutError, ValueError, sqlite3.Error):
                pass
            else:
                assert not isinstance(result, h90.CheckoutReceipt)
                assert result.final_decision.value != 'ALLOW' and result.callback_count == 0
            assert j.counts(label) == counts
    assert not Path(tmp).exists()
    # Construct the trusted predecessor schema, not an anti-rollback test.
    with tempfile.TemporaryDirectory(prefix='h92-legacy-') as tmp:
        j = h90.setup(tmp)
        receipt = h90.stop(j, event_id='event-h92-legacy')
        with closing(sqlite3.connect(j.path)) as con:
            con.execute('DROP TABLE ' + TABLE)
            con.commit()
        j.store = Ledger(j.path)
        current = view(j)
        assert current['stop_event_ref'] == receipt['event_id']
        assert current['order_status'] == 'LEGACY_UNRECORDED' and current['stop_sequence'] is None
        counts = j.counts('A')
        assert j.create('A').final_decision.value == 'DENY' and j.counts('A') == counts
    assert not Path(tmp).exists()
    return {'inherited': inherited, 'unreadable_journal': 'NO_EFFECT', 'legacy_stop': 'BLOCKED_NO_FABRICATED_HISTORY'}


def baseline():
    missing = [name for name in METHODS if not callable(getattr(Ledger, name, None))]
    assert missing == list(METHODS)
    return {'native_interface_missing': missing, 'native_control_capability': 'NOT_IMPLEMENTED',
            'basis': 'H91 accepted 13-row raw matrix; no new product run', 'product_actions': 0}


def main():
    assert os.name == 'nt' and sys.version_info[:2] == (3, 12) and not sys.flags.optimize
    command, = sys.argv[1:]
    if command == 'baseline':
        result = baseline()
    elif command == 'preserve_pre':
        result = preserve(pre=True)
    else:
        preserve()
        result = {'protocol': protocol, 'matrix': matrix, 'uncertain': uncertain_attempts,
                  'guards': guards, 'regressions': h90.h89.regressions, 'preserve': preserve}[command]()
        preserve()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
