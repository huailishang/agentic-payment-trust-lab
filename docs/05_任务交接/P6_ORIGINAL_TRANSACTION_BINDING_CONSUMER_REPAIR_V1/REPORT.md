# P6 original-transaction consumer repair v1 — Executor report

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ORIGINAL-TRANSACTION-BINDING-CONSUMER-REPAIR-V1
executor_state: READY_FOR_REVIEW
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: SUBMITTED
requested_next_role: Evaluator
```

## Repair

Every non-VALID original-transaction fact now blocks its downstream consumer.
Status-query missing provider/reference produces `BLOCKED`, `retry_allowed=false`,
and `investigate_status_observation_binding`. Refund/dispute missing payment/order
references produce `REQUIRED` and `preserve_evidence_and_investigate_remediation_binding`.
Valid status query and full refund behavior remain unchanged.

## Evidence

| EV | Command | Result |
|---|---|---|
| EV-01 | focused recovery/remediation | 18 tests OK |
| EV-02 | full discovery | 241 tests OK |
| EV-03 | experiment entrypoint | S01-S13 13/13; baseline PASS; Attack Overlay 6/6 |
| EV-04 | `git diff --check` | exit 0 |

Each EV has meta/stdout/stderr artifacts under `evidence/`.

No models, fixtures, P1-P5 gates, UI, network/API, commit, or push changed.
Please independently rerun the EV commands and review the two cited missing-reference counterexamples.

## AC mapping

- AC-01: EV-01 verifies missing provider/order queries are `BLOCKED` with no retry.
- AC-02: EV-01 verifies missing payment/order refund records remain `REQUIRED`.
- AC-03: EV-01 covers cited consumer counterexamples and valid regression cases.
- AC-04: EV-02 through EV-04 cover full regression, entrypoint, and diff check.

## Workspace snapshot

- Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
- Implementation commit: `NONE` (not authorised)
- Workspace snapshot: inherited P4/P5 worktree changes remain uncommitted and are not attributed to P6.

## Changed files

- `src/agentic_payment_experiment/payment_recovery.py`
- `src/agentic_payment_experiment/remediation.py`
- `tests/test_payment_recovery.py`
- `tests/test_remediation.py`

## Deviations / unresolved items

- Inherited P4/P5 worktree changes remain uncommitted and are not attributed to P6.
- No product deviation or unresolved acceptance item. The Windows full-suite command uses `PYTHONUTF8=1` only to preserve existing Chinese subprocess output assertions.

## Baseline

`baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Deviations

- None.
