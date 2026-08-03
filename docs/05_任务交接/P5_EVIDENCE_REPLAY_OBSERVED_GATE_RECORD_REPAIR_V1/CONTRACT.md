# P5 observed gate-record repair v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-OBSERVED-GATE-RECORD-REPAIR-V1
task_name: P5 回放只消费执行时门禁观测
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Make P5 receipts consume one immutable, execution-time runtime-gate observation. Replay must never invoke a new payment gate, create substitute P3/P4 evidence, or run a callback in order to manufacture its audit record.

## Failed counterexample

`P5_EVIDENCE_REPLAY_RUNTIME_GATE_REPAIR_V1/evidence/RV-EV-01.*` shows that the rejected repair builds a complete P4 context, synthetic P3 identity, and local callback inside `_run_replay_gate()` during replay construction. That second simulation can differ from the original action and violates receipt provenance.

## Acceptance criteria

### AC-01 — immutable observed gate record

Introduce an immutable structured observation produced at the same runtime point where the experiment invokes the payment gate. It must contain preliminary decision, final decision, P2 binding status/reasons, P3 identity status/reasons, P4 context status/reasons, callback-executed flag, and callback count/result reference. The record must be passed to P5 receipt creation unchanged; replay code may validate it but must not call `execute_with_payment_binding_gate()`.

### AC-02 — no evidence fabrication and exact blocked outcomes

For P2 missing/invalid, P3 missing/invalid, and P4 missing `request.amount`, `request.payee`, or `request.currency`, create the observed record at execution time and verify receipt/replay preserves the corresponding non-ALLOW final decision and callback=0. For one fully valid path, preserve `ALLOW` and callback=1. Tests must prove that receipt creation makes zero additional gate invocations and zero additional callbacks.

### AC-03 — runner presentation is an observation, not re-simulation

The runner must expose the original preliminary decision, observed final gate decision, P2/P3/P4 statuses, callback state, and receipt/replay result as structured fields. It may use the project’s offline callback simulation once as the actual scenario gate point, but replay assembly must only receive that already-produced observation. It must not hardcode full source coverage or create a `p5-offline-*` identity during replay construction.

### AC-04 — regression and boundaries

Focused tests, full test discovery, official entrypoint, and scope inspection pass. Existing P1–P4 business/gate semantics remain unchanged. No real payment, network/API, persistence, signature/hash chain, external policy service, P6 work, or UI redesign.

## Allowed scope

- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/trusted_execution/replay.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/trusted_execution/test_replay.py`
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_runner.py`
- `tests/test_presentation.py`

May add only this task's report/evidence artifacts. Do not alter rejected P5, completed P3/P4 artifacts, or scenario baseline fixtures.

## Exclusions

- No replay-time `execute_with_payment_binding_gate()` call, callback, synthetic identity, or synthetic complete P4 context.
- No change to P1–P4 decision/gate policy, external side effect, cryptographic claim, external service, P6, or UI redesign.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_replay tests.trusted_execution.test_payment_binding -v` | execution-time observation and all P2/P3/P4 negative cases pass | AC-01, AC-02 |
| VP-02 | `python -m unittest tests.test_runner tests.test_presentation -v` | runner shows observed—not resimulated—gate fields | AC-03 |
| VP-03 | `python -m unittest discover -s tests -v` | all tests pass | AC-04 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6 | AC-03, AC-04 |
| VP-05 | `git diff --check` and scope review | no out-of-scope changes | AC-04 |

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if a fix requires a real payment/network/API call, a frozen P1–P4 semantic change, or an unlisted file.
