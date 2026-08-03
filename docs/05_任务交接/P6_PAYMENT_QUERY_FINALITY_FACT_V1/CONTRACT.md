# P6 payment query finality fact v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-PAYMENT-QUERY-FINALITY-FACT-V1
task_name: P6 查询确认与支付最终性分层
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Represent, as one immutable offline fact, whether a payment status is only an initial execution observation or has been confirmed by a trusted query. The fact must never claim HTTP acceptance, fulfillment/business success, reconciliation, settlement, or legal finality.

## Acceptance criteria

### AC-01 — closed query-finality fact

Add a protocol-neutral payment-domain fact with a closed evidence-stage enum and deterministic serialization. It must expose the initial, queried, and effective payment statuses; whether the effective payment status is terminal; and explicit false/unknown boundaries for business success and reconciliation/settlement. Unknown enum/input combinations fail closed.

### AC-02 — recovery-derived semantics

Derive the fact only from the original `PaymentExecutionRecord`, its bound `PaymentStatusObservation`, and `PaymentRecoveryResult`. S12 (`UNKNOWN → queried SUCCEEDED`) must be `QUERY_CONFIRMED`, terminal at the payment-status layer, and must still not claim fulfillment, user-task success, reconciliation, or settlement. UNKNOWN/PENDING or blocked/conflicting recovery remains non-final and non-terminal for action purposes.

### AC-03 — structured runner output

Expose the fact for S12 as structured runner/result-card fields. Existing recovery fields and S01–S13 decisions remain unchanged. UI prose parsing is forbidden; no UI redesign is required.

### AC-04 — adversarial tests and boundaries

Tests cover S12, unresolved UNKNOWN/PENDING, conflicting observation, invalid binding, unknown enum/input, and serialization. Focused tests, full discovery, official entrypoint, and scope inspection pass. No real provider, HTTP/API, async callback, reconciliation engine, settlement claim, new scenario, P1–P5 change, commit, push, or history rewrite.

## Allowed scope

- `src/agentic_payment_experiment/payment_finality.py` (new)
- `src/agentic_payment_experiment/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/test_payment_finality.py` (new)
- `tests/test_runner.py`
- `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FACT_V1/REPORT.md`
- `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FACT_V1/evidence/EV-*`

## Exclusions

- Do not modify models, scenarios, baselines, lifecycle/remediation policy, original-transaction binding, P1–P5 gates, or presentation/UI.
- Do not represent request/HTTP acceptance, async notifications, reconciliation, clearing, settlement, chargeback finality, or business-task success as implemented capabilities.
- No external call, persistence, real payment, commit, push, or history rewrite.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_payment_finality tests.test_runner -v` | finality fact and S12 structured output pass all positive/negative cases | AC-01, AC-02, AC-03, AC-04 |
| VP-02 | `python -m unittest discover -s tests -v` | full suite passes | AC-04 |
| VP-03 | `python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 | AC-03, AC-04 |
| VP-04 | `git diff --check` and scope review | clean and within allowed paths | AC-04 |

## Inherited worktree state

P4, P5, and the original-transaction P6 changes remain intentionally uncommitted because authorization is false. Preserve them without staging, reverting, or attributing them to this task.

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if implementation requires a model/scenario/baseline change, any external observation, an async/reconciliation subsystem, UI redesign, or a claim stronger than query-confirmed payment status.
