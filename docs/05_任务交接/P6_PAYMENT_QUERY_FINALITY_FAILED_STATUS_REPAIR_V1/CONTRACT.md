# P6 payment query finality FAILED-status repair v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-PAYMENT-QUERY-FINALITY-FAILED-STATUS-REPAIR-V1
task_name: P6 可信 FAILED 查询终态分类修复
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Correct the existing P6 finality fact so a trusted, correctly bound query that confirms the original payment as `FAILED` is represented as query-confirmed and terminal at the payment-status layer, while every blocked or unresolved recovery remains non-terminal for action purposes.

## Failed counterexample

`P6_PAYMENT_QUERY_FINALITY_FACT_V1/evidence/RV-EV-01.*` proves:

```text
initial payment: UNKNOWN
bound query observation: FAILED
recovery: RETRY_CANDIDATE / effective FAILED
current finality: INITIAL_ONLY / effective_status_terminal=false
required finality: QUERY_CONFIRMED / effective_status_terminal=true
```

This correction must not turn `retry_allowed` into an execution, and must not claim fulfillment, user-task or business success, reconciliation, settlement, or legal finality.

## Acceptance criteria

### AC-01 — trusted FAILED query is payment-terminal

For a correctly bound query whose `PaymentRecoveryResult` is `RETRY_CANDIDATE` with observed/effective `FAILED`, `derive_payment_query_finality()` returns `QUERY_CONFIRMED`, `effective_status=FAILED`, and `effective_status_terminal=true`. All business, fulfillment, task, reconciliation, settlement, and legal-finality flags remain false.

### AC-02 — fail-closed boundaries remain intact

`BLOCKED` recovery remains `QUERY_BLOCKED` and non-terminal even if a contained status is `FAILED` or `SUCCEEDED`. `UNRESOLVED` UNKNOWN/PENDING remains `QUERY_UNRESOLVED` and non-terminal. S12 `UNKNOWN -> SUCCEEDED` remains `QUERY_CONFIRMED` and payment-terminal. Unknown object/enum or inconsistent status combinations still raise `ValueError` rather than being coerced.

### AC-03 — direct regression coverage

Add a direct regression for the evaluator counterexample and assertions for the false upper-layer claims. Retain the existing blocked/conflicting, invalid-binding, UNKNOWN/PENDING, S12, serialization, and runner tests.

### AC-04 — boundaries and regression

Focused tests, full discovery, official entrypoint, and diff inspection pass. No model, recovery-policy, runner/result-card schema, scenario, baseline, P1–P5 behavior, external call, real retry/payment, reconciliation subsystem, UI, commit, push, or history rewrite.

## Allowed scope

- `src/agentic_payment_experiment/payment_finality.py`
- `tests/test_payment_finality.py`
- `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/EV-*`

## Exclusions

- Do not modify models, `payment_recovery.py`, runner, scenario fixtures, baselines, P1–P5 implementation, presentation/UI, or the rejected task's implementation/report/evidence.
- Do not execute a retry or payment, and do not infer business success, fulfillment, reconciliation, settlement, or legal finality from payment status.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_payment_finality -v` | trusted FAILED regression and all finality boundaries pass | AC-01, AC-02, AC-03 |
| VP-02 | `python -m unittest tests.test_payment_finality tests.test_runner -v` | finality and structured S12 runner output pass | AC-02, AC-03, AC-04 |
| VP-03 | `python -m unittest discover -s tests -v` | full suite passes | AC-04 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 | AC-04 |
| VP-05 | `git diff --check` and scope review | clean; only the two allowed product/test files attributable to repair | AC-04 |

## Inherited worktree state

All P4, P5, original-transaction P6, and rejected parent-finality changes remain intentionally uncommitted because authorization is false. Preserve them without staging, reverting, or attributing them to this repair.

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if the repair requires a model, recovery-policy, scenario, runner schema, external observation, async/reconciliation subsystem, UI change, or claim stronger than query-confirmed payment status.

## Atomic handoff requirement

Do not request Evaluator review until all mandatory VPs have readable EV stdout/stderr plus core metadata, `REPORT.md` maps AC-01 through AC-04, declares `executor_state: READY_FOR_REVIEW`, and the workflow validator has no `BLOCKING` finding. Advisory-only report formatting differences do not delay technical review or create another round.
