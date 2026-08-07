# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.1 -->

```yaml
workflow: evaluator-executor-workflow/v2.1
task_id: P9-AUTHORITATIVE-TRACE-CONSUMER-READ-MODEL-V1
task_kind: capability_experiment
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: b4eff597ebffe79c575522b91642f82b26ad5247
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-07-r12
active_bottleneck_id: B-08
hypothesis_id: H-07
contract_path: docs/05_任务交接/P9_AUTHORITATIVE_TRACE_CONSUMER_READ_MODEL_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/P9_AUTHORITATIVE_TRACE_CONSUMER_READ_MODEL_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/P9_AUTHORITATIVE_TRACE_CONSUMER_READ_MODEL_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/P9_AUTHORITATIVE_TRACE_CONSUMER_READ_MODEL_V1/REPORT.md
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
- docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md revision 2026-08-07-r12, B-08 / H-07
- docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/REVIEW.md
- docs/02_未来规划/WebShop购买轨迹可视化UI规划_20260802.md
- docs/05_任务交接/P9_AUTHORITATIVE_TRACE_CONSUMER_READ_MODEL_V1/CONTRACT.md

Build one generic read-only Authoritative Trace Consumer; do not add more product traces and do not build UI yet:
1. Freeze task-start existing src manifest and contract hashes before implementation.
2. Add only src/agentic_payment_experiment/authoritative_trace_consumer.py.
3. Consumer accepts frozen VALID ProductAuthoritativeTrace and projects a closed deterministic read model containing trace metadata, exact events, relations and source bindings.
4. Validate with the public authoritative trace validator first; invalid/indeterminate/malformed inputs fail closed and never get a normal timeline.
5. Production consumer must have no T01/T02/T07/T10 or profile/family-specific branches/imports.
6. Do not rerun validate_request, Policy, Lineage, Attack Overlay, payment, runner or evaluator logic.
7. Add tests/test_authoritative_trace_consumer.py with >=12 tests.
8. Prove one consumer works for T01 Sidecar, T02 Prepayment, T07 Attack Overlay and T10 Duplicate/Preflight: representative consumer coverage 0/4 -> 4/4.
9. Prove exact event order/count, source_binding_ref resolution, relation preservation and source-binding projection equality.
10. Consume each representative trace 3 times and prove canonical read-model SHA is identical.
11. Cover frozen fail-closed negative matrix without fabricating missing facts.
12. Keep all existing src files, fixture, runner, registry, assembler and product traces byte-for-byte unchanged.
13. Re-run project-impact: Product Trace must remain 9/12, GESR 8/12, repeat=3 stable, non-trace SHA unchanged, old trace hashes unchanged.
14. Run consumer suite, project-impact 21/21, full unittest >=550 and workflow validator.
15. Save EV triplets and REPORT.md; after work begins CURRENT remains EXECUTING / Executor.

Allowed changes:
- src/agentic_payment_experiment/authoritative_trace_consumer.py (new)
- tests/test_authoritative_trace_consumer.py (new)
- this task REPORT/evidence
- CURRENT.md only CONTRACT_FROZEN -> EXECUTING

Do not:
- modify any existing src file, __init__.py, fixture, runner, registry, assembler, project-impact tests, UI files or prior accepted task artifacts;
- add T05/T06/T11 trace capability;
- reconstruct business facts, generate prose explanations or use an LLM;
- execute network/browser/WebShop/Buy Now/payment/order/wallet/fulfilment/callback side effects;
- install dependencies, create environments, commit, push, reset, clean or rewrite history.

If the existing ProductAuthoritativeTrace does not contain enough generic evidence for this Read Model without family-specific reconstruction, STOP and submit BLOCKED evidence rather than changing producers or the registry.
```

## Routing rule

The Executor owns `CONTRACT_FROZEN` and `EXECUTING`. After work begins it may route only to `EXECUTING / Executor`, then submits REPORT/evidence while CURRENT remains Executor-owned. Only the Evaluator may accept the snapshot, route `READY_FOR_REVIEW`, independently rerun all mandatory ACs and issue task plus project-impact verdicts. This experiment is improved only if consumer-ready representative families reach `4/4` while Product Trace remains `9/12`, GESR remains `8/12`, and all existing product/trace guardrails remain unchanged.
