# P5 Evidence / Replay v1 contract

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-V1
task_name: P5 最小证据回放链
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Objective

Add an offline, deterministic receipt/replay model that turns the existing P1–P4 decision inputs and payment execution result into a replayable event chain. A replay must explain who acted, under which authority and transaction references, what decision/reason codes were recorded, and whether evidence is missing—without inferring facts from UI text.

## Baseline and pre-existing worktree

The accepted P4 implementation and its reports are intentionally uncommitted because commit authorization is false. Treat the current P4 product/test diff as the pre-existing implementation baseline; do not revert, reformat, or attribute it to P5. The frozen P4 PASS review is the authoritative acceptance record.

## Acceptance criteria

### AC-01 — closed replay-event record

Provide a typed, serializable replay-event/receipt model with at least: `event_id`, `event_type`, `occurred_at`, `subject_ref`, `agent_ref`, `authority_ref`, `transaction_object_ref`, `payment_ref`, `source_type`, `source_ref`, `decision`, `reason_codes`, and `previous_event_ref`. The model must reject missing required identity/reference fields and unknown event/source/decision values deterministically. `previous_event_ref` may be empty only for the first event. P5 v1 does not claim cryptographic integrity.

### AC-02 — deterministic chain and fail-closed replay

Create/replay a compact S09-class chain that records authority/order/request, runtime decision, and payment execution outcome. Replay must return structured facts, not parse result-card HTML or prose. It must preserve event order and reference links; explain `ALLOW`, `CONFIRMATION_REQUIRED`, and `DENY` from recorded decision/reason codes; explicitly mark missing evidence/references as `INDETERMINATE` or an equivalent structured missing-evidence result; and fail closed for a broken previous-event reference, duplicate event ID, reference mismatch, or missing required event.

### AC-03 — runtime consumption and presentation contract

The offline scenario runner must produce and expose the P5 replay result from structured runtime facts for at least one allow path and one non-allow S09-class path. Existing S01–S13 decisions, lifecycle behavior, P2/P3/P4 gates, and Attack Overlay behavior must not change. The result card may show a compact replay summary, but it cannot become the replay source of truth.

### AC-04 — regression and boundaries

Focused P5 tests, full unit discovery, and `python run_experiment.py` must pass. No real payment, network call, external storage, external policy engine, signature service, blockchain, hash-chain claim, P6 payment-base change, or UI rearchitecture is permitted.

## Allowed scope

May add or modify only:

- `src/agentic_payment_experiment/trusted_execution/replay.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `src/agentic_payment_experiment/result_card.py`
- `tests/trusted_execution/test_replay.py`
- `tests/test_runner.py`
- `tests/test_presentation.py`

May add the executor `REPORT.md` and evidence triplets only under this task directory. Do not modify completed P3/P4 handoff artifacts.

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_replay -v` | receipt schema, chain, and negative replay cases pass | AC-01, AC-02 |
| VP-02 | `python -m unittest tests.test_runner tests.test_presentation -v` | structured runner/result-card integration passes | AC-03 |
| VP-03 | `python -m unittest discover -s tests -v` | all tests pass | AC-04 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13, internal baseline PASS, Attack Overlay 6/6 | AC-03, AC-04 |
| VP-05 | `git diff --check` plus allowed-scope inspection | no out-of-scope product changes | AC-04 |

## Authorization and stop conditions

## Exclusions

- Do not change P1–P4 business decisions, payment callback gates, or completed handoff artifacts.
- Do not add cryptographic tamper proof, hash-chain validation, network/storage integrations, real payment, P6 changes, or UI rearchitecture.

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop and return control to the Evaluator if satisfying an AC requires changing the frozen P1–P4 behavior, expanding beyond the allowed files, adding a cryptographic/non-local dependency, or making a real payment/network/API call.
