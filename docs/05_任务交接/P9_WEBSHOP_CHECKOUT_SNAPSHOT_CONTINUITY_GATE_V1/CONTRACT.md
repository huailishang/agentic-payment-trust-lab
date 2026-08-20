# Task Contract

Task ID: `P9-WEBSHOP-CHECKOUT-SNAPSHOT-CONTINUITY-GATE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P9-C1 支付与履约 Sidecar 已通过。P9-C2 的第一组外部环境异常是：

```text
用户选择商品时的订单
        ↓
页面继续变化
        ↓
结账时价格、商品、选项、商户、收款方或币种已经变化
```

现有 WebShop Runtime Gate 只接收一个 `WebShopCommerceAdaptation`，并把同一个 `Order` 同时作为：

```text
authorized_order
final_order
```

因此它不能表达“已选择订单快照”和“结账时最终订单快照”的差异。

主项目已经存在成熟的 `order_validation.py`：

- 金额、商品、选项、数量等变化 → `CONFIRMATION_REQUIRED`；
- 商品范围越界 → `DENY`；
- order id、merchant、currency、payee 等不可可靠比较或结构变化 → `INDETERMINATE`；
- 无变化 → 继续后续 P2—P4 Runtime Gate。

本任务只把这套现有规则接入 WebShop Runtime Gate，不复制订单比较规则。

## 2. Single objective

Extend the offline WebShop Buy Now gate so it can optionally consume:

```text
authorized WebShopCommerceAdaptation
+ final/current WebShopCommerceAdaptation
        ↓
existing validate_request / validate_order
        ↓
only unchanged and otherwise valid order may reach the injected checkout callback
```

The existing one-adaptation API behavior must remain backward compatible.

## 3. Required API behavior

Add one optional keyword-only input equivalent to:

```python
def gate_webshop_buy_now(
    adaptation,
    mandate,
    declared_agent_id,
    execution_candidate,
    agent_identity,
    current_provider_ref,
    current_executor_instance_ref,
    context_policy_fact,
    checkout_callback,
    *,
    current_credential_ref=None,
    confirmation_record=None,
    seen_request_ids=(),
    authorized_adaptation=None,
) -> WebShopBuyNowGateOutcome:
    ...
```

Exact naming may differ, but observable behavior must be equivalent.

Interpretation:

```text
adaptation            = current/final checkout snapshot
authorized_adaptation = earlier selected/authorized snapshot
```

When `authorized_adaptation is None`, preserve existing P9-B2 behavior by using the current adaptation as both snapshots.

## 4. Acceptance criteria

### AC-01 — optional authorized snapshot and backward compatibility

When `authorized_adaptation` is omitted:

- all existing P9-B2 decisions and callback counts remain unchanged;
- current passing ALLOW case still invokes exactly one injected callback;
- all existing DENY / CONFIRMATION_REQUIRED / INDETERMINATE cases still invoke zero callbacks;
- public API remains importable from the same module/package surface.

When supplied, `authorized_adaptation` must be ready and contain an Order and TransactionRequest. Missing or incomplete authorized snapshot must fail closed with a stable reason and zero callback.

### AC-02 — reuse existing order validation

Use the existing path:

```text
validate_request(...)
→ validate_order(...)
```

with:

```text
authorized_order = authorized_adaptation.order
final_order      = adaptation.order
request          = current adaptation payment_request projected with declared agent_id
```

Do not implement a separate WebShop price/item comparison state machine.

Preserve the existing `ValidationResult` decision, issues, evidence and order differences in `prepayment_result`.

### AC-03 — confirmation-required checkout changes

At minimum cover deterministic offline cases where the same selected product/order remains comparable but the final snapshot changes:

1. unit price and total increase;
2. unit price and total decrease;
3. selected option changes while total is unchanged;
4. quantity and total change;
5. item name or item content changes;
6. fulfilment terms change.

Expected:

```text
decision = CONFIRMATION_REQUIRED
checkout_executed = false
callback_count = 0
runtime_gate_record = null
prepayment_result preserves existing order difference reason/evidence
```

The gate must not automatically refresh authorization or synthesize user confirmation.

### AC-04 — indeterminate or denied hard changes

At minimum cover:

| Change | Expected existing decision |
|---|---|
| different ASIN causing order_id mismatch | INDETERMINATE |
| merchant changes | INDETERMINATE |
| payee changes | INDETERMINATE |
| currency changes | INDETERMINATE |
| final category outside mandate | DENY |
| missing authorized snapshot object | INDETERMINATE or equivalent fail-closed non-ALLOW |

All cases must produce zero callback.

Do not weaken the decision returned by existing order validation.

### AC-05 — unchanged snapshot continues to P1—P4 runtime gate

For a canonical unchanged authorized/current pair:

- order validation produces no blocking decision;
- existing P1 authorization, P2 execution binding, P3 identity and P4 context checks still run;
- final `ALLOW` invokes exactly one injected callback;
- a P2, P3 or P4 mismatch still blocks with zero callback and preserves existing reason codes.

Order continuity must be a new prerequisite, not a replacement for P1—P4.

### AC-06 — deterministic WebShop anomaly matrix

Add one machine-readable offline fixture or deterministic test matrix covering at least:

```text
unchanged
price_up
price_down
option_changed
quantity_changed
product_changed
merchant_changed
payee_changed
currency_changed
category_out_of_scope
```

The matrix must expose:

- baseline and final order refs/versions;
- expected and actual decision;
- callback count;
- reason codes;
- order difference codes;
- explicit `no_real_buy_now` and `no_real_payment` limitations.

This matrix is intended for later P9-D/M5 consumption. It must not execute WebShop.

### AC-07 — side-effect boundary

Production code must not:

- import or run WebShop, Flask, browser tooling or checkout environment code;
- read/write files, call network, spawn processes or access environment variables;
- execute real Buy Now, payment, status query, fulfilment, refund or dispute;
- modify the authorized or final adaptations, mandate, execution candidate or context facts;
- perform callback more than once.

The only callback remains the existing injected local test seam and may run only after all order/P1—P4 checks return final `ALLOW`.

### AC-08 — regressions and handoff

Required commands:

```text
python3 -m unittest tests.test_webshop_runtime_gate -v
python3 -m unittest tests.test_order_validation tests.test_validator -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Expected:

```text
WebShop Runtime Gate targeted tests > current count and all PASS
full suite > 366 and all PASS
formal entrypoint 13/13 PASS
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact API change;
- anomaly matrix results;
- proof existing one-snapshot behavior is unchanged;
- proof non-ALLOW cases invoke zero callback;
- changed files and SHA-256;
- complete EV triplets;
- AC-01 through AC-08 mapping;
- explicit no-WebShop/no-Buy-Now/no-payment/no-network/no-environment/no-commit/no-push statement;
- workflow validator with no `BLOCKING` finding.

## 5. Allowed scope

- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `tests/test_webshop_runtime_gate.py`
- `samples/external/webshop/checkout_snapshot_anomalies_v1.json`（optional machine-readable matrix）
- `scripts/validation/webshop/run_checkout_snapshot_anomalies.py`（optional deterministic runner）
- `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md`（factual status only）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（factual status only）
- `docs/05_任务交接/P9_WEBSHOP_CHECKOUT_SNAPSHOT_CONTINUITY_GATE_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_CHECKOUT_SNAPSHOT_CONTINUITY_GATE_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 6. Exclusions

- 不修改 `order_validation.py`、`validator.py` 或其业务规则；
- 不修改 Commerce Adapter、Sidecar、P1—P6 共享能力；
- 不执行真实 WebShop 或 `click[buy now]`；
- 不进入支付、履约、退款、争议或状态查询；
- 不实现页面 prompt injection；该项留给后续 P9-C2 切片；
- 不实现个人信息最小化；
- 不开始 P9-D 或 P9-E UI；
- 不安装依赖、不创建环境；
- 不调用网络、API、LLM、钱包或测试网；
- 不 commit、不 push、不 rewrite history；
- 不清理工作区继承改动。

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
| VP-01 | optional authorized snapshot | omitted path unchanged; malformed snapshot fails closed | AC-01 |
| VP-02 | existing order-rule reuse audit | no duplicated comparison rules | AC-02 |
| VP-03 | confirmation matrix | price/options/quantity/content/terms changes require confirmation | AC-03 |
| VP-04 | hard-change matrix | product/merchant/payee/currency/category produce existing non-ALLOW decisions | AC-04 |
| VP-05 | unchanged + P1—P4 regressions | unchanged can ALLOW once; trust mismatches remain zero callback | AC-05 |
| VP-06 | machine-readable anomaly matrix | stable expected/actual/reasons/differences/limitations | AC-06 |
| VP-07 | static/dynamic side-effect audit | no external or payment side effect | AC-07 |
| VP-08 | targeted/full/formal/workflow | all expected counts pass; validator no BLOCKING | AC-08 |

## 9. Stop conditions

Stop and report without broadening scope if:

- current Adapter output cannot represent two comparable snapshots without modifying Adapter semantics;
- reuse of existing order validation would require changing its rules;
- backward compatibility cannot be retained without redesigning the public gate API;
- any test requires WebShop runtime, network, environment changes or real Buy Now;
- unrelated inherited workspace changes prevent objective validation.
