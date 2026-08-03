# Evaluator Review

Task ID: `P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1`  
Verdict: `REJECTED`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Review date: `2026-08-01`

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1
verdict: REJECTED
commit_created: false
push_performed: false
api_call_performed: false
```

## 1. Review preflight

- `REPORT.md` declares `executor_state: READY_FOR_REVIEW`.
- VP-01 through VP-06 have readable `EV-*` meta/stdout/stderr triplets, and AC-01 through AC-05 are mapped.
- Executor validator evidence `EV-06` reports no `BLOCKING` finding.
- `CURRENT.md` was still left at `CONTRACT_FROZEN / Executor` despite the complete report package. The Evaluator normalized routing to `READY_FOR_REVIEW / Evaluator`; this is a handoff-state omission, not the product rejection reason.
- Independent validator `RV-EV-00` passed before technical reruns.

## 2. Acceptance decision

| AC | Verdict | Independent evidence | Decision basis |
|---|---|---|---|
| AC-01 bounded x402 fixture model | 通过 | `RV-EV-01`, `RV-EV-05` | The fixture is versioned, explicitly synthetic and contains the required request, requirement, proof, verification, settlement, async, delivery, reference and timestamp fields. |
| AC-02 protocol-neutral adapter boundary | **不通过** | `RV-EV-01`, `RV-EV-07` | Normal and listed negative tests pass, but a malformed list-valued `proof_ref` is accepted when linked references use the same list. The adapter returns `READY` and coerces the list into a string payment ID instead of failing closed. This directly violates the frozen requirement to reject malformed types. |
| AC-03 six deterministic conformance cases | 通过 | `RV-EV-01`, `RV-EV-05` | All six required cases are derived from binding, idempotency, finality, conflict and replay facts and match their expected outcomes. PASS status changes to FAIL when expected output is deliberately changed. |
| AC-04 evidence and limitations | 通过 | `RV-EV-01`, `RV-EV-05` | Output preserves resource, requirement, proof, facilitator, delivery, binding, conflict, replay and reason evidence; offline limitations and no-side-effect claims are explicit. |
| AC-05 regression and scope boundaries | 通过 | `RV-EV-02`, `RV-EV-03`, `RV-EV-04`, `RV-EV-06` | P4–P6 focused tests, full suite, official entrypoint and task-scoped integrity checks pass; HEAD and reported hashes match and no unexpected product path is present. |

## 3. Blocking finding

### B-01 — malformed reference types are silently string-coerced

Contract requirement:

> The adapter fails closed on missing required references, malformed enums/types, unsupported scheme/network semantics or contradictory identifiers.

Observed counterexample (`RV-EV-07`):

```text
malformed_proof_ref_type=list
adapter_status=READY
reason_codes=[]
mapped_payment_id=['proof-as-list']
RESULT=FAIL: malformed reference type was coerced instead of rejected
```

The counterexample assigns the same list object/value to:

```text
payment_proof.proof_ref
facilitator_verification.proof_ref
facilitator_settlement.proof_ref
facilitator_settlement.payment_ref
facilitator_async_observation.payment_ref
resource_delivery.proof_ref
```

Because equality checks still match, the current validation accepts the structure. The root cause is in `src/agentic_payment_experiment/adapters/x402.py`:

- `_required_field_errors()` checks whether a value is empty, but does not require identifier/text fields to be strings;
- later construction uses `str(...)` for IDs and references, converting malformed lists, dictionaries, booleans or numbers into apparently valid identifiers.

This is not a cosmetic validation gap. It weakens the adapter boundary that P8 is intended to establish. External protocol input must not be normalized into trusted local facts before its type is validated.

## 4. Independent evidence summary

### RV-EV-00 — workflow validator

- Exit code: `0`
- Result: no structural blocking finding.

### RV-EV-01 — P8 focused tests

- Command: `env PYTHONPATH=src python3 -m unittest tests.test_x402_adapter tests.test_x402_conformance -v`
- Exit code: `0`
- Result: `Ran 14 tests`; `OK`.

### RV-EV-02 — P4–P6 regressions

- Exit code: `0`
- Result: `Ran 35 tests`; `OK`.

### RV-EV-03 — full suite

- Exit code: `0`
- Result: `Ran 275 tests`; `OK`.

### RV-EV-04 — official entrypoint

- Exit code: `0`
- Result: S01–S13 `13/13`; internal regression `PASS`; AP2 `2/2`; Attack Overlay `6/6`; HTML generated.

### RV-EV-05 — six-case matrix

- Exit code: `0`
- Result: six synthetic cases pass with side effects all false.

### RV-EV-06 — scope and integrity

- Exit code: `0`
- Result: baseline HEAD unchanged; all reported product hashes match; task-scoped diff check and scope review pass.

### RV-EV-07 — malformed reference-type counterexample

- Exit code: `1`
- Result: a list-valued proof reference was accepted as `READY`; AC-02 fails.

## 5. Final decision

`REJECTED`

The offline harness architecture, six target cases, regression results and no-side-effect boundary are substantially correct. However, the central adapter contract requires malformed external types to fail closed. Since the independent counterexample enters protocol-neutral payment facts, P8 cannot receive PASS.

## 6. Continuation

A bounded repair task has been created and frozen:

- Task ID: `P8-X402-STRICT-REFERENCE-TYPE-REPAIR-V1`
- Contract: `docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/CONTRACT.md`
- State: `CONTRACT_FROZEN / Executor`
- Objective: add strict non-empty string validation for bounded identifier/text/reference fields and permanent adversarial regressions, without changing conformance outcomes, fixtures, payment algorithms or external-side-effect boundaries.
