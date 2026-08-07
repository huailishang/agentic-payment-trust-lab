from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path('.')
EVIDENCE = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/evidence'
COVERAGE_PATH = EVIDENCE / 'EV-01-coverage-source-binding.json'
DESIGN_PATH = ROOT / 'docs/03_架构设计/产品权威轨迹最小合同_v1.md'
ADAPTER_PATH = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md'
RUNNER_PATH = ROOT / 'scripts/validation/run_project_impact_baseline.py'
MODELS_PATH = ROOT / 'src/agentic_payment_experiment/models.py'
SIDECAR_PATH = ROOT / 'src/agentic_payment_experiment/webshop_payment_sidecar.py'

coverage = json.loads(COVERAGE_PATH.read_text(encoding='utf-8'))
registry = coverage['projection_registry']
t10 = next(task for task in coverage['tasks'] if task['task_id'] == 'T10')
design = DESIGN_PATH.read_text(encoding='utf-8')
adapter = ADAPTER_PATH.read_text(encoding='utf-8')
runner = RUNNER_PATH.read_text(encoding='utf-8')


def class_fields(path: Path, class_name: str) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            result: dict[str, str] = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    result[item.target.id] = ast.unparse(item.annotation)
            return result
    raise RuntimeError(f'class not found: {class_name}')


def all_class_names() -> set[str]:
    result: set[str] = set()
    for path in (ROOT / 'src').rglob('*.py'):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                result.add(node.name)
    return result


def finding(fid: str, title: str, facts: dict[str, object], minimum_repair: list[str]) -> None:
    findings.append({
        'id': fid,
        'severity': 'BLOCKING',
        'title': title,
        'facts': facts,
        'minimum_repair': minimum_repair,
    })


findings: list[dict[str, object]] = []

# F-01: T10 uses the same current/authorized Order object but two schema-specific
# bindings under one source_object_ref key.
t10_by_role = {event['entity_role']: event for event in t10['events']}
authorized = t10_by_role['AUTHORIZED_ORDER_SNAPSHOT']
current = t10_by_role['CURRENT_ORDER_SNAPSHOT']
runner_t10_default_context = 'if task_id == "T10":' in runner and 'context = _gate_context()' in runner
runner_authorized_alias = 'authorized = authorized_adaptation or current' in runner
same_native_ref = (
    authorized['source_object_type'] == current['source_object_type'] == 'Order'
    and authorized['ref_mode'] == current['ref_mode'] == 'NATIVE_REF'
    and authorized['entity_ref_derivation'] == current['entity_ref_derivation']
)
different_schema = authorized['projection_schema'] != current['projection_schema']
if runner_t10_default_context and runner_authorized_alias and same_native_ref and different_schema:
    finding(
        'F-01',
        'T10 两个订单角色在真实路径上共享同一 native ref，却要求两个不同 canonical binding',
        {
            't10_calls_default_gate_context': runner_t10_default_context,
            'gate_context_aliases_authorized_to_current': runner_authorized_alias,
            'authorized_schema': authorized['projection_schema'],
            'current_schema': current['projection_schema'],
            'both_ref_mode': 'NATIVE_REF',
            'binding_lookup_rule': coverage['source_binding_contract']['event_binding_rule'],
            'contradiction': 'same source_object_ref + different projection_schema/canonical bytes cannot resolve to exactly one binding',
        },
        [
            '给 source binding 单独定义 binding_ref，事件按 binding_ref 解析；或统一两个订单角色使用同一 projection schema',
            '明确同一 native object 在多个 entity_role 下复用一个 binding 的规则',
            '用 T10 当前/授权订单相同对象的反例做机器校验',
        ],
    )

# F-02: target entity ref includes order version, but several T10 relation paths
# provide only order_id/order_ref.
current_order_ref_expr = current['entity_ref_derivation']
relation_mismatches: list[dict[str, object]] = []
for event in t10['events']:
    for relation in event['relations']:
        if relation['target_entity_role'] == 'CURRENT_ORDER_SNAPSHOT':
            path = relation['target_ref_path']
            if 'order_version' not in path and 'authority_version' not in path:
                relation_mismatches.append({
                    'event': event['event_type'],
                    'source_role': event['entity_role'],
                    'target_ref_path': path,
                    'target_entity_ref_derivation': current_order_ref_expr,
                })
if relation_mismatches:
    finding(
        'F-02',
        'T10 关系 target_ref 与 CURRENT_ORDER_SNAPSHOT 的实体 ref 规则不一致',
        {
            'current_order_entity_ref': current_order_ref_expr,
            'mismatches': relation_mismatches,
            'validator_rule': 'relation target must exist with matching role/ref',
        },
        [
            '冻结唯一 entity_ref 语法并让每个 relation 使用目标实体的同一推导规则',
            '若 entity_ref 含 order_version，则 Request/Payment relation 必须能提供 version；否则将 entity_ref 明确定义为 role + native id 并把 version 留在 binding',
            '增加逐 relation 的解析后 ref 相等测试，而不是只检查 path 字符串存在',
        ],
    )

# F-03: Decimal fields are included in primitive projections but the canonical
# conversion contract has no Decimal rule.
model_types = {
    'Order': class_fields(MODELS_PATH, 'Order'),
    'TransactionRequest': class_fields(MODELS_PATH, 'TransactionRequest'),
    'PaymentExecutionRecord': class_fields(MODELS_PATH, 'PaymentExecutionRecord'),
}
decimal_fields: list[dict[str, str]] = []
for schema, spec in registry.items():
    source_type = spec['source_object_type']
    if source_type not in model_types:
        continue
    for field in spec.get('fields', []):
        annotation = model_types[source_type].get(field)
        if annotation == 'Decimal':
            decimal_fields.append({'schema': schema, 'source_type': source_type, 'field': field})
canonical_section_has_decimal = 'Decimal' in design
if decimal_fields and not canonical_section_has_decimal:
    finding(
        'F-03',
        'primitive/canonical 合同遗漏 Decimal 转换，金额 projection 无法按合同序列化',
        {
            'decimal_fields_in_registry': decimal_fields,
            'design_mentions_decimal_conversion': canonical_section_has_decimal,
            'declared_conversions': ['Enum=.value', 'datetime=ISO-8601', 'tuple=array'],
        },
        [
            '冻结 Decimal 的唯一表示方式（建议规范化十进制字符串，禁止 float）',
            '给 total_amount/amount 正负、尾零和不同精度增加固定 canonical/ref 样例',
        ],
    )

# F-04: duplicate-identical binding behavior differs between design and adapter.
design_normalizes_identical = 'validator 可先归一为一个' in design
adapter_rejects_identical = 'duplicate identical binding 未归一' in adapter
if design_normalizes_identical and adapter_rejects_identical:
    finding(
        'F-04',
        '完全相同的重复 binding 到底归一还是拒绝，设计与后续测量合同相互矛盾',
        {
            'design_behavior': 'validator may normalize identical duplicate',
            'adapter_negative_case': 'duplicate identical binding not normalized must not be VALID',
        },
        [
            '二选一冻结 exact verdict：INVALID 或 canonical dedupe 后继续',
            '设计、coverage、measurement adapter 和测试矩阵使用同一规则',
        ],
    )

# F-05: coverage names a source object that does not exist in product code.
classes = all_class_names()
unknown_source_types = sorted({spec['source_object_type'] for spec in registry.values()} - classes)
if unknown_source_types:
    affected = []
    for task in coverage['tasks']:
        for event in task['events']:
            if event['source_object_type'] in unknown_source_types:
                affected.append({
                    'task_id': task['task_id'],
                    'event_type': event['event_type'],
                    'source_object_type': event['source_object_type'],
                })
    finding(
        'F-05',
        'T01—T12 coverage 仍引用不存在的产品 source object 类型',
        {
            'unknown_source_types': unknown_source_types,
            'affected_events': affected,
            'actual_type_present': 'PaymentStatusConflictFact' in classes,
        },
        [
            '将 PaymentStatusConflictOutcome 修正为实际 PaymentStatusConflictFact',
            'projection fields 和 status path 按实际 resolution/effective_status/reason_codes 冻结',
            '增加 registry source_object_type 必须存在于代码对象清单的机器校验',
        ],
    )

# F-06: FINAL_OUTCOME projection claims a decision field that the named sidecar
# object does not contain, with no extraction/derivation contract.
sidecar_fields = class_fields(SIDECAR_PATH, 'WebShopPaymentFulfilmentOutcome')
sidecar_schema = registry['webshop-payment-fulfilment-outcome-result-trace/v1']
missing_direct_fields = sorted(set(sidecar_schema['fields']) - set(sidecar_fields))
uses_sidecar_final = []
for task in coverage['tasks']:
    for event in task['events']:
        if event['projection_schema'] == 'webshop-payment-fulfilment-outcome-result-trace/v1':
            uses_sidecar_final.append(task['task_id'])
if 'decision' in missing_direct_fields and uses_sidecar_final:
    finding(
        'F-06',
        '多个 RESULT_RECORDED 把不存在于 WebShopPaymentFulfilmentOutcome 的 decision 当作 source projection',
        {
            'actual_sidecar_fields': sorted(sidecar_fields),
            'declared_projection_fields': sidecar_schema['fields'],
            'missing_direct_fields': missing_direct_fields,
            'affected_tasks': uses_sidecar_final,
            'hidden_gate_context_forbidden': True,
        },
        [
            'RESULT 使用真实包含 decision 的 gate outcome，或定义并实现一个真实的组合 outcome 类型',
            '若 projection 允许从嵌套字段派生，必须冻结 source extraction paths；不得从未声明的另一个对象补 decision',
            '对每个 projection field 增加“可从指定 source object 读取/派生”的静态核验',
        ],
    )

# F-07: entity_ref_path is declared as a path but contains an undefined '+' expression.
plus_expressions = sorted({
    event['value_paths']['entity_ref_path']
    for task in coverage['tasks']
    for event in task['events']
    if isinstance(event['value_paths']['entity_ref_path'], str)
    and '+' in event['value_paths']['entity_ref_path']
})
plus_grammar_defined = any(token in design for token in ('concat(', 'entity_ref expression grammar', '字段拼接分隔符'))
if plus_expressions and not plus_grammar_defined:
    finding(
        'F-07',
        'entity_ref_path 实际写成未定义的“+”表达式，不是可执行的字段路径',
        {
            'expressions': plus_expressions,
            'grammar_or_separator_defined': plus_grammar_defined,
            'collision_example': {'left': ['ab', 'c'], 'right': ['a', 'bc'], 'both_naive_concat': 'abc'},
        },
        [
            '将 path 与 derivation 分开：path 只能是单字段路径，复合 ref 使用关闭的函数/模板',
            '复合 ref 必须使用带类型和分隔符的无歧义编码，并给出解析器与碰撞反例',
        ],
    )

# F-08: NATIVE_REF does not commit the supplied projection, so a self-contained
# validator can verify only self-consistency, not that status/amount/payee came
# from the named source object.
native_specs_with_non_identity_fields = []
for schema, spec in registry.items():
    if spec.get('ref_mode') != 'NATIVE_REF':
        continue
    identity_fields = {
        spec.get('native_id_path', '').removeprefix('projection.'),
        (spec.get('version_path') or '').removeprefix('projection.'),
    } - {''}
    extra = sorted(set(spec.get('fields', [])) - identity_fields)
    if extra:
        native_specs_with_non_identity_fields.append({'schema': schema, 'uncommitted_fields': extra})
if native_specs_with_non_identity_fields:
    finding(
        'F-08',
        'NATIVE_REF 只绑定 ID/version，source binding 中其余关键 projection 字段未被 ref 承诺',
        {
            'affected_schemas': native_specs_with_non_identity_fields,
            'hidden_source_resolver_forbidden': True,
            'consequence': 'runner can detect internal mismatch against the supplied projection, but cannot detect a single fabricated projection carrying the same native ref',
        },
        [
            '为所有 binding 增加 projection_digest/binding_ref=hash(schema+projection)，事件引用 binding_ref',
            '保留 native source_object_ref 作为对象身份，但不要把它当作 projection 完整性证明',
            '明确当前验证只证明产品输出内部一致性，不证明外部密码学真实性；签名/可信执行可后置',
        ],
    )

result = {
    'schema': 'evaluator-semantic-executability-review/v1',
    'task_id': 'P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1',
    'finding_count': len(findings),
    'findings': findings,
    'verdict': 'BLOCKING_FINDINGS_PRESENT' if findings else 'NO_BLOCKING_FINDINGS',
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if findings else 1)
