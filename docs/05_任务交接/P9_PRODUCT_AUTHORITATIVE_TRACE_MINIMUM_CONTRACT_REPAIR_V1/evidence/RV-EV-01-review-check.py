from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
TASK = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1'
EVIDENCE = TASK / 'evidence'


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def require(name: str, condition: bool, details: object | None = None) -> None:
    checks[name] = {'pass': bool(condition), 'details': details}


checks: dict[str, dict[str, object]] = {}
coverage_path = EVIDENCE / 'EV-06-coverage-repaired.json'
coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
tasks = coverage['tasks']
by_id = {item['task_id']: item for item in tasks}
expected_ids = [f'T{i:02d}' for i in range(1, 13)]

require('coverage_exact_12', len(tasks) == 12 and sorted(by_id) == expected_ids, sorted(by_id))
require('coverage_no_duplicates', len(by_id) == len(tasks))
require('coverage_all_not_available', all(t['current_status'] == 'NOT_AVAILABLE' for t in tasks))
require('coverage_no_new_business_rule', all(t['new_business_rule_required'] is False for t in tasks))
require('coverage_consistency_key', coverage['consistency_key'] == ['entity_type', 'entity_role'])
require('coverage_sha256', sha256(coverage_path) == '2f7ee5dc446efbe4c0b55f1cc0e705c3aa939606309154cb7e38babf1f70821d', sha256(coverage_path))

for task_id in ('T02', 'T03', 'T04'):
    seq = by_id[task_id]['event_sequence']
    require(f'{task_id}_two_order_snapshots', 'ORDER_RECORDED[AUTHORIZED_ORDER_SNAPSHOT]' in seq and 'ORDER_RECORDED[CURRENT_ORDER_SNAPSHOT]' in seq, seq)
require('T04_no_orderdifference_source', all('OrderDifference' not in src for src in by_id['T04']['source_objects']), by_id['T04']['source_objects'])
require('T04_evidence_source_present', any('ValidationResult.evidence' in src for src in by_id['T04']['source_objects']))

for task_id, expected_value in (('T05', 'DENY'), ('T06', 'INDETERMINATE')):
    task = by_id[task_id]
    source = [d for d in task['decision_sources'] if d['event'] == 'ACTION_BINDING_DECISION_RECORDED']
    require(
        f'{task_id}_action_binding_decision',
        len(source) == 1 and source[0]['value'].endswith(expected_value),
        source,
    )
    require(f'{task_id}_event_sequence', 'ACTION_BINDING_DECISION_RECORDED' in task['event_sequence'])

roles = set(by_id['T10']['entity_roles'])
require('T10_dual_payment_roles', {'CURRENT_PAYMENT_CANDIDATE', 'HISTORICAL_SUCCEEDED_PAYMENT'} <= roles, sorted(roles))
require('T10_historical_event', 'PAYMENT_OUTCOME_RECORDED[HISTORICAL_SUCCEEDED_PAYMENT]' in by_id['T10']['event_sequence'])

t10 = json.loads((EVIDENCE / 'EV-06-t10-dual-payment.json').read_text(encoding='utf-8'))
entities = {e['entity_role']: e for e in t10['entities']}
require('T10_two_entities', set(entities) == {'CURRENT_PAYMENT_CANDIDATE', 'HISTORICAL_SUCCEEDED_PAYMENT'}, sorted(entities))
require('T10_distinct_refs', entities['CURRENT_PAYMENT_CANDIDATE']['entity_ref'] != entities['HISTORICAL_SUCCEEDED_PAYMENT']['entity_ref'])
require('T10_historical_succeeded', entities['HISTORICAL_SUCCEEDED_PAYMENT'].get('status') == 'SUCCEEDED')
require('T10_current_action_relation', any('GovernedPaymentAction.payment_ref' in rel for rel in entities['CURRENT_PAYMENT_CANDIDATE']['relations']))
require('T10_historical_preflight_relation', any('related_attempt_refs' in rel for rel in entities['HISTORICAL_SUCCEEDED_PAYMENT']['relations']))

design = read('docs/03_架构设计/产品权威轨迹最小合同_v1.md')
for term in (
    'AUTHORIZED_ORDER_SNAPSHOT', 'CURRENT_ORDER_SNAPSHOT', 'CURRENT_PAYMENT_CANDIDATE',
    'HISTORICAL_SUCCEEDED_PAYMENT', 'ACTION_BINDING_DECISION_RECORDED',
    '(entity_type, entity_role)', 'projection_schema',
    'RESULT ref 只 hash outcome projection excluding authoritative_trace',
):
    require(f'design_contains::{term}', term in design)
require('design_stage_split', '阶段 A：测量适配' in design and '阶段 B：单一产品能力实验' in design)
require('design_no_runner_product_same_experiment', '不得在同一 capability experiment 中同时修改 runner 和产品 trace 产出' in design)

adapter = (TASK / 'MEASUREMENT_ADAPTER.md').read_text(encoding='utf-8')
for term in ('Task kind: `maintenance`', 'runner 只读取 `outcome.authoritative_trace`', 'evaluator replay 不得回退计入', '产品 outcome 继续不产出 trace', '0/12 VALID'):
    require(f'adapter_contains::{term}', term in adapter)

next_slice_path = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md'
next_slice = next_slice_path.read_text(encoding='utf-8')
for term in ('CONDITIONAL_NOT_FROZEN', 'prerequisite = measurement adapter accepted', 'runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE', 'before hash = TBD_AFTER_ADAPTER_ACCEPTANCE'):
    require(f'next_slice_contains::{term}', term in next_slice)
capability_contract = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md'
require('T10_capability_contract_absent', not capability_contract.exists())

known_payment = read('src/agentic_payment_experiment/trusted_execution/known_payment_attempt.py')
require('known_payment_current_request_ref', 'current_request_ref: str | None' in known_payment)
require('known_payment_related_attempt_refs', 'related_attempt_refs: tuple[str, ...]' in known_payment)
require('known_payment_same_request_filter', 'if attempt_request_ref != current_request_ref:' in known_payment)

governed_action = read('src/agentic_payment_experiment/trusted_execution/governed_action.py')
require('governed_action_request_ref', 'request_ref: str' in governed_action)
require('governed_action_payment_ref', 'payment_ref: str' in governed_action)

src_trace_hits = []
for path in (ROOT / 'src').rglob('*.py'):
    text = path.read_text(encoding='utf-8')
    if 'authoritative_trace' in text:
        src_trace_hits.append(path.as_posix())
require('zero_product_trace_producers_static', not src_trace_hits, src_trace_hits)

manifest = json.loads((EVIDENCE / 'immutable_manifest.json').read_text(encoding='utf-8'))['files']
changed = []
missing = []
for rel, expected in manifest.items():
    path = ROOT / rel
    if not path.exists():
        missing.append(rel)
    elif sha256(path) != expected:
        changed.append(rel)
require('protected_manifest_no_missing', not missing, missing)
require('protected_manifest_unchanged', not changed, changed)
require('protected_manifest_count', len(manifest) == 256, len(manifest))

head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
status = subprocess.check_output(['git', 'status', '--short'], text=True).strip().splitlines()
require('reviewed_head', head == '979ffc505bec0b626858d0d186f655867b5491bf', head)
require('workspace_clean_before_evaluator_files', all('RV-EV-' in line or 'REVIEW.md' in line for line in status), status)

failed = [name for name, result in checks.items() if not result['pass']]
result = {
    'schema': 'evaluator-independent-review/v1',
    'task_id': 'P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1',
    'reviewed_head': head,
    'checks': checks,
    'failed': failed,
    'summary': {
        'passed': len(checks) - len(failed),
        'failed': len(failed),
        'total': len(checks),
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
