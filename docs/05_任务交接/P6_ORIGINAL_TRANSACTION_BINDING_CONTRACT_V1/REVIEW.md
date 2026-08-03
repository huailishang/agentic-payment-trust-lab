# P6 original-transaction binding v1 — Evaluator review

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ORIGINAL-TRANSACTION-BINDING-CONTRACT-V1
reviewer_role: Evaluator
review_verdict: REJECTED
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
```

## Pre-review checks

| Check | Result | Basis |
|---|---|---|
| Contract frozen | yes | `CONTRACT.md` states `CONTRACT_FROZEN`. |
| Scope / authority | yes | Product changes are within the listed P6 files; no commit, push, API, or real payment observed. |
| Executor evidence | no | `REPORT.md` has no EV triplets or required report fields; this is a `FIX_IN_PLACE` handoff defect, not the rejection reason. |
| Independent reproduction | yes | RV-EV-01 and RV-EV-02. |

## Acceptance matrix

| AC | Decision | Executor EV | Independent evidence | Specific basis |
|---|---|---|---|---|
| AC-01 | 通过 | unavailable | RV-EV-02 | `verify_original_transaction()` returns non-VALID facts for the tested bad references. |
| AC-02 | 不通过 | unavailable | RV-EV-01 | Consumers ignore some non-VALID fact reasons and proceed as if the follow-up were valid. |
| AC-03 | 不通过 | unavailable | RV-EV-01, RV-EV-02 | Existing tests assert the fact but omit the downstream missing-provider and missing-reference cases. |
| AC-04 | 不通过 | unavailable | RV-EV-01 | A mandatory fail-closed acceptance fact fails; broad regression cannot override it. |

## Independent evidence

### RV-EV-01

- Meta: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-01.meta.json`
- Stdout: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-01.stderr.log`
- Result: exit code 1 (expected assertion failure). A status query with the original provider reference removed returned `RECOVERED / continue_with_original_payment`; a refund with `payment_id=None` returned `RESOLVED / economic_remediation_completed_by_full_refund`.

### RV-EV-02

- Meta: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-02.meta.json`
- Stdout: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/RV-EV-02.stderr.log`
- Result: 18 focused tests passed, demonstrating the suite missed the consumer-level counterexamples above.

## Blocking finding

`verify_original_transaction()` produces `original_transaction_provider_ref_missing` and `original_transaction_required_reference_missing`, but `assess_payment_recovery()` maps neither to a blocking issue. `assess_remediation()` checks only mismatch reason codes, so a missing original-transaction reference can still reach the successful full-refund branch. This violates AC-02 and AC-03.

## Final verdict

REJECTED.

The minimal repair is isolated to downstream consumption of the existing fact and regression tests. It must not modify the frozen P6 objective, models, scenarios, or P1–P5 behavior.

## Next execution package

- Continuation action: bounded repair task.
- Next task ID: `P6-ORIGINAL-TRANSACTION-BINDING-CONSUMER-REPAIR-V1`.
- Next contract: `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONSUMER_REPAIR_V1/CONTRACT.md`.
- Initial state: `CONTRACT_FROZEN / Executor`.
- Executor-ready check: one observable objective, narrow allowed files, explicit counterexamples, atomic ACs, validation commands, and no missing human authority.
