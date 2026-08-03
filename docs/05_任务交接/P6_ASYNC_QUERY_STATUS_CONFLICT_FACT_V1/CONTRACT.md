# P6 async/query status conflict fact v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ASYNC-QUERY-STATUS-CONFLICT-FACT-V1
task_name: P6 同步、异步与查询状态冲突事实
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
roadmap_ref: docs/02_未来规划/整体修正执行计划_20260729.md#18.3
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Five-question readiness check

1. First-principles problem: status evidence can arrive at different times through execution, async notification, and query; silently choosing one can authorize an unsafe follow-up.
2. Mature-payment or Agent-new: status convergence and conflict handling are mature-payment concerns; the Agent-specific requirement is to consume their result without overstating business success.
3. Existing mechanism: reuse original-transaction binding, payment status enums, deterministic facts, temporal ordering, and fail-closed investigation; do not invent a payment network.
4. Stable capability: this is a protocol-neutral conflict-resolution fact, not another S14/S15 scenario.
5. Proof: pairwise temporal transitions, terminal conflicts, binding failures, deterministic serialization, full regression, and official entrypoint.

## Single objective

Add one immutable offline fact that binds one query observation and one asynchronous status observation to the same original payment, orders their evidence deterministically, and makes every synchronous/async/query status conflict explicit without performing payment, retry, reconciliation, or business-success decisions.

## Acceptance criteria

### AC-01 — async observation uses original-transaction binding

Extend the closed `FollowUpAction` set with `ASYNC_STATUS_NOTIFICATION`. A `PaymentStatusObservation` used through this action must match the original payment ID, order ID, and—when the original has one—provider reference. Missing/mismatched references and unknown actions fail closed with deterministic status/reason codes. Existing query/refund/dispute binding remains unchanged.

### AC-02 — immutable conflict fact

Add a protocol-neutral immutable fact and closed resolution enum with deterministic primitive-only serialization. It exposes the initial execution status, query status/time, async status/time, effective payment status, whether that status is terminal at the payment layer, and deterministic reason codes. It must explicitly keep business success, fulfillment, user-task success, reconciliation, settlement, and legal finality false.

### AC-03 — deterministic temporal and conflict policy

Derive only from one `PaymentExecutionRecord`, one query `PaymentStatusObservation`, one async `PaymentStatusObservation`, and both original-transaction binding facts. Apply these rules:

- any non-VALID binding, missing/invalid enum, or observation before the original execution is `BLOCKED` and non-terminal;
- equal-time observations with different statuses are `CONFLICT` and non-terminal;
- `UNKNOWN/PENDING -> SUCCEEDED/FAILED` in chronological order is an allowed monotonic confirmation, with the later terminal status effective;
- matching terminal observations are consistent and terminal;
- `SUCCEEDED <-> FAILED` disagreement, or a later regression from terminal to `UNKNOWN/PENDING`, is `CONFLICT`, non-terminal for action, and must not silently select either terminal claim;
- unresolved observations without a later trusted terminal confirmation remain non-terminal.

No resolution may execute a retry/payment or claim reconciliation/settlement/business success.

### AC-04 — adversarial coverage and boundaries

Direct tests cover valid async binding; missing/mismatched payment/order/provider references; unknown action; monotonic PENDING-to-SUCCEEDED and UNKNOWN-to-FAILED; matching terminal observations; opposite terminal conflict in both channel orders; terminal-to-unresolved regression; equal-time disagreement; invalid temporal order; invalid enum/input; and deterministic serialization. Focused tests, full discovery, official entrypoint, and diff inspection pass.

## Allowed scope

- `src/agentic_payment_experiment/trusted_execution/original_transaction.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/payment_status_conflict.py` (new)
- `src/agentic_payment_experiment/__init__.py`
- `tests/trusted_execution/test_original_transaction.py`
- `tests/test_payment_status_conflict.py` (new)
- `docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/REPORT.md`
- `docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/evidence/EV-*`

## Exclusions

- No new scenario, baseline, runner/result-card section, presentation/UI, HTTP/API callback, webhook receiver, polling loop, persistence, queue, provider adapter, reconciliation/clearing/settlement engine, real payment/retry, or P1–P5 policy change.
- Do not modify existing payment recovery/finality/remediation decisions.
- `PaymentStatusObservation.source` remains an offline fixture label; this task does not prove provider authenticity or cryptographic trust.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_original_transaction tests.test_payment_status_conflict -v` | binding and all temporal/conflict cases pass | AC-01, AC-02, AC-03, AC-04 |
| VP-02 | `python -m unittest tests.test_payment_recovery tests.test_payment_finality tests.test_remediation -v` | existing payment consumers and finality remain unchanged | AC-01, AC-03, AC-04 |
| VP-03 | `python -m unittest discover -s tests -v` | full suite passes | AC-04 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 | AC-04 |
| VP-05 | `git diff --check` and scope review | clean and attributable changes stay within allowed files | AC-04 |

## Inherited worktree state

P4, P5, original-transaction P6, payment-finality P6, and their repair records remain intentionally uncommitted because authorization is false. Preserve them without staging, reverting, or attributing them to this task.

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if implementation requires a new scenario/model, real async/network behavior, persistence, a reconciliation/settlement decision, runner/UI redesign, external dependency, or a claim stronger than offline payment-status conflict classification.

## Atomic handoff requirement

Do not request Evaluator review until all mandatory VPs have readable EV stdout/stderr plus core metadata, `REPORT.md` maps AC-01 through AC-04, declares `executor_state: READY_FOR_REVIEW`, and the workflow validator has no `BLOCKING` finding. Advisory-only report formatting differences do not delay technical review or create another round.
