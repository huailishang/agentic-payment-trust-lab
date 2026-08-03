# Evaluator Review

Task ID: `P9-WEBSHOP-BUY-NOW-RUNTIME-GATE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Final verdict: `REJECTED`

## 1. 裁决

```text
P9-B2 Buy Now Runtime Gate：REJECTED
```

安全边界本身成立：

- `ALLOW` 才调用本地注入 callback，且恰好一次；
- `DENY / CONFIRMATION_REQUIRED / INDETERMINATE` 均为零调用；
- callback 抛异常只尝试一次，不重试，不声称结账成功；
- 没有运行 WebShop、真实 Buy Now、支付、履约、UI 或网络。

但合同同时要求 P2/P3/P4 失配具有可消费的结构化证据。独立复核发现两类 P4 失配虽然正确阻断，却没有暴露实际阻断原因：

```text
p4_stale_wrong_action
p4_value_digest_mismatch
```

两者均得到：

```text
final decision = INDETERMINATE
callback_count = 0
context_policy_status = VALID
reason_codes = p4:context_policy_valid
```

即结果说“P4 有效”，却没有说明是 `current_action` 错误还是 source coverage value digest 与当前请求不一致。安全上没有错误放行，但证据链无法解释裁决，因此 AC-03 / VP-04 不通过。

## 2. 独立复核结果

### AC-01 — explicit facts only

**通过。**

- mandate、Agent、execution、identity、provider/executor refs、ContextPolicyFact 和 callback 均由调用方显式提供；
- request 通过 `replace` 复制后绑定 Agent；
- P9-B1 adaptation 及原 request 未改变；
- 没有从 instruction、商品标题、reward 或页面内容推导授权。

独立证据：`RV-EV-01.*`、`RV-EV-02.*`。

### AC-02 — P1 pre-payment validation

**通过。**

独立重建确认：

- 限制性 mandate：`DENY`，callback 0；
- 过期 confirmation：`CONFIRMATION_REQUIRED`，callback 0；
- confirmation 缺失：`INDETERMINATE`，callback 0；
- P1 非 `ALLOW` 时没有生成 runtime gate record。

独立证据：`RV-EV-01.*`、`RV-EV-02.*`。

### AC-03 — P2 / P3 / P4 runtime gate composition

**不通过。**

实现确实复用了现有 `observe_payment_execution_gate`，没有复制 P2/P3/P4 决策规则；P2/P3 的失配原因也可追溯。

但共享 Runtime Gate 对以下 P4 合同失配只返回 `INDETERMINATE`，没有生成对应因果 reason code：

1. `current_action != execute_payment`；
2. `source_coverage` 的 value digest 与当前 request 不一致。

`RuntimeGateRecord` 只保留 `context_policy_status=VALID` 和 `context_policy_valid`，也不携带 current action、coverage 或 digest 差异，因此下游无法从结构化结果判断为何阻断。

独立证据：`RV-EV-01.*`、`RV-EV-07.*`；执行者自己的矩阵 `EV-02.runtime_mismatch_matrix.json` 也复现该问题。

### AC-04 — callback side-effect boundary

**通过。**

- 最终 `ALLOW`：callback 1 次；
- 所有非 `ALLOW`：callback 0 次；
- callback 异常：实际尝试 1 次、无自动重试、`checkout_executed=false`、最终 `INDETERMINATE`。

独立证据：`RV-EV-01.*`、`RV-EV-02.*`。

### AC-05 — realistic WebShop boundary examples

**通过。**

固定 `877.80 USD / home_furniture` console table：

- `max_amount=30` 且仅允许 clothing 时得到 `DENY`；
- 显式许可且 P1—P4 全部匹配时得到 `ALLOW`，本地 callback 1 次。

这证明“到达 Buy Now”不会自动等价为允许购买。

独立证据：`RV-EV-01.*`。

### AC-06 — dependency and side-effect boundary

**通过。**

生产模块没有文件、网络、进程、环境变量、WebShop、浏览器或 UI 依赖；`models.py`、`validator.py` 和 P9-B1 文件未修改。

独立证据：`RV-EV-03.*`、`RV-EV-06.*`。

### AC-07 — tests and regressions

**通过。**

```text
Runtime Gate 专项：14/14 PASS
完整 unittest：336/336 PASS
正式入口：13/13 PASS
```

独立证据：`RV-EV-02.*`、`RV-EV-04.*`、`RV-EV-05.*`。

测试全绿不能覆盖本次证据语义缺口，因为现有测试只断言 P4 失配被阻断，没有断言 reason code 能解释阻断原因。

### AC-08 — roadmap and handoff consistency

**通过。**

- HEAD 与基线一致；
- 核心文件哈希与执行报告一致；
- 工作流 validator 为 `OK`；
- 没有 commit 或 push；
- P9-C、P9-D、P9-E 未开始。

独立证据：`RV-EV-06.*`。

## 3. VP 裁决

| VP | 结果 | 独立依据 |
|---|---|---|
| VP-01 permissive mandate + fake callback | PASS | `RV-EV-01` |
| VP-02 restrictive fixture mandate | PASS | `RV-EV-01` |
| VP-03 confirmation and indeterminate matrix | PASS | `RV-EV-01` |
| VP-04 P2/P3/P4 mismatch matrix | **FAIL**：两类 P4 阻断无因果 reason | `RV-EV-01`、`RV-EV-07` |
| VP-05 callback exception / no retry | PASS | `RV-EV-01` |
| VP-06 static imports / side-effect audit | PASS | `RV-EV-03`、`RV-EV-06` |
| VP-07 runtime-gate tests | PASS | `RV-EV-02` |
| VP-08 full regression / formal entrypoint | PASS | `RV-EV-04`、`RV-EV-05` |
| VP-09 scope / hash / workflow | PASS | `RV-EV-06` |

## 4. 为什么必须修

后续 P9-E UI 要从轨迹生成购买各环节展示。当前结果只能显示：

```text
P4 = VALID
最终 = INDETERMINATE
```

却不能显示：

```text
当前动作不是 execute_payment
或
可信来源摘要绑定的是另一个金额
```

这会让普通用户和评估者无法判断系统为什么停止，也会使 P5 Evidence / Replay 的结构化裁决事实不完整。

## 5. 明确未发现的问题

本次没有发现：

- 错误放行；
- 非 ALLOW 调用 callback；
- callback 自动重试；
- 原 adaptation 被修改；
- WebShop、Buy Now、支付、履约、UI、网络或环境副作用；
- commit 或 push。

## 6. 后续路由

修复任务：

```text
P9-WEBSHOP-RUNTIME-GATE-REASON-EVIDENCE-REPAIR-V1
```

修复目标不是新增规则，而是让共享 Runtime Gate 对每个阻断分支生成明确、稳定、机器可读的 gate reason，并由 WebShop outcome 原样消费。

下一合同：

```text
docs/05_任务交接/P9_WEBSHOP_RUNTIME_GATE_REASON_EVIDENCE_REPAIR_V1/CONTRACT.md
```
