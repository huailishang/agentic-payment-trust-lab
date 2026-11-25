"""Frozen checks for H92's independently observed terminal-evidence defect."""
from contextlib import closing
from importlib import util
from pathlib import Path
from unittest.mock import patch
import json
import sqlite3
import tempfile

TASK = Path(__file__).resolve().parent
spec = util.spec_from_file_location('h93_original', TASK / 'CHECK.py')
c = util.module_from_spec(spec)
spec.loader.exec_module(c)


def outcomes():
    findings = []
    for case in ('missing', 'allow_zero', 'invalid_decision', 'effect_then_store_failure'):
        with tempfile.TemporaryDirectory(prefix='h93-evidence-') as tmp:
            j = c.h90.setup(tmp)
            u = j.units['A']
            if case == 'effect_then_store_failure':
                native = u['client'].create_session

                def lost(*args, **kwargs):
                    native(*args, **kwargs)
                    raise RuntimeError('synthetic_response_lost_after_effect')

                def unavailable(*args, **kwargs):
                    raise RuntimeError('synthetic_outcome_store_unavailable')

                with patch.object(u['client'], 'create_session', lost), patch.object(j.store, 'finish_stored_action', unavailable):
                    try:
                        j.create('A')
                    except RuntimeError as error:
                        assert str(error) == 'synthetic_response_lost_after_effect'
                    else:
                        raise AssertionError('lost return hidden')
                ref, = c.view(j)['unresolved_admission_refs']
                assert j.counts('A') == [1, 0, 0]
            else:
                ref = j.store.begin_stored_action(u['op'], expected_sha256=u['ref'], action='CREATE_SESSION')['admission_ref']
            c.h90.stop(j, event_id='event-h93-' + case)
            before = c.view(j)
            gate = {'missing': None, 'effect_then_store_failure': None,
                    'allow_zero': {'decision': 'ALLOW', 'callback_count': 0, 'reason': []},
                    'invalid_decision': {'decision': 'INVENTED', 'callback_count': 0, 'reason': []}}[case]
            try:
                j.store.finish_stored_action(ref, outcome='NO_EFFECT', gate_record=gate)
            except c.h90.StripeCheckoutError:
                pass
            else:
                raise AssertionError('unproven NO_EFFECT accepted: ' + case)
            after = c.view(j)
            assert before == after and after['state'] == 'STOP_ACCEPTED_PENDING'
            counts = j.counts('A')
            j.store = c.Ledger(j.path)
            assert j.create('A').final_decision.value == 'DENY'
            assert j.counts('A') == counts
            findings.append({'case': case, 'invalid_write': 'REJECTED', 'state': after['state'], 'effects': counts})
        assert not Path(tmp).exists()
    # A genuine existing-gate denial is the positive NO_EFFECT control.
    with tempfile.TemporaryDirectory(prefix='h93-gate-') as tmp:
        j = c.h90.setup(tmp)
        u = j.units['A']
        denied = u['adapter'].create_stored_session(j.store, operation_id=u['op'],
            expected_authority_sha256=u['ref'], success_url='http://127.0.0.1:8768/success',
            cancel_url='http://127.0.0.1:8768/cancel', now=c.h90.NOW + c.h90.timedelta(days=1))
        assert denied.callback_count == 0 and denied.final_decision.value != 'ALLOW'
        current = c.view(j)
        attempt, = [a for a in current['attempts'] if a['operation_id'] == u['op']]
        assert attempt['outcome'] == 'NO_EFFECT' and j.counts('A') == [0, 0, 0]
        event, = [e for e in current['events'] if e['kind'] == 'OUTCOME' and e['operation_id'] == u['op']]
        gate = event['details']['gate_record']
        assert gate['decision'] == denied.final_decision.value and gate['callback_count'] == 0
        c.h90.stop(j, event_id='event-h93-genuine-noeffect')
        assert c.view(j)['state'] == 'STOP_ACCEPTED_LOCAL_QUIESCENT'
    assert not Path(tmp).exists()
    return {'negative_controls': findings, 'genuine_gate_NO_EFFECT': 'PASS', 'cleanup': 'PASS'}


if __name__ == '__main__':
    c.preserve()
    print(json.dumps(outcomes(), ensure_ascii=False, indent=2))
    c.preserve()
