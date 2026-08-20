# Task Contract

Task ID: `P9-WEBSHOP-BUY-NOW-RUNTIME-GATE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P9-B1 已由独立评估者裁决 `PASS`：固定 WebShop pre-Buy-Now 候选能够被纯离线、失败关闭地映射为现有 `Order + TransactionRequest`。

当前仍未解决：

```text
WebShop 准备 Buy Now
        ↓
谁在真正副作用前拦截？
        ↓
如何消费明确授权、订单绑定、Agent / Executor 身份和可信上下文？
        ↓
什么条件下才允许调用下游 checkout callback？
```

P9-B2 只实现这个离线控制点。它不运行 WebShop，也不执行真正的 `click[buy now]`。

Primary references:

- `docs/05_任务交接/P9_WEBSHOP_COMMERCE_ADAPTER_V1/REVIEW.md`
- `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md`
- `docs/03_架构设计/Agent_Trust_Control_Plane_最小领域模型_v1.md`
- `src/agentic_payment_experiment/adapters/webshop.py`
- `src/agentic_payment_experiment/validator.py`
- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/trusted_execution/`

## 2. Single objective

Create one deterministic, offline WebShop Buy Now runtime gate that accepts:

```text
WebShopCommerceAdaptation
+ explicit IntentMandate
+ explicit declared Agent identity
+ explicit PaymentExecutionRecord candidate
+ explicit AgentIdentity / executor references
+ explicit ContextPolicyFact
+ optional ConfirmationRecord / seen request IDs
+ injected checkout callback
        ↓
WebShopBuyNowGateOutcome
```

The gate must:

1. fail closed when the Commerce Adapter output is not ready;
2. add the explicitly supplied declared Agent ID to a copied `TransactionRequest`, without mutating the adaptation;
3. run existing `validate_request(...)` against the explicit mandate and current order;
4. only when the pre-payment result is `ALLOW`, pass the same order/request/execution/identity/context facts into the existing runtime payment-binding gate;
5. call the injected checkout callback exactly once only when the final decision is `ALLOW`;
6. preserve structured pre-payment and runtime-gate evidence;
7. never import or run WebShop.

## 3. Required API

Implement an immutable outcome and one public function, with names equivalent to:

```python
@dataclass(frozen=True)
class WebShopBuyNowGateOutcome:
    decision: Decision
    checkout_executed: bool
    callback_count: int
    callback_result_ref: str | None
    bound_request: TransactionRequest | None
    prepayment_result: ValidationResult | None
    runtime_gate_record: RuntimeGateRecord | None
    reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]


def gate_webshop_buy_now(..., checkout_callback: Callable[[], Any]) \
        -> WebShopBuyNowGateOutcome:
    ...
```

Exact internal helper names may differ, but the observable contract must remain equivalent.

Required limitations:

```text
offline_interception_only
no_webshop_runtime_execution
no_real_buy_now_execution
no_real_payment_or_fulfilment
instruction_is_not_authorization_mandate
checkout_callback_is_injected_test_seam
```

## 4. Acceptance criteria

### AC-01 — explicit facts only

The gate must require explicit inputs for:

- `IntentMandate`;
- declared Agent ID;
- `PaymentExecutionRecord` candidate;
- `AgentIdentity`;
- current provider and executor references;
- `ContextPolicyFact`;
- checkout callback.

It must not derive any of these from `instruction_text`, product title, WebShop reward or page content.

The original `WebShopCommerceAdaptation` and its nested neutral objects must remain unchanged.

### AC-02 — P1 pre-payment validation

The gate must create a copied request with the explicitly supplied declared Agent ID and run existing `validate_request(...)` using:

```text
mandate
bound request
authorized_order = adaptation.order
final_order = adaptation.order
optional confirmation_record
seen_request_ids
```

If `validate_request` returns:

```text
DENY
CONFIRMATION_REQUIRED
INDETERMINATE
```

then:

- the checkout callback is not called;
- no runtime execution callback is reached;
- the final outcome preserves the same non-ALLOW decision;
- reason codes expose the pre-payment block.

### AC-03 — P2 / P3 / P4 runtime gate composition

Only after the pre-payment result is `ALLOW`, call the existing runtime gate with the same bound request and explicit facts:

- order/request/execution continuous binding;
- Agent / executor identity;
- provider and executor references;
- `ContextPolicyFact` and its current value digests;
- injected checkout callback.

Do not duplicate P2/P3/P4 rules in a second WebShop-specific implementation.

The result must preserve an immutable `RuntimeGateRecord` created at the actual callback gate.

### AC-04 — callback side-effect boundary

The callback contract is strict:

```text
final decision == ALLOW
    -> callback exactly once

final decision != ALLOW
    -> callback zero times
```

Required fail-closed cases include:

1. adaptation `ready == false`;
2. missing or blank declared Agent ID;
3. missing mandatory explicit inputs;
4. request denied by amount, currency, merchant, category, expiry or count;
5. confirmation required but missing or stale confirmation;
6. duplicate request ID;
7. execution candidate references another request/order/authority/agent/payee/amount/currency;
8. missing or mismatched executor identity;
9. missing, invalid, stale or value-mismatched context-policy coverage;
10. upstream decision not `ALLOW`;
11. callback raises an exception.

For callback exception:

- do not claim checkout success;
- expose a deterministic failure result or propagate a documented exception;
- never retry the callback automatically.

### AC-05 — realistic WebShop boundary examples

Tests must include at least two explicit mandates against the fixed P9-B1 fixture:

#### Case A — instruction-like restrictive mandate

```text
max_amount < 877.80
allowed category excludes home_furniture
```

Expected:

```text
DENY
callback_count = 0
```

This demonstrates that the console table is not silently accepted merely because WebShop reached Buy Now.

#### Case B — explicit permissive experiment mandate

```text
max_amount >= 877.80
merchant/category/currency/order/authority/agent facts match
P2/P3/P4 facts valid
```

Expected:

```text
ALLOW
callback_count = 1
```

The callback must be a local fake returning a marker such as `simulated-webshop-checkout`.

Also include `CONFIRMATION_REQUIRED` and `INDETERMINATE` cases with zero callbacks.

### AC-06 — dependency and side-effect boundary

Production code must:

- import only main-project modules and Python standard library;
- not import `gym`, `web_agent_site`, `pyserini`, Flask, browser tooling or the fixed WebShop checkout;
- not read/write files, access environment variables, call network or spawn processes;
- not construct or execute a literal WebShop action string;
- not call payment provider, wallet, testnet, fulfilment or UI code;
- not modify `models.py`, existing P1—P6 rule implementations or the Commerce Adapter.

### AC-07 — tests and regressions

Add deterministic tests covering every AC above.

Required validation:

```text
python3 -m unittest tests.test_webshop_runtime_gate -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

The full suite must be at least the 322-test baseline plus new runtime-gate tests. Formal entrypoint must remain 13/13.

### AC-08 — roadmap and handoff consistency

Update factual status only:

```text
P9-A1 PASS
P9-A2 PASS
P9-B1 PASS
P9-B2 this task / READY_FOR_REVIEW
P9-C not started
P9-D not started
P9-E planned after base capabilities
```

The report must explicitly state:

- WebShop runtime was not executed;
- real Buy Now was not executed;
- callback was only an injected local test seam;
- no payment, fulfilment, UI, network, environment, commit or push occurred.

## 5. Allowed scope

- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `src/agentic_payment_experiment/__init__.py`（only export of the new public API）
- `tests/test_webshop_runtime_gate.py`
- `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md`（factual status only）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（factual status only）
- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 6. Exclusions

- 不修改 `models.py`；
- 不修改 P9-B1 adapter、fixture 或 export helper；
- 不修改 `validator.py`、`payment_execution.py` 或 `trusted_execution/` 既有规则；
- 不运行 WebShop、`webshop38`、Flask、浏览器或后台服务；
- 不执行真实或模拟环境中的 `click[buy now]`；
- 不调用 `SimServer.done()`；
- 不实现 Payment / Fulfilment Sidecar；
- 不修改现有 UI，不开始 P9-E；
- 不调用网络、API、LLM、测试网、钱包或真实支付；
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
| VP-01 | happy-path permissive mandate + fake callback | final `ALLOW`, callback exactly once | AC-01—AC-05 |
| VP-02 | restrictive fixture mandate | `DENY`, callback zero | AC-02、AC-05 |
| VP-03 | confirmation and indeterminate matrix | non-ALLOW preserved, callback zero | AC-02、AC-04、AC-05 |
| VP-04 | P2/P3/P4 mismatch matrix | fail closed, callback zero, structured evidence | AC-03、AC-04 |
| VP-05 | callback exception and no-retry check | no false success, callback count one maximum | AC-04 |
| VP-06 | static imports and dynamic side-effect audit | no WebShop/network/file/process/UI dependency | AC-06 |
| VP-07 | runtime-gate tests | all pass | AC-01—AC-06 |
| VP-08 | full regression and formal entrypoint | suite >322; 13/13 | AC-07 |
| VP-09 | task-scoped diff/hash/workflow validator | no scope creep, no commit/push, no BLOCKING | AC-08 |

## 9. Required evidence

For every VP, save complete evidence triplets:

```text
EV-xx.meta.json
EV-xx.stdout.log
EV-xx.stderr.log
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact public API and outcome fields;
- explicit input-source table;
- machine-readable ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE examples;
- callback counts and results;
- P2/P3/P4 mismatch matrix;
- callback exception behavior;
- static dependency and side-effect audit;
- exact changed files and SHA-256;
- full test count and 13/13 entrypoint result;
- explicit no-runtime/no-Buy-Now/no-payment/no-UI/no-network/no-commit/no-push statement;
- AC-01 through AC-08 and VP-01 through VP-09 mappings.

## 10. Stop conditions

Stop and report without broadening scope if:

- the objective requires changing `models.py` or existing trust rules;
- the existing runtime gate cannot consume an explicit execution candidate without semantic distortion;
- implementation would require importing or running WebShop;
- tests would need real Buy Now, network, environment changes, payment or UI;
- explicit Agent, execution or context facts cannot be supplied without inference from natural language or page content.
