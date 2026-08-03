# P5 Evidence / Replay runtime-gate repair v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-RUNTIME-GATE-REPAIR-V1
task_name: P5 回放记录最终 Runtime Authorization Gate 裁决
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Repair P5 receipts so their runtime-decision event is derived from the same final P1–P4 execution-gate outcome that determines whether the payment callback may run, rather than from the preliminary `validate_request()` result alone.

## Failed counterexample

`P5_EVIDENCE_REPLAY_V1/evidence/RV-EV-01_runtime_gate_omission.py` proves that P4 can be `MISSING_EVIDENCE` while `_build_replay_case(scenario, result)` has no P4/context fact or payment-gate input. A receipt built from that function cannot distinguish a blocked execution from a preliminary `ALLOW`.

## Acceptance criteria

### AC-01 — receipt binds final gate outcome

The runtime-decision replay event must consume a structured final gate outcome or an equivalent immutable record containing the actual P1/P2/P3/P4 statuses, final decision, callback-executed flag, and reason codes. A bare `validate_request()` result is insufficient. The receipt must preserve the preliminary business decision separately when it differs from the final gate decision.

### AC-02 — P2/P3/P4 failure is faithfully replayed

For otherwise-allowable requests, each of these cases must create a receipt whose replay result is non-ALLOW and whose structured evidence states callback=0:

- P2 binding missing/invalid;
- P3 identity missing/invalid;
- P4 required source missing, including `request.amount`, `request.payee`, or `request.currency`.

A valid fully-bound P1–P4 path must produce `ALLOW` and callback=1. Replay must never convert a blocked gate into `VALID / ALLOW` merely because `validate_request()` allowed the request.

### AC-03 — runner contract and regression

Runner P5 cases must expose preliminary and final gate decisions, gate evidence statuses, and callback execution state as structured fields, without parsing UI text. Existing S01–S13 decisions, P1–P4 gate behavior, lifecycle behavior, and Attack Overlay behavior must remain unchanged.

### AC-04 — boundaries and verification

All focused repair tests, full test discovery, formal entrypoint, and allowed-scope inspection pass. No real payment, network/API call, persistence, signature/hash chain, policy-engine dependency, P6 work, or UI rearchitecture is permitted.

## Allowed scope

- `src/agentic_payment_experiment/trusted_execution/replay.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/trusted_execution/test_replay.py`
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_runner.py`
- `tests/test_presentation.py`

May add this task's `REPORT.md` and evidence triplets only. Do not modify the rejected P5 task artifacts or completed P3/P4 artifacts.

## Exclusions

- No change to P1–P4 domain decisions or payment callback gate semantics.
- No cryptographic integrity, hash chain, external store/service, real payment, network/API, P6 work, or UI redesign.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_replay tests.trusted_execution.test_payment_binding -v` | gate-bound receipt positive/negative cases pass | AC-01, AC-02 |
| VP-02 | `python -m unittest tests.test_runner tests.test_presentation -v` | structured P5 runner fields pass | AC-03 |
| VP-03 | `python -m unittest discover -s tests -v` | all tests pass | AC-04 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6 | AC-03, AC-04 |
| VP-05 | `git diff --check` and scope review | no out-of-scope change | AC-04 |

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if a solution requires modifying P1–P4 behavior, an unlisted file, external state, or an unauthorised operation.
