# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: P9-AUTONOMOUS-WEBSHOP-PREBUY-BEHAVIOR-CAPTURE-V1
task_kind: capability_experiment
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: a9d02f9dbe3dd1ca580a8c4ac278151081a281be
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-24-r18
active_bottleneck_id: B-04
hypothesis_id: H-11
contract_path: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/CONTRACT.md
executor_report_path: NONE
evaluator_review_path: NONE
next_artifact_path: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/REPORT.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Current action

```text
Executor owns the Amendment A1-corrected B-04/H-11 package. Use fixed-shuffle goal
index/session 10. Implement only the bounded deterministic local policy, real WebShop
pre-Buy-Now driver, result validator and dedicated tests.
Run the frozen Validation Plan as L2 and submit REPORT only after all six mandatory
checks pass. Local WebShop runtime execution is authorized; network, LLM/API, Buy Now,
payment/order side effects, dependency changes, commit, push, reset, clean and history
rewrite remain forbidden.
```

## Routing rule

The frozen v2.2 Validation Plan is the acceptance semantics. Executor owns both
CONTRACT_FROZEN and EXECUTING, and may submit only after L2-GATE is PASS and the
workflow validator is OK. Validator success does not transfer ownership. Evaluator
accepts only the unchanged submitted snapshot, routes READY_FOR_REVIEW / Evaluator,
runs L3 with the two frozen anti-cheating procedures, and then decides the task and
project-impact verdicts. Format-only defects are FIX_IN_PLACE in this task; technical
failure or contract/scope change requires one bounded repair selected by Evaluator.
