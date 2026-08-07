# Next Capability Slice — Conditional Freeze

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`
Task kind: `capability_experiment`
State: `SUPERSEDED_BY_FROZEN_CONTRACT`
Project map revision: `2026-08-04-r5`
Active bottleneck: `B-03`
Hypothesis: `H-03`
Slice task: `T10`
Trace profile: `WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2`

## 1. 前置条件

```text
prerequisite = measurement adapter accepted
runner hash = cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100
before target output hash = ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488
target fixture hash = f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee
non-trace projection hash = 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
state = SUPERSEDED_BY_FROZEN_CONTRACT
```

正式执行合同已冻结为：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/
CONTRACT.md
```

本文件只保留原条件切片设计，不再作为执行入口。

## 2. 单一产品变量

前置条件满足后，只允许 T10 duplicate-preflight `BLOCKED` 返回的 `WebShopBuyNowGateOutcome` 携带：

```text
ProductAuthoritativeTrace
source = PRODUCT_OBSERVED
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2
events = exact 12
source_bindings = exact 11 unique bindings
```

两个 ORDER event 必须共享同一个 `source_binding_ref`；Action、当前付款候选和历史成功付款分别记录。

## 3. 四类引用

```text
source_object_ref = 对象身份
binding_ref = projection digest
entity_ref = typed profile identity
relation.target_entity_ref = exact target event ref
```

每个 event 只能通过 `source_binding_ref` 解析 binding。禁止 hidden resolver、evaluator replay 和外部 registry。

## 4. BEFORE / AFTER

```text
BEFORE: T10 product_trace_status = NOT_AVAILABLE
AFTER:  T10 product_trace_status = VALID
```

以下业务投影必须不变：

```text
decision = DENY
callback_count = 0
known_payment_attempt_preflight_status = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
```

## 5. Exact 12-event sequence

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
9  KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
10 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
11 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
12 RESULT_RECORDED [FINAL_OUTCOME]
```

## 6. 回滚条件

- runner/validator 不等于阶段 A accepted hash；
- 不是 12 events / 11 unique bindings；
- 两个 Order event 未共享 binding；
- duplicate binding_ref 未判 INVALID；
- Decimal canonicalization 或 source grounding 不一致；
- relation target 不能精确解析；
- decision、callback、状态、binding 或 side effect 变化；
- 需要网络、真实支付、WebShop runtime 或外部副作用。

## 7. 当前裁定

Measurement Adapter 已由 Evaluator 判定 `PASS / NOT_APPLICABLE`。本条件设计已被正式冻结合同取代，不再作为执行入口；执行者只读取 `CURRENT.md` 指向的新 `CONTRACT.md`。
