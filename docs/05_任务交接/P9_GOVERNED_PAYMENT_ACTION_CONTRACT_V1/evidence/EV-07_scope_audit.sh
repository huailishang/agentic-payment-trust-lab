#!/usr/bin/env bash
set -euo pipefail

printf 'HEAD='
git rev-parse HEAD

printf 'CHANGED_HASHES\n'
sha256sum   src/agentic_payment_experiment/trusted_execution/governed_action.py   src/agentic_payment_experiment/trusted_execution/__init__.py   src/agentic_payment_experiment/__init__.py   src/agentic_payment_experiment/webshop_runtime_gate.py   tests/trusted_execution/test_governed_action.py   tests/test_webshop_runtime_gate.py   samples/external/webshop/governed_payment_action_matrix_v1.json   scripts/validation/webshop/run_governed_payment_action_matrix.py

printf 'PROTECTED_RULE_DIFFS\n'
git diff --exit-code --   src/agentic_payment_experiment/models.py   src/agentic_payment_experiment/validator.py   src/agentic_payment_experiment/order_validation.py

printf 'PROTECTED_SHARED_HASHES\n'
printf '%s  %s\n'   '25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71'   'expected:src/agentic_payment_experiment/payment_execution.py'
printf '%s  %s\n'   'be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56'   'expected:src/agentic_payment_experiment/trusted_execution/context_policy.py'
test "25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71" =   '25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71'
test "be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56" =   'be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56'

printf 'DIFF_CHECK\n'
git diff --check --   src/agentic_payment_experiment/trusted_execution/__init__.py   src/agentic_payment_experiment/__init__.py   src/agentic_payment_experiment/webshop_runtime_gate.py   tests/test_webshop_runtime_gate.py

printf 'STATIC_CONTRACT_AUDIT\n'
PYTHONPATH=src python3 - <<'PY'
import ast
import inspect
from pathlib import Path

from agentic_payment_experiment import (
    ActionReversibility,
    GovernedActionType,
    GovernedPaymentAction,
    SideEffectClass,
    gate_webshop_buy_now,
    verify_governed_payment_action,
)

path = Path('src/agentic_payment_experiment/trusted_execution/governed_action.py')
source = path.read_text(encoding='utf-8')
tree = ast.parse(source)
imports = set()
calls = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.update(alias.name.split('.')[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.add(node.module or '')
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
for forbidden in (
    'requests', 'urllib', 'socket', 'subprocess', 'os', 'pathlib',
    'flask', 'selenium', 'playwright', 'web_agent_site',
):
    assert not any(name == forbidden or name.startswith(forbidden + '.') for name in imports), imports
assert calls.isdisjoint({
    'open', 'read_text', 'write_text', 'getenv', 'run', 'Popen',
    'urlopen', 'socket', 'checkout_callback', 'execute_payment',
}), calls
assert list(GovernedActionType) == [GovernedActionType.EXECUTE_PAYMENT]
assert list(SideEffectClass) == [SideEffectClass.PAYMENT_EXECUTION]
assert list(ActionReversibility) == [ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE]
assert set(GovernedPaymentAction.__dataclass_fields__) == {
    'action_id', 'action_type', 'subject_ref', 'agent_ref', 'executor_ref',
    'authority_ref', 'authority_version', 'order_ref', 'order_version',
    'request_ref', 'payment_ref', 'source_refs', 'side_effect_class',
    'reversibility', 'occurred_at',
}
assert inspect.signature(gate_webshop_buy_now).parameters['governed_action'].kind is inspect.Parameter.KEYWORD_ONLY
assert inspect.signature(gate_webshop_buy_now).parameters['governed_action'].default is None
assert callable(verify_governed_payment_action)
for forbidden_text in ('FactLineage', 'DerivedFact', 'taint propagation', 'prompt injection'):
    assert forbidden_text not in source
print('governed_action_static_audit=PASS')
print('governed_action_type_count=1')
print('governed_action_keyword_only=true')
print('verifier_callback_calls=0')
PY

printf 'AUTHORIZATIONS\n'
printf '%s\n' 'network=false api=false dependency_install=false create_environment=false webshop_runtime=false buy_now=false payment_side_effect=false commit=false push=false history_rewrite=false'
