# Task Contract

Task ID: `P9-WEBSHOP-PAYMENT-FULFILMENT-SIDECAR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P9-A1、P9-A2、P9-B1 已通过。P9-B2 及其原因证据修复也已通过独立复核：

```text
WebShop pre-Buy-Now 商品候选
→ Commerce Adapter
→ P1—P4 Runtime Gate
→ 四态决策 + 可解释原因
```

当前缺口是：原始 WebShop 把点击购买直接视为任务结束，不表达支付执行后的状态、状态查询、异步通知、重复付款风险或履约结果。

P9-C1 只建立纯离线 Sidecar，不执行真实支付或履约。

Primary references:

- `docs/05_任务交接/P9_WEBSHOP_RUNTIME_GATE_REASON_EVIDENCE_REPAIR_V1/REVIEW.md`
- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/REVIEW.md`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`
- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `src/agentic_payment_experiment/payment_recovery.py`
- `src/agentic_payment_experiment/payment_status_conflict.py`
- `src/agentic_payment_experiment/lifecycle.py`
- `src/agentic_payment_experiment/remediation.py`
- `src/agentic_payment_experiment/models.py`

## 2. Single objective

Create one deterministic, offline WebShop payment and fulfilment sidecar that consumes:

```text
PASSed WebShopBuyNowGateOutcome
+ P9-B1 Order / TransactionRequest
+ explicit PaymentExecutionRecord
+ explicit FulfillmentRecord
+ optional trusted query status observation
+ optional trusted async status observation
+ optional known payment attempts
        ↓
WebShopPaymentFulfilmentOutcome
```

The sidecar must reuse existing P5/P6/payment-domain functions to produce one structured post-gate result covering:

- initial and effective payment status;
- query recovery result when supplied;
- query/async conflict fact when both are supplied;
- duplicate-payment/retry protection;
- fulfilment and end-to-end task status;
- remediation requirement;
- evidence and reason codes suitable for later M5 evaluation and P9-E trajectory display.

No real payment, retry, status query, async callback, fulfilment, refund or dispute may occur.

## 3. Required API

Implement an immutable result and one public function equivalent to:

```python
@dataclass(frozen=True)
class WebShopPaymentFulfilmentOutcome:
    ready: bool
    initial_payment: PaymentExecutionRecord | None
    effective_payment: PaymentExecutionRecord | None
    query_recovery: PaymentRecoveryResult | None
    status_conflict: PaymentStatusConflictFact | None
    lifecycle: LifecycleResult | None
    retry_allowed: bool
    duplicate_payment_blocked: bool
    reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]


def assess_webshop_payment_fulfilment(
    gate_outcome,
    adaptation,
    mandate,
    payment,
    fulfillment,
    *,
    query_observation=None,
    async_observation=None,
    known_attempts=(),
) -> WebShopPaymentFulfilmentOutcome:
    ...
```

Exact internal names may differ, but the observable contract must remain equivalent.

Required limitations:

```text
offline_sidecar_only
no_real_payment_execution
no_real_status_query_or_async_callback
no_real_fulfilment
no_automatic_payment_retry
no_real_refund_or_dispute
webshop_reward_not_used_as_payment_or_task_success
```

## 4. Acceptance criteria

### AC-01 — gate prerequisite and explicit facts

The sidecar may proceed only when all of the following hold:

```text
gate_outcome.decision == ALLOW
gate_outcome.checkout_executed == true
gate_outcome.callback_count == 1
gate_outcome.runtime_gate_record.final_decision == ALLOW
adaptation.ready == true
Order and TransactionRequest exist
```

For a non-ALLOW or incomplete gate result:

- `ready == false`;
- no effective payment or lifecycle result is produced;
- retry is not allowed;
- explicit reason identifies the failed prerequisite.

The sidecar must not infer payment success from:

- WebShop reward;
- Buy Now availability;
- callback result text;
- product selection;
- natural-language instruction.

All payment and fulfilment records must be explicitly supplied.

### AC-02 — binding and immutable composition

The sidecar must preserve and verify the existing chain:

```text
IntentMandate
→ Order
→ TransactionRequest
→ PaymentExecutionRecord
→ FulfillmentRecord
```

Use existing binding/lifecycle/recovery functions. Do not duplicate their rules.

The input gate outcome, adaptation, payment and fulfilment records must remain unchanged. Any effective-status projection must use an immutable copy.

Binding mismatch must fail closed with:

- no successful task status;
- no automatic retry;
- structured reason/evidence.

### AC-03 — payment status and original-transaction query

Support explicit initial payment status:

```text
SUCCEEDED / FAILED / PENDING / UNKNOWN
```

When a query observation is supplied, call existing `assess_payment_recovery(...)` with the original mandate/request/order and known attempts.

Required behavior:

- trusted query confirms SUCCEEDED → effective payment may become SUCCEEDED;
- query remains PENDING/UNKNOWN → unresolved, retry false;
- trusted FAILED may only become retry candidate if existing recovery rules allow it;
- existing successful or unresolved parallel attempt blocks retry;
- status observation not bound to the original transaction blocks recovery.

The sidecar never performs a retry.

### AC-04 — query and async status convergence

When both query and async observations are supplied:

1. verify both against the original payment using existing original-transaction binding;
2. call existing `derive_payment_status_conflict(...)`;
3. preserve its resolution and reason codes.

Required behavior:

- consistent or monotonic terminal confirmation may determine effective payment status;
- opposite terminal claims, equal-time disagreement or terminal regression must remain conflict/unknown;
- blocked or conflicting evidence must not mark payment, fulfilment or user task as successful;
- retry remains false while status evidence is conflicting or unresolved.

Do not reimplement the P6 conflict state machine.

### AC-05 — fulfilment and task lifecycle

Call existing `assess_lifecycle(...)` using the final effective payment copy and explicit fulfilment record.

Required examples:

```text
payment SUCCEEDED + fulfilment SUCCEEDED
→ task SUCCEEDED
→ remediation NOT_REQUIRED

payment SUCCEEDED + fulfilment FAILED
→ task FAILED
→ remediation REQUIRED

payment SUCCEEDED + fulfilment PENDING
→ task PENDING

payment FAILED
→ task FAILED

payment PENDING / UNKNOWN
→ task PENDING / UNKNOWN
```

Payment success alone must never be reported as fulfilment or user-task success.

P9-C1 does not execute refund/dispute handling. It may expose remediation state from `LifecycleResult`, but P9-C2 handles attack/exception overlays and later remediation scenarios.

### AC-06 — duplicate payment protection

Use the existing recovery/idempotency result to expose:

```text
retry_allowed
duplicate_payment_blocked
```

At minimum test:

1. original payment UNKNOWN/PENDING plus another unresolved attempt → retry false, blocked;
2. another attempt already SUCCEEDED → retry false, blocked;
3. trusted terminal FAILED with an explicit idempotency boundary and no conflicting attempt → retry candidate may be true, but no callback/payment is executed;
4. missing idempotency boundary → retry false.

`retry_allowed=true` means only “offline retry candidate”; it must not invoke any callback or create another `PaymentExecutionRecord`.

### AC-07 — evidence and M5/P9-E consumability

The outcome must expose stable machine-readable reasons for:

- gate prerequisite failure;
- payment binding failure;
- payment recovery status;
- query/async status conflict;
- duplicate-payment block;
- fulfilment/lifecycle result.

Provide a primitive-only `to_dict()` or equivalent serializer suitable for later:

```text
M5 evaluation
P9-E purchase trajectory UI
```

Do not modify M5 or UI in this task.

### AC-08 — dependency and side-effect boundary

Production code must:

- import only main-project modules and Python standard library;
- not import or run WebShop, Flask, browser tooling or checkout code;
- not read/write files, call network, spawn processes or access environment variables;
- not execute payment, retry, status query, async callback, fulfilment, refund or dispute;
- not modify `models.py`, existing payment recovery/status conflict/lifecycle/remediation rules, P9-B1 or P9-B2 code.

### AC-09 — tests and regressions

Add deterministic offline tests covering all ACs and at least these scenarios:

1. gate non-ALLOW blocks sidecar;
2. payment success + fulfilment success;
3. payment success + fulfilment failure;
4. UNKNOWN/PENDING recovered to SUCCEEDED by trusted query;
5. query/async terminal conflict;
6. unresolved query/async state;
7. duplicate successful attempt blocks retry;
8. unresolved parallel attempt blocks retry;
9. terminal failed retry candidate without execution;
10. payment/order/fulfilment binding mismatch.

Required commands:

```text
python3 -m unittest tests.test_webshop_payment_sidecar -v
python3 -m unittest tests.test_payment_recovery tests.test_payment_status_conflict tests.test_lifecycle -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Full suite must exceed the current 337-test baseline. Formal entrypoint must remain 13/13.

### AC-10 — roadmap and handoff

Update factual status only:

```text
P9-A1 PASS
P9-A2 PASS
P9-B1 PASS
P9-B2 PASS
P9-C1 this task / READY_FOR_REVIEW
P9-C2 not started
P9-D not started
P9-E planned after base capabilities
```

The report must explicitly state that all post-payment facts are offline fixtures and that no real WebShop, Buy Now, payment, retry, status query, fulfilment or UI occurred.

## 5. Allowed scope

- `src/agentic_payment_experiment/webshop_payment_sidecar.py`
- `src/agentic_payment_experiment/__init__.py`（only export new public API）
- `tests/test_webshop_payment_sidecar.py`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`（factual status only）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（factual status only）
- `docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 6. Exclusions

- 不修改 `models.py`；
- 不修改 `payment_recovery.py`、`payment_status_conflict.py`、`lifecycle.py`、`remediation.py`；
- 不修改 P9-B1 adapter/fixture/helper；
- 不修改 P9-B2 Runtime Gate 或共享 P1—P6 规则；
- 不运行 WebShop、`webshop38`、Flask、浏览器或后台服务；
- 不执行真实或模拟环境中的 `click[buy now]`；
- 不调用网络、API、LLM、钱包、测试网或支付机构；
- 不自动重试支付；
- 不执行真实履约、退款或争议；
- 不开始 P9-C2、P9-D 或 P9-E；
- 不修改 UI；
- 不安装依赖或修改环境；
- 不 commit、不 push、不 rewrite history。

## 7. Authorization

```yaml
network_call: false
api_call: false
data_download: false
dependency_install: false
create_environment: false
background_process: false
webshop_runtime_execution: false
buy_now_execution: false
payment_or_order_side_effect: false
commit: false
push: false
history_rewrite: false
```

## 8. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | gate prerequisite matrix | non-ALLOW/incomplete gate produces no sidecar lifecycle | AC-01 |
| VP-02 | success/failure fulfilment matrix | lifecycle and task status match existing rules | AC-02、AC-05 |
| VP-03 | query recovery matrix | effective status/retry follow existing recovery rules | AC-03、AC-06 |
| VP-04 | query/async conflict matrix | existing P6 resolution preserved; conflict never implies success | AC-04 |
| VP-05 | duplicate-payment matrix | existing success/unresolved attempt blocks retry | AC-06 |
| VP-06 | evidence and serialization | stable reasons; primitive-only output | AC-07 |
| VP-07 | static/dynamic side-effect audit | no WebShop/network/file/process/payment/UI side effect | AC-08 |
| VP-08 | targeted sidecar tests | all pass | AC-01—AC-08 |
| VP-09 | full regression/formal entrypoint | suite >337; 13/13 | AC-09 |
| VP-10 | scope/hash/workflow validator | no scope creep, no commit/push, no BLOCKING | AC-10 |

## 9. Required evidence

For every VP, save complete triplets:

```text
EV-xx.meta.json
EV-xx.stdout.log
EV-xx.stderr.log
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact public API and outcome fields;
- explicit input-source table;
- machine-readable normal, failure, pending/unknown, conflict and duplicate-payment examples;
- initial/effective payment statuses;
- query recovery and conflict facts;
- lifecycle/task/remediation results;
- retry and duplicate-block decisions;
- proof no callbacks or payment attempts were created;
- dependency/side-effect audit;
- exact changed files and SHA-256;
- test counts and 13/13 formal entrypoint;
- explicit no-WebShop/no-Buy-Now/no-payment/no-retry/no-query/no-fulfilment/no-UI/no-network/no-commit/no-push statement;
- AC-01 through AC-10 and VP-01 through VP-10 mappings.

## 10. Stop conditions

Stop and report without broadening scope if:

- the objective requires changing `models.py` or existing P5/P6/payment-domain rules;
- status convergence cannot be expressed through existing recovery/conflict functions;
- fulfilment interpretation cannot use existing `assess_lifecycle` without semantic distortion;
- implementation would need to create a new payment attempt or perform a callback;
- any test requires WebShop runtime, real Buy Now, network, payment, environment changes or UI.
