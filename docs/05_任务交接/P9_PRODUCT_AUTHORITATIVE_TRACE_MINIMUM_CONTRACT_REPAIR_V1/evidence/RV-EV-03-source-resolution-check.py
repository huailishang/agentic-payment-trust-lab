from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path('.')
DESIGN = ROOT / 'docs/03_架构设计/产品权威轨迹最小合同_v1.md'
ADAPTER = ROOT / 'docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md'
RUNNER = ROOT / 'scripts/validation/run_project_impact_baseline.py'
GATE = ROOT / 'src/agentic_payment_experiment/webshop_runtime_gate.py'
SIDECAR = ROOT / 'src/agentic_payment_experiment/webshop_payment_sidecar.py'


def dataclass_fields(path: Path, class_name: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            result: list[str] = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    result.append(item.target.id)
            return result
    raise RuntimeError(f'class not found: {class_name}')


design = DESIGN.read_text(encoding='utf-8')
adapter = ADAPTER.read_text(encoding='utf-8')
runner = RUNNER.read_text(encoding='utf-8')
gate_fields = dataclass_fields(GATE, 'WebShopBuyNowGateOutcome')
sidecar_fields = dataclass_fields(SIDECAR, 'WebShopPaymentFulfilmentOutcome')

required_t10_sources = {
    'IntentMandate',
    'Order(authorized/current)',
    'TransactionRequest',
    'GovernedPaymentAction',
    'GovernedActionBindingFact',
    'PaymentExecutionRecord(current candidate)',
    'PaymentExecutionRecord(historical succeeded)',
    'KnownPaymentAttemptPreflightFact',
    'RuntimeGateRecord',
    'WebShopBuyNowGateOutcome',
}

available_from_gate_outcome = {
    'TransactionRequest' if 'bound_request' in gate_fields else '',
    'ValidationResult' if 'prepayment_result' in gate_fields else '',
    'RuntimeGateRecord' if 'runtime_gate_record' in gate_fields else '',
    'GovernedActionBindingFact' if 'governed_action_fact' in gate_fields else '',
    'KnownPaymentAttemptPreflightFact' if 'known_payment_attempt_preflight_fact' in gate_fields else '',
    'WebShopBuyNowGateOutcome',
}
available_from_gate_outcome.discard('')

trace_event_fields = [
    'sequence_no', 'event_type', 'entity_type', 'entity_role', 'entity_ref',
    'source_object_type', 'source_object_ref', 'relations', 'decision', 'status',
    'reason_codes', 'native_occurred_at',
]
source_verification_carriers = {
    'source_object_projection',
    'source_projection',
    'source_registry',
    'source_bindings',
    'source_resolver',
    'projection_schema',
}
present_carriers = sorted(source_verification_carriers.intersection(trace_event_fields))

facts = {
    'design_requires_ref_recomputation': 'source object ref 可按冻结规则重算' in design,
    'design_requires_value_match_to_existing_fact': '核对事件值与既有 fact 输出一致' in design,
    'adapter_requires_strict_ref_recomputation': 'stable ref 不能重算' in adapter,
    'adapter_runner_reads_only_trace': 'runner 只读取 `outcome.authoritative_trace`' in adapter,
    'runner_only_passes_outcomes_to_trace_reader': (
        '_product_observed_trace(("webshop_gate_outcome", gate))' in runner
        and '("webshop_payment_fulfilment_outcome", sidecar)' in runner
    ),
    'event_contract_has_verification_carrier': bool(present_carriers),
    'event_contract_present_carriers': present_carriers,
    'gate_outcome_fields': gate_fields,
    'sidecar_outcome_fields': sidecar_fields,
    't10_required_sources': sorted(required_t10_sources),
    'sources_directly_available_from_gate_outcome': sorted(available_from_gate_outcome),
    't10_sources_not_directly_available_from_gate_outcome': sorted(
        required_t10_sources - available_from_gate_outcome
    ),
}

blocking = (
    facts['design_requires_ref_recomputation']
    and facts['adapter_requires_strict_ref_recomputation']
    and facts['adapter_runner_reads_only_trace']
    and not facts['event_contract_has_verification_carrier']
    and bool(facts['t10_sources_not_directly_available_from_gate_outcome'])
)

result = {
    'schema': 'evaluator-source-resolution-audit/v1',
    'task_id': 'P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1',
    'facts': facts,
    'finding': {
        'id': 'F-06',
        'severity': 'BLOCKING' if blocking else 'NONE',
        'title': 'source_object_ref 缺少可执行的独立重算载体',
        'reason': (
            '合同要求 runner/validator 独立重算 source_object_ref 并核对事件值，'
            '但 trace event/envelope 未冻结 source projection、source registry 或 resolver；'
            '当前 runner 只拿到 outcome.authoritative_trace，而 outcome 不暴露 T10 所需的全部源对象。'
        ),
        'minimum_repair': [
            '冻结自包含的最小 source binding/registry，或冻结等价的显式 resolver 输入合同',
            '每个 source ref 必须绑定 projection_schema 与 primitive canonical projection',
            '冻结 event/entity/source-object 的 profile 映射及可核对字段路径',
            '保持最小披露，不允许把任意完整对象无选择塞入 trace',
            '修订 measurement adapter，先验证 source resolution 可执行，再冻结 runner 任务',
        ],
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if blocking else 1)
