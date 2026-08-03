# P6 payment query finality fact v1 — Executor report

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-PAYMENT-QUERY-FINALITY-FACT-V1
executor_state: READY_FOR_REVIEW
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: SUBMITTED
requested_next_role: Evaluator
```

## Delivered

Added one immutable, protocol-neutral `PaymentQueryFinalityFact` and closed
`PaymentQueryEvidenceStage` enum. It derives only from the original payment,
bound query observation, and recovery result. S12 is `QUERY_CONFIRMED` and
payment-status terminal, while fulfillment, business/user-task success,
reconciliation, settlement, and legal finality all remain explicit `false`.
Unresolved, blocked, conflicting, and invalid input paths fail closed.

The runner now exposes `payment_finality` as a structured S12 result-card
field. No UI parsing or presentation change was made.

## Evidence

| EV | Command | Result |
|---|---|---|
| EV-01 | `python -m unittest tests.test_payment_finality tests.test_runner -v` | 9 tests OK |
| EV-02 | `PYTHONUTF8=1 python -m unittest discover -s tests -v` | 249 tests OK |
| EV-03 | `PYTHONUTF8=1 python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 |
| EV-04 | `git diff --check` + allowed-scope review | exit 0; scope clean |

Each EV has matching stdout/stderr/meta artifacts under `evidence/`. The
UTF-8 setting is an existing Windows test-environment requirement for Chinese
subprocess-output assertions; it is not a code or product behavior change.

## Acceptance mapping

- AC-01: EV-01 verifies closed-stage serialization and unknown enum/input failure.
- AC-02: EV-01 verifies S12, UNKNOWN/PENDING, conflicting observation, and invalid binding boundaries.
- AC-03: EV-01 and EV-03 verify the structured `payment_finality` S12 field without changing recovery decisions.
- AC-04: EV-01 adversarial cases; EV-02 full regression; EV-03 official entrypoint; EV-04 scope/diff check.

## Workspace snapshot

- Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
- Implementation commit: `NONE` (not authorised)
- Preserved: inherited P4/P5/original-P6 uncommitted worktree changes, untouched and not attributed to this task.

## Changed files

- `src/agentic_payment_experiment/payment_finality.py`
- `src/agentic_payment_experiment/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/test_payment_finality.py`
- `tests/test_runner.py`

## Baseline

`baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Deviations

- No product deviation or unresolved acceptance item.
- Full-suite verification uses `PYTHONUTF8=1` solely to preserve existing Windows Chinese-output assertions.
