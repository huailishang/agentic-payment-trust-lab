# P6 payment query finality FAILED-status repair v1 — Executor report

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-PAYMENT-QUERY-FINALITY-FAILED-STATUS-REPAIR-V1
executor_state: READY_FOR_REVIEW
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: SUBMITTED
requested_next_role: Evaluator
```

## Delivered

Corrected the rejected classification: a trusted, correctly bound `UNKNOWN →
FAILED` query with recovery `RETRY_CANDIDATE / FAILED` is now
`QUERY_CONFIRMED` and terminal only at the payment-status layer. This does not
make a retry execute, and all business, fulfillment, user-task,
reconciliation, settlement, and legal-finality fields remain `false`.

The repair changes only the finality classifier and adds its direct regression.
Blocked/conflicting and UNKNOWN/PENDING paths remain query-blocked/unresolved
and non-terminal; S12 remains unchanged.

## Evidence

| EV | Command | Result |
|---|---|---|
| EV-01 | `python -m unittest tests.test_payment_finality -v` | 7 tests OK, including trusted FAILED regression |
| EV-02 | `python -m unittest tests.test_payment_finality tests.test_runner -v` | 10 tests OK |
| EV-03 | `PYTHONUTF8=1 python -m unittest discover -s tests -v` | 250 tests OK |
| EV-04 | `PYTHONUTF8=1 python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 |
| EV-05 | `git diff --check` and scope review | exit 0; only two repair files attributable |

Each EV has matching `stdout`, `stderr`, and metadata artifacts under
`evidence/`. `PYTHONUTF8=1` is the existing Windows test-environment setting
for Chinese subprocess-output assertions, not a product behavior change.

## Acceptance mapping

- AC-01: EV-01 directly covers the evaluator’s `UNKNOWN → FAILED / RETRY_CANDIDATE` counterexample and verifies `QUERY_CONFIRMED`, `FAILED`, terminal `true`, and all upper-layer flags `false`.
- AC-02: EV-01 retains S12, UNKNOWN/PENDING, blocked conflict, invalid binding, and invalid input boundaries; EV-02 retains runner regression coverage.
- AC-03: EV-01 contains the direct new regression; EV-02 confirms it alongside the existing structured S12 runner test.
- AC-04: EV-03 full regression, EV-04 official entrypoint, EV-05 diff/scope inspection.

## Workspace snapshot

- Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
- Implementation commit: `NONE` (not authorised)
- Preserved: inherited P4, P5, original-transaction P6, and rejected parent-finality changes remain uncommitted and are not attributed to this repair.

## Changed files

- `src/agentic_payment_experiment/payment_finality.py`
- `tests/test_payment_finality.py`

## Baseline

`baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Deviations

- No product deviation or unresolved acceptance item.
- Full-suite verification uses `PYTHONUTF8=1` solely to preserve existing Windows Chinese-output assertions.
