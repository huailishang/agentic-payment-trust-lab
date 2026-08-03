# P5 runtime-gate repair v1 — Evaluator review

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-RUNTIME-GATE-REPAIR-V1
reviewer_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
verdict: REJECTED
```

## Pre-review checks

- Executor report lacks its EV triplets and report snapshot fields; this is a secondary FIX_IN_PLACE defect.
- Modified product/test files are within the frozen repair scope.
- Independent full regression and formal entrypoint pass, but replay provenance remains the mandatory acceptance boundary.

## Acceptance matrix

Criterion decision: 不通过。

| AC | Verdict | Reason |
|---|---|---|
| AC-01 | FAIL | Receipt has a `RuntimeGateRecord`, but `_run_replay_gate()` constructs a new gate invocation rather than consuming the original action's observed outcome. |
| AC-02 | FAIL | The runtime path always constructs complete P4 sources and a synthetic P3 identity before invoking the gate; P2/P3/P4 failure tests only inject an outcome into a test helper, not the runner receipt path. |
| AC-03 | FAIL | Runner exposes preliminary/final fields, but the reported final gate decision is from a replay-time simulation and local callback, not the payment action that the receipt purports to audit. |
| AC-04 | PASS | `RV-EV-02`: 238 tests / OK. `RV-EV-03`: S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6. `RV-EV-04`: clean diff check. |

## RV-EV-01

- AC: AC-01, AC-02, AC-03
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-01.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-01.stderr.log`

The inspected runtime code shows the defect directly: it hardcodes all seven P4 trusted source paths, constructs `p5-offline-provider` / `p5-offline-executor`, and invokes `execute_with_payment_binding_gate()` with a local callback while building the replay. This proves a new simulation, not a receipt of the original execution observation.

## RV-EV-02

- AC: AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-02.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-02.stderr.log`

## RV-EV-03

- AC: AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-03.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-03.stderr.log`

## RV-EV-04

- AC: AC-04
- Meta: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-04.meta.json`
- Stdout: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-04.stderr.log`

## Final verdict

REJECTED. The failure is semantic: a replay receipt must preserve one observed execution decision, never manufacture a second decision with more favorable evidence. Continuation is `P5-EVIDENCE-REPLAY-OBSERVED-GATE-RECORD-REPAIR-V1`, a bounded repair that requires an execution-time gate observation and prohibits replay-time gate invocation.
