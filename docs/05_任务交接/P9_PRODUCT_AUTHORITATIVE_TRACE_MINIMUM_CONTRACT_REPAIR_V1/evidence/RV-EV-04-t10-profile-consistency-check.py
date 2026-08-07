from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('.')
EVIDENCE = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence'
coverage = json.loads((EVIDENCE / 'EV-06-coverage-repaired.json').read_text(encoding='utf-8'))
t10 = next(item for item in coverage['tasks'] if item['task_id'] == 'T10')
next_slice = (ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md').read_text(encoding='utf-8')
design = (ROOT / 'docs/03_架构设计/产品权威轨迹最小合同_v1.md').read_text(encoding='utf-8')

roles = set(t10['entity_roles'])
sequence = t10['event_sequence']
authorized_role_declared = 'AUTHORIZED_ORDER_SNAPSHOT' in roles
authorized_event_present = any('ORDER_RECORDED[AUTHORIZED_ORDER_SNAPSHOT]' == event for event in sequence)
current_event_present = any('ORDER_RECORDED[CURRENT_ORDER_SNAPSHOT]' == event for event in sequence)

action_sequence_items = [event for event in sequence if event.startswith('ACTION_RECORDED')]
action_coverage_role = action_sequence_items[0] if action_sequence_items else None
next_slice_ambiguous_action = 'ACTION_RECORDED [GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE]' in next_slice
single_entity_role_contract = '- entity_role: closed enum' in design
single_source_object_contract = '- source_object_type: closed type name' in design
profile_field_matrix_present = any(
    token in design
    for token in (
        'profile event mapping matrix',
        '事件—实体—源对象映射表',
        'event_entity_source_mapping',
    )
)

findings = []
if authorized_role_declared and not authorized_event_present:
    findings.append({
        'id': 'F-07A',
        'severity': 'BLOCKING',
        'title': 'T10 角色清单与事件序列不一致',
        'details': {
            'declared_role': 'AUTHORIZED_ORDER_SNAPSHOT',
            'event_present': authorized_event_present,
            'current_snapshot_event_present': current_event_present,
            'event_sequence': sequence,
        },
    })
if next_slice_ambiguous_action and single_entity_role_contract and single_source_object_contract and not profile_field_matrix_present:
    findings.append({
        'id': 'F-07B',
        'severity': 'BLOCKING',
        'title': 'T10 ACTION_RECORDED 的 entity 与 source-object 映射未冻结',
        'details': {
            'coverage_action': action_coverage_role,
            'next_slice_action': 'ACTION_RECORDED [GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE]',
            'event_contract': 'one entity_role + one source_object_type/ref',
            'missing': 'profile-specific exact mapping for entity_type/entity_role/source_object_type/projection/value paths',
        },
    })

result = {
    'schema': 'evaluator-t10-profile-consistency-audit/v1',
    'task_id': 'P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1',
    'facts': {
        't10_entity_roles': sorted(roles),
        't10_event_sequence': sequence,
        'authorized_role_declared': authorized_role_declared,
        'authorized_event_present': authorized_event_present,
        'next_slice_ambiguous_action': next_slice_ambiguous_action,
        'profile_field_matrix_present': profile_field_matrix_present,
    },
    'findings': findings,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if len(findings) == 2 else 1)
