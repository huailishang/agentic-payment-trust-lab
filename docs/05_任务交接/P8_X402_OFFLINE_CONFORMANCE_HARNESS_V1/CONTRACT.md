# Task Contract

Task ID: `P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P7 has passed and the project now presents six stable business capabilities rather than M/S/project labels. The roadmap enters external validation.

Public x402 documentation provides a real protocol flow:

```text
HTTP request
  -> 402 payment requirement
  -> signed payment payload
  -> facilitator verify / settle
  -> resource response + settlement details
```

Before any testnet or production interaction, the project needs a deterministic offline harness that proves x402 objects can be mapped into the existing protocol-neutral trust and payment facts without bypassing authorization, binding, replay, state-finality or evidence rules.

Primary reference:

- `docs/reference/智能体支付产业动态核验与外部测试路线_20260801.md`
- Coinbase x402 buyer/seller and facilitator documentation linked from that file

## 2. Single objective

Create an offline, fixture-driven x402 conformance harness that maps a bounded x402 request/payment/settlement/resource-delivery flow into existing protocol-neutral facts and deterministically evaluates binding, replay and finality cases. The harness must not make network calls, use wallets or execute real/testnet payments.

## 3. Acceptance criteria

### AC-01 — bounded x402 fixture model

Provide a small, versioned fixture model covering only the fields needed for conformance testing:

- HTTP method and resource path or stable resource identifier;
- payment scheme;
- network;
- asset;
- amount;
- payee/receiving address;
- payment requirement identifier or deterministic requirement digest;
- signed payment payload/proof reference;
- facilitator verification observation;
- facilitator settlement observation;
- resource delivery observation;
- request/payment/original-transaction references and timestamps where applicable.

Fixtures must be synthetic and contain no real secret, private key, customer identity, card data, production credential or real-money transaction.

### AC-02 — protocol-neutral adapter boundary

Implement an x402 adapter that:

- parses/validates only the bounded fixture model;
- maps x402-specific names into existing protocol-neutral authorization, transaction/payment binding, replay and state-observation concepts;
- keeps raw protocol fields as source evidence rather than introducing x402 terminology into the payment business core;
- fails closed on missing required references, malformed enums/types, unsupported scheme/network semantics or contradictory identifiers;
- performs no payment, wallet, signing, settlement, callback or network action.

The adapter must not change existing authorization, payment, trusted-execution, replay, finality or evaluator algorithms.

### AC-03 — six deterministic conformance cases

Provide at least the following offline cases with explicit expected result and reason code/evidence:

1. unchanged requirement and proof bind to the same resource/payment context;
2. changed payee is rejected or blocked;
3. changed amount, network or asset is rejected or blocked;
4. proof reused for another resource/API path is rejected or blocked;
5. duplicate/concurrent reuse of the same proof does not create a second successful delivery fact;
6. facilitator verification/settlement and resource-delivery observations remain separate; settlement success plus delivery failure must not be reported as complete business success, and contradictory terminal observations must be explicit conflict/indeterminate rather than silently selected.

Each case must report a closed status such as `PASS`, `FAIL`, `UNSUPPORTED` or equivalent; success status must be derived from actual evaluator output, not hard-coded presentation metadata.

### AC-04 — evidence and limitations

The harness output must preserve enough evidence to answer:

```text
哪个资源要求付款？
付款要求绑定了什么金额、资产、网络和收款方？
哪个证明被使用？
是否发生重复或跨资源使用？
facilitator观察到了什么？
资源是否交付？
为什么最终判为允许、阻断、冲突、未决或不支持？
```

Documentation must state that an offline fixture pass cannot prove official SDK security, facilitator production safety, merchant correctness, regulatory compliance or mainnet readiness.

### AC-05 — regression and scope boundaries

- Existing P4 trusted-context/runtime-gate tests pass.
- Existing P5 replay tests pass.
- Existing P6 original-transaction/finality/conflict tests pass.
- Full suite passes.
- `run_experiment.py` remains S01–S13 `13/13`, internal baseline `PASS`, AP2 `2/2`, Attack Overlay `6/6`.
- Changes remain within the allowed scope.

## 4. Allowed scope

- `src/agentic_payment_experiment/adapters/x402.py`
- `src/agentic_payment_experiment/x402_conformance.py`
- `src/agentic_payment_experiment/adapters/__init__.py`（仅导出新增适配器时）
- `tests/test_x402_adapter.py`
- `tests/test_x402_conformance.py`
- `samples/protocols/x402/`（仅合成fixture）
- `docs/04_验证体系/x402离线一致性验证方案_v1.md`
- `docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1/REPORT.md`
- `docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1/evidence/EV-*`

## 5. Exclusions

- No external HTTP/API call.
- No Coinbase/CDP account or API key.
- No x402.org testnet facilitator call.
- No wallet creation, signing, faucet, token, gas or blockchain transaction.
- No real/testnet/mainnet funds.
- No new external dependency or copied full x402 SDK/framework.
- No UI or P7 navigation change.
- No scenario-number expansion.
- No modification to existing payment/authorization/identity/binding/context/replay/finality/evaluator business logic.
- No claim that offline conformance equals production security or regulatory approval.
- No commit, push or history rewrite.

## 6. Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_x402_adapter tests.test_x402_conformance -v` | Fixture parsing, fail-closed adapter and six conformance cases pass | AC-01, AC-02, AC-03, AC-04 |
| VP-02 | `python -m unittest tests.trusted_execution.test_context_policy tests.trusted_execution.test_replay tests.trusted_execution.test_original_transaction tests.test_payment_finality tests.test_payment_status_conflict -v` | P4–P6 focused regressions pass | AC-02, AC-03, AC-05 |
| VP-03 | `python -m unittest discover -s tests -v` | Full suite passes | AC-05 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13; internal PASS; AP2 2/2; Attack 6/6; HTML generated | AC-05 |
| VP-05 | task-scoped `git diff --check`, hashes and path review | Clean, baseline unchanged, no unexpected product paths | AC-05 |
| VP-06 | workflow validator | No `BLOCKING` finding | handoff |

Use `python3` with `PYTHONPATH=src` when this environment does not expose `python`.

## 7. Required report evidence

`REPORT.md` must include:

- exact changed files and SHA-256 hashes;
- fixture inventory with synthetic-data statement;
- mapping table from x402 fields to protocol-neutral facts;
- six-case result matrix with expected/actual/reason/evidence;
- explicit statement that no network/API/wallet/payment action occurred;
- AC-01 through AC-05 mapping to EV identifiers;
- raw EV meta/stdout/stderr triplets;
- deviations and unsupported semantics.

## 8. Stop conditions

Stop and report rather than expanding scope if:

- official x402 semantics cannot be represented without changing existing business algorithms;
- implementation requires an external SDK/dependency;
- a case requires a live facilitator, wallet or chain state to be meaningful;
- a fixture field cannot be traced to an official source or explicitly labelled project-local;
- the harness would need to treat facilitator success as complete business success;
- any P4–P7 regression appears.

## 9. Inherited worktree state

P4–P7 product changes, tests, task packets and evidence remain uncommitted because commit/push authorization is false. The Executor must preserve them and attribute only allowed P8 files to this task. The user-directed research document under `docs/reference/` is also inherited context, not a P8 implementation output.

## 10. Authorization

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
network_call: false
real_funds: false
```

A later testnet interaction package may be drafted only after this offline harness passes. It will require an explicit network/API authorization boundary and must remain separate from this task.

## 11. Atomic handoff

Do not request Evaluator review until VP-01 through VP-06 have readable raw evidence, every AC is mapped in `REPORT.md`, `executor_state: READY_FOR_REVIEW` is declared, and the workflow validator reports no `BLOCKING` finding.
