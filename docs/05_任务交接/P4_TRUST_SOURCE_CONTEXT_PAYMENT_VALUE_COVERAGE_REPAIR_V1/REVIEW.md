# P4 Payment-value source coverage repair — Evaluator review

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P4-TRUST-SOURCE-CONTEXT-PAYMENT-VALUE-COVERAGE-REPAIR-V1
reviewer_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
verdict: PASS
```

## Independent review

The previous rejection was reproduced conceptually: only identity/association
paths were covered, so an otherwise valid P4 fact could still execute without
provenance for amount, payee, or currency. This repair closes that exact gap.

`PAYMENT_REQUIRED_SOURCE_PATHS` now requires seven paths. The payment gate
requires a complete, ordered coverage set whose source types and canonical
value digests equal the current mandate, order, and request values. Therefore
removing any one of `request.amount`, `request.payee`, or `request.currency`,
using an untrusted source, or reusing coverage from a different payment yields
`INDETERMINATE` before the callback.

## Pre-review checks

- Workflow validator: PASS before accepting the handoff.
- Authorization: commit, push, history rewrite, and API call are all `false`.
- Scope: PASS; only the seven frozen product/test paths are modified.
- Evidence integrity: PASS; every executor and reviewer evidence label has a metadata/stdout/stderr triplet.

## Acceptance matrix

Criterion decision: 通过。

| AC | Verdict | Independent evidence |
|---|---|---|
| AC-01 | PASS | `RV-EV-01`: focused independent execution passes the three payment-value coverage counterexamples and the valid callback path. `RV-EV-03`: formal runner completes with seven P4 coverage records. |
| AC-02 | PASS | `RV-EV-01`: each missing amount/payee/currency source and digest mismatch is fail-closed with no callback; the valid continuous binding is the only execution path. |
| AC-03 | PASS | `RV-EV-02`: 232 tests / OK. `RV-EV-03`: S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6. `RV-EV-04`: `git diff --check` exit 0; product/test changes stay within the frozen allowed scope. |

## Raw evidence

## RV-EV-01

- AC: AC-01, AC-02
- Meta: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-01.meta.json`
- Stdout: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-01.stderr.log`

## RV-EV-02

- AC: AC-03
- Meta: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-02.meta.json`
- Stdout: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-02.stderr.log`

## RV-EV-03

- AC: AC-01, AC-03
- Meta: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-03.meta.json`
- Stdout: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-03.stderr.log`

## RV-EV-04

- AC: AC-03
- Meta: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-04.meta.json`
- Stdout: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/evidence/RV-EV-04.stderr.log`

- RV-EV-01
  - Command: `python -m unittest tests.trusted_execution.test_payment_binding.PaymentExecutionBindingTests.test_p4_gate_requires_each_payment_value_source_and_current_digest tests.trusted_execution.test_payment_binding.PaymentExecutionBindingTests.test_valid_continuous_binding_is_the_only_path_that_executes -v`
  - Exit code: 0
  - Stdout: `evidence/RV-EV-01.stdout.log` (0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
  - Stderr: `evidence/RV-EV-01.stderr.log` (527 bytes, SHA-256 `a1581ca13856ce307f0e4584310811eb67bd8e9dc9d55a0aae43b0fc3bbe52cd`)
- RV-EV-02
  - Command: `python -m unittest discover -s tests -v`
  - Exit code: 0
  - Stdout: `evidence/RV-EV-02.stdout.log` (0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
  - Stderr: `evidence/RV-EV-02.stderr.log` (38011 bytes, SHA-256 `ea9e53865f3d36bf554fae74920c8592f1094aff20871858439e715f6a51d84d`)
- RV-EV-03
  - Command: `python run_experiment.py`
  - Exit code: 0
  - Stdout: `evidence/RV-EV-03.stdout.log` (1768 bytes, SHA-256 `69db2e6d5954dfe6b3b94f7f27fb914dfd2d945815f62877e6ec3a7dabb6316e`)
  - Stderr: `evidence/RV-EV-03.stderr.log` (0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
- RV-EV-04
  - Command: `git diff --check`
  - Exit code: 0
  - Stdout/Stderr/meta: `evidence/RV-EV-04.*`

## Process correction applied

The handoff had only formatting defects (missing report headings and a
Windows UTF-8 BOM in evidence metadata). They were corrected in place; no new
task or product change was created. The shared workflow validator now accepts
UTF-8 BOM metadata and accepts older evidence packets that provide
`command_display` without a tokenized `command_argv`.

## Deviations / unresolved items

None. No commit, push, history rewrite, or external API call was authorized or
performed.
