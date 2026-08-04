# Next Capability Slice — Conditional Freeze

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`  
Task kind: `capability_experiment`  
State: `CONDITIONAL_NOT_FROZEN`  
Project map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Slice task: `T10`  
Trace profile: `WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1`

## 1. 前置条件

```text
prerequisite = measurement adapter accepted
runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE
before hash = TBD_AFTER_ADAPTER_ACCEPTANCE
target hash = TBD_AFTER_ADAPTER_ACCEPTANCE
non-trace projection hash = TBD_AFTER_ADAPTER_ACCEPTANCE
state = CONDITIONAL_NOT_FROZEN
```

在 Evaluator 独立接受阶段 A 的 runner 和重新冻结的 `0/12 VALID` BEFORE 前：

- 不得创建本任务 `CONTRACT.md`；
- 不得进入 `CONTRACT_FROZEN`；
- 不得修改 T10 产品 outcome；
- 当前旧 runner hash `a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4` 只能作为阶段 A 输入基线，不能作为阶段 B runner。

## 2. 单一产品变量

前置条件满足后，本 slice 只允许：

> 在 `gate_webshop_buy_now` 的 known-payment duplicate preflight `BLOCKED` 返回中，让 `WebShopBuyNowGateOutcome` 直接携带一条 `PRODUCT_OBSERVED`、profile 为 `WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1` 的权威轨迹。

不得同时修改 runner、trace validator 或项目指标计算。

## 3. BEFORE / AFTER

### BEFORE

由“阶段 A 已接受 runner + 旧产品行为”生成：

```text
T10 product_trace_status = NOT_AVAILABLE
decision = DENY
callback_count = 0
known_payment_attempt_preflight_status = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
```

### AFTER

由“同一阶段 A runner + 仅 T10 产品 trace”生成：

```text
T10 product_trace_status = VALID
decision = DENY
callback_count = 0
known_payment_attempt_preflight_status = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
```

唯一预期收益是 T10 产品轨迹从 `NOT_AVAILABLE` 变为 `VALID`。

## 4. T10 事件序列

```text
1 AUTHORITY_RECORDED
2 ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
3 REQUEST_RECORDED [CURRENT_REQUEST]
4 ACTION_RECORDED [GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE]
5 ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
6 PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
7 KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
8 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
9 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
10 RESULT_RECORDED [FINAL_OUTCOME]
```

## 5. 双 Payment 关系

```text
CURRENT_PAYMENT_CANDIDATE
payment_ref = GovernedPaymentAction.payment_ref
payment_ref = execution_candidate.payment_id

HISTORICAL_SUCCEEDED_PAYMENT
payment_ref ∈ KnownPaymentAttemptPreflightFact.related_attempt_refs
status = SUCCEEDED

两个 payment ref 允许不同
两个角色都必须通过现有 fact 关系闭合到 current request
```

一致性按 `(entity_type, entity_role)` 校验，不得要求两个 Payment ref 相同。

## 6. 稳定引用

- native ID 使用 `<type>:<id>[:<version>]`；
- `RuntimeGateRecord` 使用 `runtime-gate-record-ref/v1 + to_dict()` canonical hash；
- `GovernedActionBindingFact`、`KnownPaymentAttemptPreflightFact` 使用各自 `to_dict()` canonical hash；
- `WebShopBuyNowGateOutcome` RESULT ref 使用排除 `authoritative_trace` 的 outcome projection，避免循环 hash。

## 7. 守护线

阶段 B 合同冻结时至少继承：

```text
重复或禁止副作用 = 0/12
callback match = 12/12
false refusal = 0/6
missed confirmation = 0/2
forbidden state write = 0/2
formal entry = 13/13
full tests >= 阶段 A accepted baseline
其余 11 项非 trace 业务投影 hash 完全不变
```

## 8. 回滚条件

- runner 或 validator 与阶段 A accepted hash 不同；
- decision、callback、状态、binding 或 side effect 变化；
- evaluator replay 被用于补齐产品事件；
- T10 两个 Payment 角色发生错误合并；
- RESULT ref 包含 trace 自身；
- 其余 11 项业务投影变化；
- 需要网络、真实支付、WebShop runtime 或外部副作用。

## 9. 当前裁定

本文件只保留条件设计，不构成可执行合同。下一步必须先由 Evaluator 冻结独立 measurement-adapter 任务。