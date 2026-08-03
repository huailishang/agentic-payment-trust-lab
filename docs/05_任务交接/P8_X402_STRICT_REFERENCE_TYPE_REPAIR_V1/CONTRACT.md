# Task Contract

Task ID: `P8-X402-STRICT-REFERENCE-TYPE-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Rejected parent task

Parent task:

- `P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1`
- Review: `docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1/REVIEW.md`
- Failed criterion: `AC-02 protocol-neutral adapter boundary`

Independent counterexample `RV-EV-07` proved that a list-valued `payment_proof.proof_ref` is accepted when all linked references carry the same list. The adapter returns `READY` and converts the list into a string payment ID.

## 2. Single objective

Make every bounded x402 identifier, reference and text field type-safe before normalization: required textual fields must be non-empty strings, malformed lists/dictionaries/tuples/booleans/numbers must produce `X402AdaptationStatus.INVALID` with a path-specific reason, and no malformed external value may enter protocol-neutral payment facts through `str(...)` coercion.

## 3. Acceptance criteria

### AC-01 — strict textual-field validation

Before identifier comparison, hashing or model construction, validate all required textual fields in the bounded fixture, including:

- root `case_id` and `fixture_version`;
- HTTP method, resource reference and request reference;
- payment requirement ID, digest, resource, scheme, network, asset and payee;
- payment proof ID/reference, requirement reference/digest, request/resource references, scheme, network, asset, payee and original-transaction reference;
- facilitator verification status and references;
- facilitator settlement status, proof/payment/original-transaction/provider references;
- async status, payment/original-transaction/provider references;
- resource-delivery status and request/resource/proof/delivery references;
- project-context user, agent, authority, authority-version, merchant and category references;
- delivery-attempt execution/request/resource/proof references and status;
- optional textual `failure_code` when present.

A valid field must be an actual `str` whose stripped value is non-empty. Do not accept booleans, integers, decimals, lists, tuples, sets, mappings or other objects by string conversion.

Datetime and decimal handling retain their existing dedicated validation semantics.

### AC-02 — path-specific fail-closed results

Malformed textual values must return:

```text
status = INVALID
reason code identifies the exact path
no mandate/order/request/payment/status/delivery model is constructed
```

Use one stable reason convention, for example:

```text
x402_string_invalid:payment_proof.proof_ref
```

or an equivalent deterministic path-specific code. Missing/blank-string behavior may retain the existing `x402_required_field_missing:<path>` convention.

### AC-03 — permanent adversarial regressions

Add focused tests that independently cover at least:

1. list-valued linked `payment_proof.proof_ref` counterexample from `RV-EV-07`;
2. mapping-valued payee shared by requirement and proof;
3. boolean or integer requirement/reference ID;
4. list/dictionary project-context identity or authority reference;
5. malformed delivery-attempt reference;
6. malformed protocol text field such as method, scheme or network;
7. valid six fixtures remain unchanged;
8. valid but unsupported string scheme/network still returns `UNSUPPORTED`, not `INVALID`.

Tests must assert the malformed path reason and that neutral models remain `None`.

### AC-04 — no scope creep

- Do not change the six fixture cases or expected outcomes.
- Do not modify x402 conformance decision ordering, duplicate handling, finality/conflict logic, replay logic or side-effect record.
- Do not modify existing payment, authorization, identity, trusted-context, replay, finality or evaluator algorithms.
- Do not add dependencies, network calls, wallets, signatures or payment behavior.

### AC-05 — regressions and evidence

- Repair-focused adapter/conformance tests pass.
- P4–P6 focused regressions pass.
- Full suite passes.
- `run_experiment.py` remains S01–S13 `13/13`, internal `PASS`, AP2 `2/2`, Attack `6/6`.
- Parent six-case matrix remains six passing cases with all side-effect flags false.
- Task-scoped integrity and workflow validation pass.

## 4. Allowed scope

- `src/agentic_payment_experiment/adapters/x402.py`
- `tests/test_x402_adapter.py`
- `tests/test_x402_conformance.py` only if an existing public result contract needs a regression assertion; otherwise do not modify
- `docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/evidence/EV-*`

## 5. Exclusions

- No fixture JSON modification.
- No `x402_conformance.py` decision change.
- No UI or P7 navigation change.
- No official SDK, external dependency, network/API call, wallet, signing, testnet/mainnet or funds.
- No real payment or resource-delivery side effect.
- No commit, push or history rewrite.

## 6. Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_x402_adapter tests.test_x402_conformance -v` | Original 14 tests plus strict-type regressions pass | AC-01, AC-02, AC-03, AC-04 |
| VP-02 | dedicated counterexample script/test covering `RV-EV-07` | list-valued linked proof reference returns `INVALID`, path-specific reason, neutral models `None` | AC-01, AC-02, AC-03 |
| VP-03 | `python -m unittest tests.trusted_execution.test_context_policy tests.trusted_execution.test_replay tests.trusted_execution.test_original_transaction tests.test_payment_finality tests.test_payment_status_conflict -v` | P4–P6 regressions pass | AC-04, AC-05 |
| VP-04 | `python -m unittest discover -s tests -v` | Full suite passes | AC-05 |
| VP-05 | `python run_experiment.py` | S01–S13 13/13; internal PASS; AP2 2/2; Attack 6/6 | AC-05 |
| VP-06 | parent six-case matrix | six results remain PASS; no side effects | AC-04, AC-05 |
| VP-07 | task-scoped diff/hash/path check and workflow validator | baseline unchanged, clean allowed scope, no `BLOCKING` finding | AC-04, AC-05 |

Use `python3` with `PYTHONPATH=src` when this environment does not expose `python`.

## 7. Required report evidence

`REPORT.md` must include:

- exact changed files and SHA-256 hashes;
- textual-field inventory covered by strict validation;
- malformed-type matrix with path, input type, expected/actual status and reason;
- explicit rerun of the exact `RV-EV-07` counterexample;
- confirmation that valid fixtures and valid unsupported string semantics are unchanged;
- AC-01 through AC-05 mapping to raw EV triplets;
- explicit no-network/no-wallet/no-payment statement;
- deviations and inherited-worktree statement.

## 8. Stop conditions

Stop rather than expanding scope if:

- repair requires changing protocol-neutral business models;
- valid fixture behavior or six expected outcomes would change;
- a field requires an ambiguous coercion rule rather than strict string validation;
- any existing P4–P8 regression appears;
- implementation requires fixture, network or dependency changes.

## 9. Inherited worktree state

P4–P7 and the rejected P8 parent implementation remain uncommitted because commit/push authorization is false. Preserve all inherited work. Attribute only the strict-type repair files and new repair task packet to this task.

## 10. Authorization

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
network_call: false
real_funds: false
```

## 11. Atomic handoff

Do not request Evaluator review until VP-01 through VP-07 have readable evidence triplets, AC-01 through AC-05 are fully mapped in `REPORT.md`, `executor_state: READY_FOR_REVIEW` is declared, and the workflow validator reports no `BLOCKING` finding.
