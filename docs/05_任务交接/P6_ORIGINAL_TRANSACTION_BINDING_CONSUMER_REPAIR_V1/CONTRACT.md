# P6 original-transaction binding consumer repair v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ORIGINAL-TRANSACTION-BINDING-CONSUMER-REPAIR-V1
task_name: P6 原交易绑定消费者拒绝修复
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Make payment recovery and remediation fail closed for every non-VALID result from the existing P6 original-transaction binding fact. A missing or invalid provider/reference must never be converted into recovered payment status or resolved economic remediation.

## Failed counterexample

`P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-01.*` proves both failures:

- Removing the original provider reference from a `SUCCEEDED` status query returns `RECOVERED` instead of blocking investigation.
- Setting a full refund's `payment_id` to `None` returns `RESOLVED` instead of preserving remediation.

## Acceptance criteria

### AC-01 — recovery consumes every non-VALID result

For status query, `assess_payment_recovery()` must turn every non-VALID original-transaction fact reason — including missing provider reference and missing payment/order reference — into `BLOCKED`, `retry_allowed=false`, and `investigate_status_observation_binding`. It must retain the fact reason in deterministic validation issues/evidence. A valid query continues the current original-payment behavior.

### AC-02 — remediation consumes every non-VALID result

For refund and dispute, `assess_remediation()` must turn every non-VALID original-transaction fact result — including missing payment/order reference — into `REQUIRED / preserve_evidence_and_investigate_remediation_binding`; no such record may produce `RESOLVED` or `IN_PROGRESS` as if binding were valid. Keep current amount/currency checks and valid full-refund behavior.

### AC-03 — regressions cover consumer outcomes

Add direct downstream tests for the two cited counterexamples and for missing order references. Assert both shared-fact reason codes and recovery/remediation outcomes. The focused suite must demonstrate that existing valid query/refund/dispute behavior remains unchanged.

### AC-04 — boundaries

No new model, scenario, action enum, provider/network call, persistence, UI, P1–P5 policy change, commit, push, or history rewrite. Focused tests, full discovery, official entrypoint, and scope inspection pass.

## Allowed scope

- `src/agentic_payment_experiment/payment_recovery.py`
- `src/agentic_payment_experiment/remediation.py`
- `tests/test_payment_recovery.py`
- `tests/test_remediation.py`
- `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONSUMER_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONSUMER_REPAIR_V1/evidence/EV-*`

## Exclusions

- Do not modify `original_transaction.py`, models, scenario fixtures, P1–P5 implementation, reports/evidence for the rejected P6 task, or presentation/UI.
- Do not make real payment/provider/API calls or introduce a reversal model.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_payment_recovery tests.test_remediation -v` | cited missing-reference cases block; valid behavior remains | AC-01, AC-02, AC-03 |
| VP-02 | `python -m unittest discover -s tests -v` | full suite passes | AC-04 |
| VP-03 | `python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 | AC-04 |
| VP-04 | `git diff --check` and scope review | clean and in scope | AC-04 |

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop for any required change outside the listed files, a new record/model, a scenario fixture, external call, or P1–P5 semantic change.

## Atomic handoff requirement

Do not request Evaluator review until all mandatory VPs have readable EV stdout/stderr
plus core metadata, `REPORT.md` maps AC-01 through AC-04, declares
`executor_state: READY_FOR_REVIEW`, and the workflow validator has no `BLOCKING`
finding. Workspace/change/deviation summaries are recommended but their heading or
layout is not an acceptance gate. Advisory-only formatting differences do not delay
technical review or create another round.
