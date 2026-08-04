from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

name = "rv_project_runner"
spec = importlib.util.spec_from_file_location(
    name, Path("scripts/validation/run_project_impact_baseline.py")
)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[name] = runner
spec.loader.exec_module(runner)

design = Path("docs/03_架构设计/产品权威轨迹最小合同_v1.md").read_text(
    encoding="utf-8"
)
coverage = json.loads(
    Path(
        "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/"
        "evidence/EV-05-coverage.json"
    ).read_text(encoding="utf-8")
)
rows = {row["task_id"]: row for row in coverage["rows"]}

# T10 contains two distinct payment entities: the current candidate bound to the
# governed action and the historical succeeded payment that triggers blocking.
context = runner._gate_context()
historical = replace(
    runner._sidecar_payment(context, runner.PaymentStatus.UNKNOWN),
    payment_id="project-baseline-payment-existing-success",
    status=runner.PaymentStatus.SUCCEEDED,
    provider_ref="offline-existing-payment-provider",
)
gate, callbacks = runner._invoke_gate(
    context, known_payment_attempts=(historical,)
)
print("t10_current_candidate_payment_ref", context.execution.payment_id)
print("t10_action_payment_ref", context.action.payment_ref)
print("t10_historical_payment_ref", historical.payment_id)
print(
    "t10_preflight_related_refs",
    gate.known_payment_attempt_preflight_fact.related_attempt_refs,
)
print("t10_callback_count", gate.callback_count)
print("t10_decision", gate.decision.value)
print(
    "t10_two_payment_entities",
    context.action.payment_ref != historical.payment_id,
)
print(
    "schema_has_payment_role",
    "payment_role" in design or "historical_payment_ref" in design,
)
print(
    "runtime_gate_record_has_stable_ref",
    any(hasattr(gate.runtime_gate_record, field) for field in ("record_id", "runtime_id")),
)
print(
    "runtime_gate_record_has_time",
    hasattr(gate.runtime_gate_record, "occurred_at"),
)
print(
    "outcome_has_stable_ref",
    any(hasattr(gate, field) for field in ("outcome_id", "result_id", "record_id")),
)
print(
    "design_requires_nonempty_source_object_ref",
    "source_object_ref | string | 指向真实对象的稳定引用" in design,
)
print(
    "design_freezes_content_addressed_ref_rule",
    "content-address" in design
    or "content_address" in design
    or "canonical_hash" in design,
)

# T05/T06 final decisions come from governed-action verification, while the
# coverage matrix only records a PREPAYMENT decision event.
for task_id, action in (
    ("T05", replace(context.action, agent_ref="agent-evil")),
    ("T06", replace(context.action, action_id="")),
):
    task_gate, _ = runner._invoke_gate(context, action=action)
    print(
        task_id,
        {
            "prepayment_decision": task_gate.prepayment_result.decision.value,
            "final_decision": task_gate.decision.value,
            "reason_codes": list(task_gate.reason_codes),
            "mapped_events": rows[task_id]["event_candidates"],
        },
    )

print(
    "taxonomy_has_action_binding_decision",
    "ACTION_BINDING_DECISION_RECORDED" in design,
)

# T02-T04 compare two snapshots. The mapping freezes only one ORDER event and
# does not define an order-snapshot role/version field.
for task_id, mutation in (("T02", "price_up"), ("T03", "price_down"), ("T04", "payee")):
    current, authorized = runner._mutated_adaptation(mutation)
    assert current.order is not None and authorized.order is not None
    task_context = runner._gate_context(
        adaptation=current, authorized_adaptation=authorized
    )
    task_gate, _ = runner._invoke_gate(task_context)
    print(
        task_id,
        {
            "authorized_order_id": authorized.order.order_id,
            "authorized_order_version": authorized.order.order_version,
            "current_order_id": current.order.order_id,
            "current_order_version": current.order.order_version,
            "differences": [
                {
                    "code": diff.code,
                    "field_path": diff.field_path,
                    "before": diff.before,
                    "after": diff.after,
                }
                for diff in task_gate.prepayment_result.order_differences
            ],
            "mapped_events": rows[task_id]["event_candidates"],
        },
    )

print(
    "schema_has_order_snapshot_role",
    "order_snapshot_role" in design
    or "AUTHORIZED_ORDER_RECORDED" in design
    or "CURRENT_ORDER_RECORDED" in design,
)

assert context.action.payment_ref != historical.payment_id
assert "payment_role" not in design and "historical_payment_ref" not in design
assert not any(
    hasattr(gate.runtime_gate_record, field) for field in ("record_id", "runtime_id")
)
assert not any(hasattr(gate, field) for field in ("outcome_id", "result_id", "record_id"))
assert "ACTION_BINDING_DECISION_RECORDED" not in design
assert "order_snapshot_role" not in design
assert "AUTHORIZED_ORDER_RECORDED" not in design
assert "CURRENT_ORDER_RECORDED" not in design
print("finding", "REFERENCE_AND_COVERAGE_MODEL_INCOMPLETE")
