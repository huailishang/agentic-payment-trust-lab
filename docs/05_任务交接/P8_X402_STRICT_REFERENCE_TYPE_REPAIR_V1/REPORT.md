# Executor Report

Task ID: `P8-X402-STRICT-REFERENCE-TYPE-REPAIR-V1`
Executor status: `READY_FOR_REVIEW`
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
Implementation commit: `NONE`

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P8-X402-STRICT-REFERENCE-TYPE-REPAIR-V1
executor_state: READY_FOR_REVIEW
commit_created: false
push_performed: false
api_call_performed: false
network_call_performed: false
wallet_created: false
signature_created: false
payment_executed: false
funds_used: false
```

## Workspace snapshot

- Baseline and final HEAD remain `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`.
- The rejected P8 parent implementation and inherited P4–P7 work remain uncommitted and were preserved.
- This repair changes only `adapters/x402.py`, its focused adapter tests and this repair task packet.
- The fixture JSON, x402 conformance decision logic, P7 UI and existing payment/trust algorithms were not changed.
- No network/API call, wallet, signature, payment, commit, push or history rewrite was performed.

## 1. Repair result

The rejected adapter accepted malformed list/dictionary/boolean/integer identifiers because it compared external values first and later converted them with `str(...)`.

The repair now applies this rule before hashing, comparison or neutral-model construction:

```text
valid text field
= actual Python str
+ stripped value is non-empty
```

Results:

```text
None or blank string → x402_required_field_missing:<path>
non-string object    → x402_string_invalid:<path>
valid unsupported string scheme/network → UNSUPPORTED
valid supported fixture → READY
```

No malformed textual external value is converted into a payment identifier, request reference, authority reference, payee, protocol field, delivery reference or evidence field.

## 2. Changed files

| File | Action | SHA-256 | Factual change |
|---|---|---|---|
| `src/agentic_payment_experiment/adapters/x402.py` | modify | `146317c4e54cffd2c7616d5ad0c77086da888141e0549d400ff5ce7a1f8e94a3` | Added strict required-text validation before digest/comparison/model construction; removed textual `str(...)` coercions; made invalid root metadata safe; retained decimal/datetime parsers. |
| `tests/test_x402_adapter.py` | modify | `1e51fdf8db040308d9cc2ebd0aa7cd801e1260cb1d388ee4755936ccbfa7f3c5` | Added RV-EV-07 and malformed list/mapping/boolean/integer/context/delivery/protocol/failure-code regressions plus valid-six-fixture assertion. |
| `evidence/EV-02_rv_ev_07_counterexample.py` | add | `bcb24f6d929b8474ca2ccc51458cc9af6fd33c5b2a8b6f185cb827c0dce6d83c` | Reproduces the exact linked list-valued proof-reference counterexample and asserts no neutral models are created. |
| `evidence/EV-07_scope_check.py` | add | `d4dd363a924ebcb1b7c37e131f47b7efaa869ad260783d7160019dddeaba2a82` | Verifies baseline, parent hashes, repair hashes, whitespace, forbidden imports/coercions and inherited global findings. |
| `REPORT.md` | add | recorded by final `EV-07` | Records repair facts, field inventory, malformed matrix, evidence and boundaries. |

## 3. Strict textual-field inventory

The following required fields are validated as actual non-empty strings before use.

### Root and HTTP

```text
case_id
fixture_version
http_request.method
http_request.resource_ref
http_request.request_ref
```

### Payment requirement

```text
payment_requirement.requirement_id
payment_requirement.requirement_digest
payment_requirement.resource_ref
payment_requirement.scheme
payment_requirement.network
payment_requirement.asset
payment_requirement.payee
```

### Payment proof

```text
payment_proof.proof_ref
payment_proof.requirement_ref
payment_proof.requirement_digest
payment_proof.request_ref
payment_proof.resource_ref
payment_proof.scheme
payment_proof.network
payment_proof.asset
payment_proof.payee
payment_proof.original_transaction_ref
```

### Facilitator verification and settlement

```text
facilitator_verification.status
facilitator_verification.proof_ref
facilitator_verification.requirement_ref
facilitator_settlement.status
facilitator_settlement.proof_ref
facilitator_settlement.payment_ref
facilitator_settlement.original_transaction_ref
facilitator_settlement.provider_ref
```

### Async observation and delivery

```text
facilitator_async_observation.status
facilitator_async_observation.payment_ref
facilitator_async_observation.original_transaction_ref
facilitator_async_observation.provider_ref
resource_delivery.status
resource_delivery.request_ref
resource_delivery.resource_ref
resource_delivery.proof_ref
resource_delivery.delivery_ref
resource_delivery.failure_code when present
```

### Project context and delivery attempts

```text
project_context.user_ref
project_context.agent_ref
project_context.authority_ref
project_context.authority_version
project_context.merchant_ref
project_context.category
delivery_attempts[*].execution_id
delivery_attempts[*].request_ref
delivery_attempts[*].resource_ref
delivery_attempts[*].proof_ref
delivery_attempts[*].status
```

Amounts and timestamps keep their pre-existing dedicated decimal/datetime validation semantics.

## 4. Malformed-type regression matrix

| Input path | Malformed input | Actual status | Path-specific reason | Neutral models |
|---|---|---|---|---|
| `payment_proof.proof_ref` and linked proof/payment refs | `list` | `INVALID` | `x402_string_invalid:payment_proof.proof_ref` plus linked paths | all `None`; attempts empty |
| `payment_requirement.payee` and proof payee | `dict` | `INVALID` | `x402_string_invalid:payment_requirement.payee` | all `None` |
| `payment_requirement.requirement_id` and linked refs | `bool` | `INVALID` | `x402_string_invalid:payment_requirement.requirement_id` | all `None` |
| `payment_requirement.requirement_id` and linked refs | `int` | `INVALID` | `x402_string_invalid:payment_requirement.requirement_id` | all `None` |
| `project_context.agent_ref` | `list` | `INVALID` | `x402_string_invalid:project_context.agent_ref` | all `None` |
| `project_context.authority_ref` | `dict` | `INVALID` | `x402_string_invalid:project_context.authority_ref` | all `None` |
| `delivery_attempts[0].proof_ref` | `dict` | `INVALID` | `x402_string_invalid:delivery_attempts[0].proof_ref` | all `None`; attempts empty |
| `http_request.method` | `list` | `INVALID` | `x402_string_invalid:http_request.method` | all `None` |
| `payment_requirement.scheme` | `dict` | `INVALID` | `x402_string_invalid:payment_requirement.scheme` | all `None` |
| `payment_requirement.network` | `int` | `INVALID` | `x402_string_invalid:payment_requirement.network` | all `None` |
| `resource_delivery.failure_code` | `list` | `INVALID` | `x402_string_invalid:resource_delivery.failure_code` | all `None` |

Blank proof reference still returns the existing `x402_required_field_missing:payment_proof.proof_ref` reason. Valid unsupported string scheme/network still returns `UNSUPPORTED`, not `INVALID`.

## 5. Exact RV-EV-07 rerun

Raw evidence: `EV-02.stdout.log`.

Observed:

```text
malformed_proof_ref_type=list
adapter_status=INVALID
reason_codes=[
  x402_string_invalid:payment_proof.proof_ref,
  x402_string_invalid:facilitator_verification.proof_ref,
  x402_string_invalid:facilitator_settlement.proof_ref,
  x402_string_invalid:facilitator_settlement.payment_ref,
  x402_string_invalid:facilitator_async_observation.payment_ref,
  x402_string_invalid:resource_delivery.proof_ref
]
mandate=None
order=None
request=None
payment=None
settlement_observation=None
async_observation=None
resource_delivery=None
delivery_attempts=()
RESULT=PASS
```

The rejected behavior `READY + mapped_payment_id="['proof-as-list']"` no longer occurs.

## 6. Parent behavior preserved

The following parent P8 artifacts retain their exact hashes:

| File | Preserved SHA-256 |
|---|---|
| `src/agentic_payment_experiment/x402_conformance.py` | `5240369a4620b5339538f62a294564fe2d4cda06c11b5a4aefb00fdb16cc9b2e` |
| `tests/test_x402_conformance.py` | `78f952ec07d6b3a8a90296a001bbaeaef8de96c3ebec34744d115fc72d001526` |
| `samples/protocols/x402/x402_offline_cases_v1.json` | `5e34d70667faf7c2d91e0bf7b70086a7bb106bb552a85989f6f6f12915292153` |
| `src/agentic_payment_experiment/adapters/__init__.py` | `d6ea7127d18c791b51e15e603966ca03e8ed90f3ec7af21ae19ce1f9074e6754` |
| `docs/04_验证体系/x402离线一致性验证方案_v1.md` | `5edd674080d1526aca16bd8370d2bee83123dbcaec68c04cebdc2e271653a9d6` |

The parent six-case matrix remains:

```text
C01 PASS ALLOW
C02 PASS BLOCK
C03 PASS BLOCK
C04 PASS BLOCK
C05 PASS BLOCK
C06 PASS CONFLICT
```

All side-effect flags remain false.

## 7. Validation evidence

Each label has a readable `.meta.json`, `.stdout.log` and `.stderr.log` triplet.

| EV | Validation | Raw result |
|---|---|---|
| `EV-01` | repair-focused adapter and conformance tests | exit `0`; `Ran 19 tests`; `OK` |
| `EV-02` | exact RV-EV-07 linked-list counterexample | exit `0`; `adapter_status=INVALID`; exact path reasons; all models `None`; `RESULT=PASS` |
| `EV-03` | P4–P6 focused regressions | exit `0`; `Ran 35 tests`; `OK` |
| `EV-04` | full suite | exit `0`; `Ran 280 tests`; `OK` |
| `EV-05` | official experiment entrypoint | exit `0`; S01–S13 `13/13`; internal baseline `PASS`; AP2 `2/2`; Attack `6/6` |
| `EV-06` | parent six-case matrix | exit `0`; `case_count=6`; `all_pass=true`; side effects all false |
| `EV-07` | task scope, parent-hash preservation and integrity | exit `0`; `REPAIR_SCOPE_RESULT=PASS` |
| `EV-08` | workflow validator | exit `0`; `OK: v2 routing and required artifacts are structurally valid` |

Evidence output hashes for EV-01 through EV-06:

| EV | stdout SHA-256 | stderr SHA-256 |
|---|---|---|
| EV-01 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `083c68264eec4f2c49721f07ed634c51de7321e3208cf652f62e5d4cda2f4067` |
| EV-02 | `ce094da86abd87d00b7d90dfd6fdbc42bd233b3850442216b26c15c363089704` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| EV-03 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `ace9acda69da4a45c73a93c6cc8a205849fffabf72c1dd342beffad039a060c9` |
| EV-04 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `9f3ef412a5dad010a52663b58feef7b0514a1351560903d448ff8459b38a7668` |
| EV-05 | `82fb3f51147e6ef6f5a4952db9e94ca4ac0eec9ab149524e4ab97353bcd0d81b` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| EV-06 | `fdba8bfc5bda97e921727e627c248f8bf87ee6875d88a5fd029a9a8eda7ff649` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## 8. Acceptance criteria mapping

| AC | Executor result | Evidence |
|---|---|---|
| AC-01 strict textual-field validation | implemented before hashing/comparison/model construction for the full bounded field inventory | EV-01, EV-02, EV-07 |
| AC-02 path-specific fail-closed | malformed values return `INVALID`, exact path reason and no neutral models | EV-01, EV-02 |
| AC-03 permanent adversarial regressions | list proof ref, map payee, bool/int ID, context refs, delivery attempts, protocol text, six valid fixtures and unsupported strings covered | EV-01, EV-02 |
| AC-04 no scope creep | fixture/conformance/UI/payment/trust hashes preserved; no dependency/network/wallet/payment behavior | EV-06, EV-07 |
| AC-05 regressions and evidence | focused 19, P4–P6 35, full 280, official entrypoint, six-case matrix, scope and workflow validation pass | EV-01 through EV-08 |

## 9. No external side effects

```yaml
network_call: false
api_call: false
wallet_created: false
signature_created: false
payment_executed: false
testnet_or_mainnet_used: false
real_or_test_funds_used: false
resource_delivery_callback_executed: false
```

## 10. Deviations and inherited state

- The contract examples use `python`; this environment exposes `python3`, so validation uses `env PYTHONPATH=src python3 ...`.
- A batch evidence-wrapper invocation was affected by local shell path parsing; no test ran in that failed wrapper attempt. Every final EV was captured with an explicit absolute path and exit `0`.
- Global `git diff --check` still reports inherited historical evidence whitespace outside this repair. Repair files are checked independently and recorded by EV-07.
- P4–P7 and the rejected P8 parent remain uncommitted because commit/push authorization is false.
