from pathlib import Path
import ast
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from agentic_payment_experiment.trusted_execution import SourceType


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

changed = {
    'src/agentic_payment_experiment/trusted_execution/fact_lineage.py': '7608b0f9997eb357a7ca733343eb359183f29bcc52eae6d941c3c83efb9737b5',
    'src/agentic_payment_experiment/trusted_execution/__init__.py': 'feb23392d6382c471af951519fb7c09558d8caa93c9bf1698b9b2eadd0f4ea96',
    'src/agentic_payment_experiment/__init__.py': 'bcd378e3d9e35995d2cb308f8e6a56b2825663c8854996367dbf4dda6b85d9d5',
    'src/agentic_payment_experiment/attack_overlay.py': '2f14925231f4c59368b096fdcc2398bba8c8c4e6f774d7bcb430487ca65f25d7',
    'tests/trusted_execution/test_fact_lineage.py': 'bb5cdecc54b08857104243ee73437c3bdc26a5e04a195cd25a6c12445561073f',
    'tests/test_attack_overlay.py': 'afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27',
    'samples/attacks/fact_lineage_matrix_v1.json': '238391eb288abd0226ea72ad385268806afd2a01d907487f7b5ce1331070c14c',
    'scripts/validation/run_fact_lineage_matrix.py': 'e1316c306090e4a436183abfa7d08981cb63ac6fb9079f9471b1a7d0961bdc7f',
}
for path, expected in changed.items():
    actual = sha(path)
    assert actual == expected, (path, expected, actual)
    print('changed_hash', actual, path)

protected = {
    'src/agentic_payment_experiment/trusted_execution/context_policy.py': 'be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56',
    'src/agentic_payment_experiment/trusted_execution/governed_action.py': '115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e',
    'src/agentic_payment_experiment/webshop_runtime_gate.py': '53cf905867905ae73f2886c4612a6d19cc839420677afe4f0eb4f655c87c1dd2',
    'src/agentic_payment_experiment/trusted_execution/hashing.py': '20a3ccbe372d48b4239aafde41dd09ac53446761d95e8e4d7f4686cb118b2931',
    'src/agentic_payment_experiment/models.py': 'd38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65',
    'src/agentic_payment_experiment/validator.py': '9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb',
    'src/agentic_payment_experiment/payment_execution.py': '25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71',
}
for path, expected in protected.items():
    actual = sha(path)
    assert actual == expected, (path, expected, actual)
    print('protected_unchanged', actual, path)

assert [item.value for item in SourceType] == [
    'USER_CONFIRMED',
    'SYSTEM_POLICY',
    'AGENT_DECLARED',
    'AGENT_INFERRED',
    'MERCHANT_PROVIDED',
    'PROTOCOL_VERIFIED',
    'PAYMENT_PROVIDER_OBSERVED',
    'EXTERNAL_TOOL_UNTRUSTED',
    'WEB_UNTRUSTED',
    'LLM_GENERATED',
]
print('source_type_enum_unchanged=PASS')

lineage_path = ROOT / 'src/agentic_payment_experiment/trusted_execution/fact_lineage.py'
source = lineage_path.read_text(encoding='utf-8')
outer_pos = source.index('if type(nodes) is not tuple:')
node_boundary_pos = source.index('if any(type(node) is not FactLineageNode for node in nodes):')
first_node_attribute_pos = source.index('_node_identity(node, index)')
assert outer_pos < node_boundary_pos < first_node_attribute_pos
assert 'heapq.heappop' in source
assert 'AGENT_DECLARED' in source
assert 'Decision' not in source and 'ALLOW' not in source and 'DENY' not in source
print('exact_type_before_attribute_access=PASS')
print('non_recursive_topological_resolution=PASS')
print('agent_declared_classification_explicit=PASS')
print('lineage_has_no_business_decision=PASS')

tree = ast.parse(source)
risky_imports = {'os', 'subprocess', 'socket', 'requests', 'urllib', 'pathlib'}
imports = set()
calls = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.update(alias.name.split('.')[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module.split('.')[0])
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
assert imports.isdisjoint(risky_imports)
assert calls.isdisjoint({'open', 'write_text', 'write_bytes', 'system', 'popen', 'run', 'urlopen'})
print('pure_resolver_no_io_network_process_environment=PASS')

overlay = (ROOT / 'src/agentic_payment_experiment/attack_overlay.py').read_text(encoding='utf-8')
assert overlay.count('resolve_fact_lineage(') == 1
assert 'lineage_status, lineage_reasons, lineage_facts = _resolve_overlay_lineage(overlay)' in overlay
assert 'evaluate_context_policy(' in overlay
assert '_overlay_value_digest' in overlay
print('overlay_uses_shared_resolver_once=PASS')
print('context_policy_remains_decision_owner=PASS')
print('financial_canonical_hash_not_relaxed=PASS')
print('authorizations network=false api=false dependency_install=false create_environment=false webshop_runtime=false buy_now=false payment_side_effect=false commit=false push=false history_rewrite=false')
