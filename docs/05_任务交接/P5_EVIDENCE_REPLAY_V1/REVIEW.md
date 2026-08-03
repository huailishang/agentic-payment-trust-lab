# P5 Evidence / Replay v1 — Evaluator review

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-V1
reviewer_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
verdict: REJECTED
```

## Pre-review checks

- Executor report is present but its EV triplets and workspace-snapshot fields are absent; this is a FIX_IN_PLACE documentation defect.
- Product scope is within the P5 contract, and no commit/push/API authorization was used.
- Independent regression and formal entrypoint both pass, but passing regression does not prove receipt provenance.

## Acceptance matrix

Criterion decision: 不通过。

| AC | Verdict | Reason |
|---|---|---|
| AC-01 | PASS | `ReplayEvent` has the required fields, typed enums, serialisation, and constructor validation. |
| AC-02 | FAIL | The replay chain has structural checks, but its purported runtime decision is taken from `validate_request()` rather than the P1–P4 payment gate outcome. It cannot expose an invalid/missing P2/P3/P4 fact. |
| AC-03 | FAIL | S09/S10 replay is structured and not parsed from UI, but it records the preliminary business decision, not the final execution-side decision required by the contract. |
| AC-04 | PASS | `RV-EV-02` passes 237 tests; `RV-EV-03` passes S01–S13 13/13, internal baseline, and Attack Overlay 6/6; `RV-EV-04` is clean. |

## RV-EV-01

- AC: AC-02, AC-03
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-01.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-01.stderr.log`

Independent counterexample output shows `p4_status=MISSING_EVIDENCE`, while `_build_replay_case` accepts only `(scenario, result)`, contains neither `context_policy_fact` nor a call to `execute_with_payment_binding_gate`. The receipt builder therefore has no input from which to distinguish a P4-blocked action from an allow path.

## RV-EV-02

- AC: AC-01, AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-02.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-02.stderr.log`

## RV-EV-03

- AC: AC-03, AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-03.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-03.stderr.log`

## RV-EV-04

- AC: AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-04.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-04.stderr.log`

## Final verdict

REJECTED. This is a product-semantics failure, not a report-format failure. Completed artifacts remain immutable. Continuation is the bounded repair task `P5-EVIDENCE-REPLAY-RUNTIME-GATE-REPAIR-V1`, because the P5 roadmap remains the next declared capability and the failing boundary is objective.
