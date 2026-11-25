"""Frozen offline measurement of mandate-level control, not a revocation service."""
import ast
from contextlib import closing
from dataclasses import fields, replace
from datetime import timedelta
import hashlib
from importlib import util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H88_STORED_CONFIRMATION_WITHDRAWAL_V1')
spec = util.spec_from_file_location('h89_parent_h88', PARENT / 'CHECK.py')
h88 = util.module_from_spec(spec)
spec.loader.exec_module(h88)
h87 = h88.prepare_imports()

from agentic_payment_experiment.adapters.stripe_checkout import CheckoutReceipt, StripeCheckoutAdapter
from agentic_payment_experiment.models import IntentMandate
from agentic_payment_experiment.payment_execution import PAYMENT_CONTEXT_ACTION, PAYMENT_REQUIRED_SOURCE_PATHS
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.trusted_execution import SourceType, evaluate_context_policy
from agentic_payment_experiment.trusted_execution.confirmation import create_confirmation_record
from tests.test_stripe_checkout_adapter import NOW, SHA, FakeStripe, valid_context
from tests.test_stripe_authority_context import _Fixture

UNITS = (('A', 'N01', 1), ('B', 'C01', 2), ('C', 'R01', 3), ('D', 'D01', 1))
BRANCHES = ('none', 'withdraw_A', 'withdraw_B')
RUN = 'run-h89-synthetic'
SUCCESS = 'http://127.0.0.1:8768/success'
CANCEL = 'http://127.0.0.1:8768/cancel'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def source_set():
    return sorted(p.relative_to(ROOT).as_posix()
                  for directory in ('src', 'tests', 'scripts')
                  for p in (ROOT / directory).rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')


def preserve():
    lock = read(TASK / 'INPUTS.json')
    router = (ROOT / 'CURRENT.md').read_text(encoding='utf-8')
    assert 'frozen_manifest_sha256: ' + sha(TASK / 'INPUTS.json') in router
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == lock['head']
    assert source_set() == lock['source_files'], 'source set drift'
    for name, digest in lock['files'].items():
        assert sha(ROOT / name) == digest, name
    return {'protected_files': len(lock['files']), 'preservation': 'PASS'}


def inventory():
    ledger_path = ROOT / 'src/agentic_payment_experiment/stripe_checkout_lab.py'
    tree = ast.parse(ledger_path.read_text(encoding='utf-8'))
    ledger = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'StripeLabLedger')
    public = {n.name: {'line': n.lineno, 'signature': ast.unparse(n.args)} for n in ledger.body
              if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')}
    candidates = [name for name in public if 'mandate' in name.lower() and any(
        word in name.lower() for word in ('revoke', 'withdraw', 'shutdown', 'stop'))]
    result = {'public_ledger_methods': public,
              'mandate_fields': [f.name for f in fields(IntentMandate)],
              'mandate_receiver_candidates': candidates,
              'surface': ['IntentMandate', 'StripeLabLedger',
                          'StripeCheckoutAdapter.create_stored_session',
                          'StripeCheckoutAdapter.authorize_stored_browser_payment'],
              'scope_caveat': 'Only the frozen native stored consumer; no whole-repository absence claim.'}
    links = {}
    for relative, needles in {
        'src/agentic_payment_experiment/models.py': ('class IntentMandate',),
        'src/agentic_payment_experiment/stripe_checkout_lab.py': (
            'confirmation_withdrawals', 'def record_confirmation_withdrawal', 'def get_confirmation_withdrawal'),
        'src/agentic_payment_experiment/adapters/stripe_checkout.py': (
            'def _effective_stored_authority', 'def create_stored_session',
            'def authorize_stored_browser_payment'),
    }.items():
        lines = (ROOT / relative).read_text(encoding='utf-8').splitlines()
        links[relative] = [{'line': i, 'text': line.strip()}
                           for i, line in enumerate(lines, 1) if any(s in line for s in needles)]
    result['source_links'] = links
    if candidates:
        result['receiver_status'] = 'UNBOUND_EXISTING_CANDIDATE_RETURN_TO_EVALUATOR'
    else:
        result['receiver_status'] = 'NOT_REPRESENTABLE_IN_FROZEN_NATIVE_SURFACE'
    return result


def context(label, sequence):
    base = valid_context()
    mandate = replace(base.mandate, mandate_id=('mandate-h89-other' if label == 'D'
                                               else 'mandate-h89-shared'), max_count=3)
    order = replace(base.order, order_id='order-h89-' + label, mandate_ref=mandate.mandate_id)
    request = replace(base.request, request_id='request-h89-' + label,
                      authority_ref=mandate.mandate_id, order_ref=order.order_id,
                      sequence_count=sequence)
    payment = replace(base.execution, payment_id='payment-h89-' + label,
                      request_id=request.request_id, order_id=order.order_id,
                      authority_ref=mandate.mandate_id, transaction_object_ref=request.request_id)
    confirmation = create_confirmation_record(
        confirmation_id='confirmation-h89-' + label, authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version, order=order,
        confirmed_at=base.confirmation_record.confirmed_at,
        expires_at=base.confirmation_record.expires_at)
    fact = evaluate_context_policy({
        'mandate': {'mandate_id': mandate.mandate_id}, 'final_order': {'order_id': order.order_id},
        'request': {'request_id': request.request_id, 'agent_id': request.agent_id,
                    'amount': request.amount, 'payee': request.payee, 'currency': request.currency}},
        trusted_sources={path: (SourceType.PROTOCOL_VERIFIED if path == 'request.request_id'
                                else SourceType.USER_CONFIRMED)
                         for path in PAYMENT_REQUIRED_SOURCE_PATHS},
        required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
        current_action=PAYMENT_CONTEXT_ACTION).fact
    return replace(base, mandate=mandate, order=order, request=request, execution=payment,
                   confirmation_record=confirmation, context_policy_fact=fact)


class Journey:
    def __init__(self, directory):
        self.path = Path(directory) / 'synthetic.sqlite3'
        self.store = StripeLabLedger(self.path)
        self.units = {}
        for label, case, sequence in UNITS:
            ctx = context(label, sequence)
            client = FakeStripe()
            client.session |= {'id': 'cs_test_h89_' + label,
                               'client_reference_id': ctx.order.order_id,
                               'metadata': {'h68_resource_sha256': SHA, 'h68_run_id': RUN,
                                            'h68_operation_id': 'operation-h89-' + label}}
            self.units[label] = {'ctx': ctx, 'client': client,
                                 'adapter': StripeCheckoutAdapter(client), 'case': case,
                                 'op': 'operation-h89-' + label, 'clicked': []}

    def register(self, label, at=NOW):
        unit = self.units[label]
        ctx = unit['ctx']
        self.store.register(operation_id=unit['op'], run_id=RUN, case_id=unit['case'],
                            order_id=ctx.order.order_id, request_id=ctx.request.request_id,
                            payment_id=ctx.execution.payment_id, resource_sha256=SHA)
        unit['ref'] = self.store.record_authority(unit['op'], ctx, resource_sha256=SHA, recorded_at=at)

    def create(self, label):
        u = self.units[label]
        return u['adapter'].create_stored_session(self.store, operation_id=u['op'],
            expected_authority_sha256=u['ref'], success_url=SUCCESS, cancel_url=CANCEL,
            now=NOW + timedelta(seconds=2))

    def pay(self, label):
        u = self.units[label]
        return u['adapter'].authorize_stored_browser_payment(self.store, operation_id=u['op'],
            expected_authority_sha256=u['ref'], now=NOW + timedelta(seconds=2),
            browser_payment=u['clicked'].append)

    def counts(self, label):
        u = self.units[label]
        return [len(u['client'].created), len(u['client'].queries), len(u['clicked'])]

    def originals(self):
        with closing(sqlite3.connect(self.path)) as con:
            return dict((op, [digest, payload]) for op, digest, payload in con.execute(
                'SELECT operation_id,snapshot_sha256,payload_json FROM authority_contexts ORDER BY operation_id'))


def preflight():
    assert not sys.flags.optimize and sys.version_info[:2] == (3, 12)
    assert os.name == 'nt', 'native Windows only'
    assert len(set(label for label, _, _ in UNITS)) == 4
    values = {label: context(label, sequence) for label, _, sequence in UNITS}
    key = lambda c: (c.mandate.user_id, c.mandate.mandate_id, c.mandate.authority_version)
    assert key(values['A']) == key(values['B']) == key(values['C']) != key(values['D'])
    assert len({c.order.order_id for c in values.values()}) == 4
    assert len({c.confirmation_record.confirmation_id for c in values.values()}) == 4
    with tempfile.TemporaryDirectory() as tmp:
        j = Journey(tmp)
        for label in ('A', 'B', 'D'):
            j.register(label)
        created = j.create('B')
        assert isinstance(created, CheckoutReceipt) and created.gate.final_decision.value == 'ALLOW'
        j.store.bind_session(j.units['B']['op'], j.units['B']['client'].session)
        assert j.store.get(j.units['A']['op'])['state'] == 'CREATED'
        assert j.store.get(j.units['B']['op'])['state'] == 'SESSION_OPEN'
        assert 'ref' not in j.units['C']
    assert not Path(tmp).exists()
    return {'fixture_qualification': 'PASS', 'units': 4, 'external_effects': 0,
            'formal_measurement': False, 'cleanup': 'PASS', 'python': sys.version.split()[0]}


def branch(mode):
    with tempfile.TemporaryDirectory() as tmp:
        j = Journey(tmp)
        for label in ('A', 'B', 'D'):
            j.register(label)
        created = j.create('B')
        assert isinstance(created, CheckoutReceipt) and created.gate.final_decision.value == 'ALLOW'
        j.store.bind_session(j.units['B']['op'], j.units['B']['client'].session)
        originals = j.originals()
        receipt = None
        target = None if mode == 'none' else mode[-1]
        if target:
            u = j.units[target]
            receipt = j.store.record_confirmation_withdrawal(u['op'], expected_sha256=u['ref'],
                confirmation_id=u['ctx'].confirmation_record.confirmation_id,
                subject_ref=u['ctx'].mandate.user_id, event_id='event-h89-' + target, received_at=NOW)
        j.store = StripeLabLedger(j.path)
        j.register('C', NOW + timedelta(seconds=1))
        result = {}
        for label, _, _ in UNITS:
            u = j.units[label]
            before = j.counts(label)
            out = j.pay(label) if label == 'B' else j.create(label)
            gate = out.gate if isinstance(out, CheckoutReceipt) else out
            delta = [b - a for a, b in zip(before, j.counts(label))]
            expected = ([0, 0, 0] if label == target else
                        ([0, 1, 1] if label == 'B' else [1, 0, 0]))
            assert delta == expected, (mode, label, delta)
            assert gate.final_decision.value == ('CONFIRMATION_REQUIRED' if label == target else 'ALLOW')
            assert gate.callback_count == (0 if label == target else 1)
            fact = j.store.get_confirmation_withdrawal(u['op'], expected_sha256=u['ref'])
            assert fact == (receipt if label == target else None)
            original = j.store.load_authority(u['op'], expected_sha256=u['ref'])
            assert original == u['ctx'] and original.confirmation_record.status.value == 'CONFIRMED'
            result[label] = {'operation_id': u['op'], 'mandate_id': original.mandate.mandate_id,
                'subject_ref': original.mandate.user_id, 'authority_version': original.mandate.authority_version,
                'confirmation_id': original.confirmation_record.confirmation_id,
                'snapshot_sha256': u['ref'], 'gate_decision': gate.final_decision.value,
                'callback_count': gate.callback_count, 'effect_delta': delta,
                'withdrawal_fact': fact,
                'registered_after_event_position': label == 'C',
                'single_event_present': target is not None}
        after = j.originals()
        assert all(after[op] == row for op, row in originals.items())
        assert len(after) == 4
        result = {'mode': mode, 'single_event_receipt': receipt, 'units': result,
                  'original_snapshots_unchanged': True,
                  'whole_mandate_event': {'status': 'NOT_SUBMITTED_NO_NATIVE_RECEIVER', 'accepted': False}}
    assert not Path(tmp).exists()
    result['temporary_cleanup'] = 'PASS'
    return result


def measurement():
    surface = inventory()
    assert not surface['mandate_receiver_candidates'], 'new candidate requires Evaluator to freeze invocation'
    observations = [branch(mode) for mode in BRANCHES]
    return {'inventory': surface, 'observations': observations,
            'conclusion': 'SINGLE_CONFIRMATION_SCOPE_MEASURED; WHOLE_MANDATE_RECEIVER_NOT_REPRESENTABLE',
            'capability_gain': 'NOT_APPLICABLE',
            'warning': 'No mandate revocation was accepted. ALLOW rows are not post-revocation mispayments.'}


def guards():
    output = {}
    for precreate in (True, False):
        f = _Fixture()
        f.setUp()
        try:
            f.ref = f.recorded()
            output['before_create' if precreate else 'before_pay'] = h88.run_withdrawn(f, precreate)
            assert h88.rejected_conflicts(f, output['before_create' if precreate else 'before_pay']['receipt']) == 2
        finally:
            f.doCleanups()
            assert not f.db.parent.exists()
    for precreate in (True, False):
        f = _Fixture()
        f.setUp()
        try:
            f.ref = f.recorded()
            h88.unreadable_state(f, precreate)
        finally:
            f.doCleanups()
            assert not f.db.parent.exists()
    output['unreadable_state'] = 'FAIL_CLOSED_BOTH_ENTRIES'
    return output


def regressions():
    total = 0
    for name, expected in h87.SUITES.items():
        suite = unittest.defaultTestLoader.loadTestsFromName(name)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        assert result.wasSuccessful() and not result.skipped and result.testsRun == expected, name
        total += result.testsRun
    assert total == 124
    return {'passed': total, 'skipped': 0}


def main():
    assert not sys.flags.optimize, 'assertions must remain enabled'
    command, = sys.argv[1:]
    if command == 'preflight':
        result = preflight()
    else:
        preserve()
        commands = {'qualification': preflight, 'preserve': preserve, 'inventory': inventory, 'measure': measurement,
                    'guards': guards, 'regressions': regressions}
        result = commands[command]()
        preserve()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
