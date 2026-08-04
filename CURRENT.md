# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.1 -->

```yaml
workflow: evaluator-executor-workflow/v2.1
task_id: P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1
task_kind: repair
state: EXECUTING
current_role: Executor
baseline_commit: 71a3acbbd9622b68a8064381b9034e07c1f4d700
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
contract_path: docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REPORT.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_network_call: false
authorization_data_download: false
authorization_dependency_install: false
authorization_create_environment: false
authorization_webshop_runtime_execution: false
authorization_buy_now_execution: false
authorization_payment_or_order_side_effect: false
```

## Current action

```text
Read:
- docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md revision 2026-08-04-r5, B-03 and H-03
- docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/REVIEW.md
- docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/CONTRACT.md

Repair the rejected design only:
1. Split measurement-adapter work from the later T10 product capability experiment.
2. Revise the schema with closed entity roles and profile-specific reference consistency.
3. Freeze deterministic refs for objects without native IDs, including RESULT without circular hashing.
4. Model T10 current payment candidate and historical succeeded payment as different roles with explicit relations.
5. Add ACTION_BINDING_DECISION_RECORDED for T05/T06 final decisions.
6. Model authorized/current order snapshots separately for T02—T04 and correct T04 source mapping.
7. Rebuild the T01—T12 coverage map and structured evidence from actual product outputs.
8. Change NEXT_SLICE to conditional, pending acceptance of a separate measurement-adapter task.
9. Do not implement trace types, modify runner, or make any product outcome emit a trace.
10. Save EV evidence and REPORT while CURRENT remains EXECUTING / Executor.

Required outputs:
- updated docs/03_架构设计/产品权威轨迹最小合同_v1.md
- updated docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md
- updated parent NEXT_SLICE.md
- repair MEASUREMENT_ADAPTER.md
- repair REPORT.md and evidence/EV-*

Do not:
- modify src, tests, scripts, samples, metrics or existing product evidence;
- create or freeze the T10 capability contract;
- count evaluator replay as product trace;
- update the project map or change B-03/H-03;
- execute WebShop runtime, real Buy Now, network, LLM, payment, wallet or external side effects;
- install dependencies, create environments, commit, push, reset or rewrite history.
```

## Routing rule

The Executor owns `CONTRACT_FROZEN` and `EXECUTING`. It must submit only corrected design artifacts, evidence and REPORT without changing to `READY_FOR_REVIEW`. Only the Evaluator may accept the repair and authorize the separate measurement-adapter task. The repair project-impact verdict is `NOT_APPLICABLE`.
