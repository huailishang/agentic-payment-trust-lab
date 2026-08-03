# P6 original-transaction binding v1 — Executor report

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ORIGINAL-TRANSACTION-BINDING-CONTRACT-V1
executor_state: EXECUTING
implementation_commit: NONE
executor_verdict: NOT_ISSUED
requested_next_role: Evaluator
```

Added the closed `FollowUpAction` and immutable `OriginalTransactionBindingFact`.
It validates status-query, refund, and dispute records against the original payment
and order; status queries also reject a missing or conflicting provider reference.

`assess_payment_recovery()` now consumes the shared status-query fact.
`assess_remediation()` now consumes the same shared fact for refund/dispute
payment and order references while retaining its existing amount/currency business checks.

Validation: VP-01 18 tests OK; full discovery 241 tests OK; experiment S01-S13
13/13, internal baseline PASS, Attack Overlay 6/6; `git diff --check` exit 0.

No model, scenario, P1-P5 gate, UI, network/API, commit, or push change was made.
