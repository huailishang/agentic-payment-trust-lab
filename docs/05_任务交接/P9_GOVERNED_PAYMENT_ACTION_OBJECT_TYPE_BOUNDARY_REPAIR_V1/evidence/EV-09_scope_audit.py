from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]

def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

current_hashes = {
    'src/agentic_payment_experiment/trusted_execution/governed_action.py': '115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e',
    'tests/trusted_execution/test_governed_action.py': '67bfd682ae9fc5e1bf31b4431004f486577067cbf3d521c03691e7ca6f159cb9',
    'tests/test_webshop_runtime_gate.py': '6f35dc764e4596921fd11ad5d1fe9d636bee53a53dec7c0b4568d03c1db762ac',
    'samples/external/webshop/governed_payment_action_matrix_v1.json': 'fe79911c986166f260e04650370a487e808c182f1b9e9e84804bb5a390c16b40',
    'scripts/validation/webshop/run_governed_payment_action_matrix.py': 'a30ecba6a5e4ed2f2562efb158db1515446db673ee6b4399e388a4c36ca10e2b',
}
for path, expected in current_hashes.items():
    actual = sha(path)
    assert actual == expected, (path, expected, actual)
    print(f'changed_hash {actual} {path}')

protected_hashes = {
    'src/agentic_payment_experiment/webshop_runtime_gate.py': '53cf905867905ae73f2886c4612a6d19cc839420677afe4f0eb4f655c87c1dd2',
    'src/agentic_payment_experiment/trusted_execution/__init__.py': '62ebd2a8a9d06d57f3948461e306ad4603b5750104de052e15a3deed35d29551',
    'src/agentic_payment_experiment/__init__.py': '3d7c3cc93654d5353eaa6b7f9c371f890f79712cd1e158c2e430aeab628fadbe',
    'src/agentic_payment_experiment/models.py': 'd38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65',
    'src/agentic_payment_experiment/validator.py': '9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb',
    'src/agentic_payment_experiment/order_validation.py': '504fa1dfc6d2c18f685599ff937e34de759c949bcd999ae1eb4df7cf40554d25',
    'src/agentic_payment_experiment/payment_execution.py': '25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71',
    'src/agentic_payment_experiment/trusted_execution/context_policy.py': 'be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56',
}
for path, expected in protected_hashes.items():
    actual = sha(path)
    assert actual == expected, (path, expected, actual)
    print(f'protected_unchanged {actual} {path}')

source = (ROOT / 'src/agentic_payment_experiment/trusted_execution/governed_action.py').read_text(encoding='utf-8')
none_pos = source.index('if action is None:')
exact_pos = source.index('if type(action) is not GovernedPaymentAction:')
checked_pos = source.index('checked = _checked_values(action)')
attribute_pos = source.index('_require_text(action.action_id')
assert none_pos < exact_pos < checked_pos < attribute_pos
assert '("governed_action_invalid_type",)' in source
assert 'isinstance(action, GovernedPaymentAction)' not in source
print('strict_type_before_attribute_access=PASS')
print('strict_boundary=type(action) is GovernedPaymentAction')

parent_path = ROOT / 'docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-01.stdout.log'
current_path = ROOT / 'docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_OBJECT_TYPE_BOUNDARY_REPAIR_V1/evidence/EV-05.stdout.log'
parent = json.loads(parent_path.read_text(encoding='utf-8'))
current = json.loads(current_path.read_text(encoding='utf-8'))
assert parent['summary'] == {'failed': 0, 'matched': 16, 'total': 16}
assert current['summary'] == {'failed': 0, 'matched': 18, 'total': 18}
current_by_id = {item['case_id']: item for item in current['cases']}
for old in parent['cases']:
    assert current_by_id[old['case_id']] == old, old['case_id']
assert current['primitive_serialization_example'] == parent['primitive_serialization_example']
new_ids = {'mutable_lookalike_action_object', 'serialized_dict_action_object'}
assert set(current_by_id) - {item['case_id'] for item in parent['cases']} == new_ids
for case_id in sorted(new_ids):
    item = current_by_id[case_id]
    assert item['actual_verification_status'] == 'INVALID'
    assert item['actual_gate_decision'] == 'DENY'
    assert item['callback_count'] == 0
    assert item['reason_codes'] == ['governed_action_invalid_type']
print('parent_16_cases_exactly_unchanged=PASS')
print('new_2_cases_invalid_deny_zero_callback=PASS')
print('authorizations network=false api=false dependency_install=false create_environment=false webshop_runtime=false buy_now=false payment_side_effect=false commit=false push=false history_rewrite=false')
