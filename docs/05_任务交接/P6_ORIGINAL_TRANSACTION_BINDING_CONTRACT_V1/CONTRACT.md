# P6 original-transaction binding v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P6-ORIGINAL-TRANSACTION-BINDING-CONTRACT-V1
task_name: P6 原交易绑定统一事实
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Single objective

Provide one protocol-neutral original-transaction binding fact for the existing offline follow-up observations: status query, refund, and dispute. Each must fail closed when it does not refer to the original payment and order; status query must additionally fail closed for a conflicting provider reference. Payment-domain recovery and remediation continue to choose business actions from that fact.

## Scope decision

This v1 deliberately covers only the three follow-up record types the repository already models:

- Query: `PaymentStatusObservation`
- Refund: `RefundRecord`
- Dispute: `DisputeRecord`

`Reversal` is named in the roadmap but has no current model or scenario. It is not silently represented as a refund and is excluded from this slice. A later P6 contract may add it once its domain semantics are defined.

## Acceptance criteria

### AC-01 — one closed verification fact

Trusted Execution exposes one immutable, deterministic original-transaction verification fact (or equivalent closed result) for a declared follow-up action and an existing original `PaymentExecutionRecord`. It records validation status and stable reason codes; it makes no refund, dispute, retry, or lifecycle decision.

The fact rejects unknown action types and missing required references. For all three actions it compares original `payment_id` and `order_id`. For status query it also compares `provider_ref` whenever the original record declares one. A mismatch or missing required reference must never return `VALID`.

### AC-02 — payment-domain consumers use the shared fact

`assess_payment_recovery()` consumes the shared fact for the status observation. `assess_remediation()` consumes it for refund and dispute records. Remove duplicated local original-transaction reference checks rather than maintaining competing rule sets.

Preserve the existing business outcomes: UNKNOWN remains query-first/non-retry; a trusted successful query continues the original payment without a second charge; a mismatched follow-up record is blocked or requires investigation; a fully bound full refund may resolve only economic remediation, never the original failed task.

### AC-03 — adversarial binding coverage

Tests prove each action's valid path and these fail-closed cases:

- Query: wrong payment, wrong order, missing required reference, and conflicting provider reference.
- Refund: wrong payment, wrong order, zero/excess amount, and currency mismatch remain non-resolving.
- Dispute: wrong payment and wrong order remain non-resolving.
- An unsupported follow-up action is invalid, not treated as a known action.

The tests must assert the stable fact/reason codes as well as the downstream recovery or remediation outcome.

### AC-04 — regression and boundaries

Focused tests, full discovery, official experiment entrypoint, and scope inspection pass. P1–P5 pre-payment decisions and gates remain unchanged. The implementation remains deterministic and offline: no real payment, provider call, HTTP/API success inference, persistence, reversal model, hash/signature claim, UI redesign, or new scenario fixture.

## Allowed scope

- `src/agentic_payment_experiment/trusted_execution/original_transaction.py` (new)
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/payment_recovery.py`
- `src/agentic_payment_experiment/remediation.py`
- `tests/trusted_execution/test_original_transaction.py` (new)
- `tests/test_payment_recovery.py`
- `tests/test_remediation.py`
- `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/REPORT.md`
- `docs/05_任务交接/P6_ORIGINAL_TRANSACTION_BINDING_CONTRACT_V1/evidence/EV-*`

## Exclusions

- No change to `models.py`, scenario fixtures, pre-payment P1–P5 gate semantics, or existing public payment statuses.
- No reversal, real provider, network/API call, database/persistence, cryptographic integrity claim, UI/presentation redesign, commit, push, or history rewrite.
- Do not edit prior P3–P5 handoff records or their evidence.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_original_transaction tests.test_payment_recovery tests.test_remediation -v` | shared fact and all valid/adversarial downstream cases pass | AC-01, AC-02, AC-03 |
| VP-02 | `python -m unittest discover -s tests -v` | complete suite passes | AC-04 |
| VP-03 | `python run_experiment.py` | S01–S13 13/13; internal baseline PASS; Attack Overlay 6/6 | AC-02, AC-04 |
| VP-04 | `git diff --check` plus allowed-scope review | no whitespace errors or scope violation | AC-04 |

## Baseline and inherited worktree state

The baseline commit is `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`. Earlier P4/P5 changes and handoff artifacts are intentionally uncommitted because commit authorization is false. Preserve them; do not stage, amend, revert, or fold them into this task. The P6 implementation must be identifiable by allowed paths and its own evidence/report.

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop and return to Evaluator if the implementation needs a new follow-up record schema, scenario fixture, real provider interaction, a P1–P5 semantic change, or any file outside the allowed scope.
