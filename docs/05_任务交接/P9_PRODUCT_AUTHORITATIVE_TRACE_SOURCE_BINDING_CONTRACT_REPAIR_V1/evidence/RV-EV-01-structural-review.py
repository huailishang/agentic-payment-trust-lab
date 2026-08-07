from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
TASK = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1'
EVIDENCE = TASK / 'evidence'
COVERAGE = EVIDENCE / 'EV-01-coverage-source-binding.json'
DESIGN = ROOT / 'docs/03_架构设计/产品权威轨迹最小合同_v1.md'
ADAPTER = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md'
NEXT_SLICE = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md'
CURRENT = ROOT / 'CURRENT.md'


def check(name: str, passed: bool, detail: object | None = None) -> None:
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


checks: list[dict[str, object]] = []
data = json.loads(COVERAGE.read_text(encoding='utf-8'))
registry = data['projection_registry']
tasks = data['tasks']
by_id = {item['task_id']: item for item in tasks}
expected_ids = [f'T{i:02d}' for i in range(1, 13)]

check('exact-t01-t12', len(tasks) == 12 and sorted(by_id) == expected_ids, sorted(by_id))
check('all-not-available', all(t['current_status'] == 'NOT_AVAILABLE' for t in tasks))
check('all-no-new-business-rule', all(t['new_business_rule_required'] is False for t in tasks))

required_event_keys = {
    'sequence_no', 'event_type', 'entity_type', 'entity_role',
    'entity_ref_derivation', 'source_object_type', 'projection_schema',
    'ref_mode', 'source_binding_required', 'value_paths', 'relations',
}
required_path_keys = {
    'decision_path', 'status_path', 'reason_codes_path',
    'entity_ref_path', 'relation_ref_paths',
}
for task in tasks:
    events = task['events']
    roles = [event['entity_role'] for event in events]
    check(f"{task['task_id']}-roles-match-events", task['entity_roles'] == roles, {'declared': task['entity_roles'], 'actual': roles})
    check(f"{task['task_id']}-sequence-contiguous", [e['sequence_no'] for e in events] == list(range(1, len(events) + 1)))
    for event in events:
        prefix = f"{task['task_id']}-{event['sequence_no']}"
        check(f'{prefix}-event-keys', set(event) == required_event_keys, sorted(set(event) ^ required_event_keys))
        check(f'{prefix}-path-keys', set(event['value_paths']) == required_path_keys, sorted(set(event['value_paths']) ^ required_path_keys))
        check(f'{prefix}-schema-known', event['projection_schema'] in registry, event['projection_schema'])
        if event['projection_schema'] in registry:
            spec = registry[event['projection_schema']]
            check(f'{prefix}-source-type-match', spec['source_object_type'] == event['source_object_type'], {'registry': spec['source_object_type'], 'event': event['source_object_type']})
            check(f'{prefix}-ref-mode-match', spec['ref_mode'] == event['ref_mode'], {'registry': spec['ref_mode'], 'event': event['ref_mode']})
        check(f'{prefix}-binding-required', event['source_binding_required'] is True)

for schema, spec in registry.items():
    fields = spec.get('fields')
    check(f'{schema}-fields-list', isinstance(fields, list) and len(fields) == len(set(fields)), fields)
    check(f'{schema}-known-ref-mode', spec.get('ref_mode') in {'NATIVE_REF', 'HASH_REF'}, spec.get('ref_mode'))

for forbidden in data['forbidden_projection_fields']:
    offenders = [schema for schema, spec in registry.items() if forbidden in spec.get('fields', [])]
    check(f'forbidden-field-{forbidden}', not offenders, offenders)

expected_t10_events = [
    'AUTHORITY_RECORDED', 'ORDER_RECORDED', 'ORDER_RECORDED',
    'REQUEST_RECORDED', 'ACTION_RECORDED', 'PAYMENT_CANDIDATE_RECORDED',
    'ACTION_BINDING_DECISION_RECORDED', 'PAYMENT_OUTCOME_RECORDED',
    'KNOWN_PAYMENT_PREFLIGHT_RECORDED', 'PREPAYMENT_DECISION_RECORDED',
    'RUNTIME_DECISION_RECORDED', 'RESULT_RECORDED',
]
expected_t10_roles = [
    'AUTHORITY', 'AUTHORIZED_ORDER_SNAPSHOT', 'CURRENT_ORDER_SNAPSHOT',
    'CURRENT_REQUEST', 'GOVERNED_ACTION', 'CURRENT_PAYMENT_CANDIDATE',
    'ACTION_BINDING_FACT', 'HISTORICAL_SUCCEEDED_PAYMENT',
    'KNOWN_PAYMENT_PREFLIGHT_FACT', 'PREPAYMENT_VALIDATION',
    'RUNTIME_GATE_OBSERVATION', 'FINAL_OUTCOME',
]
t10 = by_id['T10']
check('t10-exact-12-events', [e['event_type'] for e in t10['events']] == expected_t10_events)
check('t10-exact-12-roles', [e['entity_role'] for e in t10['events']] == expected_t10_roles)

texts = {
    'design': DESIGN.read_text(encoding='utf-8'),
    'adapter': ADAPTER.read_text(encoding='utf-8'),
    'next_slice': NEXT_SLICE.read_text(encoding='utf-8'),
    'current': CURRENT.read_text(encoding='utf-8'),
}
check('design-has-source-bindings', 'source_bindings: tuple[TraceSourceBinding, ...]' in texts['design'])
check('design-has-payment-candidate-event', 'PAYMENT_CANDIDATE_RECORDED' in texts['design'])
check('adapter-no-hidden-resolver', '唯一 source resolver 是 `outcome.authoritative_trace.source_bindings`' in texts['adapter'])
check('next-slice-conditional', 'State: `CONDITIONAL_NOT_FROZEN`' in texts['next_slice'] and 'TBD_AFTER_ADAPTER_ACCEPTANCE' in texts['next_slice'])
check('current-ready-for-review', 'state: READY_FOR_REVIEW' in texts['current'] and 'current_role: Evaluator' in texts['current'])

head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
check('head-is-baseline', head == '979ffc505bec0b626858d0d186f655867b5491bf', head)
changed = subprocess.check_output(['git', 'status', '--porcelain=v1'], text=True).splitlines()
forbidden_changes = []
for line in changed:
    path = line[3:].strip('"')
    if path.startswith(('src/', 'tests/', 'scripts/', 'samples/')):
        forbidden_changes.append(line)
check('no-protected-worktree-changes', not forbidden_changes, forbidden_changes)

trace_hits = []
for path in (ROOT / 'src').rglob('*.py'):
    if 'authoritative_trace' in path.read_text(encoding='utf-8'):
        trace_hits.append(path.as_posix())
check('no-product-trace-producer', not trace_hits, trace_hits)

failed = [item for item in checks if not item['passed']]
result = {
    'schema': 'evaluator-independent-structural-review/v1',
    'task_id': 'P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1',
    'summary': {'total': len(checks), 'passed': len(checks) - len(failed), 'failed': len(failed)},
    'failed_checks': failed,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
