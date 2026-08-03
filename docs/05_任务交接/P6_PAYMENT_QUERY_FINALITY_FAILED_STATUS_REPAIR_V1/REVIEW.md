# P6 payment query finality FAILED-status repair v1 — Evaluator review

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-PAYMENT-QUERY-FINALITY-FAILED-STATUS-REPAIR-V1
reviewer_role: Evaluator
review_verdict: PASS
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
```

## Pre-review checks

- Task ID, frozen contract, baseline, role, report, and raw EV package match `CURRENT.md`.
- Workflow validator reports no `BLOCKING` finding.
- The attributable repair is limited to the finality classifier and its direct test; inherited uncommitted P4/P5/P6 changes remain distinguishable.
- Commit, push, history rewrite, external API, real payment/retry, model, scenario, runner-schema, and UI changes remain unauthorized and were not observed in this repair.

## Acceptance matrix

| AC | Decision | Executor evidence | Independent evidence | Basis |
|---|---|---|---|---|
| AC-01 | PASS | EV-01 | RV-EV-01, RV-EV-06 | The exact rejected `UNKNOWN -> FAILED / RETRY_CANDIDATE` counterexample is now `QUERY_CONFIRMED`, effective `FAILED`, and payment-terminal; all upper-layer claims remain false. |
| AC-02 | PASS | EV-01, EV-02 | RV-EV-02, RV-EV-06 | PENDING remains unresolved, conflict remains blocked, S12 remains query-confirmed, and inconsistent initial/observed recovery statuses raise `ValueError`. |
| AC-03 | PASS | EV-01, EV-02 | RV-EV-01, RV-EV-02 | The direct trusted-FAILED regression is present and the existing finality/runner boundaries remain green. |
| AC-04 | PASS | EV-03–EV-05 | RV-EV-03–RV-EV-05 | Full 250-test regression, official entrypoint, diff check, offline boundaries, and authorization constraints pass. |

## Independent evidence

### RV-EV-01

- AC: AC-01, AC-03
- Command: `python docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FACT_V1/evidence/RV-EV-01_trusted_failed_query.py`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-01.*`
- Observed: `RETRY_CANDIDATE / FAILED` now yields `QUERY_CONFIRMED / effective_status_terminal=true`.

### RV-EV-02

- AC: AC-02, AC-03, AC-04
- Command: `python -m unittest tests.test_payment_finality tests.test_runner -v`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-02.*`
- Observed: 10 focused tests passed.

### RV-EV-03

- AC: AC-04
- Command: `python -m unittest discover -s tests -v`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-03.*`
- Observed: 250 tests passed.

### RV-EV-04

- AC: AC-04
- Command: `python run_experiment.py`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-04.*`
- Observed: S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6.

### RV-EV-05

- AC: AC-04
- Command: `git diff --check`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-05.*`
- Observed: no whitespace error; line-ending notices are non-blocking.

### RV-EV-06

- AC: AC-01, AC-02
- Command: `python docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-06_finality_boundaries.py`
- Exit code: `0`
- Evidence: `docs/05_任务交接/P6_PAYMENT_QUERY_FINALITY_FAILED_STATUS_REPAIR_V1/evidence/RV-EV-06.*`
- Observed: trusted FAILED is terminal; PENDING and conflict are non-terminal; inconsistent initial/observed status combinations raise `ValueError`; upper-layer claims remain false.

## Final verdict

PASS. The demonstrated finality classification defect is repaired without broadening payment status into retry execution, business success, fulfillment, reconciliation, settlement, or legal finality.

## Next execution package

- Continuation action: next ordered P6 capability from roadmap §18.3 and the P6 Gate.
- Next task ID: `P6-ASYNC-QUERY-STATUS-CONFLICT-FACT-V1`.
- Contract: `docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/CONTRACT.md`.
- Initial state: `CONTRACT_FROZEN / Executor`.
- Reason: the roadmap now requires a minimal offline Async/Query experiment and explicit handling of synchronous, asynchronous, and queried status conflicts before P6 can close.
