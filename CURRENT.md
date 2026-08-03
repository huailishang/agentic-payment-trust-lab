# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.1 -->

```yaml
workflow: evaluator-executor-workflow/v2.1
task_id: P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1
task_kind: capability_experiment
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-03-r4
active_bottleneck_id: B-07
hypothesis_id: H-06
contract_path: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REPORT.md
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
- docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md revision 2026-08-03-r4, especially B-07 and H-06
- docs/04_验证体系/项目级能力评测基线_v1.md section 10
- docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/REVIEW.md
- docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/CONTRACT.md

Execute in strict phase order:

Phase A — evaluator target and BEFORE
1. Capture initial workspace and src hashes.
2. Materialize the contract-frozen T10 target fixture.
3. Add only the evaluator fields/tests needed to measure known-payment-attempt preflight.
4. Before changing any src file, run BEFORE and prove:
   - T10 ALLOW / callback 1;
   - duplicate side effect 1/12;
   - target fixture and evaluator runner hashes are frozen.

Phase B — product capability
5. Add a frozen known-payment-attempt preflight fact.
6. Reuse verify_payment_execution_binding; do not copy binding rules.
7. Make Runtime Gate consume a bound SUCCEEDED same-request attempt before callback.
8. Run AFTER with the identical target fixture and runner.
9. Prove T10 DENY / callback 0, duplicate side effect 0/12, callback match 12/12.
10. Prove the other 11 task projections are unchanged.
11. Run mandatory regressions, save complete diff/hashes, and write REPORT.md.

Do not:
- modify Sidecar, Recovery, Status Conflict, Lifecycle or Authoritative Trace;
- trust raw request IDs without a bound PaymentExecutionRecord;
- change target fixture or evaluator runner after BEFORE is frozen;
- broaden to PENDING / UNKNOWN retry policy;
- execute WebShop runtime, real Buy Now, network, LLM, payment, wallet or external side effects;
- install dependencies, create environments, commit, push or clean inherited changes.
```

## Routing rule

The Executor owns `CONTRACT_FROZEN` and `EXECUTING`. It must preserve the phase boundary: target fixture and evaluator runner are frozen before any product source change. REPORT and EV evidence remain Executor-owned until validator `OK`; only the Evaluator may accept the package and route to `READY_FOR_REVIEW`. This capability experiment requires separate task verdict and project-impact verdict.
